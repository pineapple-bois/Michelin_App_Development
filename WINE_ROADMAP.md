# Wine map hover investigation roadmap

Status: documentation-only current-state note. The AOC map migration,
regional-outline restoration, restaurant overlay restoration, search navigation,
and feature-ID click path are complete. This document now tracks the remaining
Wine map hover and overlap investigation without prescribing an implementation.

## Current state

The Wine page uses the current Dash Pages architecture:

* page registration: `app/pages/wine.py`
* layout: `app/layouts/wine.py`
* callbacks: `app/callbacks/wine.py`
* figure construction: `app/utils/wine_figures.py`
* Wine data loading and validation: `app/app_data.py`

The production Wine geography is `assets/data/wine_regions_aoc.geojson`, loaded
with Pyogrio into `DATA.wine_df`. The loader requires `region`, `app`, `colour`,
and `geometry`, accepts only `Polygon` and `MultiPolygon`, validates unique
`(region, app)` pairs, enforces one colour per parent region, and generates an
in-memory stable feature ID:

```text
aoc-<sha256(region + NUL + app)>
```

The current checked-out data loads 348 AOC features across 12 parent regions:
178 `Polygon` features and 170 `MultiPolygon` features.

The old thousands-of-traces Wine renderer has been replaced by a small semantic
trace structure:

| Trace | Type            | Purpose                | Initial hover/click role           |
|------:|-----------------|------------------------|------------------------------------|
|     0 | `choroplethmap` | Wine AOC polygons      | Native polygon hover and AOC click |
|     1 | `scattermap`    | One-star restaurants   | Restaurant hover when visible      |
|     2 | `scattermap`    | Two-star restaurants   | Restaurant hover when visible      |
|     3 | `scattermap`    | Three-star restaurants | Restaurant hover when visible      |

Regional outlines are not data traces. They are a single non-interactive
`layout.map.layers[0]` line layer built from regional geometry boundaries and
toggled with a Dash `Patch`.

The Wine map preserves camera state through `layout.map.uirevision =
"wine-aoc-map-v1"` and through `map-view-store`, which records `relayoutData`
containing `map.center` and `map.zoom`. Search navigation patches only map
center and zoom.

Click-to-information flow is stable and semantic:

```text
clickData.points[0].location
  -> feature_id lookup
  -> region/app/colour
  -> cache key wine_info_<appellation>_<parent region>
  -> generated Wine information panel
```

The callback consumes `clickData`, not `hoverData`. Missing, malformed,
restaurant, and unknown click payloads fail closed without invoking OpenAI or
request-limit accounting.

Current tests cover the loader contract, stable feature IDs, one
`choroplethmap` geography trace, semantic hover `customdata`, `location`-based
click resolution, map `uirevision`, regional-outline patching, restaurant trace
structure and visibility patching, layout IDs, search navigation, and invalid
Wine information payloads. They do not cover browser hover anchoring, Plotly
hover event payload shape, mobile hover/touch behaviour, or visual overlap
disambiguation.

## Problem statement

Observed issue: while moving the cursor within or between Wine appellation
polygons, the native Plotly hover label can appear to jump abruptly around the
map. The movement may look centroid-related, but that has not been demonstrated.

Possible contributors include multipart geometries, elongated geometries, very
small polygons, overlapping AOCs, trace ordering, restaurant marker interception,
and Plotly.js internals for anchoring hover labels on MapLibre polygon traces.
It is not yet known whether Plotly anchors `choroplethmap` hover labels to a
centroid, representative point, polygon part, nearest rendered segment, mouse
position, or another internal point.

Treat these as separate problems during investigation:

1. Tooltip position jumps while the hovered AOC remains the same.
2. Hover identity switches between overlapping appellations.
3. Click identity and hover identity disagree at the same apparent cursor
   position.
4. Map center or zoom changes after interaction.
5. The tooltip obscures the small polygon being inspected.

Do not describe all of these as a "centroid bug" unless browser evidence proves
that centroid anchoring is the cause.

## Verified current implementation

| Question                                     | Current answer                                                                                                                                      |
|----------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| What renders the AOC polygons?               | One `go.Choroplethmap` trace on `subplot="map"`.                                                                                                    |
| What identifies features?                    | `featureidkey="properties.feature_id"`, with `locations` and `ids` set to generated feature IDs.                                                    |
| What fields are exposed to hover?            | `customdata = [[region, app, feature_id], ...]`; the hover template shows appellation and parent region.                                            |
| Is hover generated by the polygon trace?     | Yes, current AOC hover is native Plotly hover from the `choroplethmap` trace.                                                                       |
| Is `hovermode` configured?                   | Yes, `layout.hovermode="closest"`.                                                                                                                  |
| Is `hoverdistance` configured?               | No. Whether it affects `choroplethmap` polygon hit-testing must be verified against Plotly.js behaviour.                                            |
| Are regional outlines hoverable?             | They are a `layout.map.layers` line layer, not a Plotly trace; no explicit hover is defined.                                                        |
| Can restaurant traces intercept hover?       | Yes when visible: restaurant traces are `scattermap` marker traces with their own hover templates.                                                  |
| Are restaurant traces above geography?       | They are appended after the AOC trace and use `below=""`; browser verification should confirm actual MapLibre ordering.                             |
| How are overlapping AOCs ordered?            | Render order follows the loaded `wine_df` / GeoJSON feature order. There is no overlap-aware ordering rule.                                         |
| Are Polygon and MultiPolygon both present?   | Yes: 178 Polygon and 170 MultiPolygon features in the current data.                                                                                 |
| Are duplicate appellation rows allowed?      | Duplicate `(region, app)` pairs are rejected by the loader. Physical geometry overlap is not rejected.                                              |
| Does the callback consume hover data?        | No Wine callback consumes `hoverData`; the information panel uses only `clickData`.                                                                 |
| Is camera state independent of hover?        | The code only stores `relayoutData` for pan/zoom and uses `uirevision`; hover should not change camera state, but this should be browser-confirmed. |
| Is there a wrapper for a fixed HTML overlay? | The layout has `.wine-map.editorial-map` around `dcc.Graph`, so a future overlay has a plausible container, but no tooltip node exists today.       |
| Are external JS assets present?              | Yes, `assets/scroll-script.js` handles nav scrolling. There is no existing Wine Plotly hover listener.                                              |
| Is custom JavaScript already used for hover? | Only the Guide page has an inline clientside callback for cursor styling from `hoverData`; Wine has none.                                           |

Installed stack in the current environment:

| Package | Current installed version | Requirement |
|---|---:|---|
| Dash | 2.18.2 | `dash~=2.18.1` |
| Plotly.py | 5.24.1 | `plotly~=5.24.1` |
| Plotly.js bundled by Plotly.py | 2.35.2 | indirect |

## Data-derived investigation candidates

Use these as starting points for reproducing and classifying the issue. They
come from the current repository data; the hover symptom itself still needs
browser confirmation.

| Case type | Candidate appellations |
|---|---|
| Highly fragmented multipart features | `Crémant de Bourgogne`, `Languedoc`, `Bourgogne Passe-tout-grains`, `Muscadet`, `Gros Plant du Pays Nantais` |
| Large appellations | `Taureau de Camargue`, `Côtes de Provence`, `Entre-deux-Mers`, `Bordeaux supérieur`, `Languedoc`, `Côtes du Rhône` |
| Very small features | `Mazoyères-Chambertin`, `Limoux`, `Bourgogne aligoté`, `Pouilly-sur-Loire`, `Crémant de Bordeaux` |
| Burgundy Grand Cru / dense Burgundy targets | `Chambertin`, `Chambertin-Clos de Bèze`, `Clos de Vougeot`, `Montrachet`, `Romanée-Conti`, `Mazoyères-Chambertin` |
| Candidate overlap pairs from geometry intersection checks | `Saussignac` / `Côtes de Bergerac`, `Arbois` / `Crémant du Jura`, `Seyssel` / `Vin de Savoie`, `Bordeaux supérieur` / `Côtes de Duras`, `Entre-deux-Mers` / `Côtes de Duras` |
| AOC near or containing starred restaurant markers | `Saint-Emilion`, `Pessac-Léognan`, `Sauternes`, `Gevrey-Chambertin`, `Chassagne-Montrachet`, `Crémant d’Alsace` |

Notes:

* The overlap candidates are not a final topology audit. A projected diagnostic
  intersection pass encountered GEOS topology exceptions, so overlap analysis
  may require a separate read-only repair/diagnostic workflow.
* Regional-outline-near cases should be chosen in the browser by enabling the
  regional outline layer and testing AOCs near parent-region boundaries.

## Unknowns requiring browser inspection

These cannot be established from the Python source alone:

* whether the hovered feature changes when the tooltip jumps;
* whether `hoverData.points[0].location`, `customdata`, `bbox`, `lon`, or `lat`
  are present for `choroplethmap` hover events;
* whether Dash `hoverData` includes a usable bounding box for `dcc.Tooltip`;
* whether raw `plotly_hover` events expose mouse or container coordinates that
  Dash `hoverData` omits;
* whether `layout.hoverdistance` affects MapLibre `choroplethmap` polygons;
* whether restaurant marker traces intercept polygon hover or click events when
  visible;
* whether regional outline layers affect hit-testing even though they are not
  Plotly traces;
* whether hover and click resolve to the same `location` in overlapping areas;
* whether the jump is label anchoring only, feature identity switching only, or
  both;
* whether mobile/touch behaviour should preserve hover at all.

## Option comparison

| Option                                                      | Summary                                                                                                                                                               | Strengths                                                                                                                                               | Limits and risks                                                                                                                                                                                                                      | When to keep considering it                                                                                        |
|-------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| A. Retain native Plotly polygon hover                       | Keep current native `choroplethmap` hover; test `hovertemplate`, `hoverlabel`, `hovermode`, `namelength`, and feature ordering.                                       | No architecture change; preserves hover anywhere over polygons; works with current click contract; likely best accessibility baseline for Plotly users. | Jumping may be unavoidable Plotly behaviour; overlapping polygons remain ambiguous; trace ordering may only hide the problem; mobile hover remains limited.                                                                           | If browser tests show identity is stable and shorter/lighter labels make the visual movement acceptable.           |
| B. Native hover with less content                           | Keep native hover but reduce label content, for example appellation plus parent region only or appellation only.                                                      | Very small change if implemented later; smaller labels may make jumps less distracting; preserves default Plotly accessibility/touch behaviour.         | Does not change the anchor point; does not solve overlap identity switching; may remove useful context.                                                                                                                               | If label size is the main UX pain and feature identity is reliable.                                                |
| C. Disable native polygon hover                             | Set polygon hover off while keeping polygons clickable.                                                                                                               | Removes the jumping tooltip entirely; leaves click-to-panel as the primary interaction; simplest UX contract.                                           | Reduces discoverability; keyboard/screen-reader implications need thought; users may not know what polygon they are about to click; overlapping AOCs become harder to inspect.                                                        | If hover is more harmful than useful and click/search provide enough understanding.                                |
| D. Fixed-position information overlay                       | Show hovered appellation in a fixed corner of the map container, driven by hover state.                                                                               | Stable position; no centroid-style label jumping; can reuse `region/app/feature_id`; can avoid obscuring tiny polygons.                                 | Still depends on reliable `hoverData`; needs clear-on-unhover behaviour; may duplicate the right-hand information panel; mobile layout needs a separate design.                                                                       | If Dash hover payload reliably identifies the hovered AOC but native label position is unstable.                   |
| E. Dash `dcc.Tooltip`                                       | Use Dash tooltip machinery anchored from hover event data.                                                                                                            | Framework-native; less custom JS than a hand-written listener; can render HTML content.                                                                 | Needs a usable `bbox` or equivalent from current `choroplethmap` hover payload; if Plotly supplies an unstable anchor, it may recreate the same problem.                                                                              | Only after inspecting real `hoverData` and confirming a stable bounding box or acceptable anchor exists.           |
| F. Custom cursor-following HTML tooltip                     | Add a clientside `plotly_hover` / `plotly_unhover` listener and position an HTML tooltip from mouse or event coordinates.                                             | Could follow the cursor instead of Plotly's polygon anchor; maximum control over placement and clearing.                                                | Highest maintenance cost; resize/scroll offsets, pan/zoom interactions, listener cleanup, touch behaviour, and Dash remounts must be handled; may be disproportionate for a visual defect.                                            | Only after native hover and fixed-overlay experiments fail and the UX benefit is clearly worth custom JS.          |
| G. Representative-point or centroid marker layer            | Precompute centroid or `representative_point` locations and use marker hover instead of polygon hover.                                                                | Gives deterministic anchor points; `representative_point` can stay inside polygons; marker payloads are easier for tooltips.                            | Not equivalent to stable hover across the polygon; hover only works near points unless markers are large/invisible; CRS matters for centroid calculation; multipart features can be misleading; may conflict with restaurant markers. | If the desired interaction becomes "hover labels at known label points" rather than "hover anywhere over polygon." |
| H. Broad invisible hover markers or sampled interior points | Generate multiple invisible points inside each polygon to approximate polygon hover.                                                                                  | Could create more coverage than one centroid; may expose point-like event payloads.                                                                     | Adds client payload and maintenance complexity; coverage is uneven; invisible markers may intercept clicks; can reintroduce performance problems removed by the trace migration.                                                      | Rarely; only if fixed overlays need point payloads and performance tests show the payload is still acceptable.     |
| I. Overlap-aware feature selection                          | Treat overlap identity separately through deterministic ordering, smallest-containing-polygon rules, cycling, listing all AOCs under cursor, or click disambiguation. | Addresses the real ambiguity where several AOCs exist under one cursor; can improve correctness beyond tooltip placement.                               | Plotly configuration alone may not provide all containing polygons; likely needs geometry hit-testing from lon/lat or client coordinates; UI design is non-trivial.                                                                   | If browser tests show identity switching or click/hover disagreement in overlapping areas.                         |

## Risks and constraints

| Risk                                      | Why it matters                                                                                                          |
|-------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| Overlap ambiguity                         | Multiple valid AOCs may exist under one cursor; choosing one may be a data/model decision, not just a tooltip decision. |
| Reliance on undocumented Plotly internals | Hover anchoring and feature selection may change across Plotly.js versions.                                             |
| Loss of hover accessibility               | Removing native hover may reduce discoverability and keyboard/screen-reader affordances.                                |
| Degraded touch interaction                | Hover-first designs rarely translate cleanly to mobile.                                                                 |
| Hover layers intercept clicks             | Invisible markers or custom overlays may block AOC clicks or pan/zoom gestures.                                         |
| Restaurant marker interception            | Visible restaurant traces can legitimately take hover/click priority over polygons.                                     |
| Performance regression                    | Extra traces, sampled points, or custom listeners could undo the benefits of the single-trace migration.                |
| Incorrect centroid calculations           | Centroids calculated directly in EPSG:4326 can be misleading; projected CRS and multipart handling matter.              |
| Stale tooltip state                       | Pan, zoom, search navigation, resize, page remount, or filter toggles may leave a custom tooltip showing old content.   |
| Browser differences                       | Local and deployed browsers may differ in pointer event and Plotly rendering behaviour.                                 |
| Oversized solution                        | A large custom tooltip system may not be justified if the defect is only a minor visual annoyance.                      |

## Recommended investigation sequence

Run these as local experiments first. Do not commit behaviour changes until the
classification evidence is clear.

1. Reproduce and classify the jump with a small named set: one fragmented
   multipart AOC, one very small Burgundy Grand Cru, one large appellation, one
   candidate overlap pair, one AOC containing a restaurant marker, and one AOC
   near an enabled regional outline.
2. Inspect Dash `hoverData`, `clickData`, and raw browser `plotly_hover` /
   `plotly_unhover` events for the same cursor positions.
3. Determine whether the hovered `location` changes, the label anchor changes,
   click identity differs from hover identity, or camera state changes.
4. Test native-hover configuration changes locally without committing:
   shorter `hovertemplate`, hover label styling, `hovermode`, possible
   `hoverdistance`, and feature/trace ordering.
5. Prototype a fixed-position map overlay locally if `hoverData` reliably
   provides `location` / `customdata`.
6. Evaluate `dcc.Tooltip` only after confirming whether the real
   `choroplethmap` hover payload includes a usable and stable `bbox`.
7. Evaluate a custom cursor-following HTML tooltip only if native hover,
   shorter native labels, and fixed overlay are insufficient.
8. Investigate overlap-aware selection separately from tooltip positioning.
9. Decide whether the UX benefit justifies implementation, tests, and
   maintenance.

## Decision criteria

Use these criteria when choosing whether to implement anything:

| Criterion                        | Prefer a solution that...                                                             |
|----------------------------------|---------------------------------------------------------------------------------------|
| Tooltip stability                | avoids abrupt movement and does not obscure the inspected polygon.                    |
| Correctness for overlapping AOCs | makes ambiguity visible or deterministic rather than accidental.                      |
| Full-polygon hover               | preserves hover anywhere on the polygon if that remains a product requirement.        |
| Click reliability                | keeps `location`-based AOC click resolution stable and restaurant clicks fail-closed. |
| Touch/mobile support             | has a reasonable non-hover path on small screens.                                     |
| Implementation complexity        | fits the current Dash/Plotly architecture without a large side system.                |
| Maintenance                      | avoids undocumented internals where practical.                                        |
| Performance                      | preserves the single-trace migration's responsiveness and payload gains.              |
| Accessibility                    | does not remove useful native affordances without an alternative.                     |

## Deferred work

Keep these out of the hover investigation unless they become necessary evidence:

* appellation-specific OpenAI prompt expansion;
* production GeoJSON changes or overlap clipping;
* new mapping libraries;
* visual redesign of the whole Wine page;
* broad mobile/responsive cleanup beyond documenting hover/touch constraints;
* changes to `WINE_AOC.md` or prompt-context hierarchy.

## Definition of done for the investigation

The investigation is complete when it produces a short evidence note answering:

* which of the five problem classes are actually present;
* what the current Dash `hoverData`, `clickData`, and raw Plotly event payloads
  contain for representative cases;
* whether native Plotly configuration can reduce the issue acceptably;
* whether `dcc.Tooltip` is compatible with `choroplethmap` payloads;
* whether a fixed overlay is enough if native hover is not;
* whether overlap disambiguation needs a separate design;
* whether the recommended implementation, if any, is proportionate to the UX
  benefit.
