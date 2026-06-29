# Wine map integration roadmap

This is the authoritative Wine integration document. `WINE_REPORT.md` was the
temporary architecture investigation report; its durable findings have been
folded into this roadmap.

## Current state

The Wine page now renders `assets/data/wine_regions_aoc.geojson` as the
production Wine geography. The AOC dataset loads successfully, each feature has
a deterministic in-memory `feature_id`, and the map uses one feature-based
Plotly trace rather than one trace per polygon part.

The current implementation deliberately keeps generated Wine content
region-level:

```text
AOC click location -> server-side feature_id lookup -> parent region
                  -> generate_optimized_prompt(parent region)
                  -> wine_info_<parent region> cache
```

The `app` appellation field is retained for hover, feature identity, and future
functionality, but it does not yet change OpenAI prompts or cache keys.

Temporarily disabled UI:

* regional-outline controls are disabled until outlines are restored as
  separate non-interactive map layers;
* restaurant overlay controls are disabled until restaurant traces are restored
  as separate overlays;
* `selected-stars-wine` and `map-view-store` remain in place for compatibility
  while overlay restoration and view-persistence behaviour are tested.

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
* it produced 4,804 Wine geography traces for the AOC asset;
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
* figure tests for one Wine geography trace, 354 locations, stable feature IDs,
  semantic hover customdata, hidden colour bar, and the expected `map` subplot;
* callback resolution tests for valid, missing, non-AOC, and unknown feature IDs;
* layout tests confirming the obsolete curve-number store is absent.

Measured outcome:

| Measurement | Result |
|---|---:|
| AOC features | 354 |
| Polygon features | 192 |
| MultiPolygon features | 162 |
| Total geometry parts in source data | 3,628 |
| Interior rings in source data | 1,176 |
| Approximate vertices in source data | 58,817 |
| Old Wine geography traces | 4,804 |
| New Wine geography traces | 1 |
| Old server-side construction time | approx. 1.29 s |
| New median construction time | approx. 0.309 s |
| New serialized figure size | approx. 2.46 MB |
| Test suite | 36 passed |

Browser smoke result:

* the AOC map renders quickly;
* hover shows appellation and parent region;
* `clickData` registration was verified at the browser level;
* no browser warnings or errors were observed.

This smoke test does not claim complete live OpenAI click-through, mobile
behaviour, or overlapping-AOC interaction behaviour.

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

## Next: restore overlays incrementally

The next active phase is overlay restoration, not renderer selection.

### Phase A — verify live region-level click path

* Manually verify one complete live AOC click through:
  `location -> server lookup -> parent region -> regional cache/OpenAI output`.
* Verify repeated AOCs in the same parent region reuse region-level prompt and
  cache behaviour.
* Confirm request-limit behaviour still applies only when an OpenAI request is
  actually needed.

### Phase B — restore regional outlines

* Restore regional outlines as a non-interactive `layout.map.layers` line layer.
* Toggle outline visibility without rebuilding or resending the AOC geography.
* Preserve pan and zoom while toggling outlines.
* Ensure outline layers do not obscure AOC hit testing.

### Phase C — restore restaurant overlays

* Restore the three fixed restaurant `Scattermap` traces.
* Use Dash `Patch` or an equivalent visibility-only update so restaurant filter
  changes do not reconstruct the static AOC geography.
* Ensure restaurant clicks cannot invoke the Wine OpenAI callback.
* Re-enable restaurant controls only when the restored interaction is covered.

### Phase D — cleanup and responsive verification

* Remove temporary disabled-control scaffolding and compatibility comments.
* Review whether `map-view-store` remains necessary after route remount and
  `uirevision` testing.
* Review whether `selected-stars-wine` remains necessary after restaurant
  overlay restoration.
* Complete responsive and mobile testing.

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
* Region-level OpenAI cache reuse must be manually verified with live clicks
  before treating the full click-to-content path as complete.

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
