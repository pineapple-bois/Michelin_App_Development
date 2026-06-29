# Wine map integration roadmap

This is the authoritative Wine integration document. `WINE_REPORT.md` was the
temporary architecture investigation report; its durable findings have been
folded into this roadmap.

## Current state

The Wine page now renders `assets/data/wine_regions_aoc.geojson` as the
production Wine geography. The AOC dataset loads successfully, each feature has
a deterministic in-memory `feature_id`, and the map uses one feature-based
Plotly trace rather than one trace per polygon part. The current checked-out
asset loads 348 AOC features.

The current implementation deliberately keeps generated Wine content
region-level:

```text
AOC click location -> server-side feature_id lookup -> parent region
                  -> generate_optimized_prompt(parent region)
                  -> wine_info_<parent region> cache
```

The `app` appellation field is retained for hover, feature identity, and future
functionality, but it does not yet change OpenAI prompts or cache keys.

Retained Wine page state:

* `map-view-store` remains in place because Wine `relayoutData` still writes
  pan/zoom state and the base Wine figure callback still reads it when the page
  is rebuilt.

Overlapping AOCs are now visible as a separate data and interaction-design
issue. They are outside the immediate renderer-restoration phase and will be
handled separately from the overlay work.

## Completed

### AOC loading and validation

Completed in `app/app_data.py`:

* load `assets/data/wine_regions_aoc.geojson`;
* require `region`, `app`, `colour`, and `geometry`;
* preserve CRS, required-value, missing-geometry, and empty-geometry checks;
* support only `Polygon` and `MultiPolygon`;
* validate `(region, app)` uniqueness;
* generate deterministic `feature_id` values from `(region, app)`;
* validate generated feature-ID uniqueness;
* validate that each parent region has exactly one colour;
* keep individual AOC features rather than dissolving by parent region.

### Architecture investigation and renderer decision

Completed by investigation and implementation:

* inspected the installed stack: Dash `2.18.2`, Plotly.py `5.24.1`, and
  Plotly.js `2.35.2`;
* confirmed the current MapLibre-style `map` subplot and `carto-positron` style
  are compatible with `go.Choroplethmap`;
* measured and rejected the old geometry-part `Scattermap` renderer;
* selected the single-trace `go.Choroplethmap` architecture;
* determined that no new mapping dependency is justified.

Historical renderer finding:

* the old renderer expanded AOC geography into one trace per exterior geometry
  part plus interior-ring traces;
* it produced 4,804 Wine geography traces in the architecture-report
  measurement;
* the old `curveNumber -> trace-list position -> dataframe row` identity model
  was unsafe and was removed;
* old curve-number semantics were already broken for the AOC dataset because
  geometry-part order diverged from dataframe row order.

### Production vertical slice

Completed in the application:

* replaced the Wine geography with one `go.Choroplethmap`;
* use the complete AOC FeatureCollection as the trace `geojson`;
* use `featureidkey="properties.feature_id"`;
* use generated feature IDs for `locations` and `ids`;
* include `[region, app, feature_id]` in `customdata`;
* show appellation and parent region in hover;
* preserve existing parent-region colours through a categorical stepped
  colorscale;
* hide the colour bar;
* preserve the `carto-positron` map style and initial France viewport;
* set stable `layout.map.uirevision`;
* resolve Wine clicks from `clickData["points"][0]["location"]`;
* fail closed for missing, malformed, restaurant, or unknown feature IDs;
* continue passing only the parent region to the existing prompt;
* preserve the explicit `wine_info_<region>` cache;
* remove callback-level memoization from the Wine information callback;
* remove `wine-region-curve-numbers` and its layout store.

### Tests and smoke validation

Completed coverage:

* loader tests for deterministic feature IDs, feature-ID uniqueness,
  `(region, app)` uniqueness, supported geometry types, and one colour per
  parent region;
* figure tests for one Wine geography trace, one location per loaded AOC,
  stable feature IDs, semantic hover customdata, hidden colour bar, and the
  expected `map` subplot;
* callback resolution tests for valid, missing, non-AOC, and unknown feature IDs;
* layout tests confirming the obsolete curve-number store is absent.

Measured outcome:

| Measurement                          |          Result |
|--------------------------------------|----------------:|
| AOC features currently loaded        |             348 |
| Polygon features                     |             178 |
| MultiPolygon features                |             170 |
| Total geometry parts in source data  |           7,309 |
| Interior rings in source data        |             606 |
| Approximate vertices in source data  |          60,115 |
| Historical old Wine geography traces |           4,804 |
| New Wine geography traces            |               1 |
| Current total Wine map traces         |               4 |
| Old server-side construction time    |  approx. 1.29 s |
| Current median construction time     | approx. 0.376 s |
| Current serialized figure size       | approx. 2.78 MB |
| Test suite                           |       74 passed |

Browser smoke result:

* the AOC map renders quickly;
* hover shows appellation and parent region;
* `clickData` registration was verified at the browser level;
* no browser warnings or errors were observed.

This smoke test did not claim complete live OpenAI click-through, mobile
behaviour, or overlapping-AOC interaction behaviour.

### Phase A: live region-level click path

Completed with automated callback tests and manual browser verification against
a local fake OpenAI-compatible endpoint.

Automated tests now verify:

* a valid AOC feature ID resolves through `location` to the expected parent
  region;
* two different Bourgogne AOCs resolve to the same parent region;
* the second Bourgogne AOC reuses the same explicit `wine_info_Bourgogne` cache
  entry;
* an AOC in another parent region uses a different cache key;
* missing, malformed, unknown, restaurant-style, and other non-AOC payloads fail
  closed;
* failed payloads do not invoke OpenAI or request-limit accounting;
* cached responses do not invoke OpenAI or request-limit accounting;
* request-limit accounting occurs only for a valid, uncached AOC click.

Manual browser verification used real map clicks on:

* Beaujolais -> parent region `Bourgogne`;
* Bourgogne -> parent region `Bourgogne`;
* Crémant d’Alsace -> parent region `Alsace`.

Observed result:

* the displayed parent-region heading was correct for Bourgogne and Alsace;
* generated content remained parent-region level;
* the second Bourgogne AOC reused the existing regional response;
* switching to Alsace produced a separate regional response;
* no browser console warnings, browser console errors, or Dash callback errors
  were observed.

Caveat: the browser run used a local fake OpenAI-compatible endpoint, not the
real OpenAI service. Cache reuse was directly observed through the fake endpoint
request counts and the server-side cache hit; external API availability and
real-account authentication were not tested.

### Phase B: regional outlines

Completed in the application:

* regional outlines are restored as a non-interactive `layout.map.layers` line
  layer;
* the outline layer uses existing regional geometry rather than rebuilding the
  AOC choropleth;
* the outline dropdown toggles only `layout.map.layers[0].visible` via Dash
  `Patch`;
* the Wine geography remains one `Choroplethmap` trace.

Automated tests cover the outline layer contract, visibility patch, enabled
outline control, and restaurant control state. Browser smoke confirmed selection
and clearing work without browser console warnings or errors.

### Phase C: restaurant overlays

Completed in the application:

* restored three fixed `go.Scattermap` restaurant traces in the base Wine
  figure;
* preserved the previous one-, two-, and three-star marker colours and
  restaurant hover content;
* gave each restaurant trace explicit metadata:
  `{"kind": "restaurant", "stars": <1|2|3>}`;
* re-enabled the Wine restaurant overlay button;
* kept the star filter hidden until restaurants are shown;
* toggled restaurant visibility with Dash `Patch` assignments to trace
  `visible` values only;
* preserved the AOC click contract and region-level OpenAI/cache behaviour;
* made restaurant-style click payloads fail closed without invoking OpenAI,
  incrementing request-limit accounting, or replacing existing Wine-region
  content.

Final trace order:

```text
0: Choroplethmap — Wine appellations
1: Scattermap — one-star restaurants
2: Scattermap — two-star restaurants
3: Scattermap — three-star restaurants
```

Initial restaurant visibility is `False` for all three restaurant traces.

Automated tests cover the fixed trace structure, stable restaurant identities,
initial visibility, visibility-only patches, restaurant click fail-closed
behaviour, AOC click preservation, and regional-outline patch behaviour.

Browser verification for star-filter combinations, map-view preservation while
toggling, AOC clicks while restaurants are visible, restaurant clicks,
coexistence with regional outlines, and browser/Dash console output is left for
manual user verification.

### Phase D: code cleanup

Completed in the application:

* removed the obsolete `selected-stars-wine` layout store;
* retained `map-view-store` because it still has an active runtime purpose:
  `store_map_view` writes map pan/zoom from `relayoutData`, and the base Wine
  figure callback reads it when constructing the figure;
* removed active roadmap language that treated restored outline or restaurant
  controls as temporary disabled scaffolding.

`selected-stars-wine` was removed because no callback read or wrote the store;
restaurant visibility derives from the current overlay button state and star
filter button click state.

Responsive and mobile verification remains manual user work; it is not covered
by the current automated tests.

## Current data and callback contract

### Feature identity

The source asset is not modified. The loader generates:

```text
aoc-<sha256(region + NUL + app)>
```

The generated ID is stable across restarts and independent of dataframe order,
feature order, trace order, geometry-part order, or coordinate changes.

### Figure trace contract

The Wine geography trace is:

```text
type: choroplethmap
subplot: map
featureidkey: properties.feature_id
locations: [feature_id, ...]
ids: [feature_id, ...]
z: numeric parent-region colour code
customdata: [[region, app, feature_id], ...]
showscale: false
```

Hover displays:

```text
Appellation: <app>
Parent region: <region>
```

### Click contract

The Wine callback consumes only:

```text
clickData.points[0].location
```

It resolves that value through the server-side `feature_id -> region/app/colour`
lookup. Positional Plotly fields such as `curveNumber`, `pointNumber`,
`pointIndex`, dataframe row position, and trace order are not trusted.

Non-AOC payloads fail closed and must not invoke OpenAI.

## Next: manual responsive and mobile verification

Renderer selection, live region-level click-path verification, regional-outline
restoration, restaurant-overlay restoration, and code cleanup are complete.
Responsive and mobile testing remains a manual verification task.

## Future work

Keep these separate from the immediate renderer and overlay phases:

* overlapping AOC organisation and hit-testing;
* appellation-specific OpenAI content;
* AOC search or selection state;
* multi-resolution geometry;
* visual redesign and broader Wine content modernisation;
* migration to a new mapping library, unless the current Plotly stack is later
  shown to be unsuitable.

## Risks and watch points

* A single trace still sends a multi-megabyte GeoJSON-backed figure; monitor
  browser responsiveness on slower devices.
* Overlapping polygons may make only the topmost AOC selectable at shared
  coordinates.
* Regional layer ordering must not interfere with AOC hover or click targets.
* Restaurant traces must be semantically rejected by the Wine information
  callback.
* Dash `Patch` behaviour should be tested across Dash Page unmount/remount.
* Real OpenAI service availability and authentication still need a production or
  credentialed environment check; Phase A intentionally used a fake local
  endpoint.

## Obsolete architecture removed from active work

Do not reintroduce:

* one trace per polygon or geometry part;
* Wine interior-ring traces used solely by the old renderer;
* `wine-region-curve-numbers`;
* curve-number membership checks;
* dataframe-row lookup through trace-list position;
* callback-level memoization keyed by raw click payloads;
* renderer optimisation work aimed at salvaging the old `Scattermap` trace
  architecture.
