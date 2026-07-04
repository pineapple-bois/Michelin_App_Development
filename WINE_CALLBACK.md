# Wine map callback audit

Date: 4 July 2026

## Scope

This is a fact-finding report. No Wine callback, map, layout, data, or styling behaviour was changed.

The audit covers:

- the payload used to initialise and navigate the Wine map;
- every callback that writes to `wine-map-graph.figure`;
- the interaction between region selection, appellation selection, `uirevision`, `relayoutData`, and `map-view-store`;
- whether Alsace and Corse indicate bad source coordinates, bad viewport calculations, or a more general callback-ordering problem;
- systematic options that do not require region-specific rules.

The state-ownership approach in the second part of `Development/documents_plans/MAP_ZOOM.md` remains sound: a geographic selection must take precedence over stale persisted viewport state, and persisted state must belong to a named geography. The Wine implementation now follows that principle on the server. That principle does not, however, guarantee the order in which multiple browser-side Plotly updates finish.

## Executive finding

The evidence does **not** support an Alsace-specific CRS defect.

- The deployed Wine geometry is EPSG:4326, which is the coordinate system expected by Plotly MapLibre.
- `Brand` has valid coordinates in Alsace. Its current bounding-box anchor is within approximately 120 metres of its projected geometric centroid.
- The server-side navigation helper returns the expected centre and zoom for both Alsace and Brand.
- A navigation patch is only a few hundred bytes and contains the expected `uirevision`, `map.center`, and `map.zoom` operations.

The observed sequence is more consistent with a **stale navigation command being rendered after a newer selection**:

1. Alsace is selected, starting a regional navigation update.
2. Brand is selected while the regional update is still being delivered or rendered.
3. The older Alsace viewport becomes visible while the control already displays Brand.
4. A later appellation selection supplies another command and the map appears to correct itself.

This explains why the map can look one interaction behind even though each isolated server payload is correct. It also explains why custom Alsace rules have not solved the problem.

Alsace and Corse are useful stress cases, not exceptional cases requiring patches:

- they are spatially detached or fragmented;
- a late regional view is visually very different from a close appellation view;
- their geometry makes the weaknesses of the current regional bounding-box anchor more obvious.

The most reliable direction is therefore:

1. **Region selection filters and highlights; it does not navigate the viewport.**
2. **Appellation selection is the only selector-driven viewport command.**
3. **One viewport owner applies only the command matching the currently selected appellation.**
4. **The appellation anchor is calculated as a projected centroid, not a longitude/latitude bounding-box midpoint.**

This removes the region/appellation command race rather than attempting to tune it region by region.

## Current data and map structure

`app/utils/wine_figures.py::plot_wine_choropleth_plotly()` constructs one Plotly MapLibre figure containing:

- one `Choroplethmap` trace with all 347 appellation features;
- three initially hidden `Scattermap` restaurant traces;
- one regional-outline MapLibre layer;
- metropolitan-France bounds;
- a France-wide initial centre and zoom;
- `layout.map.uirevision`.

The graph has no initial `figure` in `app/layouts/wine.py`. Its full figure is supplied after the `/wine` route callback runs.

### Measured payload

Measurements were made by serialising the current production figure and current Dash `Patch` objects.

| Payload | Approximate size |
|---|---:|
| Complete initial figure, JSON | 3,623,595 bytes |
| Complete initial figure, gzip | 1,373,381 bytes |
| Appellation GeoJSON within the figure | 3,266,090 bytes |
| Regional-outline GeoJSON within the figure | 221,628 bytes |
| Alsace navigation patch | 365 bytes |
| Brand navigation patch | 431 bytes |

The navigation payload is not intrinsically too large. The expensive operation is the initial figure transfer and browser render. The current `wine-map-ready=True` flag is returned in the same server response as that full figure; it confirms that the server produced the figure, not that the browser has completed Plotly/MapLibre rendering.

## Figure writers

There are five independent callback registrations that write to `wine-map-graph.figure`.

| Writer | Trigger | Figure path changed |
|---|---|---|
| Initialiser | `/wine` pathname | Entire figure |
| Navigator | region, appellation, or `wine-map-ready` | `layout.map.uirevision`, `center`, and `zoom` |
| Regional-outline toggle | outline button | `layout.map.layers[0].visible` |
| Restaurant overlay/filter | overlay and rating buttons | restaurant trace visibility and `below` |
| Hover highlighter | `hoverData` and unhover | appellation trace `selectedpoints` |

The patch writers mostly address different subtrees, so a simple field overwrite is not the only concern. The fragility is that every update still targets the same Plotly figure and the callback graph contains no browser-render barrier or latest-command check.

`clear_on_unhover=True` also means ordinary pointer movement can generate additional figure patches while navigation is being rendered.

## Current navigation path

### Server calculation

`wine_navigation_patch()` performs the following work:

1. Validate the selected appellation against the selected region.
2. Choose either `map_view_for_feature()` or `map_view_for_region()`.
3. Generate a geography-specific `uirevision`.
4. Patch `layout.map.center` and `layout.map.zoom`.

This calculation is deterministic in isolation.

### Parallel state update

The same region and appellation controls independently trigger `store_map_view()`.

That callback correctly gives a selector trigger precedence over `relayoutData`, records the owning geography, and rejects a later relayout payload belonging to another geography. This protects persisted state and page reconstruction.

It does **not** order or cancel a navigation patch already in flight. `map-view-store` is not an input to the navigation callback and does not act as a command sequence number.

### Browser application

The current effective sequence is:

```text
selector value
  +--> navigation callback --> figure Patch --> Plotly/MapLibre render
  |
  +--> viewport-store callback --> map-view-store
  |
  +--> appellation-options callback when region changes

Plotly/MapLibre render --> relayoutData --> viewport-store callback
```

There is no contract at the final render step saying “apply this only if these selector values are still current.” A correct but older regional command can therefore become visible after the user has selected an appellation.

## Why Alsace is pronounced

The current regional target is calculated by merging every feature bounding box assigned to the region and taking the midpoint of the resulting longitude/latitude rectangle. It is not the centroid of the union.

Alsace contains 55 feature rows and a fragmented union. The group includes detached north-eastern features such as Moselle and Côtes de Toul as well as the main north-south Alsace strip. Consequently:

- current bounding-box centre: approximately `48.6287, 6.8865`;
- projected union centroid: approximately `48.3037, 7.3053`;
- separation: approximately 47.6 km.

The regional view is therefore a broad classification extent, not an anchor on the familiar Alsace strip. If that regional command arrives late, it looks dramatically wrong for Brand.

Corse is also fragmented by island and appellation geometry. Its bounding-box midpoint is approximately 12.9 km from its projected union centroid. The symptom is less about that numerical distance than the fact that any stale mainland or France-wide view is immediately obvious when the selected control says Corse.

Other regions prove this is a generic geometry issue:

| Region | Bounding-box midpoint to projected union centroid |
|---|---:|
| Loire | 74.6 km |
| Rhône | 49.0 km |
| Alsace | 47.6 km |
| Bourgogne | 28.2 km |
| Savoie | 22.1 km |
| Corse | 12.9 km |

No region-specific correction can make a bounding-box midpoint a reliable semantic centre for every disconnected wine classification.

## Appellation anchors

Appellations currently use the midpoint of their WGS84 bounds. The zoom is derived from the larger of longitude span and a scaled latitude span, with fixed padding and a clamp from 5.0 to 11.5.

This is a useful approximation, but it is not the requested centroid contract and it does not use the rendered map's pixel dimensions.

For Brand:

- bounds: approximately `7.26867–7.28439 E`, `48.08626–48.09501 N`;
- current anchor: approximately `48.09064, 7.27653`;
- projected centroid: approximately `48.09118, 7.27543`;
- difference: approximately 120 metres.

Brand's source geometry and isolated server target are therefore credible. A Brand view around Gérardmer is evidence that the wrong navigation state was rendered, not evidence that Brand's coordinates use another reference system.

For a systematic appellation implementation:

- calculate the centroid after projecting the geometry to a metric CRS such as Lambert-93 (`EPSG:2154`);
- transform the centroid back to EPSG:4326 for MapLibre;
- calculate framing separately from the anchor;
- if every polygon must remain visible, derive zoom from full bounds or use a browser-side `fitBounds` operation;
- decide explicitly whether a centroid outside a highly concave or multipart polygon is acceptable. If the anchor must lie inside the feature, use `representative_point()` instead and name that contract honestly.

## Reliability findings

### 1. Geography-owned persistence is necessary but insufficient

The `MAP_ZOOM.md` state-ownership pattern prevents stale stored viewports from winning during a figure rebuild. Wine now has that protection. The reported defect persists because the remaining risk is after the server chooses the right target: delivery and rendering of successive commands.

### 2. “Map ready” is not render ready

`initialize_wine_map()` returns the 3.62 MB figure and `wine-map-ready=True` together. The readiness value can trigger navigation once Dash has accepted the response, but it is not tied to Plotly's `afterplot` or MapLibre's settled state. The name currently promises more than the signal proves.

### 3. Navigation has no freshness identity

`uirevision` identifies geography for Plotly state semantics, but it is not a monotonic command ID and it does not make an older response invalid. There is no check immediately before application that the patch's region and feature ID still equal the controls' current values.

### 4. Region and appellation share one navigation channel

A region choice and the immediately following appellation choice both invoke the same navigator. A late region result can therefore overwrite the more specific appellation result. Removing regional zoom eliminates this entire class of collision.

### 5. The selected appellation is not cleared when the region changes

Changing region filters the appellation options, but no callback writes `wine-appellation-search.value`. The server safely ignores an appellation that does not belong to the selected region, yet the control and navigation state can temporarily describe different geographies. This is another reason to define an explicit region/appellation state transition rather than relying on independent control values.

### 6. Several duplicate-output patches share the figure

Hover, restaurant visibility, outlines, navigation, and initialisation all write the figure. Their paths are mostly disjoint, but the architecture makes callback completion order part of correctness. A future patch that touches layout more broadly could reintroduce viewport loss without an obvious local error.

### 7. Bounds are not the root cause

Metropolitan bounds remain present in the full figure and are not removed by the current patches. They constrain legal movement; they do not generate the wrong Brand coordinates. They may make an invalid or stale command more visually obvious, just as in the earlier Guide investigation.

## Existing test coverage and its limit

The current Wine tests cover useful pure contracts, including:

- geography validation;
- region and feature view calculation;
- navigation patch structure;
- geographic reset taking precedence over stale stored state;
- stale `relayoutData` rejection;
- preservation of a manual viewport for the current geography;
- callback separation between search/navigation and OpenAI content;
- the absence of a callback that clears appellation value;
- hover, regional-outline, and restaurant patch behaviour.

These tests prove that isolated server functions return the intended payload. They do not exercise:

- two selector changes while an earlier Plotly update is still rendering;
- whether `wine-map-ready` corresponds to an actual completed plot;
- out-of-order or delayed callback responses;
- the final MapLibre centre after Dash applies several duplicate-output patches;
- a narrow viewport's effect on the bounds-to-zoom approximation.

No browser network/render trace was captured during this audit, so the late-command explanation remains a strongly supported diagnosis rather than a directly timestamped proof. The next prototype should add temporary development-only command logging or an end-to-end test that records selector value, command identity, `uirevision`, and final Plotly centre in sequence.

The existing test suite was run after the audit: **165 tests passed**. No application or test code was changed.

## Options

### Option A — region filters/highlights; appellation alone navigates

**Recommended.**

Region selection would:

- filter the appellation options;
- optionally highlight the matching region features;
- leave the user's viewport unchanged.

Appellation selection would:

- emit the sole selector-driven viewport command;
- zoom to the selected appellation's projected centroid;
- frame its full geometry using a generic rule;
- reject any command whose feature ID is no longer the dropdown's current value.

Advantages:

- removes the region/appellation viewport race;
- avoids misleading centres for disconnected regional classifications;
- preserves useful regional context through highlighting;
- requires no region-specific exceptions;
- gives “region” and “appellation” distinct, understandable roles.

Important implementation detail: the existing hover effect owns the AOC trace's `selectedpoints`. Regional highlighting must not independently write the same property. Either consolidate hover and regional highlight into one selection-state owner or use a separate outline/mask layer for the regional highlight.

### Option B — retain regional navigation with generic geometry fitting

If regional zoom is considered essential:

- fit the union bounds generically in Web Mercator or through MapLibre `fitBounds`;
- remove the fixed `REGION_SELECTION_ZOOM_BOOST`;
- use one navigation controller for both region and appellation;
- attach a command identity and discard stale commands at application time;
- do not add Alsace, Corse, or other regional constants.

This can produce better regional framing, but it keeps the higher-risk competition between broad and specific navigation commands.

### Option C — rebuild the complete figure on each selection

This would make one server callback the obvious figure authority, but each selection would resend roughly 3.62 MB of JSON and ask Plotly to rebuild the full geometry. It is deterministic in Python and expensive in the browser. It is not recommended.

### Option D — retain the current patch model and add more readiness flags

The payload remains small, but another server-side boolean does not prove that Plotly has finished rendering and does not invalidate older commands. Timing delays and retries would mask rather than define the state transition. This is not recommended.

## Proposed target callback contract

The safest next prototype is a small state-machine change, not another zoom constant.

1. The full Wine figure is initialised once.
2. Region selection updates appellation options and a dedicated regional-highlight state only.
3. Changing region explicitly resolves what happens to an existing appellation value: normally clear it as part of the same state transition.
4. Appellation selection creates a navigation command containing at least:
   - feature ID;
   - projected centroid transformed to WGS84;
   - framing bounds or zoom;
   - a command identity or current-value guard.
5. A single viewport executor applies the command only if its feature ID still matches the selected appellation.
6. Programmatic navigation and manual `relayoutData` remain distinct events.
7. Manual pan/zoom is persisted only after the current appellation command owns the viewport.
8. Hover, restaurant, and outline updates remain unable to write viewport fields.

The executor could be implemented as one consolidated server callback or as a small clientside controller. A clientside controller has the strongest access to actual graph readiness and MapLibre fitting, but it should be event-driven and freshness-checked—not delay-driven.

## Validation required for the next prototype

The next change should not be accepted on isolated centroid tests alone. It should record or assert the final rendered centre for:

1. Fresh `/wine` load, immediately select Alsace, then Brand.
2. Fresh load, immediately select Corse, then a Corsican appellation.
3. Rapid region-to-appellation selection.
4. Rapid appellation-to-appellation selection.
5. Manual pan/zoom, then change region when regional navigation is disabled.
6. Manual pan/zoom, then select an appellation.
7. Hover/unhover during or immediately after navigation.
8. Toggle outlines and restaurant overlays before and after navigation.
9. Repeat at a narrow viewport.
10. Navigate away from `/wine`, return, and verify persisted state ownership.

The critical assertion is not merely “the callback returned the right patch.” It is:

> After the system settles, the rendered map centre belongs to the appellation currently displayed in the dropdown, and no older regional or appellation command can replace it.

## Recommendation

Prototype Option A first: disable viewport navigation on regional selection, use region selection for filtering and a restrained highlight, and make appellation selection the only selector-driven zoom operation.

At the same time, replace the appellation bounding-box midpoint with a projected centroid and make the viewport executor reject stale feature IDs. This addresses both identified classes of weakness:

- unreliable callback/render ordering;
- imprecise spatial anchoring.

It does so with one general contract for all regions and appellations, including Alsace and Corse.
