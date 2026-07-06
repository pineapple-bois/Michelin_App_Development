# Touchscreen audit

## Scope and evidence

This report records the touchscreen audit and the first implemented responsive-input stage for the current Michelin Dash application. It is not a redesign proposal. The live Dash Pages implementation is the baseline.

This revision gives the Guide and Wine maps explicit smaller-screen interaction contracts. Map work now precedes generic shared touch-target work in the implementation sequence; the earlier shell and control findings remain evidence, not the active priority.

The audit covered:

- the shared header, navigation, footer, page shell, and 404 page;
- Guide, Analysis, Economics, and Wine layouts and callbacks;
- Plotly `dcc.Graph` configuration, MapLibre figures, hover/click payloads, and viewport stores;
- the complete active responsive cascade in `assets/styles.css`;
- the current Dash, Plotly, and Dash Bootstrap Components versions and `dcc.Dropdown` contract;
- existing layout, callback, figure, route, and map-constraint tests.

Static inspection was supplemented by rendered checks in the local app at 320×568, 390×844, 820×1180, and 1024×768. Those checks used a desktop Chromium browser with viewport overrides, not iOS or Android device emulation. They establish current dimensions, wrapping, overlap, focus targets, and overflow, but they do not prove mobile-browser gesture or on-screen-keyboard behaviour.

After Stage 1 implementation, a focused local Chromium check at 1250/1251 px confirmed that the Guide region selector had no text input/`is-searchable` class at 1250 px and regained both at 1251 px, while `city-input-mainpage` remained present in both modes. On Wine at 1250 px, both selectors were non-searchable and opening the appellation menu rendered the full virtualised option list; at 1251 px both selectors regained searchable inputs. This desktop viewport check does not prove physical-device software-keyboard behaviour or every value-preservation path.

Relevant platform baseline:

- `assets/custom_header.html:4-9` includes `width=device-width, initial-scale=1`.
- `requirements.txt:1-2,12` specifies Dash 2.18, Dash Bootstrap Components 1.4.2, and Plotly 5.24; the inspected environment resolved Dash 2.18.2 and Plotly 5.24.1.
- Dash 2.18 `dcc.Dropdown` defaults to `searchable=True`, `clearable=True`, `optionHeight=35`, and `maxHeight=200` unless a layout overrides those properties.

Confirmed product requirement: the existing 1250 px transition into the smaller-screen layout also controls dropdown text entry. At widths up to and including 1250 px, every `dcc.Dropdown` is selection-only and the Guide `city-input-mainpage` is the only user-facing text input. At 1251 px and wider, all dropdowns retain searchable desktop behaviour. This is deliberately viewport-based: pointer, hover, touch, pen, and hybrid-device capabilities do not participate in the policy.

The findings fall into distinct implementation lanes:

| Lane | Findings in this report |
| --- | --- |
| Shared application-wide | Header/menu/footer targets and semantics, viewport-based dropdown input policy, 30–35 px control heights, breakpoint layering, safe-area/dynamic-viewport gaps. |
| Page-specific | Economics chip overlap; Analysis chip density and long graph flow; Guide modebar/search/title; Wine hover, tap, and camera behaviour. |
| Component configuration | `searchable`, `clearable`, Plotly `config`, semantic/pressed attributes, option height, and menu behaviour. |
| CSS/layout | Hit-area dimensions, wrapping, max-height overlap, fixed map heights, top spacing, title clipping, and breakpoint-specific composition. |
| Interaction/callback | Tap versus hover, click-count parity, clear values, map `clickData`/`relayoutData`, and viewport ownership. |
| Browser/device only | On-screen keyboards, visual viewport, safe areas, one-finger page/map scroll, pinch/double-tap, tap-versus-pan, and MapLibre camera order. |

## Interactive surface inventory

### Shared application shell

The fixed shared header contains a non-button `html.Div` hamburger (`hamburger-icon`) and four links inside `navigation-menu`; the footer contains a GitHub image link. The menu opens and closes by click-count callback, and route changes update active link classes (`app/components/shared.py:14-46,115-181`; `app/callbacks/navigation.py:6-25`). There is no outside-tap or Escape-key close path in application code.

The hamburger's rendered box was 24×18 px. Open menu links were about 106×40 px at 390 px width. The footer GitHub link is 28×28 px (`assets/styles.css:124-175,259-307`). All are below a comfortable roughly 44 px touch target in at least one dimension.

The 404 page adds a text-only `Return to Home Page` link but no page-specific touch sizing. Its body uses `height: 100vh` while the shared fixed header and footer remain present (`app/layouts/layout_404.py:6-35`; `assets/styles.css:314-325`). It should be included in phone-height checks, especially landscape and browser-chrome expansion/collapse.

### Guide (`/` and `/home`)

Direct controls and outputs are:

- `info-toggle-button`, `city-input-mainpage`, `submit-city-button-mainpage`, and `clear-city-button-mainpage` in the collapsible location search;
- `region-dropdown`, `department-dropdown`, and conditional `arrondissement-dropdown`;
- rating buttons and `toggle-selected-btn`;
- `map-display`, whose restaurant markers are tapped to populate `restaurant-details`;
- the Guide rating legend and restaurant website link.

Definitions: `app/layouts/layout_main.py:35-90,93-245,248-343`. Search and map interactions: `app/callbacks/guide.py:172-269,430-485,511-671`.

Current touch-relevant behaviour:

- Search deliberately accepts keyboard text and either Enter (`n_submit`) or the Submit button. On a phone, the on-screen keyboard will therefore be part of the intended flow. The callback does not manage focus, scroll the input into view, or account for visual-viewport shrinkage (`app/layouts/layout_main.py:64-82`; `app/callbacks/guide.py:187-269`).
- The search button explanation exists only as `.info-toggle-button:hover:after`; there is no tap, focus, or persistent equivalent (`assets/styles.css:226-248`). Touch users do not reliably receive it.
- A restaurant is selected from `clickData`; hover text is supplementary rather than required for details (`app/callbacks/guide.py:430-485`; `app/utils/guide_figures.py:231-266`). Markers are only 9 or 11 px, with some 11/15 px Green Star underlays, so dense areas require precise taps (`app/utils/guide_figures.py:224-229,251-266,318-359`).
- `map-display` explicitly enables `scrollZoom`, responsiveness, and a desktop modebar. The remaining rendered buttons are Zoom in, Zoom out, Reset view, and Plotly attribution; at 390 px they were about 24×26 px (`app/layouts/layout_main.py:318-343`). Mouse-wheel zoom is therefore explicitly enabled on this page, although touch users need pinch/double-tap or the undersized modebar controls.
- Manual `map.zoom` and `map.center` are persisted only for the owning geography. Geography changes reset to canonical views; rating-only changes preserve a valid manual view (`app/callbacks/guide.py:99-161,511-671`). This is a sound state boundary but needs gesture-level browser testing.
- At 390×844 the page had no horizontal overflow and stacked to a 352 px-wide, approximately 549 px-high map. At 320×568 the map was 282×420 px. The later Guide media queries successfully override older tablet layout rules (`assets/styles.css:3598-3834`).
- At 320 px the nowrap header title was clipped: its 305 px scroll width exceeded its 264 px client width. The clipping follows `.header-title { overflow: hidden }` and `.title-section { white-space: nowrap }` (`assets/styles.css:97-114,3271-3288`).
- The Guide map is deliberately tall on small screens (`min-height: 420px`) and the details panel follows it, producing a long but orderly page. Whether a one-finger map pan prevents normal page scrolling near the map is a real-browser question (`assets/styles.css:3740-3747,3775-3796`).

### Analysis (`/analysis`)

Direct controls and outputs are:

- multi-select `region-dropdown-analysis` and regional rating buttons;
- `department-dropdown-analysis` and departmental rating buttons;
- conditional `arrondissement-dropdown-analysis` and arrondissement rating buttons;
- three bar-chart/map pairs;
- `granularity-dropdown`, `ranking-dropdown`, `star-dropdown-ranking`, and `toggle-show-details`;
- generated ranking cards and links.

Definitions: `app/layouts/analysis.py:30-298,332-458`. State and figure updates: `app/callbacks/analysis.py:14-270`.

Current touch-relevant behaviour:

- The regional multi-select starts with all 13 regions represented as removable chips. Its rendered height was about 242 px at 320 px, 217 px at 390 px, 88 px at 820 px, and 139 px in the half-width control at 1024 px landscape. It dominates the first interaction area on phones and remains visually heavy on tablet landscape.
- Each selected chip has a rendered remove target of about 17.5×20.8 px. The multi-select clear zone is 17 px wide. These are precise-pointer controls, even though the overall selector is large (`assets/styles.css:1271-1286,1581-1623`).
- The responsive rules stack chart/map pairs below 900 px, but each graph remains approximately 450 px high. At 390×844 the page was about 2,717 px tall before opening department/arrondissement results; at 320×568 it was about 2,892 px tall (`assets/styles.css:3392-3520`). This is not horizontal overflow, but it creates substantial scrolling and separates related controls from their results.
- At 1024×768 the regional chart and map remain side by side at about 483 px each. This breakpoint is plausible for tablet landscape but leaves a relatively narrow map plotting area and crowded all-region chips. It needs direct tablet testing rather than an automatic assumption that desktop layout is appropriate.
- Plotly modebars are hidden on all Analysis graphs, but bar and choropleth values are exposed through hover templates (`app/layouts/analysis.py:99-115,183-200,273-292`; `app/utils/analysis_figures.py:60-101,158-202`). No application callback requires chart or map clicks. Touch users may therefore be unable to obtain hover-only values consistently even though no core state change depends on them.
- Analysis has no persisted viewport store. Any pan or zoom is local to the current rendered figure and a selector/rating update returns a complete new figure (`app/layouts/analysis.py`; `app/callbacks/analysis.py:25-62,89-136,171-214`).
- Rating filters use click-count parity. Rapid or accidental double taps can perform two logical toggles and finish where they started (`app/utils/star_filters.py:20-39`; `app/callbacks/analysis.py:42-44,113-115,191-193`). No callback requires a deliberate double-click.

### Economics (`/economics`)

Direct controls and outputs are:

- `category-dropdown-demographics` for the metric;
- `granularity-dropdown-demographics` for All France versus one region;
- multi-select `demographics-dropdown-analysis` for included regions;
- `toggle-show-details-demographics` and three rating buttons;
- `demographics-map-graph`, `demographics-bar-chart-graph`, and the weighted-mean note.

Definitions: `app/layouts/economics.py:12-188`. Callback and viewport behaviour: `app/callbacks/economics.py:14-229`.

Current touch-relevant behaviour:

- The default 13-chip selector has the same growth as Analysis, but `#demographics-add-remove` is capped at `max-height: 150px` (`assets/styles.css:2047-2151`). At 390 px the selector was about 217 px high while the next restaurant toggle began inside that vertical span; at 320 px it was about 242 px high with the same overlap. This is the clearest current phone layout defect.
- The map remains 700 px high on phones. With controls and the overlapping selector, the rendered page was about 1,514 px high at 390×844 (`app/layouts/economics.py:140-188`; no phone-specific map-height rule in `assets/styles.css:3292-3364`).
- Choosing a metric reveals the bar chart and weighted-mean content; this can make an already map-led mobile page substantially longer. Below 900 px the map and chart stack correctly (`assets/styles.css:3309-3347`).
- The region multi-select is hidden when a single region is selected for department-level display. The callback returns complete figures and resets the stored viewport when `granularity-dropdown-demographics` changes (`app/callbacks/economics.py:22-27,43-162,183-218`).
- `update_demographics_map` evaluates `'all' in selected_regions` before its later empty-selection fallback. A touch clear normally needs to be checked for the actual Dash value (`[]` versus `None`); `None` would raise before the guard (`app/callbacks/economics.py:58-66`). Existing tests do not cover this callback boundary.
- Restaurant and rating toggles use click parity, so rapid double taps have the same two-toggle risk as Analysis (`app/callbacks/economics.py:14-15,86-98,164-181`).
- Maps and bars use hover templates for exact values and restaurant names, but no Economics callback consumes map click data (`app/utils/economics_figures.py:69-103,130-135,256-260`).

### Wine (`/wine`)

Direct controls and outputs are:

- responsive `wine-region-selector` and `wine-appellation-search` (selection-only at no more than 1250 px, searchable above it);
- `toggle-regional-outlines-wine`;
- `toggle-show-details-wine` and three restaurant-rating buttons;
- `wine-map-graph`, where AOC polygons are clicked to request information;
- a fixed hover overlay and generated AOC information panel.

Definitions: `app/layouts/wine.py:11-212`. Search, patch, hover, persistence, and information callbacks: `app/callbacks/wine.py:33-315,578-783`.

Current touch-relevant behaviour:

- Appellation text search remains available above 1250 px. At smaller widths, `searchable=False` prevents typed input and the existing options callback receives an empty/`None` `search_value`; `wine_search_options(...)` then returns the complete region-scoped record list rather than an empty suggestion set (`app/callbacks/wine.py:694-706`; `app/utils/wine_search.py:86-98`). Selecting a region therefore narrows a still-selectable appellation menu, and leaving the region clear exposes all appellations.
- Both Wine selectors start with `searchable=False` and are driven from the root responsive Store by the Wine-scoped callback. Their IDs, values, options, clear behaviour, and the appellation `search_value` callback remain unchanged (`app/layouts/wine.py:54-78`; `app/callbacks/responsive.py`; `app/callbacks/wine.py:685-706`).
- AOC hover is not merely native Plotly decoration: it drives a fixed HTML overlay and owns the AOC trace's `selectedpoints` patch. Touch devices have no stable hover model, so the overlay/highlight path is not dependable as the sole preview (`app/callbacks/wine.py:49-107,740-756`; `assets/styles.css:2509-2539`). AOC `clickData` currently goes directly to generated information, which is precisely the path the smaller-screen two-step contract must separate (`app/callbacks/wine.py:769-783`).
- Restaurant markers are 8 px and provide hover text only. Their click payload intentionally fails closed in the AOC information callback, so touch users receive no persistent restaurant detail from a marker tap (`app/utils/wine_figures.py:66-90`; `app/callbacks/wine.py:33-46,769-783`).
- The complete figure is produced once, then navigation, outline visibility, restaurant visibility, and hover selection patch separate owned fields. Touch changes must not add a second authority over these fields (`app/callbacks/wine.py:607-683,740-767`).
- Manual pan/zoom is stored only for the currently owned region/appellation. Selector navigation writes `uirevision`, then zoom, then centre. Bounds-derived minimum zoom depends on rendered canvas size (`app/callbacks/wine.py:170-315,623-645,708-738`; `app/utils/map_constraints.py:14-23`). Phone and tablet canvas sizes therefore need direct validation.
- Wine's map/content columns stack below 1050 px. The current graph remains fixed at 620 px high in that layout and 500 px below 600 px; recent Wine-only rules remove the legacy right indent and align the phone sheet with the 70 px header, but the map still remains inside the editorial sheet gutters (`assets/styles.css:2484-2554,2738-2788,3096-3100`). At 1024 px the controls remain close to their wrap threshold, so text zoom and tablet landscape still require direct checks.

## Dropdown and keyboard-entry audit

Dash defaults `dcc.Dropdown.searchable` to true. Before this stage, the rendered phone check showed that tapping `region-dropdown` focused an `<input type="text" role="combobox">`; omission of the property was therefore not equivalent to a non-editable selector. Every current dropdown now has the safe layout value `searchable=False`, and page-scoped clientside callbacks enable search only after the root viewport Store reports a width above 1250 px.

| Page | Component ID | Definition | Implemented classification | Repository-specific reason |
| --- | --- | --- | --- | --- |
| Guide | `region-dropdown` | `app/layouts/layout_main.py:263-270` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | Fixed 13-region list; callbacks consume `value`. |
| Guide | `department-dropdown` | `app/layouts/layout_main.py:278-282` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | Dependent options/value population is unchanged. |
| Guide | `arrondissement-dropdown` | `app/layouts/layout_main.py:296-301` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | Conditional Paris selector; callbacks consume `value`. |
| Analysis | `region-dropdown-analysis` | `app/layouts/analysis.py:68-78` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | Multi-selection and chip removal remain intact. |
| Analysis | `department-dropdown-analysis` | `app/layouts/analysis.py:157-164` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | Despite its ID, this selects one region; dependent callbacks consume `value`. |
| Analysis | `arrondissement-dropdown-analysis` | `app/layouts/analysis.py:246-254` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | Dynamically populated options remain callback-owned. |
| Analysis | `granularity-dropdown` | `app/layouts/analysis.py:361-372` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | Three fixed choices. |
| Analysis | `ranking-dropdown` | `app/layouts/analysis.py:380-392` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | Three fixed choices and fixed default. |
| Analysis | `star-dropdown-ranking` | `app/layouts/analysis.py:400-413` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | Three fixed choices and fixed default. |
| Economics | `category-dropdown-demographics` | `app/layouts/economics.py:47-63` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | Seven fixed metrics. |
| Economics | `granularity-dropdown-demographics` | `app/layouts/economics.py:70-79` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | All France or one region; callbacks consume `value`. |
| Economics | `demographics-dropdown-analysis` | `app/layouts/economics.py:90-100` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | Multi-selection and Select All remain available. |
| Wine | `wine-region-selector` | `app/layouts/wine.py:54-63` | **Selection-only at ≤1250 px; searchable at ≥1251 px** | Bounded region list. |
| Wine | `wine-appellation-search` | `app/layouts/wine.py:69-78` | **Selection-only with full selectable options at ≤1250 px; typed search at ≥1251 px** | Empty `search_value` returns every region-scoped record; typed `search_value` retains exact/fuzzy search (`app/utils/wine_search.py:86-152`). |

Changing only the public `searchable` property leaves each dropdown's ID, `value`, `options`, `multi`, and `clearable` properties in place. It also leaves every existing value callback and dependent option callback connected to the same component. The only callback consuming dropdown `search_value` is Wine appellation options; it remains registered in both modes and already has a useful no-query branch (`app/callbacks/wine.py:694-706`).

`city-input-mainpage` is the only standalone text input and should remain keyboard-enabled on every device (`app/layouts/layout_main.py:64-82`). No `dcc.Tabs`, sliders, checklists, or radio-item controls are currently present.

## Implemented responsive input model

The policy reuses the app's existing layout boundary, not a new device classification. `assets/styles.css:2841-2842` names `max-width: 1250px` as the tablet/smaller-screen layout, while `assets/styles.css:3598-3600` and `3653-3655` split the Guide desktop and tablet/mobile compositions at 1251/1250 px. `SMALL_SCREEN_MAX_WIDTH = 1250` in `app/callbacks/responsive.py` mirrors that established boundary without changing CSS behaviour.

`michelin_app.py` mounts the memory-backed root `responsive-input-mode-store`. Its initial payload is conservative:

```text
ready: false
is_small_screen: true
max_width: 1250
```

Consequently, every dropdown starts non-searchable before browser state is known. The root clientside callback then reads `window.innerWidth`, writes a ready snapshot, and listens for `resize` and `orientationchange`. It publishes only when the responsive state changes, removes any previous listener set when it is re-registered after navigation, and removes its listeners on page unload (`app/callbacks/responsive.py`; `michelin_app.py`). A desktop viewport therefore becomes searchable after the initial clientside callback rather than remaining in the safe fallback state.

Four page-scoped clientside callbacks map Store state to the public `searchable` property for the Guide, Analysis, Economics, and Wine dropdown groups. Each also uses a page-local mounted component as an input, avoiding one cross-page callback that targets components absent from the current Dash Pages route. The callback changes configuration only; it neither renders replacement components nor owns dropdown values or options.

The support boundary is explicit:

| Mechanism | Status for this app |
| --- | --- |
| `dcc.Store.data`, `dcc.Dropdown.searchable`, and `app.clientside_callback` | Supported public Dash configuration used by this stage. |
| `window.innerWidth`, `resize`, and `orientationchange` | Browser viewport APIs used to follow the existing CSS layout boundary. |
| `window.dash_clientside.set_props` | Dash renderer API used to publish event-driven Store changes without a server round trip; validate when upgrading Dash. |
| Pointer/hover/touch/pen media queries or events | Deliberately out of scope for dropdown policy. |
| `.Select-input`, `.Select-control`, focus interception, `blur()`, or `readOnly` mutation | Internal React Select DOM coupling; not used or recommended for this requirement. |

## Hybrid devices under a viewport rule

Hybrid devices are not classified by active modality. A tablet at 1024 px remains in selection-only mode even with a keyboard or trackpad attached; a touchscreen laptop at 1366 px remains searchable even when operated by touch. Likewise, a narrow desktop browser at 390 px is selection-only despite having a mouse and physical keyboard. These outcomes follow the confirmed product rule and are not detection defects.

Orientation and window resizing may cross 1250 px, so the Store and dropdown configuration update at runtime. Selected values and callback wiring should survive because only `searchable` changes, but open-menu/focus behaviour during the transition remains a browser-level validation item. No future dropdown work should add coarse-pointer, hover, `maxTouchPoints`, pen, or recent-modality detection unless the product requirement is explicitly changed.

## Guide map smaller-screen contract

### Current interaction state

The Guide map is the application's principal restaurant-browsing surface. `map-display` is a responsive `dcc.Graph` with `scrollZoom=True` and a customised visible modebar (`app/layouts/layout_main.py:315-343`). The map figure is rebuilt in full when geography or rating state changes. A region displays an outline; a valid department or Paris arrondissement displays its outline, and a subsequent rating-state update supplies restaurant traces (`app/callbacks/guide.py:511-606`). Restaurant traces carry the source row index in `customdata` and `meta`; `clickData` resolves that index and renders `restaurant-details` (`app/utils/guide_figures.py:231-266`; `app/callbacks/guide.py:430-485`).

Selection is currently persistent only in the details content. There is no selected-restaurant Store and no selected marker trace or `selectedpoints` styling. Panning or zooming does not itself clear details, but a region, department, or rating callback does. Marker sizes are 9 px for Selected restaurants and 11 px for Bib/starred restaurants; Green Star underlays are 11 or 15 px (`app/utils/guide_figures.py:215-266,318-359,443-484`).

### Guide and Wine camera constraints below 1050 px

#### Rendered map dimensions

Neither map receives its narrow-layout dimensions from its figure builder. The dimensions come from the layout/CSS cascade and therefore exist only in the browser:

| Map | Width at no more than 1050 px | Height at no more than 1050 px |
| --- | --- | --- |
| Guide `map-display` | `.guide-map-panel` is `width: 100%` of the padded Guide sheet; `.map-display` fills that wrapper. It is not full viewport width (`assets/styles.css:2917-2931,3706-3712`; `app/layouts/layout_main.py:321-346`). | `clamp(28rem, 72svh, 46rem)`, with a `72vh` fallback, throughout the existing no-more-than-1250 px layout. There is no later phone-height override (`assets/styles.css:3706-3709,3741-3789`). |
| Wine `wine-map-graph` | The layout's inline 50% map width is overridden below 1050 px: the flex composition stacks and `.wine-map` becomes `width: 100%` of its padded editorial sheet (`app/layouts/wine.py:119-151`; `assets/styles.css:2479-2502,2733-2744`). | `620px` with `min-height: 520px` from 601–1050 px; `500px` with `min-height: 420px` at no more than 600 px. These `!important` rules override the graph's inline `700px` and the desktop CSS `760px` (`app/layouts/wine.py:127-132`; `assets/styles.css:2498-2502,2753-2756,2779-2781`). |

The Guide explicitly sets `dcc.Graph(responsive=True)`. Wine leaves `responsive` at the Dash default and supplies no figure width, while its wrapper width and CSS height change responsively (`app/layouts/layout_main.py:323-333`; `app/layouts/wine.py:127-132`; `app/utils/wine_figures.py:143-158`). Source inspection can establish the requested sizes, but final canvas resize timing remains browser-owned.

#### Two different minimum-zoom mechanisms

`layout.map.bounds` is a MapLibre maximum-panning envelope, not a request to fit that envelope. Plotly exposes no separate `layout.map.minzoom` property here. MapLibre derives an effective minimum zoom from the envelope and the rendered canvas: the entire visible canvas must remain inside the bounds. A taller or wider canvas therefore changes the effective minimum even though the Python dictionary is unchanged (`app/utils/map_constraints.py:1-23,44-53`). Every Guide figure applies `METROPOLITAN_FRANCE_MAP_BOUNDS` (`west=-6`, `east=10.5`, `south=40.5`, `north=52`); every Wine figure applies the wider `WINE_MAP_BOUNDS` (`app/utils/guide_figures.py:4-15`; `app/utils/wine_figures.py:160`; `app/utils/map_constraints.py:7-23`).

Guide canonical zooms are constants, not fits. MapLibre may raise a requested constant when the canvas-derived minimum is higher. Wine has an additional application clamp before rendering: `map_view_from_bounds(...)` clamps its heuristic result to `MIN_WINE_APPELLATION_ZOOM = 5.0` and `MAX_WINE_APPELLATION_ZOOM = 11.5`; region navigation then adds a `0.75` zoom boost and clamps only to the same maximum (`app/utils/wine_search.py:9-12,196-230,244-264`). Those Wine constants constrain generated canonical views, not subsequent user zoom gestures. The MapLibre bounds remain the actual interactive minimum and can clamp the generated view again if their canvas-derived minimum exceeds it.

Static Web-Mercator calculations using the deployed region geometry and current CSS dimensions illustrate the Guide contradiction. These are diagnostics, not substitutes for renderer checks:

| Approximate Guide canvas | Bounds-derived minimum | Largest zoom that still fits metropolitan France and Corsica | Result |
| --- | ---: | ---: | --- |
| 284×448 (320 px phone) | 4.24 | 3.77 | No zoom can both fit France and satisfy the current bounds. |
| 354×608 (390 px phone) | 4.68 | 4.09 | No valid fit. The requested zoom 5 is closer still. |
| 772×736 (820 px tablet) | 5.04 | 5.20 | A narrow valid range exists; MapLibre may raise the requested zoom 5 slightly. |
| 994×736 (near 1050 px) | 5.40 | 5.20 | The canvas/bounds aspect ratios again leave no valid full-France fit. |

The deployed regional extent is approximately `(-5.10, 41.37, 9.56, 51.09)`, whereas the constraint is only modestly larger. On a tall narrow canvas, zooming out enough to include France's east-west extent makes the visible north-south extent exceed the constraint; MapLibre must honour the constraint and crops the geography instead. This is why changing only the constant `map_zoom=5` cannot solve the phone case.

#### Canonical camera selection

Guide uses four distinct paths:

- France/default: fixed centre `46.603354, 1.888334`, zoom `5` (`app/utils/guide_figures.py:505-526`).
- Region: the selected region outline changes, but the camera still uses the same France centre and zoom `5`; no region bounds or centroid participate (`app/utils/guide_figures.py:65-102`; `app/callbacks/guide.py:599-606`).
- Department: geometry centroid plus zoom `8`, except Paris `11` and Monaco code `98` at `13.5` (`app/callbacks/guide.py:47-67`). The outline/restaurant builders consume that view, with their own legacy defaults only when it is absent (`app/utils/guide_figures.py:104-141,268-391`).
- Paris arrondissement: geometry centroid and zoom `13` (`app/callbacks/guide.py:83-96`; `app/utils/guide_figures.py:143-187,393-503`).

Corsica has no special canonical view. A `Corse` region selection therefore remains centred near mainland central France at zoom 5. At a roughly 390 px viewport, zoom 5 exposes too little longitude to reach geometry beginning around 8.55°E; Corsica is outside the view. Corsica itself is compact and would fit easily if centred from its own bounds. Its failure is primarily the region-camera path, while the full-France failure is the incompatible fixed zoom/bounds/canvas combination. Fixed zoom 8 also gives no source-level guarantee that every large or unusually shaped department fits.

Wine region and appellation views are geometry-informed but not canvas fits. Each search record stores the complete feature bounds. `map_view_for_feature(...)` passes one feature's bounds to `map_view_from_bounds(...)`; `map_view_for_region(...)` unions every appellation bound in the selected region, calculates the same view, then applies the `0.75` region boost (`app/utils/wine_search.py:33-54,196-264`). The centre is the arithmetic bounds midpoint. Zoom uses the larger of longitude span and `latitude span × 1.45`, adds a fixed `1.35` padding multiplier, applies `log2(360 / padded_span) - 1.1`, and clamps to 5.0–11.5. Canvas width, canvas height, Web-Mercator latitude distortion, and orientation are not inputs. Consequently the result is a useful heuristic but cannot promise that a region/appellation fits a 296×500 phone map and a 772×620 tablet map. The initial all-Wine figure is another fixed France-centred zoom-5 view (`app/utils/wine_figures.py:137-160`).

#### Resize, orientation, and persistence ownership

There is no Guide or Wine callback whose input is map dimensions, browser resize, or orientation. CSS/Plotly resize the canvas; MapLibre then recalculates its bounds-derived minimum against the new aspect ratio. The Python canonical centre/zoom is not recalculated. Crossing 600 px also changes the Wine height from 620 to 500 px, and crossing 1050 px changes both its width composition and height (`assets/styles.css:2733-2781`). Guide `svh` height can change with orientation or browser chrome even without crossing a media query (`assets/styles.css:3706-3709`).

For Guide, `map-view-store-mainpage` records relayout `map.zoom` and `map.center` with a region/department/arrondissement ownership key. Geography input clears stored camera values; department and arrondissement rating-only rebuilds reuse a valid stored manual view and reject stale geography (`app/callbacks/guide.py:99-161,511-597,635-671`). The region path always rebuilds its fixed France-centred view and does not consume the stored camera (`app/callbacks/guide.py:599-606`). An autosize-only relayout is ignored; if a browser resize/bounds clamp emits `map.zoom` or `map.center`, the current code can record that result as though it were manual. Whether Plotly emits those fields on orientation change requires browser validation.

For Wine, region/appellation dropdowns independently generate the canonical `uirevision`, zoom, then centre patch and update `map-view-store` with the same geography ownership. Manual relayout is accepted only for that owner; stale relayout is rejected. Route initialisation rebuilds the full figure from the Store, while unrelated outline/restaurant/hover patches do not own camera fields (`app/callbacks/wine.py:170-315,607-645,708-738`; `tests/test_wine_callbacks.py:336-551`). Autosize-only relayout is likewise ignored, but a resize event containing map camera fields can enter the Store. No static test proves the renderer's final camera after a resize.

#### Recommended smallest first implementation: Guide canonical fitting only

Do not start by lowering zoom 5 or deleting `METROPOLITAN_FRANCE_MAP_BOUNDS`: the former still fails at some aspect ratios, while the latter removes useful pan/zoom-out containment. The smallest coherent first stage is Guide-only and should make canonical fitting and interaction constraints two explicit calculations:

1. Add one pure Web-Mercator fit helper that accepts geography bounds, rendered map width/height, and a modest pixel padding, and returns centre/zoom. Use the deployed union bounds for France, selected geometry bounds for every region (including Corse), department bounds, and arrondissement bounds. This replaces the current Guide constants only for canonical views.
2. Supply the actual `.guide-map-panel` content-box width and height through one Guide page-level memory Store updated initially and by a narrowly scoped `ResizeObserver`. The existing boolean responsive-input Store is insufficient because fit depends on both dimensions and aspect ratio, not merely the 1250 px mode.
3. Retain a finite France-wide MapLibre bounds constraint, but aspect-pad that constraint enough for the calculated canonical France fit at the current canvas. The fit target and the interaction envelope must be separate: the former includes the selected geometry; the latter still prevents users panning or zooming out into irrelevant world space. Tests should assert that the requested fitted zoom is not below the effective minimum produced by that envelope at supported dimensions.
4. Preserve `map-view-store-mainpage` as the sole post-fit camera owner. Geography change and a resize while still in canonical mode may calculate a new fit; a stored manual view for the same geography must survive resize/orientation. Do not let a programmatic resize relayout silently reclassify the canonical view as manual—this transition needs an explicit flag/token or verified event gate.

This stage can be reviewed independently of Wine and without changing gestures. Pure tests can cover every deployed region/department/arrondissement at representative 320×448, 354×608, 772×736, and 994×736 canvases, including Corse and full France. Real-browser checks must still verify ResizeObserver timing, MapLibre's final clamped camera, orientation changes, and manual-view survival. Once that contract works, the same fit helper can replace Wine's span heuristic in a separate stage; Wine's region boost should then be reconsidered because deliberately zooming in after a fit conflicts with a strict “entire geography visible” contract.

### Proposed state machine at no more than 1250 px

| State | Visible result | Transition |
| --- | --- | --- |
| `geography-only` | Canonical region/department/arrondissement view; no selected restaurant. | Geography selection resets camera ownership and restaurant selection. |
| `browsing` | Restaurant markers for the active rating filters; no details selection. | Tap a valid restaurant marker to enter `restaurant-selected`. Pan/pinch changes only camera state. |
| `restaurant-selected` | The selected marker has a persistent visual treatment and the corresponding details panel sits immediately below the map. | Tap another valid marker to replace the selection; pan/pinch/orientation retain it; geography or a rating change that removes the restaurant clears it. |

A tap on an outline or empty map area should not fabricate a restaurant selection. A small movement that MapLibre interprets as a pan must not replace the current selection. These are behavioural requirements, but the tap-versus-pan threshold is renderer-owned and must be validated rather than inferred from Python callbacks.

### Proposed layout and gesture contract

| Concern | Smaller-screen contract | Implementation boundary |
| --- | --- | --- |
| Horizontal gutters | Keep normal sheet padding around search, selectors, filters, prose, details, and the rating legend. Let only `.guide-map-panel` break out to the viewport edges. The full-bleed rule must not alter desktop or the other pages. | Guide-scoped CSS at `max-width: 1250px`; a calculated full-viewport width/negative inline margin is sufficient. Check vertical-scrollbar and safe-area behaviour before fixing exact values. |
| Height | Give the map a stable, substantial working area: prototype approximately 65–75% of the small viewport with sensible phone/landscape minima and tablet maxima. Prefer an `svh`-based primary height with a `vh` fallback; `svh` avoids repeated jumps as mobile browser chrome expands or collapses. Use `dvh` only if device testing shows the resizing is desirable rather than distracting. | CSS. Candidate values such as `height: clamp(28rem, 72svh, 46rem)` are starting hypotheses, not a committed cross-device constant. Short landscape needs its own check and may need a lower minimum. |
| One-finger gesture | A gesture beginning on the map pans the map. The map is the principal surface, so one-finger panning should not be disabled merely to make page scrolling easier. | Existing MapLibre/Plotly interaction; real iOS Safari and Android Chrome testing required. |
| Pinch/double tap | Pinch zoom remains available. Observe double-tap behaviour before deciding whether it should zoom; no application callback currently requires double-click. | Renderer behaviour and supported Plotly configuration where exposed; device testing required. |
| Page scroll | A one-finger gesture beginning outside the map scrolls the document. Users must be able to reach details immediately below and then return to the map without a trapped page. Do not apply a broad `touch-action` override until the rendered MapLibre canvas is tested. | Mostly browser/renderer behaviour. CSS can provide clear space immediately before/after the map but cannot prove gesture arbitration. |
| Wheel/trackpad | At no more than 1250 px, wheel/trackpad scrolling should favour page movement rather than unexpectedly zooming the map. | A page-scoped responsive update to the public `dcc.Graph.config.scrollZoom` property is supported; verify that changing config does not remount or reset the figure. |
| Modebar | Hide the current Plotly modebar at no more than 1250 px. Its small desktop controls duplicate pan/pinch and geography-reset paths, and the present button set is not a coherent touch toolbar. If testing reveals a real need for reset, add one explicit application-level “Reset map view” action later rather than retaining the desktop modebar. | Public `dcc.Graph.config.displayModeBar`; page-scoped responsive callback. Desktop configuration remains unchanged. |
| Marker selection | A marker tap selects by the existing stable restaurant index, never by curve number. The selected restaurant must gain a persistent visual treatment that survives camera changes. Do not enlarge every marker indiscriminately; dense departments need testing for overlap and wrong-marker activation. | Callback/state and supported Plotly trace configuration or a dedicated selection-overlay trace. CSS alone cannot style one Plotly point. |
| Details | Keep details directly after the full-bleed map but inside normal content gutters. Add an explicit selected heading/summary if needed; do not place the full card as a floating map overlay that obscures geography. | Existing layout order plus Guide-scoped CSS; selection content remains callback-owned. |
| Viewport persistence | Preserve the current geography-owned `map-view-store-mainpage` rules. Orientation/resize should resize the canvas without changing the stored centre/zoom or claiming a new geography. | Existing callbacks plus browser validation. Bounds-derived effective minimum zoom can change with canvas aspect ratio. |

### Callback and state ownership

The current `restaurant-details` callback is not enough for persistent visual state because its output is rendered content rather than a stable selection contract. A later implementation should add one page-level selected-restaurant Store keyed by the existing restaurant index. One selection callback should own that Store from validated `map-display.clickData` plus geography/rating reset inputs. Details and marker-highlight callbacks should read the Store; they should not independently interpret clicks and become competing selection authorities.

The complete-figure callback should continue to own geography, ratings, traces, and camera application. A selected-marker overlay or selected-point patch must be reapplied from the Store after a full figure rebuild. The map-view Store remains camera-only and must not be overloaded with restaurant selection. The existing hover cursor clientside callback is desktop decoration, not selection state (`app/callbacks/guide.py:164-185`).

Desktop remains unchanged in the first implementation: fixed Guide composition, visible current modebar, wheel zoom, hover labels, click-to-details, and geography-owned viewport persistence at 1251 px and wider. Persistent selected-marker styling could later be shared with desktop, but the smaller-screen prototype must not require that expansion.

### Risks, minimal prototype, and device validation

Likely regressions are horizontal overflow from the full-bleed calculation, the fixed header or safe areas covering map edges, orientation changes producing an unusable minimum height, MapLibre bounds recentering after resize, wheel/config changes resetting the figure, and selection styling targeting the wrong trace after complete figure reconstruction. Enlarging marker hit areas may make dense points harder rather than easier to select.

The minimal Guide prototype should therefore be layout-only: make the existing map full-bleed at no more than 1250 px and replace fixed `vh`-based sizing with one `svh`-backed height rule, while leaving callbacks, gestures, selection, and desktop untouched. This independently reviewable CSS stage answers whether the larger surface improves browsing before callback/config work is layered onto it.

Real-device acceptance criteria:

- iOS Safari and Android Chrome, phone portrait/landscape and tablet portrait/landscape, show no horizontal document overflow and no clipped attribution;
- browser chrome expansion/collapse does not repeatedly jump the map height or lose the camera;
- one-finger pan and pinch zoom work, while swiping before/after the map scrolls the page normally;
- a small pan does not emit a false marker selection, and realistic markers can be selected in dense and sparse departments;
- selected marker and details stay associated through pan, pinch, orientation, and browser-chrome changes, then reset on the documented geography/rating transitions;
- the modebar/config decision is tested with touch and a narrow desktop window, not inferred from viewport emulation alone.

## Wine map smaller-screen contract

### Current interaction and callback ownership

The complete Wine figure has one AOC `Choroplethmap` trace at index 0, fixed one-/two-/three-star restaurant traces at indices 1–3, and regional outline layer 0 (`app/utils/wine_figures.py:7-19,93-160`). The AOC trace starts with `selectedpoints=[]`; its selected style lowers opacity to 0.58 while unselected polygons remain at 1.0 (`app/utils/wine_figures.py:111-131`).

The current hover callback has sole practical ownership of `selectedpoints`: validated AOC `hoverData` populates the fixed HTML overlay and patches the hovered feature index; unhover clears the list (`app/callbacks/wine.py:49-107,740-756`). This is transient desktop preview, not durable selection.

The current API event is unequivocally `wine-map-graph.clickData`. `update_wine_info(...)` passes it directly to `build_wine_info_response(...)`, which resolves the stable `location` feature ID, checks the appellation cache, then consumes the per-session request count and calls `gpt-4.1-mini` for an uncached valid AOC (`app/callbacks/wine.py:33-46,484-575,769-783`). Restaurant clicks and malformed payloads fail closed, but an AOC click is both selection-like input and submission; there is no confirmation boundary.

Camera ownership is separate and should remain so. Dropdown values drive a geography-specific `uirevision`, then zoom, then centre patch. `map-view-store` accepts manual `map.zoom`/`map.center` only for the currently owned region/appellation (`app/callbacks/wine.py:170-315,623-645,708-738`). Outline visibility, restaurant visibility, and hover each own separate figure fields through `Patch`; a new selection path must not add another writer to those same fields without consolidation.

### Proposed state machine at no more than 1250 px

| State | Visible result | Allowed events |
| --- | --- | --- |
| `none` | No persistent AOC highlight. Selection panel is empty/hidden and no request action is enabled. | Tap a valid AOC or choose an appellation to enter `selected`. Region change, appellation clear, or route unmount remains `none`. |
| `selected(feature_id)` | Exactly one AOC is persistently highlighted. A visible panel names its appellation and region and exposes an explicit “Get appellation details” action. No API request has occurred. | Tap another AOC or choose another appellation to replace selection; clear/change region to reset; press the explicit action to enter `requesting`. Pan/zoom changes camera only. |
| `requesting(feature_id, request_id)` | Selection remains highlighted; action is disabled and loading is visible. | Completion for the same feature/request enters `ready` or `error`. A later selection may replace the visible selection, but the old response must not render against it. |
| `ready(feature_id)` | Generated information is displayed and visibly labelled with the submitted appellation. | Tap/select another appellation to return to `selected`; resubmit only through the action. |
| `error(feature_id)` | A scoped error appears for that selected appellation and the explicit action can retry. | Change selection or retry. |

The critical invariant is: map `clickData` never invokes the API in smaller-screen mode. It may only update validated selection state. A pan, pinch, or tap that does not resolve an AOC therefore cannot consume a request.

### Selection, hover, dropdown, and reset ownership

Add one page-level memory Store, conceptually `wine-selected-appellation-store`, containing at least the stable `feature_id`. It must be distinct from `map-view-store`, because selection and camera have different reset/persistence rules. One selection reducer callback should own it:

- at no more than 1250 px, a valid AOC map tap selects that feature without requesting information;
- at no more than 1250 px, `wine-appellation-search.value` selects the same feature and retains its existing camera navigation;
- clearing the appellation, changing `wine-region-selector`, or leaving `/wine` clears selection and any pending selection panel;
- page-level placement means route unmount naturally discards state;
- restaurant clicks and malformed/stale AOC IDs leave selection unchanged or fail closed according to a tested contract.

The region dropdown currently scopes appellation options and camera navigation; it does not filter polygons out of the figure. The selection panel must therefore always show the selected feature's actual region. The first prototype should not force a map tap back into `wine-appellation-search.value`, because doing so would also trigger the existing canonical camera jump. Map-tap selection and dropdown navigation can share the selected Store while retaining those distinct camera effects. If product testing finds that divergence confusing, synchronising the dropdown is a later explicit decision, not an incidental callback side effect.

Persistent and hover styling must have one figure-field authority. Refactor the existing highlight patch so it reads both hover data and selected Store state and remains the only callback writing AOC `selectedpoints`:

- at no more than 1250 px, ignore hover for styling and patch the persistent selected feature index;
- on desktop, preserve the current behaviour exactly: validated hover supplies the temporary feature index and unhover clears it; desktop map click does not populate the smaller-screen selection Store;
- the fixed desktop hover overlay remains hover-owned and can stay hidden/unused on smaller screens;
- region/appellation reset patches `selectedpoints=[]` through the same authority.

This uses supported Dash Stores, Plotly `clickData`/`hoverData`, and `Patch`. No DOM-level JavaScript is justified by the static inspection.

### Explicit submission and stale-request protection

The selection panel should sit immediately below or adjacent to the map in the stacked Wine layout, before the generated-information area. It identifies the current appellation/region and contains the only smaller-screen submission action. The LLM callback should take that button's `n_clicks` as its request Input and the selected Store as State. The existing `build_wine_info_response` logic can be narrowed to accept a validated feature ID/feature rather than pretending submission still originated from map `clickData`.

Submission should retain the current cache-before-request-limit order. The action should be disabled while its callback is running using supported Dash callback `running` output if retained by the installed Dash version. API results should be stored/rendered with the submitted `feature_id` (and, if necessary, a monotonically increasing request token); the rendering callback displays a result only when that ID still matches current selection. This prevents a slow response for A from being presented after the user selects B. Disabling during the request plus the existing cache handles ordinary duplicate taps; true cross-worker in-flight deduplication would require a shared backend or lock and is not provided by the current process-local `SimpleCache`, so it must not be claimed by client tests.

Changing region or clearing selection should immediately hide the selection panel's action/result association. A result arriving later may remain cacheable but must fail the selected-ID render check. No request should be made when the selected ID is absent, stale, outside the lookup, or produced by a restaurant trace.

For the first smaller-screen implementation, desktop remains unchanged at 1251 px and wider: hover overlay/highlight and direct AOC click-to-request continue. The submission callback can distinguish the responsive Store and triggering input so desktop `clickData` follows the existing path while smaller-screen `clickData` is selection-only. Sharing the explicit-action model across desktop would be cleaner long term and reduce accidental API calls, but it is a product change beyond the minimum touchscreen stage and should be decided after the two-step model is validated.

### Layout, gestures, risks, prototype, and validation

Wine remains a stacked map-then-information composition below 1050 px (`assets/styles.css:2738-2762`). The map does not need the Guide's browsing-scale full-bleed contract by default: its primary smaller-screen task is selecting a large polygon, then acting in the adjacent selection panel. Keep the map within the Wine sheet for the prototype, retain the hidden modebar, and place the persistent selection panel directly after the map so it stays visible in reading order. Reassess the fixed 500/620 px heights only after the selection flow is usable.

Pan and pinch remain navigation gestures. They may update `map-view-store`, but must not select, submit, clear the panel, or overwrite selected styling. A tap after a small pan is the key real-device ambiguity; even if Plotly emits `clickData`, the two-step contract limits the consequence to selection rather than an API call.

Likely regressions are competing `selectedpoints` patches, hover clearing a persistent selection, changing fixed trace indices, full initial figures overwriting later patches, selector navigation and map selection disagreeing, region changes leaving stale dropdown/selection values, slow responses rendering under a newer selection, and rapid action taps issuing duplicate uncached requests. Camera regressions remain possible because selection/dropdown changes and manual relayout are separate authorities.

The minimal Wine prototype should include only: the page Store, map-tap/appellation-dropdown selection reducer, persistent `selectedpoints` patch, compact selection panel, and explicit action replacing map-click submission at no more than 1250 px. Keep restaurant/outline patches, prompt/rendering, camera ownership, and desktop direct-click behaviour otherwise unchanged. Tests should prove that selection alone never calls OpenAI before visual polish is added.

Real-device acceptance criteria:

- first tap selects/highlights exactly one AOC and shows its correct name/region without an API request;
- tapping another AOC replaces selection and still makes no request;
- only the explicit action produces one request, becomes disabled while pending, and preserves cache-before-limit behaviour;
- pan, pinch, small pan-then-lift, restaurant-marker taps, and empty-map taps never submit;
- selection survives pan/zoom/orientation, while region change, appellation clear, and route navigation reset it;
- a stale response cannot appear beneath a newer selection, and rapid double taps do not produce duplicate ordinary requests;
- desktop hover, unhover, click-to-request, camera patches, outline toggles, and restaurant trace indices remain unchanged.

## Shared touchscreen findings

### Touch targets and spacing

Rendered and source-backed target sizes are consistently smaller than comfortable touch dimensions:

| Target | Current size or rule | Source |
| --- | --- | --- |
| Hamburger | 24×18 px | `assets/styles.css:124-134` |
| Navigation links | 40 px high when open at 390 px | `assets/styles.css:166-175` |
| Footer GitHub link | 28×28 px | `assets/styles.css:285-301` |
| Shared action buttons | 34 px high | `assets/styles.css:1084-1099` |
| Guide selectors/input/buttons | 34 px high | `assets/styles.css:424-437,484-513` |
| Analysis/Economics/Wine selectors | generally 34 px minimum | `assets/styles.css:1252-1264,2081-2100,2402-2418` |
| Rating buttons | 68×30 px | `assets/styles.css:1870-1886` |
| Dropdown options | Dash default 35 px | Dash 2.18 `dcc.Dropdown` contract |
| Chip remove icon | about 17.5×20.8 px rendered | `.Select-value-icon`; `assets/styles.css:1283-1286,1611-1623` |
| Guide modebar buttons | about 24×26 px rendered | `app/layouts/layout_main.py:324-331` |
| Guide restaurant markers | 9–11 px | `app/utils/guide_figures.py:224-266` |
| Wine restaurant markers | 8 px | `app/utils/wine_figures.py:66-90` |

Spacing between control groups is usually 8–14 px, which helps prevent adjacent activation, but it does not compensate for undersized controls. Rating buttons wrap below 768/900 px, yet remain 30 px tall (`assets/styles.css:3151-3196,3421-3471`).

### Pointer-dependent behaviour

- Hover-only or hover-primary content exists in the Guide search explanation, all Analysis charts/maps, Economics charts/maps, Guide/Wine restaurant tooltips, and Wine's AOC overlay.
- No application callback intentionally depends on double-click. Plotly/MapLibre built-in double-click/double-tap behaviour is not explicitly configured, so zoom/reset behaviour should be observed rather than inferred.
- Only Guide explicitly enables wheel zoom. Other graphs hide modebars and leave `scrollZoom` unspecified in their graph configs (`app/layouts/analysis.py`, `app/layouts/economics.py`, `app/layouts/wine.py`).
- The MapLibre canvas rendered with `touch-action: none` from the third-party control and `tabindex="0"`. The application CSS has no `touch-action` override. Whether one-finger map movement traps page scrolling, and whether two-finger page gestures work consistently, requires device testing.

### Shared state and callback assumptions

- Hamburger, rating, restaurant-overlay, outline, and detail toggles are click-count based. They accept taps, but accidental rapid double taps can advance parity twice (`app/callbacks/navigation.py:6-18`; `app/utils/star_filters.py:20-39`; page callbacks cited above).
- Guide and Wine reject stale relayout data by geography ownership. Economics keeps manual view until granularity changes. Analysis does not persist view. These distinctions must remain visible in any touch implementation (`tests/test_guide_callbacks.py:51-180`; `tests/test_wine_callbacks.py:336-551`; `app/callbacks/economics.py:183-218`).
- Dropdown menus, keyboard focus, and map gestures may emit callbacks close together. Wine is particularly sensitive because complete-figure initialisation and multiple `Patch` callbacks share the figure without sharing field ownership (`app/callbacks/wine.py:607-767`).
- Navigation menu state is not closed explicitly after route selection; route replacement may remove it with the page, but direct-route and back-navigation behaviour should be checked. `assets/scroll-script.js:1-21` also performs immediate and delayed smooth scroll after Analysis/Economics/Wine nav clicks, which can interact with mobile browser scroll restoration.

## Responsive CSS audit

The responsive cascade is substantial and layered rather than governed by one breakpoint system:

- global shell: 1400 px;
- shared editorial tokens/primitives: 1366, 1024, 768, 600, and 480 px;
- legacy tablet block: 1250 px;
- Wine: 1050 and 600 px;
- Economics: 1200, 900, and 600 px;
- Analysis: 1200, 900, 600, and 480 px;
- Guide: desktop at 1251 px, then 1250, 768, 600, and 380 px.

Locations: `assets/styles.css:2791-3364,3367-3596,3598-3834`.

Consequences and gaps:

- The same token values are redefined at 1366, 1250, 1200, 1024, 900, and 600 px. Final behaviour depends on source order and page-specific specificity.
- The 1250 px legacy block still applies page padding and older Guide layout rules; later Guide rules deliberately supersede it. Removing or consolidating either block without full-page checks would be risky (`assets/styles.css:2841-3094,3653-3834`).
- Analysis and Economics still use large phone top-margin clamps. Wine now aligns its sheet with the 70 px small-screen header, so map work should not reintroduce a second vertical offset there (`assets/styles.css:2764-2768,3355-3360,3528-3537`).
- There are no active `pointer: coarse` or `hover: none` queries. This is now intentional for dropdown searchability, whose policy is viewport-based; safe-area, dynamic-viewport, and reduced-motion gaps remain separate concerns.
- The fixed header does not use safe-area insets, and fixed-height/`100vh` rules do not use dynamic viewport units. iOS browser chrome, notches, and landscape safe areas remain untested (`assets/styles.css:54-73,314-343`).
- No general rule raises controls, options, chip removers, map controls, or links to touch-sized targets.
- The Economics multi-select cap is an actual cascade defect, not just a missing enhancement (`assets/styles.css:2148-2151`).
- Phone maps use fixed or minimum heights: Guide 420 px minimum, Economics 700 px, Wine 500 px. These values should be judged in context rather than normalised globally because the pages have different interaction roles.

## Touch-related accessibility considerations

This is limited to issues directly coupled to touchscreen changes:

- `hamburger-icon` is a `div` with `n_clicks`, but no button role, keyboard focus, accessible name, or `aria-expanded` state (`app/components/shared.py:127-136`). Increasing its hit area without fixing semantics would leave switch-control and keyboard users behind.
- Visible `H6`/`P` selector headings are not programmatically associated with the React Select combobox inputs. Rendered comboboxes had no `aria-label` or `aria-labelledby`. Any selector reconfiguration should preserve or improve accessible naming.
- Rating buttons contain icon images without `alt` or button-level accessible names. Their visible distinction is icon count/colour, and active/inactive state is class/opacity rather than `aria-pressed` (`app/layouts/analysis_shared.py:32-89`; `app/layouts/layout_main.py:93-245`). Touch target work should include persistent pressed-state semantics.
- The Wine hover overlay is not an accessible substitute for tappable content. The click-generated panel is the stronger persistent path, but map polygons and marker targets need clear tap/focus behaviour.
- Hover colour changes should not be reused as the only touch feedback. Existing active classes are persistent and should remain the primary state signal.
- The footer GitHub link already has an accessible label; its issue is target size, not naming (`app/components/shared.py:155-181`).

## Testing position and opportunities

Current automated coverage is strong for data and state contracts but does not prove responsive browser rendering, real gestures, or software-keyboard suppression:

- `tests/test_responsive_input.py` checks the root memory Store, its safe initial state, the 1250 px policy constant, all 14 governed dropdown IDs, initial `searchable=False`, preserved values/options/multi/clear contracts, Guide text input, page-scoped searchable outputs, viewport listener source, and continued Wine `search_value` registration.
- `tests/test_layouts.py:80-232` checks page IDs, shared classes, Wine selector defaults, toggle defaults, and hover-overlay structure.
- `tests/test_guide_callbacks.py:51-180` checks geography-owned viewport resets and persistence.
- `tests/test_map_constraints.py:25-116` checks MapLibre bounds and stored view application.
- `tests/test_wine_callbacks.py:336-551` checks patch order, stale-view rejection, and manual view persistence; `tests/test_wine_callbacks.py:931-942` checks hover callback isolation.
- `tests/test_wine_search.py` checks both no-query complete appellation options and typed exact/fuzzy search; `tests/test_wine_figures.py:10-137` checks AOC trace identity, hover contract, bounds, and fixed restaurant traces.
- `tests/test_economics_callbacks.py:11-48` checks toggle parity and section visibility, but not the full callback with an empty/cleared region value.
- `tests/test_routes.py:4-13` checks route shells only.

Remaining realistic additions:

1. Guide helper/callback tests for valid restaurant selection, invalid outline clicks, rating/geography reset, full-figure reselection, and strict separation between selected-restaurant and camera Stores.
2. Wine helper/callback tests for `none → selected → requesting → ready/error`, region/appellation resets, one `selectedpoints` writer, zero request calls from map selection, explicit-action submission, stale-result rejection, and ordinary duplicate-action suppression.
3. A rendered browser smoke suite at 320, 390, 820, 1024, 1250, and 1251 px checking Guide full-bleed width/height/overflow, details order, responsive config, Wine selection-panel order, and state survival across resize. The repository has no browser-test dependency today, so this should be introduced only if its maintenance cost is accepted.
4. Manual iOS Safari and Android Chrome passes for pan/page-scroll arbitration, pinch/double-tap, tap-after-pan payloads, marker/polygon selection, orientation/browser chrome, camera persistence, and Wine request counts. Python figure tests cannot prove these renderer behaviours.

## Practical device and viewport matrix

Keep the routine matrix small; use physical devices where available and browser device emulation only as a supplement.

| Priority | Browser/device class | Viewport or representative device | Orientation/input | Guide and Wine map checks |
| --- | --- | --- | --- | --- |
| Core | Desktop Chrome or Safari | about 1440×900 | Mouse and physical keyboard | Guide fixed layout, modebar, wheel zoom, hover, click-to-details, and Wine hover/direct click-to-request remain unchanged. |
| Core | Narrow desktop browser | 390×844 window | Mouse and physical keyboard | Exercise the same ≤1250 px map contract without pretending mouse input makes it desktop layout: full-bleed Guide, page scroll, selection persistence, and Wine explicit action. |
| Core | iOS Safari, modern iPhone | about 390×844 | Portrait touch | Guide full-bleed height, pan/pinch/page scroll, marker selection/details; Wine select-highlight-action flow and zero gesture-triggered requests. |
| Core | Android Chrome, standard phone | about 360×800 | Portrait touch | Same map contracts, with particular attention to tap-after-pan payloads, browser back gestures, and dynamic browser chrome. |
| Edge | iOS Safari or smallest supported phone | 320×568 | Portrait and landscape touch | Guide full-bleed overflow/attribution and short-height rule; Wine panel visibility and ability to reach the explicit action without obscuring the map. |
| Core | iOS Safari, iPad class | about 820×1180 and 1024×768 | Portrait then landscape touch | Guide useful map area and camera survival; Wine stacked layout, polygon selection, explicit request, and orientation persistence. |
| Core where feasible | iPad/Android tablet or convertible | representative tablet ≤1250 px | Touch plus attached keyboard/trackpad | Page/wheel/pan arbitration follows the smaller-screen contract and does not clear selection or double-submit. |
| Boundary | Desktop Chrome or Safari | 1250 px then 1251 px | Mouse and physical keyboard | Resize both directions: Guide bleed/height/modebar/config transition without camera or selection loss; Wine smaller-screen action versus desktop direct-click path remains unambiguous. |
| Boundary | Tablet/browser orientation crossing 1250 px, if available | representative portrait/landscape widths | Orientation change | Responsive Store refreshes without stale patches, duplicate API events, lost selection, or camera ownership changes. |
| Secondary | Android Chrome, tablet class | about 800×1280 and 1280×800 | Portrait and landscape touch | At 800/1280 the responsive policy changes across orientation; verify both map state machines and Wine request gating on each side. |

For each map-state check, establish a manual camera and a persistent selection before resizing or rotating. Verify the camera, selection, details/panel, and request count afterward. Test at least one dense Guide department, one sparse department, Wine AOC versus restaurant clicks, and the Wine action while uncached and cached. Browser emulation is useful for layout but cannot replace physical-device gesture or software-keyboard evidence.

## Priorities

1. **Guide map usable space and gesture evidence.** Prototype a full-bleed, `svh`-backed map without changing interaction callbacks, then test page scroll, pan, pinch, orientation, browser chrome, and camera persistence on real devices.
2. **Wine two-step selection before submission.** Separate AOC selection from the paid/request-limited API event, add persistent selection and an explicit action, and prove that map gestures cannot submit.
3. **Guide persistent restaurant selection.** Give the selected marker and its immediately following details one Store-backed state contract that survives camera changes and resets predictably on geography/rating changes.
4. **Smaller-screen graph configuration.** Hide the Guide modebar and prefer page scrolling over wheel zoom at no more than 1250 px only after the larger map prototype is tested; leave Wine's hidden modebar unchanged.
5. **Rendered camera and patch validation.** Validate Guide and Wine bounds, first view, resize/orientation behaviour, and Wine patch ownership at phone/tablet aspect ratios.
6. **Previously identified non-map cleanup.** Economics overlap, shared target sizing, header/footer/navigation, and other generic touchscreen work follow these map stages rather than leading them.


## Proposed small implementation stages

### Stage 1: responsive dropdown text-entry policy — implemented

The root `responsive-input-mode-store`, 1250 px viewport listener, safe `searchable=False` layout defaults, and four page-scoped public-property callbacks are in place. All 14 dropdowns follow the same viewport rule. Wine appellations use the complete region-scoped list when no typed query is available. No pointer/capability detector, duplicate component, internal React Select manipulation, CSS change, or map change was introduced (`app/callbacks/responsive.py`; `michelin_app.py`; the four page layout modules).

Validation completed in source/unit tests: Store/default presence, callback output coverage, stable dropdown contracts, Guide text input, Wine no-query and typed-query paths, focused layout/callback suites, and the full Python suite. A local desktop Chromium check also confirmed rendered searchability on both sides of 1250 px and Wine's selectable no-query menu. Still required: broader desktop interaction, iOS Safari, and Android Chrome checks at representative widths, orientation changes, an open menu during transition, and selected-value preservation. Software-keyboard suppression must be confirmed on physical devices.

### Stage 2: Guide full-bleed map prototype

Change only Guide smaller-screen CSS: selectors/prose/details keep their gutters, while the map breaks out to viewport width and uses one `svh`-backed height rule with a fallback. Do not change marker callbacks, modebar config, camera state, or desktop in this stage.

Validation: rendered width/overflow checks at 320, 390, 768, 820, 1024, and 1250/1251 px; iOS Safari and Android Chrome pan/pinch/page-scroll passes; portrait/landscape and browser-chrome changes; Guide map view persistence tests remain green.

### Stage 3: Wine two-step selection prototype

Add the page-level selected-appellation Store, selection reducer, single `selectedpoints` authority, compact selection panel, and explicit submission action at no more than 1250 px. Preserve desktop click-to-request for this prototype. Keep camera, outline, restaurant-overlay, prompt, cache, and trace-index contracts separate.

Validation: pure helper and callback-map tests for map/dropdown selection and resets; zero OpenAI calls from selection/gesture payloads; one call from explicit action; stale-result ID checks; cache/request-limit tests; fixed trace/layer tests; iOS/Android tap-versus-pan checks.

### Stage 4: Guide persistent restaurant state and responsive config

Add one selected-restaurant Store, persistent marker styling, and details rendering from that Store. Then use the existing responsive mode to hide the Guide modebar and disable wheel zoom at no more than 1250 px. Keep the geography-owned view Store as the only camera state.

Validation: marker-index resolution, full-figure rebuild/reselection, filter/geography reset, camera persistence, invalid outline clicks, dense-marker device tests, and desktop modebar/wheel regression checks.

### Stage 5: map gesture and camera hardening from device evidence

Adjust only reproduced defects in page scroll, pan/pinch, double-tap, orientation resize, bounds, or first-visible Wine camera order. Prefer public Plotly/Dash configuration and existing Store/`Patch` paths. DOM-level JavaScript remains unjustified unless supported events/configuration prove insufficient.

### Stage 6: non-map touchscreen backlog

Return to Economics overlap, shared control targets and semantics, header/navigation, and other page-specific findings after the two principal map surfaces have coherent behaviour.

## Cross-map regression risks

- Full-bleed Guide CSS can introduce horizontal overflow, interfere with safe areas/scrollbars, or accidentally escape the 1250 px scope and alter the fixed desktop composition.
- `svh`/`dvh` choices can make maps jump with browser chrome, dominate short landscape screens, or change MapLibre's bounds-derived minimum zoom.
- Graph config changes can remount or reset figures, alter wheel/page scrolling, or cause relayout payloads that overwrite geography-owned camera state.
- Persistent Guide selection can point at a trace/index removed by rating or geography changes unless selection is validated and reset before reapplying styling.
- Enlarged or overlaid marker styling can change which dense marker wins a tap; point size should follow observed selection failures rather than a global target rule.
- Wine `selectedpoints` cannot remain independently owned by hover and persistent selection. Two patch callbacks writing it would race or clear each other.
- Wine full-figure initialisation can supersede selection, outline, restaurant, or hover patches; each field still needs one explicit authority and tests.
- Changing Wine trace construction can invalidate `WINE_AOC_TRACE_INDEX == 0`, restaurant indices 1–3, outline layer 0, click validation, and existing tests.
- Region/appellation navigation, map selection, and manual camera storage can disagree if selected feature state is folded into `map-view-store` or dropdown values implicitly.
- Slow or duplicate Wine requests can consume session limits or show content for the wrong selection unless action running state and feature-keyed result rendering are enforced.
- Responsive callbacks must stay page-scoped so root Store changes do not target absent Guide/Wine components.

## Open questions requiring real browsers or devices

- Does a full-bleed Guide map need safe-area inset padding for attribution or controls in iOS landscape, or is edge-to-edge content safe on the supported devices?
- Which `svh` height range gives useful Guide browsing space without making short landscape page navigation awkward, and does `dvh` produce visible resize jumps?
- Does one-finger interaction beginning over the Guide map consistently pan rather than scroll, while gestures immediately outside it scroll the document?
- Does MapLibre emit Guide restaurant `clickData` after a small pan, and are 9–11 px markers practically selectable in Paris and other dense departments?
- Can Guide selected-marker styling survive complete figure updates without changing trace ordering or losing the stored manual camera?
- Does hiding the Guide modebar and disabling smaller-screen wheel zoom improve touch/narrow-window behaviour, or is an explicit reset action needed?
- On Wine, what `hoverData`/`clickData` sequence is emitted for tap, long press, small pan, and pinch on iOS Safari and Android Chrome?
- Does the single Wine `selectedpoints` authority reliably restore persistent selection after desktop unhover and after full initial figure creation?
- Should map-tap selection remain independent of the appellation dropdown/canonical camera, or do users expect the dropdown value and camera to synchronise immediately?
- Can Dash callback `running` state suppress practical duplicate action taps across the supported deployment, and is a stronger shared in-flight lock required for multi-worker production?
- Does the Wine zoom-then-centre patch show the requested first view at phone/tablet canvas sizes, particularly at the bounds-derived minimum zoom?
- Do Guide and Wine manual views persist after pinch and orientation changes exactly as they do after desktop pan/wheel input?

## Recommended first implementation stage

Implement **Stage 2: Guide full-bleed map prototype** first. It is a small, Guide-only CSS change with no callback, API, trace, or state migration. It will establish the real-device evidence needed for height and gesture decisions before the more consequential Guide selection/config work. The Wine two-step prototype should follow as its own review because it changes API-trigger ownership and needs dedicated callback, stale-result, cache, and request-limit coverage. The two implementations do not currently share code beyond the already implemented responsive-mode Store, so combining them would make review and regression diagnosis harder.
