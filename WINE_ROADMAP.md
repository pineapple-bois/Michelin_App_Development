# Wine GeoJSON Integration Roadmap

## Objective

Replace assets/data/wine_regions_cleaned.geojson with assets/data/wine_regions_aoc.geojson as the Wine page’s source of truth.

Preserve the current parent-region experience initially while retaining the new app appellation field for hover content and future interactions.

The work should be staged so that data loading, runtime measurement, renderer changes, and callback changes can be assessed independently.

⸻

## Phase 1 — Load and validate the new asset

### Scope

Modify only the Wine data-loading path in `app_data.py`.

### Changes

1. Replace:

```text
wine_regions_cleaned.geojson
```

with:

```text
wine_regions_aoc.geojson
```

2. Update the required Wine columns from:

```text
("region", "colour", "geometry")
```

to:

```text
("region", "app", "colour", "geometry")
```

3. Add lightweight Wine-specific validation:

* CRS exists;
* geometry is converted to EPSG:4326 when necessary;
* no null geometries;
* no empty geometries;
* region, app, and colour contain no null values;
* geometry types are supported by the current renderer;
* all AOCs under the same parent region use a consistent colour.

4. Do not:

* dissolve by region;
* explode geometries unless required by the loader;
* simplify geometry;
* reorder features intentionally;
* modify Wine rendering;
* modify callbacks;
* modify OpenAI prompt behaviour.

Tests

Add or update tests covering:

* the new filename;
* the required app property;
* missing required columns;
* null or empty geometry rejection;
* CRS conversion or rejection;
* inconsistent parent-region colours.

### Commit boundary

Commit this phase separately.

Suggested commit message:
```text
Load and validate AOC wine GeoJSON
```

⸻

## Phase 2 — Run the existing architecture unchanged

After committing Phase 1, run the application without attempting to fix the renderer pre-emptively.

Record the following

Dataset measurements

* GeoJSON file size;
* feature count;
* unique region count;
* unique app count;
* Polygon count;
* MultiPolygon count;
* total polygon-part count;
* number of interior rings;
* invalid or empty geometry count.

Server-side measurements

* application startup time;
* memory use after loading;
* Wine figure construction time;
* figure serialisation time;
* callback response size;
* number of generated Plotly traces.

Browser behaviour

* initial Wine page load time;
* time until the map becomes interactive;
* pan and zoom responsiveness;
* hover responsiveness;
* click responsiveness;
* behaviour when regional outlines are toggled;
* behaviour when restaurants are enabled;
* behaviour when star filters change;
* browser console warnings or errors.

Functional behaviour

Test clicks on:

* a simple Polygon AOC;
* several AOCs within the same parent region;
* each part of a MultiPolygon feature;
* an area containing an interior ring;
* a Wine feature after outlines are toggled;
* a Wine feature after restaurant traces are added.

Expected risks

The current implementation may show:

* excessive trace count;
* large Dash callback payloads;
* slow browser rendering;
* repeated geometry rebuilding;
* incorrect curveNumber resolution;
* clicks resolving to the wrong parent region;
* rejected clicks on interior traces;
* poor responsiveness after controls change.

Document actual behaviour before choosing the replacement architecture.

Commit boundary

Do not commit runtime experiments unless instrumentation or tests are deliberately added.

⸻

## Phase 3 — Define the renderer rewrite

Use the measurements from Phase 2 to decide whether the existing Plotly trace architecture is viable.

Required architectural outcomes

The replacement must:

* stop deriving Wine identity from curveNumber;
* attach region and app directly to rendered features;
* preserve parent-region click behaviour;
* make app available for hover content;
* distinguish Wine geometry from restaurant and outline traces semantically;
* avoid rebuilding static Wine geometry for unrelated filter changes;
* avoid coupling callback behaviour to trace ordering;
* handle Polygon and MultiPolygon data correctly.

Likely rewrite areas

### `wine_figures.py`

Separate static Wine geometry construction from dynamic overlays.

Potential structure:

```text
build_wine_base_figure(...)
build_wine_geometry_traces(...)
add_region_outlines(...)
add_restaurant_traces(...)
apply_wine_layout(...)
```

The exact representation should be selected after measuring trace count and payload size.

Possible options include:

1. retain `Scattermap` but combine compatible geometry;
2. cache prebuilt Wine traces or a base figure;
3. use a feature-oriented map layer instead of one trace per geometry part;
4. pre-process a browser-oriented GeoJSON asset;
5. separate hover/click geometry from visual boundary rendering.

Do not select an option solely from source GeoJSON size.

### `wine_callbacks.py`

Replace:

```text
curveNumber -> stored curve-number list -> wine_df.iloc(...)
```

with semantic trace data:
```text
clicked feature -> customdata/meta -> parent region and appellation
```
Parent-region behaviour should remain:
```text
clicked AOC -> parent region -> existing regional OpenAI response
```

### `wine_layout.py`

Only change layout components if required by the new callback or figure contract.

Avoid visual redesign during this phase.

### `wine_prompts.py`

Keep prompts region-level initially.

Do not pass app into the prompt until appellation-level output is explicitly designed.

⸻

## Phase 4 — Implement semantic Wine interactions

Each rendered Wine feature should carry, at minimum:

```text
region
app
feature identity or stable key
trace type
```

Hover behaviour

Recommended initial hover hierarchy:

```text
Appellation
Parent wine region
```

For example:

```text
Chablis
Burgundy
```

### Click behaviour

Clicking any AOC should resolve directly to its parent region.

The OpenAI panel should continue to display the existing region-level content.

### Cache behaviour

Keep the application-level OpenAI cache keyed by parent region while output remains region-level.

For example:
```text
wine_info:Burgundy
```
Do not introduce appellation into the cache key until responses differ by appellation.

Review whether callback-level memoization remains useful once trace-index arguments are removed.

⸻

## Phase 5 — Performance validation

Repeat the Phase 2 measurements after the rewrite.

Acceptance criteria

The Wine page should:

* load without errors;
* preserve all existing region-level behaviour;
* resolve every tested AOC to the correct parent region;
* remain correct after outline and restaurant controls change;
* expose app in hover data;
* avoid dependence on feature order or curve numbers;
* avoid rebuilding static Wine geometry for restaurant-only changes where practical;
* have acceptable browser interaction performance;
* have an understood and documented callback payload size.

Performance acceptance should be based on measured behaviour rather than the source asset’s file size.

⸻

## Phase 6 — Cleanup and future work

After the new renderer is stable:

* remove the old Wine asset if it is no longer required;
* remove obsolete curve-number stores and callback state;
* remove superseded helper functions;
* update tests and documentation;
* document the Wine figure data contract;
* record future appellation-level functionality separately.

Potential future work:

* appellation-specific OpenAI responses;
* appellation selection state;
* richer AOC labels;
* region/AOC search;
* pre-generated appellation summaries;
* geometry simplification at multiple zoom levels;
* client-side map rendering.

These are explicitly outside the initial integration scope.