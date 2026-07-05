# Touchscreen audit

## Scope and evidence

This report records the touchscreen audit and the first implemented responsive-input stage for the current Michelin Dash application. It is not a redesign proposal. The live Dash Pages implementation is the baseline.

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
- AOC hover is not merely native Plotly decoration: it drives a fixed HTML overlay and a selected-polygon patch. Touch devices have no stable hover model, so the overlay/highlight path is not dependable as the sole preview (`app/callbacks/wine.py:49-107,740-756`; `assets/styles.css:2509-2539`). AOC tap/click is the durable path to generated information (`app/callbacks/wine.py:769-783`).
- Restaurant markers are 8 px and provide hover text only. Their click payload intentionally fails closed in the AOC information callback, so touch users receive no persistent restaurant detail from a marker tap (`app/utils/wine_figures.py:66-90`; `app/callbacks/wine.py:33-46,769-783`).
- The complete figure is produced once, then navigation, outline visibility, restaurant visibility, and hover selection patch separate owned fields. Touch changes must not add a second authority over these fields (`app/callbacks/wine.py:607-683,740-767`).
- Manual pan/zoom is stored only for the currently owned region/appellation. Selector navigation writes `uirevision`, then zoom, then centre. Bounds-derived minimum zoom depends on rendered canvas size (`app/callbacks/wine.py:170-315,623-645,708-738`; `app/utils/map_constraints.py:14-23`). Phone and tablet canvas sizes therefore need direct validation.
- At 390×844, selectors and toggles stack and the map is 322×500 px. At 320×568 it is 252×500 px because the legacy tablet padding still contributes inside the phone sheet. At 820×1180 the two selectors share a row, toggles occupy the next row, and the map is 740×620 px. At 1024×768 all four primary control groups fit on one row, but only narrowly; text zoom or longer localisation would force a different wrap (`assets/styles.css:2337-2408,2738-2788,2841-3094`).

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
- Phone layout relies on large page-specific top margins such as `clamp(148px, calc(268px - 20vw), 190px)` for Analysis, Economics, and Wine. In rendered phone checks content began around 190–214 px below the viewport top despite a 70 px header (`assets/styles.css:2764-2768,3349-3354,3522-3531`).
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

1. A browser integration test at 1250 and 1251 px that reads Store data and rendered combobox editability, then resizes across the boundary and verifies selected values.
2. Callback tests for cleared multi-select values, rapid toggle sequences, and preservation/reset of each page's viewport contract.
3. A rendered browser smoke suite at 320, 390, 820, 1024, 1250, and 1251 px checking `scrollWidth <= clientWidth`, no bounding-box overlap, expected stacking, and selected values before/after `searchable` changes. The repository has no browser-test dependency today, so this should be introduced only if its maintenance cost is accepted.
4. Manual iOS Safari and Android Chrome passes for software-keyboard invocation, orientation changes, gesture, tap/hover, and MapLibre camera behaviour. Python component tests cannot prove the software keyboard stays closed.

## Practical device and viewport matrix

Keep the routine matrix small; use physical devices where available and browser device emulation only as a supplement.

| Priority | Browser/device class | Viewport or representative device | Orientation/input | Responsive-dropdown checks |
| --- | --- | --- | --- | --- |
| Core | Desktop Chrome or Safari | about 1440×900 | Mouse and physical keyboard | All dropdowns are searchable; typed Wine search filters; Tab/Enter work; Guide location remains editable. |
| Core | Narrow desktop browser | 390×844 window | Mouse and physical keyboard | All dropdowns are selection-only because width controls the policy; Guide location remains editable. |
| Core | iOS Safari, modern iPhone | about 390×844 | Portrait touch | Every dropdown opens without software keyboard; Guide location is the only text-entry control; Wine lists selectable appellations. |
| Core | Android Chrome, standard phone | about 360×800 | Portrait touch | Same keyboard distinction, plus menu placement, back-button dismissal, and selected-value preservation. |
| Edge | iOS Safari or smallest supported phone | 320×568 | Portrait touch | Keyboard distinction plus header clipping, chip growth, narrow Wine map, and minimum-width decision. |
| Core | iOS Safari, iPad class | about 820×1180 and 1024×768 | Portrait then landscape touch | Both orientations stay selection-only; retain values and verify Wine options and layout transitions. |
| Core where feasible | iPad/Android tablet or convertible | representative tablet ≤1250 px | Attached keyboard and/or trackpad/mouse | Dropdowns remain selection-only under the viewport rule; keyboard/mouse use must not clear values or double-fire callbacks. |
| Boundary | Desktop Chrome or Safari | 1250 px then 1251 px | Mouse and physical keyboard | Resize both directions; searchability changes, selected single/multi values persist, dependent options remain populated, and desktop typing returns at 1251 px. |
| Boundary | Tablet/browser orientation crossing 1250 px, if available | representative portrait/landscape widths | Orientation change | Store refreshes, open dropdown transition is usable, and selected values survive. |
| Secondary | Android Chrome, tablet class | about 800×1280 and 1280×800 | Portrait and landscape touch | At 800/1280 the policy changes across orientation; verify keyboard suppression below and search above the boundary. |

For every responsive-dropdown check, select at least one single value and one multi-select set before resizing or changing orientation, then verify values, dependent options, Wine appellation options, maps, and ranking/economics callbacks remain correct. Also cross the boundary with a menu open. For routine changes, test desktop mouse/keyboard, one phone in each engine, and one tablet mode relevant to the change.

## Priorities

1. **Economics multi-select overlap on phones.** The 150 px wrapper cap overlaps the following controls while the selected chips grow beyond it.
2. **Touch target sizes across the shared shell and controls.** Hamburger, footer link, selectors, buttons, rating controls, clear/chip targets, Guide modebar buttons, and map markers are too small for comfortable touch.
3. **Validate the implemented responsive dropdown policy on real devices.** All 14 dropdowns are selection-only at ≤1250 px and searchable at ≥1251 px; unit tests do not prove software-keyboard suppression, open-menu transitions, or value survival in the browser.
4. **Touch-equivalent information for hover paths.** Wine AOC preview, restaurant hover text, chart values, and the Guide search explanation need durable tap/focus alternatives where the information matters.
5. **Phone header clipping and mobile vertical rhythm.** The 320 px title clips; large top gaps and fixed map heights make short viewports inefficient.
6. **Map gesture and viewport validation.** Guide/Wine persistence is well guarded in code, but touch pan, pinch, double-tap, page scroll, and Wine patch camera order remain browser-dependent.
7. **Analysis chip density and long phone flow.** No horizontal overflow was observed, but the default multi-select and 450 px graph pairs create a very long interaction path.
8. **404 and shared navigation edge behaviour.** Short-height layout, menu dismissal, route scroll, and safe-area behaviour are currently unverified.


## Proposed small implementation stages

### Stage 1: responsive dropdown text-entry policy — implemented

The root `responsive-input-mode-store`, 1250 px viewport listener, safe `searchable=False` layout defaults, and four page-scoped public-property callbacks are in place. All 14 dropdowns follow the same viewport rule. Wine appellations use the complete region-scoped list when no typed query is available. No pointer/capability detector, duplicate component, internal React Select manipulation, CSS change, or map change was introduced (`app/callbacks/responsive.py`; `michelin_app.py`; the four page layout modules).

Validation completed in source/unit tests: Store/default presence, callback output coverage, stable dropdown contracts, Guide text input, Wine no-query and typed-query paths, focused layout/callback suites, and the full Python suite. A local desktop Chromium check also confirmed rendered searchability on both sides of 1250 px and Wine's selectable no-query menu. Still required: broader desktop interaction, iOS Safari, and Android Chrome checks at representative widths, orientation changes, an open menu during transition, and selected-value preservation. Software-keyboard suppression must be confirmed on physical devices.

### Stage 2: shared touch targets and semantics

Increase hamburger, navigation, footer, action, rating, selector, option, clear, and chip-remove hit areas. Convert or augment the hamburger as a semantic button and give rating controls accessible names/pressed state. Preserve IDs and callback contracts.

Validation: layout tests for semantics and IDs; 320/390/820/1024 rendered measurements; keyboard/switch-control spot checks; navigation callback tests.

### Stage 3: page layout defects

Fix the Economics selector overlap first. Then handle 320 px header clipping and review page-specific top spacing and map heights without applying one global map rule.

Validation: bounding-box overlap checks and screenshots at the four audit widths; all routes; portrait and landscape browser checks; full Python suite because shared CSS affects every page.

### Stage 4: durable touch information paths

Define which hover information must also be available by tap or persistent content. Start with Wine AOC preview and restaurant marker behaviour, then chart/map values and the Guide search explanation. Keep Wine click-to-generate safeguards and request limits intact.

Validation: callback/figure tests for payload routing; accidental restaurant/AOC tap checks; cached and uncached Wine flows; iOS/Android tap-versus-pan testing.

### Stage 5: map gesture and camera hardening

Only after real-device testing, adjust Plotly or MapLibre configuration and introduce narrowly scoped client-side JavaScript where supported component APIs cannot resolve a reproduced gesture, viewport, focus, or keyboard defect.

## Regression risks

- Raising shared control heights can alter multi-select wrapping, Wine's narrowly fitting 1024 px control row, Guide's fixed desktop composition, and page length.
- Changing `searchable` at runtime can alter React Select focus, typing, menu opening, and selected/search values. Wine is additionally sensitive because `search_value` drives its option callback, although the no-query branch intentionally supplies all available records.
- A root responsive Store can accidentally drive outputs on pages that are not mounted unless callbacks retain their page-local presence inputs.
- Resize/orientation listeners can duplicate across route changes or leave stale width state if their cleanup/ownership changes.
- A conservative non-searchable initial state can cause a brief desktop hydration delay; a searchable initial state can violate the first-touch requirement. This tradeoff must be measured.
- `window.dash_clientside.set_props` and runtime `searchable` updates should be revalidated when Dash is upgraded.
- Enlarging marker hit areas can increase overlap and change which point/polygon wins a tap, especially Wine AOCs versus restaurant traces.
- Changing map config can break page scrolling, wheel behaviour, relayout payloads, or Guide/Economics/Wine viewport persistence.
- Reworking responsive rules can accidentally expose legacy 1250 px declarations or disturb `:has(...)`-scoped sheet/gutter rules.
- Changing click-count toggles to boolean state would be a callback-contract change, not a CSS refinement.
- Wine figure changes risk conflicting full-figure and patch authorities, fixed trace indices, outline layer index 0, or API-triggering click resolution.
- Mobile header changes can affect all routes, smooth-scroll targets, and desktop fixed-height Guide behaviour.

## Open questions requiring real browsers or devices

- Do all 14 dropdowns avoid the software keyboard at ≤1250 px on iOS Safari and Android Chrome while Guide `city-input-mainpage` still invokes it normally?
- At ≥1251 px, do all dropdowns regain mouse/physical-keyboard search, including Wine typed filtering?
- Does changing the public `searchable` property preserve single/multi values, dependent options, menu state, focus, and callbacks in the Dash 2.18 React Select implementation, including when a menu is open during the transition?
- Do resize and orientation events cross the policy boundary reliably in iOS Safari and Android Chrome, including visual-viewport/browser-chrome changes?
- On a tablet with an attached keyboard or pointing device, is the intentionally selection-only ≤1250 px experience still practical?
- Does the conservative initial state produce a visible or usable delay before desktop search is enabled?
- Does the Guide location input resize, pan, or obscure the interface on iOS Safari and Android Chrome, and does closing its keyboard restore the prior scroll position?
- Can users reliably scroll the page when a one-finger gesture begins over each MapLibre map, or does the map trap the gesture? Is two-finger page scrolling discoverable?
- How do Plotly/MapLibre distinguish tap, pan, pinch, and double-tap on each page? Does a tap after a small pan emit unwanted `clickData`?
- Is Wine `hoverData` emitted on tap, long press, or not at all, and does the fixed overlay persist or conflict with the AOC information click?
- Are 8–11 px restaurant markers tappable at realistic zooms in dense areas, and which trace wins where a marker overlaps an AOC polygon?
- Does the Wine zoom-then-centre patch show the requested first view at phone/tablet canvas sizes, particularly at the bounds-derived minimum zoom?
- Do Guide and Wine manual views persist after pinch gestures exactly as they do after desktop pan/wheel input?
- How do iOS safe areas, dynamic browser chrome, text zoom, and landscape keyboards affect the fixed header, 100vh areas, and short-height pages?
- Does the navigation menu dismiss naturally after route changes, back navigation, outside taps, and orientation changes?
- What is the project's minimum supported phone width? The current layout avoids horizontal overflow at 320 px but clips the title and is severely compressed.
