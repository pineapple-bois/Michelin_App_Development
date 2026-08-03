# Agent Guide

## Purpose

This file is the orientation and safety guide for work on the Michelin Dash application. The architecture currently present in the repository is the baseline. This document is not a roadmap, backlog, or substitute for inspecting the code.

Begin every task by checking the working tree and reading the implementation that owns the requested behaviour. Preserve unrelated changes, verify assumptions against the current checkout, and keep changes within the authority granted by the task.

## Runtime and Deployment

- `Procfile` exposes the Flask server with `gunicorn michelin_app:server`.
- `.python-version` specifies Python `3.12`.
- `Aptfile` installs the deployment GIS packages `gdal-bin` and `libgdal-dev`.
- Production dependencies are pinned or constrained in `requirements.txt`; it also installs this repository as an editable local package so package metadata is available. `requirements_dev.txt` currently adds pytest only.
- GeoPandas reads repository GeoJSON through Pyogrio. Fiona is not a direct dependency.
- Local development runs with `.venv/bin/python michelin_app.py` or `python michelin_app.py` in an activated environment.
- `app/app_config.py` loads a root `.env` file when present and exposes a frozen `RuntimeConfig` through `CONFIG`.
- `pyproject.toml` owns the application package version. The major version is the active Michelin Guide year, so version `2026.0` selects `assets/data/2026/`.

Current environment variables:

- `OPENAI_API_KEY`: passed to the OpenAI client used by the Wine information callback.
- `OPENAI_REQUEST_LIMIT`: per-session generated-summary limit; default `10`.
- `FLASK_SECRET_KEY`: required in production. Local development generates a temporary key when it is absent, so sessions reset when the process restarts.
- `CACHE_TYPE`: Flask-Caching backend; `simple` is normalised to the full `SimpleCache` backend path.
- `CACHE_DEFAULT_TIMEOUT`: cache timeout in seconds; default `3600`.
- `FORCE_HTTPS`: explicit HTTPS redirect switch. It defaults to the detected production state.
- `DASH_DEBUG`: controls the local Dash debug flag; default false.
- `DYNO`, or production values in `APP_ENV`, `FLASK_ENV`, or `DASH_ENV`: mark the process as production.

`michelin_app.py` wraps Flask with `ProxyFix(x_proto=1)` so HTTPS checks use the proxy protocol header without trusting `X-Forwarded-Host`. Production requests allow only the apex and `www` custom domains. Host and path rejection run before HTTPS redirection and session initialisation; unknown paths bypass the Dash catch-all shell and return HTTP 404. Public page and callback requests initialise a session UUID and `request_count`, while framework/static requests do not. The default `SimpleCache` is process-local and is not shared between Gunicorn workers or dynos.

The OpenAI client, Flask server, Dash app, cache, and central data object are constructed during module import. OpenAI configuration can therefore affect application import, while request-time API and response errors are handled by the Wine information callback.

## Current Architecture

### Entrypoint and service wiring

`michelin_app.py` is the deployment entrypoint and composition root. It:

- creates and exports the Flask `server`;
- applies `ProxyFix`, production host and route guards, security headers, session hooks, and optional HTTPS redirection;
- creates the Dash app with Dash Pages and `suppress_callback_exceptions=True`;
- points `pages_folder` at `CONFIG.pages_dir` (`app/pages/`);
- loads `assets/custom_header.html` as the Dash index template;
- mounts root stores, `dcc.Location(id="url")`, and `dash.page_container`;
- creates Flask-Caching and the OpenAI client;
- injects `DATA`, `CONFIG`, cache, and the OpenAI client into callback registration functions.

Preserve the `server` export unless deployment is intentionally changed. Runtime modules belong under `app/`; root `assets/` and `assets/data/` are configured runtime paths.

### Routing

Dash Pages owns routing. Page modules are deliberately thin:

| Route | Page module | Layout owner |
| --- | --- | --- |
| `/` | `app/pages/guide.py` | `app/layouts/layout_main.py` |
| `/home` | `app/pages/home.py` | Guide compatibility alias using the same layout |
| `/analysis` | `app/pages/analysis.py` | `app/layouts/analysis.py` |
| `/economics` | `app/pages/economics.py` | `app/layouts/economics.py` |
| `/wine` | `app/pages/wine.py` | `app/layouts/wine.py` |
| `/robots.txt` | `michelin_app.py` | Plain-text crawler policy; no session |
| Client-side 404 fallback | `app/pages/not_found_404.py` | `app/layouts/layout_404.py` |

Direct requests outside the five public page paths, the explicit `robots.txt` endpoint, and registered framework/static routes are rejected by the Flask request guard before Dash serves its catch-all HTML shell. Do not recreate root-level `pages/`, `callbacks/`, `layouts/`, `components/`, or `utils/` packages. Runtime imports use `app.*` paths, and page/callback modules must not import `michelin_app.py`.

### Shared components, configuration, and data

`app/components/shared.py` owns the visible navigation contract, shared header/footer builders, Michelin rating colours, and icon helpers. `app/callbacks/navigation.py` owns the hamburger state and active navigation classes; `/home` is treated as an active Guide path.

`app/app_config.py` owns repository-relative paths, package-version lookup, active Guide-year derivation, environment parsing, production detection, HTTPS/debug flags, secret-key handling, cache configuration, and OpenAI request limits.

`app/app_data.py` is the runtime data boundary. It loads and validates restaurant CSVs and deployed GeoJSON, preserves string-like department codes, normalises Wine geometry to EPSG:4326, creates stable Wine feature IDs, and builds shared derived collections. `MichelinData` provides the France/Monaco combination helpers used by Guide callbacks.

## Page Architecture

### Guide

- Pages: `app/pages/guide.py` and the `/home` alias.
- Layout: `app/layouts/layout_main.py`.
- Callbacks: `app/callbacks/guide.py` via `register_guide_callbacks(app, data)`.
- Figures: `app/utils/guide_figures.py`.
- Map: Plotly `Scattermap` traces on `layout.map` (MapLibre), with metropolitan-France bounds from `app/utils/map_constraints.py`.
- State: root rating/centroid stores plus page-level `map-view-store-mainpage`.

Guide owns location-search disclosure and matching, geographic selectors, rating filters, selected-restaurant details, Paris arrondissement visibility, full map reconstruction, and viewport persistence. Geographic changes reset to the selected geography; non-geographic changes preserve a valid manually stored view. Monaco is included only when the selected region is `Provence-Alpes-Côte d'Azur`.

The Guide graph enables scroll zoom, responsive rendering, and a customised modebar. The location-match result is an HTML overlay attached to the map container, not Plotly annotation content.

### Analysis

- Page: `app/pages/analysis.py`.
- Layout: `app/layouts/analysis.py`, wrapped by `app/layouts/analysis_shared.py`.
- Callbacks: `app/callbacks/analysis.py`.
- Figures and ranking components: `app/utils/analysis_figures.py`.
- Map: `Choroplethmap` and `Scattermap` on MapLibre with split-layout France bounds.
- State: page-level rating stores and `departments-store`; there is no persisted map viewport store.

Analysis owns regional, departmental, and arrondissement distributions, rating-button state, dependent department/arrondissement options, and restaurant rankings. Its callbacks return complete chart and map figures. Analysis graphs hide the Plotly modebar.

`plot_single_choropleth_plotly(...)` writes `total_restaurants` into its input frame. Callers currently pass copies where required; preserve that boundary when adding call sites.

### Economics

- Page: `app/pages/economics.py`.
- Layout: `app/layouts/economics.py`, wrapped by `app/layouts/analysis_shared.py`.
- Callbacks: `app/callbacks/economics.py`.
- Figures: `app/utils/economics_figures.py`.
- Map: `Choroplethmap`/`Scattermap` on MapLibre, using `assets/basicTileMap.json`.
- State: `selected-stars-demographics`, `map-view-store-demo`, and the currently unconsumed `map-view-demo-updated` layout store.

Economics owns metric and geography selection, the demographic map and bar chart, weighted-mean display, restaurant overlays, rating-button state, and map-view persistence. Its main callback returns complete figures. Manual `map.center` and `map.zoom` are stored in `map-view-store-demo`; changing the granularity selector clears that stored viewport. Overview and split map layouts use different bounds and default zooms from `app/utils/map_constraints.py` and `app/utils/economics_figures.py`.

### Wine

- Page: `app/pages/wine.py`.
- Layout: `app/layouts/wine.py`, wrapped by `app/layouts/analysis_shared.py`.
- Callbacks: `app/callbacks/wine.py` via injected data, config, cache, and OpenAI client.
- Figures: `app/utils/wine_figures.py`.
- Search and viewport calculations: `app/utils/wine_search.py`.
- Map: one feature-based `Choroplethmap` AOC trace plus fixed `Scattermap` restaurant traces on MapLibre.
- State: page-level `map-view-store` and `wine-map-ready`.

The region selector scopes the available appellation search records. Region and appellation selections both calculate a canonical view from existing WGS84 bounds. The navigation callback returns a Dash `Patch` containing geography-specific `uirevision`, then `map.zoom`, then `map.center`. The same selection state updates `map-view-store` with a geography ownership key; manual relayout is accepted only for the currently owned geography.

The initial `/wine` load returns the complete figure. Separate patch callbacks own selector navigation, regional-outline visibility, restaurant trace visibility, and AOC hover highlighting. Hover content is rendered in a fixed HTML overlay. Click handling resolves the stable `feature_id` from Plotly `location`; it does not use curve-number-to-region lookup.

The Wine map uses page-specific bounds whose rendered desktop extent produces an effective minimum zoom of approximately `4.7`. Centre and zoom remain separate Plotly patch operations. At the minimum zoom, the browser renderer can transiently constrain a requested centre using the preceding zoom before displaying the requested zoom. This is a rendering sensitivity of the current patch path, not evidence of incorrect geometry, lookup, centroid, persistence, or bounds data. Interactive browser validation is required for changes to this path.

Regional outlines are a MapLibre line layer. Restaurant overlays use fixed trace indices for one-, two-, and three-star traces. AOC clicks request a structured summary from `gpt-4.1-mini`, after checking the appellation-specific cache and the per-session request limit. The disclaimer and generated-content panel are controlled by the same information callback.

## Callback and State Ownership

### Registration boundaries

| Module | Primary ownership |
| --- | --- |
| `app/callbacks/navigation.py` | hamburger menu and active route links |
| `app/callbacks/guide.py` | Guide search, filters, details, full map figures, centroids, and viewport store |
| `app/callbacks/analysis.py` | Analysis distributions, dependent options, rating state, and rankings |
| `app/callbacks/economics.py` | Economics figures, overlays, rating state, and viewport store |
| `app/callbacks/wine.py` | Wine figure initialisation, selector navigation, hover, overlays, viewport store, and generated content |

Root stores in `michelin_app.py` are `selected-stars`, `available-stars`, `department-centroid-store`, `paris-arrondissement-centroid`, and `region-demographics-centroid`. The first four participate in Guide behaviour; `region-demographics-centroid` is present but currently has no callback consumer.

Page-level stores are:

- Guide: `map-view-store-mainpage`.
- Analysis: `departments-store`, `selected-stars-analysis`, `selected-stars-department`, and `selected-stars-arrondissement`.
- Economics: `selected-stars-demographics`, `map-view-store-demo`, and `map-view-demo-updated`.
- Wine: `map-view-store` and `wine-map-ready`.

Guide, Analysis, and Economics map-producing callbacks return complete Plotly figures. Wine returns one complete figure on route initialisation and uses Dash `Patch` for navigation, hover selection, outline visibility, and restaurant trace visibility. Those Wine patch callbacks deliberately use `allow_duplicate=True` on `wine-map-graph.figure`; each must remain restricted to its owned fields.

Selector state, hover state, overlay state, viewport persistence, and generated-content state are separate interaction paths. A callback that writes a full figure can supersede a patch, and two callbacks writing the same layout field can become competing authorities. Do not introduce a second authority for an interaction without explicit design justification and behaviour-level coverage.

## Layout Modules

- `app/layouts/layout_main.py`: Guide sheet, sidebar search/filters/details, map panel, and rating legend.
- `app/layouts/analysis.py`: regional, departmental, arrondissement, and ranking sections.
- `app/layouts/economics.py`: metric controls, demographic evidence area, restaurant controls, and weighted-mean explanation.
- `app/layouts/wine.py`: region/appellation controls, outline and restaurant controls, map/hover overlay, and generated-information panel.
- `app/layouts/analysis_shared.py`: shared Analysis/Economics/Wine page shell and editorial rating-filter builders.
- `app/layouts/layout_404.py`: shared-shell 404 layout.

The Guide has its own rating-filter helper and ID conventions. `analysis_shared.py` provides a related helper for Analysis, Economics, and Wine. Do not merge them merely because their names or visual primitives overlap.

## Utility Modules

- `app/utils/guide_figures.py`: Guide map builders, geographic outlines, restaurant traces, and Guide bounds application.
- `app/utils/analysis_figures.py`: Analysis bar charts, MapLibre choropleths, and ranking components.
- `app/utils/economics_figures.py`: Economics maps, bars, and weighted means.
- `app/utils/wine_figures.py`: complete Wine AOC figure, outline layer, and fixed restaurant traces.
- `app/utils/wine_search.py`: stable AOC search records, fuzzy options, bounds-based region/appellation centres, and zoom calculations.
- `app/utils/map_constraints.py`: page-specific declarative MapLibre bounds.
- `app/utils/restaurant_cards.py`: Guide restaurant detail cards.
- `app/utils/star_filters.py`: shared rating-button active-state calculation.
- `app/utils/wine_prompts.py`: structured Wine summary prompt.
- `app/utils/locationMatcher.py`: fuzzy Guide location matching.

## Mapping Architecture

| Page | Plotly map traces | Bounds | Viewport persistence | Interaction configuration |
| --- | --- | --- | --- | --- |
| Guide | `Scattermap` | `METROPOLITAN_FRANCE_MAP_BOUNDS` | `map-view-store-mainpage`, geography-owned | scroll zoom, responsive graph, customised modebar |
| Analysis | `Choroplethmap`, optional `Scattermap` labels | `FRANCE_SPLIT_MAP_BOUNDS` | none | modebar hidden; full figures follow selectors |
| Economics | `Choroplethmap`, optional restaurant/label `Scattermap` | overview or split France bounds | `map-view-store-demo` | modebar hidden; full figures preserve manual view until granularity changes |
| Wine | one AOC `Choroplethmap`, restaurant `Scattermap` traces, outline layer | `WINE_MAP_BOUNDS` | geography-owned `map-view-store` | modebar hidden; full initial figure plus narrowly scoped patches |

All current application maps use Plotly's `layout.map` MapLibre path. Bounds are applied by `app/utils/map_constraints.py`; they are not callback-owned. The effective minimum zoom produced by MapLibre bounds depends on rendered canvas dimensions, so responsive validation matters even when the declarative bounds are unchanged.

## Assets and Styling

`assets/styles.css` is the single primary stylesheet. It contains global chrome, shared editorial primitives, Guide-specific styles, Analysis/Economics/Wine styles, and responsive rules. Shared additive classes include the editorial sheet/page frame, page titles and descriptions, control rows/groups, selects, action/rating controls, evidence layouts, maps, charts, notes, cards, and information panels. Page-specific classes remain part of the rendered layout contract.

Keep component IDs and class names stable unless a task explicitly covers their migration and tests or browser checks cover the affected behaviour. Responsive rules include shared editorial breakpoints plus page-specific refinements; inspect the complete cascade before changing a selector rather than treating one media-query block in isolation.

Other runtime assets:

- `assets/scroll-script.js`: delegated Analysis, Economics, and Wine navigation scrolling; it retries once after Dash swaps routed content.
- `assets/custom_header.html`: Dash index template and metadata/placeholders.
- `assets/basicTileMap.json`: MapLibre tile style used by Economics. It contains deployment-sensitive external tile-service URLs and an embedded key; do not treat it as incidental styling.
- `assets/images/`: Michelin icons, OpenAI lockup, GitHub mark, and supporting images.

## Data and Generated Assets

### Runtime-loaded data

Annual Michelin restaurant and aggregate geography data live under `assets/data/<GUIDE_YEAR>/`, where `<GUIDE_YEAR>` is derived from the installed application package version. The application normally contains only the active Guide-year directory; historical annual Michelin data is retained in the upstream ET repository.

The annual application directory contains three CSV files and five GeoJSON files:

- `assets/data/<GUIDE_YEAR>/all_restaurants(arrondissements).csv`;
- `assets/data/<GUIDE_YEAR>/all_restaurants.csv`;
- `assets/data/<GUIDE_YEAR>/monaco_restaurants.csv`;
- `assets/data/<GUIDE_YEAR>/geodata/arrondissement_restaurants.geojson`;
- `assets/data/<GUIDE_YEAR>/geodata/department_restaurants.geojson`;
- `assets/data/<GUIDE_YEAR>/geodata/monaco_restaurants.geojson`;
- `assets/data/<GUIDE_YEAR>/geodata/paris_restaurants.geojson`;
- `assets/data/<GUIDE_YEAR>/geodata/region_restaurants.geojson`.

`app/app_data.py` is the runtime validation boundary. It currently loads:

- `assets/data/<GUIDE_YEAR>/all_restaurants(arrondissements).csv`;
- `assets/data/<GUIDE_YEAR>/monaco_restaurants.csv`;
- `assets/data/<GUIDE_YEAR>/geodata/region_restaurants.geojson`;
- `assets/data/<GUIDE_YEAR>/geodata/department_restaurants.geojson`;
- `assets/data/<GUIDE_YEAR>/geodata/arrondissement_restaurants.geojson`;
- `assets/data/<GUIDE_YEAR>/geodata/paris_restaurants.geojson`;
- `assets/data/<GUIDE_YEAR>/geodata/monaco_restaurants.geojson`;
- `assets/data/wine_regions_aoc_area.geojson`.

Wine geography has a separate lifecycle and remains at `assets/data/wine_regions_aoc_area.geojson`. Wine data is not part of the annual Michelin restaurant import. `assets/data/wine_regions.geojson` is ignored as a local master/source file and is not a runtime path.

The upstream canonical Michelin ET products are maintained at:

```text
https://github.com/pineapple-bois/Michelin_Rated_Restaurants
```

Canonical annual France products are published in that repository under:

```text
data/products/france/<YEAR>/
```

The application consumes approved ET products from a separately supplied local checkout. It does not clone the upstream repository, call the GitHub API, import ET implementation code, execute the ET pipeline, or modify the ET repository. `scripts/load_annual_data.py` prepares the annual application release from that local checkout; its explicit source-to-destination manifest is the contract between the repositories. The loader does not commit, tag, push, deploy, or run the application deployment process.

### Data contracts

Restaurant CSVs require:

```text
name, address, location, arrondissement, department_num, department, capital,
region, price, cuisine, url, award, stars, greenstar, longitude, latitude
```

Rating conventions:

- `stars == 0.25`: Michelin selected.
- `stars == 0.5`: Bib Gourmand.
- `stars in {1, 2, 3}`: starred restaurants.
- `greenstar == 1`: separate Green Star marker.

Aggregate geography files include their identity/geometry columns and count fields such as:

```text
selected, bib_gourmand, 1_star, 2_star, 3_star,
total_stars, starred_restaurants, green_stars
```

Economics uses the exact source column names:

```text
GDP_millions(€)
GDP_per_capita(€)
poverty_rate(%)
average_annual_unemployment_rate(%)
average_net_hourly_wage(€)
municipal_population
population_density(inhabitants/sq_km)
area(sq_km)
```

Wine runtime rows require `region`, `app`, `colour`, `source_area_m2`, and polygonal `geometry`. The loader requires non-empty EPSG:4326-compatible Polygon/MultiPolygon geometry, positive finite source area, unique `(region, app)` pairs, and one colour per parent region. It derives deterministic `feature_id` values from `region` and `app`; selectors, hover validation, and click handling use those IDs.

Department and arrondissement identifiers must remain string-like. Do not normalise away leading zeroes or Corsican `2A`/`2B` codes.

## Current Routing and State

- `dcc.Location(id="url", refresh=False)` and `dash.page_container` form the root routing shell.
- Navigation links are defined once in `NAV_LINKS`; route-active classes are callback-owned.
- Root stores persist while Dash swaps page content. Page-level stores exist only with their page layouts.
- Guide and Wine viewport stores include geography ownership checks so stale relayout data cannot automatically claim a newly selected geography.
- Economics persists manual viewport state but clears it when its granularity selector changes.
- Analysis does not persist viewport state.

Do not rename component IDs, move stores between root and page layouts, or change persistence semantics without tracing every callback input/output and direct-route layout construction.

## Gotchas

- Dash Pages owns routing, and separately registered callbacks depend on `suppress_callback_exceptions=True` because page layouts are mounted dynamically.
- Keep production host/path rejection and the HTTPS hook before session work. `ProxyFix` trusts only one `X-Forwarded-Proto` value and deliberately does not trust `X-Forwarded-Host`.
- A generated local `FLASK_SECRET_KEY` invalidates sessions on process restart.
- The active Guide year is derived from installed package metadata. Refresh the editable install after changing `pyproject.toml` version metadata.
- The default cache is in-process. Cached Wine summaries and session request counts are not shared application-wide across workers or dynos.
- Wine checks its appellation-specific cache before consuming a request-limit count. Invalid clicks and restaurant clicks fail closed without invoking OpenAI.
- The Guide includes Monaco only for Provence-Alpes-Côte d'Azur; Analysis, Economics, and Wine otherwise use France-only datasets.
- `department_num` and geography codes are identifiers, not numbers.
- Economics checks `'all' in selected_regions` before its later empty-selection fallback; preserve list-valued dropdown contracts unless that callback is explicitly hardened.
- `plot_single_choropleth_plotly(...)` mutates its frame by adding `total_restaurants`.
- Wine patch helpers depend on `WINE_AOC_TRACE_INDEX == 0`, fixed one-/two-/three-star trace indices, and regional outline layer index `0`. Changing trace/layer construction requires coordinated callback and test changes.
- Wine `wine-map-ready=True` is returned with the full server figure; it means the server produced the figure, not that the browser has emitted a Plotly completion event.
- Wine selector navigation and manual persistence are separate callbacks writing related viewport state. Preserve their geography-ownership checks and validate first-visible browser behaviour after changes.
- Bounds-derived minimum zoom is canvas-dependent. Unit tests can verify bounds presence and stored targets but cannot prove rendered camera order.
- `assets/basicTileMap.json` contains an external service key and URLs.
- Shared editorial CSS and page-specific classes overlap deliberately. Inspect selector scope, especially `:has(...)` rules and media-query overrides, before consolidating declarations.
- Do not commit `__pycache__/`, test caches, `.env`, ignored Wine source data, or generated experiment outputs.

## Quick Local Checks

Use the repository environment when available.

After cloning or changing package metadata, install the local package metadata and dependencies:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Compile runtime Python after architecture, callback, layout, or utility changes:

```bash
.venv/bin/python -m compileall -q michelin_app.py app
```

Representative focused tests:

```bash
.venv/bin/python -m pytest tests/test_guide_callbacks.py tests/test_guide_figures.py
.venv/bin/python -m pytest tests/test_economics_callbacks.py tests/test_map_constraints.py
.venv/bin/python -m pytest tests/test_wine_callbacks.py tests/test_wine_figures.py tests/test_wine_search.py tests/test_map_constraints.py
```

Run the complete suite with:

```bash
.venv/bin/python -m pytest
```

`pytest.ini` limits discovery to `tests/` and treats Flask-Caching deprecations as errors. The suite covers imports, routes, data contracts, layouts, callback helpers/registration, map constraints, Wine search/figure behaviour, and tracked AOC simplification helpers. It does not provide browser automation or visual regression coverage.

For interactive checks:

```bash
.venv/bin/python michelin_app.py
```

Then load:

```text
http://127.0.0.1:8050/
http://127.0.0.1:8050/home
http://127.0.0.1:8050/analysis
http://127.0.0.1:8050/economics
http://127.0.0.1:8050/wine
http://127.0.0.1:8050/missing
```

Passing unit tests does not prove interactive map behaviour. Browser-check map pan/zoom, selector-driven first view, persistence, hover, overlays, direct route loads, and relevant responsive breakpoints whenever those paths change.

## Change Discipline

- Inspect the working tree and the owning implementation before editing.
- Preserve unrelated tracked and untracked changes.
- Keep work tightly scoped and separate fact-finding from implementation in fragile areas.
- Prefer the smallest local correction that satisfies the approved behaviour.
- Do not create stores, callbacks, abstractions, dependencies, navigation authorities, or frameworks without demonstrated need and explicit scope.
- Do not modify unrelated pages to solve a page-specific defect.
- Keep documentation, styling, layout, callback, data, dependency, and deployment changes separate where practical.
- Preserve component IDs, callback contracts, routes, map state, and persistence unless the task explicitly authorises changing them.
- Stop and report when the requested result cannot be achieved within the approved scope; do not broaden the design to force a result.
- Run validation proportionate to the changed behaviour and report browser gaps honestly.
- Do not stage or commit automatically unless explicitly requested.
