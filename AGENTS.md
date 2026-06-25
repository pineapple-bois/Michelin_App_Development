# Agent Guide

## Purpose

This file is for future agents working on the Michelin Dash app. It documents the current architecture, dependencies, runtime assumptions, and gotchas that matter while the app is being refactored from a small monolith into a true multipage app.

## Runtime and Deployment

- Current Heroku entrypoint: `Procfile` runs `gunicorn michelin_app:server`.
- Current Python marker: `.python-version` contains `3.12`.
- README local setup should stay aligned with Python `3.12` unless the runtime marker changes deliberately.
- Native GIS packages are still declared in `Aptfile`: `gdal-bin` and `libgdal-dev`.
- Python dependencies are pinned in `requirements.txt`.
- GeoPandas reads local GeoJSON through Pyogrio. Fiona is intentionally not a direct dependency.
- Main environment variables:
  - `OPENAI_API_KEY`: used by the Wine page summary callback.
  - `FLASK_SECRET_KEY`: used for Flask sessions. It is required in production and optional in local development.
- Local development runs with `python michelin_app.py`; HTTPS redirection is config-driven and disabled by default outside production/Heroku.

## Current Architecture

### Entrypoint

`michelin_app.py` is now the root deployment entrypoint and service-wiring module:

- creates the Flask `server`
- creates the Dash `app`
- imports runtime/path configuration from `app/app_config.py`
- points Dash Pages at `CONFIG.pages_dir`, currently `app/pages/`
- creates the OpenAI client
- configures Flask session handling
- configures `Flask-Caching`
- defines root `dcc.Store` components
- mounts `dash.page_container` for Dash Pages routing
- registers Analysis callbacks from `app/callbacks/analysis.py`
- registers Economics callbacks from `app/callbacks/economics.py`
- registers Wine/OpenAI callbacks from `app/callbacks/wine.py`
- registers navigation callbacks from `app/callbacks/navigation.py`
- registers Guide callbacks from `app/callbacks/guide.py`
- exposes `server` for Gunicorn

Preserve the `server` export until deployment is intentionally changed.

The `app/` package contains runtime application modules. Keep `assets/` and `assets/Data/` at the repository root unless a dedicated data-path migration is planned.

### Page Modules

Dash Pages now owns routing. The current page modules are intentionally thin wrappers around the existing layout functions:

- `app/pages/guide.py`: `/`, current Guide layout.
- `app/pages/home.py`: `/home`, compatibility alias for the current Guide layout.
- `app/pages/analysis.py`: `/analysis`, core Michelin analysis sections and rankings.
- `app/pages/economics.py`: `/economics`, socioeconomic and demographics section.
- `app/pages/wine.py`: `/wine`, wine-region map and generated summary section.
- `app/pages/not_found_404.py`: Dash Pages 404 fallback using the existing 404 layout.

Navigation callbacks are registered from `app/callbacks/navigation.py`. Guide page callbacks are registered from `app/callbacks/guide.py`. Core Analysis callbacks are registered from `app/callbacks/analysis.py`. Economics callbacks are registered from `app/callbacks/economics.py`. Wine/OpenAI callbacks are registered from `app/callbacks/wine.py`.

Dash discovers these modules through `pages_folder=str(CONFIG.pages_dir)` in `michelin_app.py`; do not recreate a root-level `pages/` package.

### Callback Modules

`app/callbacks/navigation.py`

- Exposes `register_navigation_callbacks(app)`.
- Owns the global header/nav callbacks: hamburger menu open/close state and active visible nav link classes.
- Uses `app/components/shared.py` navigation metadata through `nav_link_class(...)`.
- Visible navigation includes Guide, Analysis, Economics, and Wine. `/home` remains an active-path alias for Guide.

`app/callbacks/guide.py`

- Exposes `register_guide_callbacks(app, data)`.
- Owns the current Guide/Home callbacks: search collapse and city matching, department/star filters, restaurant detail sidebar, Paris arrondissement visibility, Guide map updates, centroid stores, and the Guide map-view store.
- Receives `DATA` from `michelin_app.py` rather than importing `michelin_app.py`, which keeps the callback module usable during future app-factory work.
- Preserves Monaco behavior for the Guide page when the selected region is `Provence-Alpes-Côte d'Azur`.

`app/callbacks/analysis.py`

- Exposes `register_analysis_callbacks(app, data)`.
- Owns the current core Analysis callbacks: region, department, arrondissement, star-button active state, department-to-arrondissement options, and top restaurant rankings.
- Receives `DATA` from `michelin_app.py` rather than importing `michelin_app.py`.

`app/callbacks/economics.py`

- Exposes `register_economics_callbacks(app, data)`.
- Owns the current Economics/Demographics callbacks: demographic metric map and bar chart, weighted-mean visibility, starred-restaurant overlay controls, map-view persistence, and demographics star-button active state.
- Receives `DATA` from `michelin_app.py` rather than importing `michelin_app.py`.

`app/callbacks/wine.py`

- Exposes `register_wine_callbacks(app, data, config, cache, openai_client)`.
- Owns the current Wine/OpenAI callbacks: wine map, regional-outline selector behavior, starred-restaurant overlay controls, wine map-view persistence, wine star-button active state, wine map click handling, generated summary output, generated-content disclaimer visibility, request-limit handling, and cache reads/writes.
- Receives `DATA`, `CONFIG`, the configured `Flask-Caching` instance, and the initialized OpenAI client from `michelin_app.py`.
- Keeps the existing curve-number-to-wine-region lookup unchanged, even though it remains fragile for future multi-trace changes.

### Shared Components

`app/components/shared.py`

- Shared Michelin rating colours, exposed as `color_map` for compatibility with existing helpers.
- Shared Michelin icon helpers used by Guide, Analysis, and plotting/card helpers.
- Shared header and footer builders.
- `NAV_LINKS` and `nav_link_class(...)` for the currently visible Guide, Analysis, Economics, and Wine navigation.

`app/app_data.py`

- Loads the two restaurant CSVs and deployed GeoJSON files from `CONFIG.data_path(...)`.
- Uses `geopandas.read_file(..., engine="pyogrio")` for GeoJSON I/O.
- Keeps `department_num` string-like in restaurant CSVs so values such as `06`, `2A`, `2B`, and `75` continue to match existing callback logic.
- Checks required columns for restaurants, aggregate geography, demographics, Paris, Monaco, and wine data at import time.
- Builds the existing derived values used by callbacks: `geo_df`, `unique_regions`, `initial_options`, `dept_to_code`, and `region_to_name`.
- Provides `get_combined_restaurant_data(...)` and `get_geo_df(...)` methods to preserve current France/Monaco behavior.

`app/app_config.py`

- Owns runtime configuration, repo-relative paths, cache settings, debug/HTTPS flags, Flask secret handling, and OpenAI request limits.
- Because this module now lives inside `app/`, `CONFIG.base_dir` is calculated as the repository root via the package parent, while `CONFIG.package_dir` points to `app/`.
- `CONFIG.assets_dir` and `CONFIG.data_dir` still point to root `assets/` and `assets/Data/`.
- `CONFIG.pages_dir` points to `app/pages/` and is passed to Dash as the explicit `pages_folder`.

### Layout Modules

`app/layouts/layout_main.py`

- Guide page layout.
- Main Guide star-filter layout.
- Imports shared header/footer/icon helpers from `app/components/shared.py`.

`app/layouts/analysis.py`

- Analysis page layout for `/analysis`.
- Exposes Analysis section builders:
  - `build_analysis_intro_section()`
  - `build_region_distribution_section()`
  - `build_department_distribution_section()`
  - `build_arrondissement_distribution_section()`
  - `build_restaurant_distribution_section()`
  - `build_rankings_section()`
  - `build_analysis_sections()`
- Contains the Analysis page sections:
  - Michelin intro
  - region distribution
  - department distribution
  - arrondissement distribution
  - ranking section

`app/layouts/economics.py`

- Economics page layout for `/economics`.
- Owns `build_economics_section()`:
  - demographic metric selector
  - demographic map
  - demographic bar chart
  - weighted mean explanation
  - optional starred restaurant overlay controls

`app/layouts/wine.py`

- Wine page layout for `/wine`.
- Owns `build_wine_section()`:
  - wine map
  - restaurant overlay controls
  - LLM output panel
  - generated-content disclaimer

`app/layouts/analysis_shared.py`

- Shared Analysis/Economics/Wine page shell.
- Shared analysis-style star filter helpers and the `unique_regions` list used by those layouts.
- `app/layouts/layout_analysis.py` was removed rather than retained as a shim. `build_combined_analysis_content()` was removed because the old combined public page is no longer exposed and no code uses the helper.
- The layout-module cleanup did not move callbacks; callback ownership remains in `app/callbacks/guide.py`, `app/callbacks/navigation.py`, `app/callbacks/analysis.py`, `app/callbacks/economics.py`, and `app/callbacks/wine.py`.

`app/layouts/layout_404.py`

- Small 404 page using shared header/footer.

### Utility Modules

`app/utils/guide_figures.py`

- Guide/Home map figure builders and geographic outline helpers.
- Michelin hover-text helpers for Guide map traces.

`app/utils/analysis_figures.py`

- Core Analysis bar/choropleth figure builders.
- Top restaurant ranking component helper.

`app/utils/economics_figures.py`

- Economics/Demographics choropleth, bar chart, and weighted-mean helpers.

`app/utils/wine_figures.py`

- Wine-region map figure builder.

`app/utils/restaurant_cards.py`

- Restaurant detail/sidebar/card rendering helper.

`app/utils/star_filters.py`

- Shared star-filter active-state helper.

`app/utils/wine_prompts.py`

- Wine/OpenAI prompt construction helper.

`app/utils/appFunctions.py` was removed after callback imports were updated to target the purpose-specific utility modules directly.

`app/utils/locationMatcher.py`

- `LocationMatcher` uses `fuzzywuzzy`, `python-Levenshtein`, and `unidecode`.
- It normalizes accents and casing, splits the restaurant `location` field, and returns matched region/department data.

### Geospatial Dependencies

- `app/app_data.py` uses `geopandas.read_file(...)` for local GeoJSON files and `geopandas.GeoDataFrame(...)` for Monaco/France geometry combination.
- `app/utils/analysis_figures.py` uses GeoPandas CRS helpers and Shapely geometry objects. It does not read or write files.
- Pyogrio is the intended GeoPandas I/O backend. Do not re-add Fiona unless a future feature requires Fiona-specific behavior.
- `Aptfile` remains conservative for Heroku 24 builds. Pyogrio wheels include GDAL on supported platforms, but remove `gdal-bin`/`libgdal-dev` only after a dedicated deployment/build verification.

### Assets

`assets/styles.css`

- Primary styling file.
- Currently has local modified WIP commented Wine CSS at the bottom. Do not overwrite casually.

`assets/scroll-script.js`

- Uses event delegation for Analysis, Economics, and Wine nav clicks.
- Scrolls to `analysis-content-top`, `demographics-content-top`, or `wine-content-top` when that anchor exists.
- Retries once after Dash swaps page content for route changes.

`assets/custom_header.html`

- Custom Dash index template with meta tags and app placeholders.

`assets/basicTileMap.json`

- Custom tile style.
- Contains an embedded tile service key. Treat it as a deployment/config decision, not incidental styling.

`assets/Data`

- `all_restaurants(arrondissements).csv`: main France restaurant data.
- `monaco_restaurants.csv`: Monaco restaurant rows.
- `region_restaurants.geojson`: regional geometry and aggregate metrics.
- `department_restaurants.geojson`: department geometry and aggregate metrics.
- `arrondissement_restaurants.geojson`: arrondissement geometry and aggregate metrics.
- `paris_restaurants.geojson`: Paris arrondissement geometry.
- `monaco_restaurants.geojson`: Monaco geometry.
- `wine_regions_cleaned.geojson`: deployed wine region data.
- `wine_regions_simplified.geojson`: currently untracked local data.

## Data Contracts

The main restaurant CSV is expected to provide:

```text
name, address, location, arrondissement, department_num, department, capital,
region, price, cuisine, url, award, stars, greenstar, longitude, latitude
```

Important value conventions:

- `stars == 0.25`: Michelin selected restaurant.
- `stars == 0.5`: Bib Gourmand.
- `stars in {1, 2, 3}`: one-, two-, or three-star restaurant.
- `greenstar == 1`: separate green-star marker.

Aggregate GeoJSON files are expected to provide geometry plus count columns such as:

```text
bib_gourmand, 1_star, 2_star, 3_star, selected
```

Demographic/economic maps expect columns such as:

```text
GDP_millions(€)
GDP_per_capita(€)
poverty_rate(%)
average_annual_unemployment_rate(%)
average_net_hourly_wage(€)
municipal_population
population_density(inhabitants/sq_km)
```

If renaming these columns for ASCII safety later, do it as a coordinated data-loader normalization step rather than changing callback strings piecemeal.

Wine GeoJSON rows are expected to provide:

```text
region, colour, geometry
```

## Current Routing and State

Dash Pages owns the current routing shell:

- Root layout contains `dcc.Location(id="url")` for the existing active-nav callback.
- Root layout contains `dash.page_container`.
- The old `display_page(pathname)` callback has been removed.

Current routes:

- `/` -> Guide
- `/home` -> Guide compatibility page
- `/analysis` -> core Michelin analysis sections and rankings
- `/economics` -> socioeconomic and demographics section
- `/wine` -> wine-region map and generated summary section
- anything else -> Dash Pages 404 fallback using `app/pages/not_found_404.py`

Root-level stores:

- `selected-stars`
- `available-stars`
- `department-centroid-store`
- `paris-arrondissement-centroid`
- `region-demographics-centroid`

Page-level stores inside layouts:

- `map-view-store-mainpage`
- `departments-store`
- `selected-stars-analysis`
- `selected-stars-department`
- `selected-stars-arrondissement`
- `selected-stars-demographics`
- `map-view-store-demo`
- `map-view-demo-updated`
- `selected-stars-wine`
- `wine-region-curve-numbers`
- `map-view-store`

Many of these are page-specific and should move into page layouts during callback/page ownership cleanup.

## Callback Ownership

Current callback ownership:

- `michelin_app.py`: app/server setup, cache/OpenAI setup, Dash root layout, and callback registration.
- `app/callbacks/navigation.py`: hamburger menu and active-route callbacks registered through `register_navigation_callbacks(app)`.
- `app/callbacks/guide.py`: Guide/Home callbacks registered through `register_guide_callbacks(app, DATA)`.
- `app/callbacks/analysis.py`: core Analysis callbacks registered through `register_analysis_callbacks(app, DATA)`.
- `app/callbacks/economics.py`: Economics/Demographics callbacks registered through `register_economics_callbacks(app, DATA)`.
- `app/callbacks/wine.py`: Wine/OpenAI callbacks registered through `register_wine_callbacks(app, DATA, CONFIG, cache, client)`.

Phase 5 callback ownership is complete: page-specific callbacks no longer live in `michelin_app.py`.

Use `dash.callback` in page callback modules where practical, or register callbacks through explicit `register_callbacks(app, deps)` functions. Avoid importing the app object into every module.

## Gotchas

- Dash Pages owns routing. Do not import `michelin_app.py` from page modules or callback modules.
- Runtime imports should use the `app.*` package path. Do not add new root-level `callbacks/`, `components/`, `layouts/`, `pages/`, or `utils/` packages.
- `/analysis`, `/economics`, and `/wine` are real Dash Pages routes with callback ownership split by page callback module.
- `suppress_callback_exceptions=True` remains enabled. It was inspected during the navigation callback extraction and left alone because callbacks are still registered separately from page layout mounting. Revisit it during a later app-factory or page-layout cleanup.
- Flask `before_request` hooks are split between `enforce_https_redirect` and `ensure_session`. Keep the HTTPS hook before session work.
- HTTPS redirect is environment-aware and proxy-aware through `app/app_config.py` and `ProxyFix`. Keep it that way during later refactors.
- Session request counts limit OpenAI calls to 10 per session by default. Local-only generated `FLASK_SECRET_KEY` fallback resets sessions on restart.
- `Flask-Caching` uses `CACHE_TYPE="simple"`, which is per-process memory. It is not shared across Gunicorn workers or Heroku dynos.
- The Wine callback uses both `@cache.memoize` and manual `cache.get/cache.set`. Prefer one cache boundary keyed by wine region after behavior is covered by tests.
- The OpenAI client is created at import time. Missing or invalid `OPENAI_API_KEY` should be handled gracefully by the Wine page.
- Fiona is no longer installed directly. If it reappears transitively, verify why before accepting the dependency.
- `Aptfile` may eventually be removable, but that is a Heroku build/deployment validation task, not part of page-routing work.
- `department_num` is now explicitly read as string-like for both France and Monaco. Do not normalize department codes further without checking leading-zero and Corsican `2A`/`2B` behavior.
- The Guide page includes Monaco only when the selected region is `Provence-Alpes-Côte d'Azur`. Analysis, Economics, and Wine currently use France data only unless explicitly changed.
- `app/layouts/layout_main.py` and `app/layouts/analysis_shared.py` both define star-filter helpers with overlapping names but different ID conventions.
- Callback imports now target the purpose-specific `app/utils/*` modules directly. `app/utils/appFunctions.py` has been removed.
- Analysis, Economics, and Wine layout builders now live in separate modules, but they still share CSS classes and star-filter conventions. Keep IDs/classes stable until behavior is covered by targeted tests.
- Some callback function names are duplicated or misleading. Dash registers the decorated function object, but duplicate names are painful for debugging.
- Some callbacks assume dropdown values are lists and can fail if a multi-select is cleared to `None`.
- `plot_single_choropleth_plotly` mutates its input frame by writing `total_restaurants`. Pass copies or make the helper copy internally.
- Plotly map usage mixes `Scattermap`, `Choroplethmap`, `Choropleth`, and an older `mapbox_style` property in one fallback figure. Be careful when upgrading Plotly.
- Wine-region click handling maps Plotly curve numbers back through list positions. Multi-polygon regions can make this fragile. Prefer storing the wine region name in trace `customdata` or `meta`.
- `assets/scroll-script.js` maps Analysis, Economics, and Wine nav links to their current section anchors. Revisit it after callback/page modules settle.
- `Development/` is ignored scratch/reference material, not deployed code.
- Do not commit `__pycache__/` artifacts.
- `assets/Data/wine_regions_simplified.geojson` is currently untracked and unrelated to the deployed `wine_regions_cleaned.geojson` path.

## Safe Refactor Order

1. Stabilize runtime/config and add smoke checks.
2. Extract data loading with dtype normalization.
3. Extract shared header/footer/icon/star-filter components.
4. Introduce Dash Pages while keeping existing layouts intact.
5. Move Guide callbacks. Done: current Guide callbacks live in `app/callbacks/guide.py`.
6. Move navigation callbacks. Done: current navigation callbacks live in `app/callbacks/navigation.py`.
7. Add section-level builders inside the combined Analysis layout. Done; the old combined layout module has since been split into `app/layouts/analysis.py`, `app/layouts/economics.py`, and `app/layouts/wine.py`.
8. Split the combined Analysis route into Analysis, Economics, and Wine pages. Done: current routes live in `app/pages/analysis.py`, `app/pages/economics.py`, and `app/pages/wine.py`.
9. Move callbacks page by page. Done: Guide, navigation, Analysis, Economics, and Wine/OpenAI callbacks now live in dedicated callback modules.
10. Split `app/utils/appFunctions.py` by purpose. Done: implementation now lives in focused utility modules, callback imports target those modules directly, and the old shim has been removed.
11. Package the app modules under an outer `app/` package while keeping root `michelin_app.py` as the Heroku entrypoint. Done: runtime imports use `app.*`, Dash Pages uses `CONFIG.pages_dir`, and root assets/data remain in place.
12. Revisit `suppress_callback_exceptions=True` and app-factory extraction after package-level smoke tests are stable.

## Quick Local Checks

After changing architecture, run at least:

```bash
python -m py_compile michelin_app.py app/callbacks/navigation.py app/callbacks/guide.py app/callbacks/analysis.py app/callbacks/economics.py app/callbacks/wine.py app/layouts/layout_main.py app/layouts/analysis.py app/layouts/economics.py app/layouts/wine.py app/layouts/analysis_shared.py app/layouts/layout_404.py app/utils/guide_figures.py app/utils/analysis_figures.py app/utils/economics_figures.py app/utils/wine_figures.py app/utils/restaurant_cards.py app/utils/star_filters.py app/utils/wine_prompts.py app/utils/locationMatcher.py
```

If dependencies are installed:

```bash
python michelin_app.py
```

Then verify direct route loads in a browser:

```text
http://127.0.0.1:8050/
http://127.0.0.1:8050/home
http://127.0.0.1:8050/analysis
http://127.0.0.1:8050/economics
http://127.0.0.1:8050/wine
http://127.0.0.1:8050/missing
```

## Commit Hygiene

- Keep docs, routing, data loading, and visual styling changes separate where possible.
- Avoid broad CSS rewrites during the architecture migration.
- Leave unrelated local changes alone.
- Do not stage untracked bytecode.
- Treat `assets/Data/wine_regions_simplified.geojson` as local/untracked unless the user explicitly asks to add it.
