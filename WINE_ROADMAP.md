# Wine map hover status

Status: solved and accepted on 2 July 2026. The unstable native AOC hover label
has been replaced by a fixed-position HTML overlay with a lighter hovered-polygon
state. Overlapping-AOC identity selection remains a separate, deferred problem.

## Current state

The Wine page uses the current Dash Pages architecture:

* page registration: `app/pages/wine.py`
* layout: `app/layouts/wine.py`
* callbacks: `app/callbacks/wine.py`
* figure construction: `app/utils/wine_figures.py`
* Wine data loading and validation: `app/app_data.py`

The production geography is `assets/data/wine_regions_aoc.geojson`. It is
rendered as one semantic `go.Choroplethmap` AOC trace followed by three fixed
`go.Scattermap` restaurant traces. AOC features use generated stable IDs in
`locations` and expose:

```text
customdata = [parent_region, appellation, feature_id]
location = feature_id
```

Regional outlines remain a non-interactive `layout.map.layers` line layer.
Restaurant visibility is patched without rebuilding the figure. Camera state is
preserved through `layout.map.uirevision = "wine-aoc-map-v1"` and
`map-view-store`.

AOC clicks still resolve `clickData.points[0].location` through the server-side
feature lookup before the existing cached OpenAI information flow runs. The
hover work does not alter click handling, search navigation, request accounting,
regional outlines, restaurant filtering, or map camera persistence.

## Accepted hover behaviour

The native AOC label is suppressed with `hoverinfo="none"`. Plotly hover events
remain enabled so `dcc.Graph.hoverData` can drive the replacement UI. Restaurant
traces retain their original native hover templates.

The existing `.wine-map.editorial-map` wrapper now contains a compact overlay:

* `wine-map-hover-overlay`
* `wine-map-hover-appellation`
* `wine-map-hover-region`

The overlay is fixed in the map's top-right corner and uses
`pointer-events: none`, so it cannot intercept hover, click, pan, or zoom
interactions. It shows the appellation with its parent region beneath it and
does not move with the cursor, polygon geometry, or Plotly hover anchor.

`clear_on_unhover=True` clears `hoverData` when the pointer leaves an AOC. The
callback also clears and hides the overlay for missing, malformed, unknown, and
restaurant payloads, preventing stale appellation content.

The same validated AOC hover applies a lighter polygon state through the
existing choropleth trace:

```text
selectedpoints = [hovered feature index]
selected marker opacity = 0.58
unselected marker opacity = 1.0
```

The feature index is resolved from the stable `location`; it is not inferred
from a centroid or cursor position. Unhover and non-AOC hover clear
`selectedpoints`. No extra geography trace, point layer, centroid,
representative point, sampled interior point, custom JavaScript, `dcc.Tooltip`,
or new dependency was introduced.

## Payload validation

The hover callback fails closed unless all of the following are true:

1. `hoverData.points[0]` is a mapping.
2. `curveNumber` identifies the AOC geography trace.
3. `customdata` has exactly `[region, appellation, feature_id]`.
4. `location` matches the `customdata` feature ID.
5. The feature ID exists in the current lookup.
6. The payload's region and appellation match the lookup record.

This keeps restaurant hover independent and prevents synthetic or stale payloads
from displaying an AOC overlay or highlight. The hover callback has no OpenAI,
cache, session, or request-limit path.

## Validation

Focused tests cover:

* initial hidden state and `clear_on_unhover`;
* native AOC label suppression while semantic hover data remains present;
* valid AOC overlay content;
* lighter selected-polygon configuration and feature-index patching;
* clearing on unhover and restaurant hover;
* malformed, unknown, and non-AOC payloads;
* isolation from the OpenAI information callback;
* unchanged restaurant hover templates and trace structure.

At acceptance, the focused Wine/layout suite passed with 65 tests and the full
suite passed with 110 tests. `git diff --check` also passed. Browser-level
tooltip positioning is intentionally not part of the automated suite.

## Deliberately deferred

The accepted overlay solves tooltip-position instability. It does not decide
which appellation should win when AOC geometries overlap. If Plotly changes
`hoverData.location` while the pointer remains within an overlap, the fixed
overlay will remain stationary but its text and highlighted polygon may change.

Any future overlap work should be treated as a separate feature-selection task.
Possible approaches include deterministic feature ordering, listing all
containing AOCs, click-based disambiguation, or geometry hit-testing. None
should be added without reproducing the identity problem and defining the
desired product behaviour first.

Also deferred unless a regression justifies reopening the decision:

* custom cursor-following JavaScript;
* `dcc.Tooltip` anchoring;
* centroid or representative-point hover layers;
* sampled invisible hover markers;
* Wine GeoJSON changes;
* broader Wine page redesign or mobile styling work.

## Regression checklist

When changing Plotly, Dash, Wine traces, or map layout, verify:

1. A large and a fragmented AOC show a stationary overlay.
2. A small Burgundy Grand Cru remains inspectable and highlights clearly.
3. Rapid movement between adjacent AOCs updates text without stale content.
4. Leaving the polygon hides the overlay and clears the highlight.
5. Restaurant markers retain their native hover labels.
6. Restaurant filtering, regional outlines, pan, zoom, and search still work.
7. Clicking an AOC still opens the correct information panel.

## Reopen criteria

Reopen this roadmap only if the fixed overlay becomes unstable, hover events no
longer survive native-label suppression, selection patches cause performance or
camera regressions, restaurant interactions change, or overlap identity becomes
a confirmed product requirement.
