# Touchscreen audit

## Scope and evidence

This is a fact-finding report for the current Michelin Dash application. It is not a redesign proposal. The live Dash Pages implementation is the baseline, and no application code was changed for this audit.

The audit covered:

- the shared header, navigation, footer, page shell, and 404 page;
- Guide, Analysis, Economics, and Wine layouts and callbacks;
- Plotly `dcc.Graph` configuration, MapLibre figures, hover/click payloads, and viewport stores;
- the complete active responsive cascade in `assets/styles.css`;
- the current Dash, Plotly, and Dash Bootstrap Components versions and `dcc.Dropdown` contract;
- existing layout, callback, figure, route, and map-constraint tests.

Static inspection was supplemented by rendered checks in the local app at 320×568, 390×844, 820×1180, and 1024×768. Those checks used a desktop Chromium browser with viewport overrides, not iOS or Android device emulation. They establish current dimensions, wrapping, overlap, focus targets, and overflow, but they do not prove mobile-browser gesture or on-screen-keyboard behaviour.

Relevant platform baseline:

- `assets/custom_header.html:4-9` includes `width=device-width, initial-scale=1`.
- `requirements.txt:1-2,12` specifies Dash 2.18, Dash Bootstrap Components 1.4.2, and Plotly 5.24; the inspected environment resolved Dash 2.18.2 and Plotly 5.24.1.
- Dash 2.18 `dcc.Dropdown` defaults to `searchable=True`, `clearable=True`, `optionHeight=35`, and `maxHeight=200` unless a layout overrides those properties.

The findings fall into distinct implementation lanes:

| Lane | Findings in this report |
| --- | --- |
| Shared application-wide | Header/menu/footer targets and semantics, default searchable dropdowns, 30–35 px control heights, breakpoint layering, safe-area/dynamic-viewport gaps. |
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

- searchable `wine-region-selector` and `wine-appellation-search`;
- `toggle-regional-outlines-wine`;
- `toggle-show-details-wine` and three restaurant-rating buttons;
- `wine-map-graph`, where AOC polygons are clicked to request information;
- a fixed hover overlay and generated AOC information panel.

Definitions: `app/layouts/wine.py:11-212`. Search, patch, hover, persistence, and information callbacks: `app/callbacks/wine.py:33-315,578-783`.

Current touch-relevant behaviour:

- Appellation text search is an intentional interaction. Its callback consumes `search_value` and scopes options by selected region, so disabling keyboard entry would change the feature (`app/callbacks/wine.py:685-706`; `app/utils/wine_search.py`). On-screen-keyboard behaviour, menu placement, and restoration of map visibility must be tested on iOS and Android.
- Region search is explicitly enabled but its options are a bounded region list. It could mechanically become a non-searchable selector without changing value-selection semantics, but doing so would remove an explicitly configured convenience and should be treated as a product decision (`app/layouts/wine.py:50-77`).
- AOC hover is not merely native Plotly decoration: it drives a fixed HTML overlay and a selected-polygon patch. Touch devices have no stable hover model, so the overlay/highlight path is not dependable as the sole preview (`app/callbacks/wine.py:49-107,740-756`; `assets/styles.css:2509-2539`). AOC tap/click is the durable path to generated information (`app/callbacks/wine.py:769-783`).
- Restaurant markers are 8 px and provide hover text only. Their click payload intentionally fails closed in the AOC information callback, so touch users receive no persistent restaurant detail from a marker tap (`app/utils/wine_figures.py:66-90`; `app/callbacks/wine.py:33-46,769-783`).
- The complete figure is produced once, then navigation, outline visibility, restaurant visibility, and hover selection patch separate owned fields. Touch changes must not add a second authority over these fields (`app/callbacks/wine.py:607-683,740-767`).
- Manual pan/zoom is stored only for the currently owned region/appellation. Selector navigation writes `uirevision`, then zoom, then centre. Bounds-derived minimum zoom depends on rendered canvas size (`app/callbacks/wine.py:170-315,623-645,708-738`; `app/utils/map_constraints.py:14-23`). Phone and tablet canvas sizes therefore need direct validation.
- At 390×844, selectors and toggles stack and the map is 322×500 px. At 320×568 it is 252×500 px because the legacy tablet padding still contributes inside the phone sheet. At 820×1180 the two selectors share a row, toggles occupy the next row, and the map is 740×620 px. At 1024×768 all four primary control groups fit on one row, but only narrowly; text zoom or longer localisation would force a different wrap (`assets/styles.css:2337-2408,2738-2788,2841-3094`).

## Dropdown and keyboard-entry audit

Every current `dcc.Dropdown` renders a text input because Dash defaults `searchable` to true. In the rendered phone check, tapping `region-dropdown` focused an `<input type="text" role="combobox">`, confirming that omission of the property is not equivalent to a native non-editable select.

| Page | Component ID | Definition | Intended choice | Can keyboard entry be disabled without changing selection semantics? |
| --- | --- | --- | --- | --- |
| Guide | `region-dropdown` | `app/layouts/layout_main.py:258-270` | One of 13 regions | Yes; set `searchable=False`. |
| Guide | `department-dropdown` | `app/layouts/layout_main.py:272-281` | One callback-populated department | Yes; list selection remains unchanged. |
| Guide | `arrondissement-dropdown` | `app/layouts/layout_main.py:283-300` | One Paris arrondissement | Yes; list selection remains unchanged. |
| Analysis | `region-dropdown-analysis` | `app/layouts/analysis.py:60-87` | Multi-select regions plus Select All | Yes; multi-selection and chip removal remain, although chip usability still needs work. |
| Analysis | `department-dropdown-analysis` | `app/layouts/analysis.py:147-175` | One region controlling department analysis | Yes. |
| Analysis | `arrondissement-dropdown-analysis` | `app/layouts/analysis.py:233-263` | One dynamically populated department | Yes. |
| Analysis | `granularity-dropdown` | `app/layouts/analysis.py:349-370` | One of three granularities | Yes. |
| Analysis | `ranking-dropdown` | `app/layouts/analysis.py:371-389` | Top 3, Top 5, or Paris | Yes. |
| Analysis | `star-dropdown-ranking` | `app/layouts/analysis.py:390-408` | One of three rating categories | Yes. |
| Economics | `category-dropdown-demographics` | `app/layouts/economics.py:38-63` | One of seven metrics | Yes. |
| Economics | `granularity-dropdown-demographics` | `app/layouts/economics.py:64-79` | All France or one region | Yes. |
| Economics | `demographics-dropdown-analysis` | `app/layouts/economics.py:80-101` | Multi-select regions plus Select All | Yes; chip/clear targets remain a separate issue. |
| Wine | `wine-region-selector` | `app/layouts/wine.py:50-64` | One wine region | Technically yes, but search is explicitly configured; confirm the intended convenience before changing it. |
| Wine | `wine-appellation-search` | `app/layouts/wine.py:65-79` | Search many appellations | No. `search_value` is part of the intended callback contract. |

`city-input-mainpage` is the only standalone text input and should remain keyboard-enabled (`app/layouts/layout_main.py:64-82`). No `dcc.Tabs`, sliders, checklists, or radio-item controls are currently present.

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
- There are no active `pointer: coarse`, `hover: none`, orientation, safe-area, or reduced-motion queries. Touch-specific behaviour is therefore treated only as width-dependent behaviour.
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

Current automated coverage is strong for data and state contracts but does not exercise responsive layout or real gestures:

- `tests/test_layouts.py:80-232` checks page IDs, shared classes, Wine searchable selectors, toggle defaults, and hover-overlay structure.
- `tests/test_guide_callbacks.py:51-180` checks geography-owned viewport resets and persistence.
- `tests/test_map_constraints.py:25-116` checks MapLibre bounds and stored view application.
- `tests/test_wine_callbacks.py:336-551` checks patch order, stale-view rejection, and manual view persistence; `tests/test_wine_callbacks.py:931-942` checks hover callback isolation.
- `tests/test_wine_figures.py:10-137` checks AOC trace identity, hover contract, bounds, and fixed restaurant traces.
- `tests/test_economics_callbacks.py:11-48` checks toggle parity and section visibility, but not the full callback with an empty/cleared region value.
- `tests/test_routes.py:4-13` checks route shells only.

Realistic additions during implementation:

1. Layout-unit tests for every intended `searchable` setting, graph config, semantic button property, and stable component ID.
2. Callback-unit tests for cleared multi-select values, rapid toggle sequences, and preservation/reset of each page's viewport contract.
3. A small rendered browser smoke suite at 320, 390, 820, and 1024 px checking `scrollWidth <= clientWidth`, no bounding-box overlap, visible controls, and expected stacking. The repository has no browser-test dependency today, so this should be introduced only if its maintenance cost is accepted.
4. Manual iOS Safari and Android Chrome passes for keyboard, gesture, tap/hover, and MapLibre camera behaviour. These cannot be replaced by Python figure tests.

## Practical device and viewport matrix

Keep the routine matrix small; use physical devices where available and browser device emulation only as a supplement.

| Priority | Browser/device class | Viewport or representative device | Orientation | Main purpose |
| --- | --- | --- | --- | --- |
| Core | iOS Safari, modern small/standard iPhone | about 390×844 CSS px | Portrait | Header/menu, keyboard selectors, one-finger page/map scroll, AOC/restaurant taps, 390 px overlap checks. |
| Core | Android Chrome, standard phone | about 360×800 CSS px | Portrait | Dropdown keyboard/menu behaviour, compact wrapping, MapLibre gestures, back navigation. |
| Edge | iOS Safari or responsive browser | 320×568 CSS px | Portrait | Header clipping, chip growth, narrow Wine map, smallest supported width decision. |
| Core | iOS Safari, iPad class | about 820×1180 CSS px | Portrait | Two-column-to-stack transitions, map heights, selector rows, long Analysis flow. |
| Core | iOS Safari, iPad class | about 1024×768 CSS px | Landscape | Analysis split charts/maps, Wine one-row controls, fixed header and short-height scrolling. |
| Secondary | Android Chrome, tablet class | about 800×1280 and 1280×800 CSS px | Portrait and landscape | Cross-engine MapLibre, dropdown, keyboard, and breakpoint confirmation. |

For routine changes, test one phone in each engine plus one iPad orientation relevant to the change. Run the full matrix for shared shell, dropdown, or map-interaction changes.

## Priorities

1. **Economics multi-select overlap on phones.** The 150 px wrapper cap overlaps the following controls while the selected chips grow beyond it.
2. **Touch target sizes across the shared shell and controls.** Hamburger, footer link, selectors, buttons, rating controls, clear/chip targets, Guide modebar buttons, and map markers are too small for comfortable touch.
3. **Unnecessary mobile keyboard invocation.** Twelve of fourteen dropdowns can retain their selection behaviour with search disabled; the Wine appellation search must remain editable, and Wine region needs an explicit decision.
4. **Touch-equivalent information for hover paths.** Wine AOC preview, restaurant hover text, chart values, and the Guide search explanation need durable tap/focus alternatives where the information matters.
5. **Phone header clipping and mobile vertical rhythm.** The 320 px title clips; large top gaps and fixed map heights make short viewports inefficient.
6. **Map gesture and viewport validation.** Guide/Wine persistence is well guarded in code, but touch pan, pinch, double-tap, page scroll, and Wine patch camera order remain browser-dependent.
7. **Analysis chip density and long phone flow.** No horizontal overflow was observed, but the default multi-select and 450 px graph pairs create a very long interaction path.
8. **404 and shared navigation edge behaviour.** Short-height layout, menu dismissal, route scroll, and safe-area behaviour are currently unverified.


## Client-side interaction boundary

Prefer native Dash component properties, semantic HTML, CSS media features, and supported Plotly or MapLibre configuration before adding custom JavaScript.

Custom client-side JavaScript may be justified where real-device testing demonstrates behaviour that cannot be controlled reliably through those mechanisms. Possible cases include visual-viewport changes caused by the on-screen keyboard, focus and scroll restoration, outside-tap handling, orientation-specific browser behaviour, or touch gesture disambiguation.

Any proposed JavaScript should be documented against a reproduced device-specific problem. The implementation plan should identify:

* the exact browser behaviour being corrected;
* why Dash, CSS, or graph configuration is insufficient;
* the DOM element or browser API involved;
* how the JavaScript communicates with Dash state, if necessary;
* cleanup and event-listener ownership;
* fallback behaviour when the browser API is unavailable;
* regression checks for desktop pointer and keyboard interaction.

Do not introduce a general touchscreen detection framework or globally override touch events. Keep client-side handling local to a demonstrated interaction defect.


## Proposed small implementation stages

### Stage 1: configuration-only selector audit

Set `searchable=False` only on confirmed list-selection dropdowns, keep Wine appellation search enabled, and decide Wine region explicitly. Add layout tests for every setting.

Validation: focused layout tests, then iOS Safari and Android Chrome checks that non-search selectors do not summon a keyboard and that multi-select/clear behaviour is unchanged.

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
- Changing `searchable` can alter React Select focus, typing, menu opening, and existing Wine search callbacks if applied too broadly.
- Enlarging marker hit areas can increase overlap and change which point/polygon wins a tap, especially Wine AOCs versus restaurant traces.
- Changing map config can break page scrolling, wheel behaviour, relayout payloads, or Guide/Economics/Wine viewport persistence.
- Reworking responsive rules can accidentally expose legacy 1250 px declarations or disturb `:has(...)`-scoped sheet/gutter rules.
- Changing click-count toggles to boolean state would be a callback-contract change, not a CSS refinement.
- Wine figure changes risk conflicting full-figure and patch authorities, fixed trace indices, outline layer index 0, or API-triggering click resolution.
- Mobile header changes can affect all routes, smooth-scroll targets, and desktop fixed-height Guide behaviour.

## Open questions requiring real browsers or devices

- Does opening each searchable dropdown on iOS Safari and Android Chrome resize, pan, or obscure the control/menu, and does closing the keyboard restore the prior scroll position?
- Can users reliably scroll the page when a one-finger gesture begins over each MapLibre map, or does the map trap the gesture? Is two-finger page scrolling discoverable?
- How do Plotly/MapLibre distinguish tap, pan, pinch, and double-tap on each page? Does a tap after a small pan emit unwanted `clickData`?
- Is Wine `hoverData` emitted on tap, long press, or not at all, and does the fixed overlay persist or conflict with the AOC information click?
- Are 8–11 px restaurant markers tappable at realistic zooms in dense areas, and which trace wins where a marker overlaps an AOC polygon?
- Does the Wine zoom-then-centre patch show the requested first view at phone/tablet canvas sizes, particularly at the bounds-derived minimum zoom?
- Do Guide and Wine manual views persist after pinch gestures exactly as they do after desktop pan/wheel input?
- How do iOS safe areas, dynamic browser chrome, text zoom, and landscape keyboards affect the fixed header, 100vh areas, and short-height pages?
- Does the navigation menu dismiss naturally after route changes, back navigation, outside taps, and orientation changes?
- What is the project's minimum supported phone width? The current layout avoids horizontal overflow at 320 px but clips the title and is severely compressed.
