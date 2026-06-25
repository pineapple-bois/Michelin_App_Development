# Agent Guide

## Purpose

This file orients future agents working on the Michelin Dash app. The multipage refactor is complete; treat the current architecture as the baseline. The known next focus is styling, responsive cleanup, and visual/content modernisation for the Analysis, Economics, and Wine pages.

## Runtime and Deployment

- Heroku entrypoint: `Procfile` runs `gunicorn michelin_app:server`.
- Python marker: `.python-version` contains `3.12`.
- README local setup should stay aligned with Python `3.12` unless the runtime marker changes deliberately.
- Native GIS packages are declared in `Aptfile`: `gdal-bin` and `libgdal-dev`.
- Python dependencies are pinned in `requirements.txt`.
- Development test dependencies are in `requirements_dev.txt`.
- GeoPandas reads local GeoJSON through Pyogrio. Fiona is intentionally not a direct dependency.
- Main environment variables:
  - `OPENAI_API_KEY`: used by the Wine page summary callback.
  - `FLASK_SECRET_KEY`: used for Flask sessions. It is required in production and optional in local development.
  - `OPENAI_REQUEST_LIMIT`: optional per-session generated-summary limit, default `10`.
  - `CACHE_TYPE` and `CACHE_DEFAULT_TIMEOUT`: optional Flask-Caching configuration.
- Local development runs with `python michelin_app.py`.
- HTTPS redirection is config-driven and disabled by default outside production/Heroku.

## Current Architecture

### Entrypoint

`michelin_app.py` is the root deployment entrypoint and service-wiring module:

- creates the Flask `server`
- wraps the server with `ProxyFix`
- creates the Dash `app`
- imports runtime/path configuration from `app/app_config.py`
- points Dash Pages at `CONFIG.pages_dir`, currently `app/pages/`
- creates the OpenAI client
- configures Flask session handling
- configures `Flask-Caching`
- defines root `dcc.Store` components
- mounts `dash.page_container` for Dash Pages routing
- registers callbacks from `app/callbacks/*`
- exposes `server` for Gunicorn

Preserve the `server` export unless deployment is intentionally changed.

Runtime application modules live under the `app/` package. Keep root `assets/` and `assets/data/` in place unless a dedicated data-path change is requested.

### Routing and Pages

Dash Pages owns the routing shell. Page modules are thin wrappers around layout functions:

- `app/pages/guide.py`: `/`, Guide layout.
- `app/pages/home.py`: `/home`, Guide compatibility alias.
- `app/pages/analysis.py`: `/analysis`, core Michelin analysis sections and rankings.
- `app/pages/economics.py`: `/economics`, socioeconomic and demographics section.
- `app/pages/wine.py`: `/wine`, wine-region map and generated summary section.
- `app/pages/not_found_404.py`: Dash Pages 404 fallback.

Dash discovers these modules through `pages_folder=str(CONFIG.pages_dir)` in `michelin_app.py`. Do not recreate a root-level `pages/` package.

### Callback Modules

`app/callbacks/navigation.py`

- Exposes `register_navigation_callbacks(app)`.
- Owns hamburger open/close state and active visible nav link classes.
- Uses `NAV_LINKS` and `nav_link_class(...)` from `app/components/shared.py`.
- Visible navigation includes Guide, Analysis, Economics, and Wine. `/home` remains an active-path alias for Guide.

`app/callbacks/guide.py`

- Exposes `register_guide_callbacks(app, data)`.
- Owns Guide/Home callbacks: search collapse and city matching, department/star filters, restaurant detail sidebar, Paris arrondissement visibility, Guide map updates, centroid stores, and Guide map-view store.
- Receives `DATA` from `michelin_app.py`.
- Preserves Monaco behavior for the Guide page when the selected region is `Provence-Alpes-Côte d'Azur`.

`app/callbacks/analysis.py`

- Exposes `register_analysis_callbacks(app, data)`.
- Owns core Analysis callbacks: region, department, arrondissement, star-button active state, department-to-arrondissement options, and top restaurant rankings.
- Receives `DATA` from `michelin_app.py`.

`app/callbacks/economics.py`

- Exposes `register_economics_callbacks(app, data)`.
- Owns Economics/Demographics callbacks: demographic metric map and bar chart, weighted-mean visibility, starred-restaurant overlay controls, map-view persistence, and demographics star-button active state.
- Receives `DATA` from `michelin_app.py`.

`app/callbacks/wine.py`

- Exposes `register_wine_callbacks(app, data, config, cache, openai_client)`.
- Owns Wine/OpenAI callbacks: wine map, regional-outline selector behavior, starred-restaurant overlay controls, wine map-view persistence, wine star-button active state, wine map click handling, generated summary output, generated-content disclaimer visibility, request-limit handling, and cache reads/writes.
- Receives `DATA`, `CONFIG`, the configured `Flask-Caching` instance, and the initialized OpenAI client from `michelin_app.py`.
- Keeps the existing curve-number-to-wine-region lookup unchanged, even though it remains fragile for future multi-trace changes.

### Shared Components and Config

`app/components/shared.py`

- Shared Michelin rating colours, exposed as `color_map`.
- Michelin icon helpers used by Guide, Analysis, plotting helpers, and card helpers.
- Shared header and footer builders.
- `NAV_LINKS` and `nav_link_class(...)` for visible navigation.

`app/app_config.py`

- Runtime configuration, repo-relative paths, cache settings, debug/HTTPS flags, Flask secret handling, and OpenAI request limits.
- `CONFIG.base_dir` is the repository root.
- `CONFIG.package_dir` points to `app/`.
- `CONFIG.assets_dir` and `CONFIG.data_dir` point to root `assets/` and `assets/data/`.
- `CONFIG.pages_dir` points to `app/pages/`.

`app/app_data.py`

- Loads the two restaurant CSVs and deployed GeoJSON files from `CONFIG.data_path(...)`.
- Uses `geopandas.read_file(..., engine="pyogrio")` for GeoJSON I/O.
- Keeps `department_num` string-like so values such as `06`, `2A`, `2B`, and `75` match callback logic.
- Checks required columns for restaurants, aggregate geography, demographics, Paris, Monaco, and wine data at import time.
- Builds derived values used by callbacks: `geo_df`, `unique_regions`, `initial_options`, `dept_to_code`, and `region_to_name`.
- Provides `get_combined_restaurant_data(...)` and `get_geo_df(...)` for current France/Monaco behavior.

## Layout Modules

`app/layouts/layout_main.py`

- Guide page layout.
- Main Guide star-filter layout.
- Imports shared header/footer/icon helpers from `app/components/shared.py`.

`app/layouts/analysis.py`

- Analysis page layout for `/analysis`.
- Section builders:
  - `build_analysis_intro_section()`
  - `build_region_distribution_section()`
  - `build_department_distribution_section()`
  - `build_arrondissement_distribution_section()`
  - `build_restaurant_distribution_section()`
  - `build_rankings_section()`
  - `build_analysis_sections()`
- Contains Michelin intro, region distribution, department distribution, arrondissement distribution, and ranking sections.

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
  - generated summary panel
  - generated-content disclaimer

`app/layouts/analysis_shared.py`

- Shared Analysis/Economics/Wine page shell.
- Shared analysis-style star filter helpers.
- Local `unique_regions` list used by those layouts.

`app/layouts/layout_404.py`

- Small 404 page using shared header/footer.

## Utility Modules

- `app/utils/guide_figures.py`: Guide/Home map figure builders and geographic outline helpers.
- `app/utils/analysis_figures.py`: core Analysis bar/choropleth figure builders and top restaurant ranking component helper.
- `app/utils/economics_figures.py`: Economics/Demographics choropleth, bar chart, and weighted-mean helpers.
- `app/utils/wine_figures.py`: Wine-region map figure builder.
- `app/utils/restaurant_cards.py`: restaurant detail/sidebar/card rendering helper.
- `app/utils/star_filters.py`: shared star-filter active-state helper.
- `app/utils/wine_prompts.py`: Wine/OpenAI prompt construction helper.
- `app/utils/locationMatcher.py`: fuzzy location lookup using `fuzzywuzzy`, `python-Levenshtein`, and `unidecode`.

Use `app.*` imports for runtime modules. Do not add new root-level `callbacks/`, `components/`, `layouts/`, `pages/`, or `utils/` packages.

## Assets and Styling

`assets/styles.css`

- Primary styling file.
- Contains global, header/nav, Guide, Analysis, Economics, Wine, and responsive styles.
- Contains a large commented Wine work-in-progress block at the bottom; do not rely on it as active styling.
- Current next focus is CSS organisation, responsive cleanup, and a more mature visual system for Analysis, Economics, and Wine.
- Keep component IDs and class names stable unless a styling task explicitly includes covered class-name renaming.

`assets/scroll-script.js`

- Uses event delegation for Analysis, Economics, and Wine nav clicks.
- Scrolls to `analysis-content-top`, `demographics-content-top`, or `wine-content-top` when that anchor exists.
- Retries once after Dash swaps page content for route changes.

`assets/custom_header.html`

- Custom Dash index template with meta tags and app placeholders.

`assets/basicTileMap.json`

- Custom tile style.
- Contains an embedded tile service key. Treat it as a deployment/config decision, not incidental styling.

`assets/data`

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

Root layout contains:

- `dcc.Location(id="url")`
- `dash.page_container`
- root stores:
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

Current routes:

- `/` -> Guide
- `/home` -> Guide compatibility page
- `/analysis` -> core Michelin analysis sections and rankings
- `/economics` -> socioeconomic and demographics section
- `/wine` -> wine-region map and generated summary section
- anything else -> Dash Pages 404 fallback using `app/pages/not_found_404.py`

## Gotchas

- Dash Pages owns routing. Do not import `michelin_app.py` from page modules or callback modules.
- `suppress_callback_exceptions=True` remains enabled because callbacks are registered separately from page layout mounting.
- Flask `before_request` hooks are split between `enforce_https_redirect` and `ensure_session`. Keep the HTTPS hook before session work.
- HTTPS redirect is environment-aware and proxy-aware through `app/app_config.py` and `ProxyFix`.
- Session request counts limit OpenAI calls to 10 per session by default.
- Local-only generated `FLASK_SECRET_KEY` fallback resets sessions on restart.
- `Flask-Caching` uses the in-process `SimpleCache` backend via the full backend class path. It is not shared across Gunicorn workers or Heroku dynos.
- The Wine callback uses both `@cache.memoize` and manual `cache.get/cache.set`.
- The OpenAI client is created at import time. Missing or invalid `OPENAI_API_KEY` should be handled gracefully by the Wine page.
- Fiona is not installed directly. If it reappears transitively, verify why before accepting the dependency.
- `Aptfile` may eventually be removable, but only after dedicated Heroku build/deployment verification.
- `department_num` is read as string-like for both France and Monaco. Do not normalize department codes without checking leading-zero and Corsican `2A`/`2B` behavior.
- The Guide page includes Monaco only when the selected region is `Provence-Alpes-Côte d'Azur`.
- Analysis, Economics, and Wine currently use France data only unless explicitly changed.
- `app/layouts/layout_main.py` and `app/layouts/analysis_shared.py` both define star-filter helpers with overlapping names but different ID conventions.
- Analysis, Economics, and Wine share CSS conventions and star-filter classes. Keep IDs/classes stable until behaviour is covered by targeted tests.
- Some callbacks assume dropdown values are lists and can fail if a multi-select is cleared to `None`.
- `plot_single_choropleth_plotly` mutates its input frame by writing `total_restaurants`. Pass copies or make the helper copy internally.
- Plotly map usage mixes `Scattermap`, `Choroplethmap`, `Choropleth`, and an older `mapbox_style` property in one fallback figure. Be careful when upgrading Plotly.
- Wine-region click handling maps Plotly curve numbers back through list positions. Multi-polygon regions can make this fragile. Prefer storing the wine region name in trace `customdata` or `meta` in a behaviour-covered change.
- `Development/` is ignored scratch/reference material, not deployed code.
- Do not commit `__pycache__/` artifacts.
- `assets/data/wine_regions_simplified.geojson` is currently untracked and unrelated to the deployed `wine_regions_cleaned.geojson` path.

## Next Focus

The next planned work is styling and content modernisation:

- organise `assets/styles.css`
- audit class usage and unused/obsolete selectors
- consolidate media queries and responsive behaviour
- make Analysis feel like a polished data/editorial page
- make Economics feel credible and clear
- make Wine feel refined without gimmicks
- reduce excessive colour and playful/pastel styling
- preserve Guide behaviour and appearance unless a shared styling issue affects it

Use `ROADMAP.md` for the phase plan and `STYLE_AUDIT.md` for current CSS findings.

## Quick Local Checks

After changing Python architecture, callbacks, layouts, or routes, run at least:

```bash
python -m py_compile michelin_app.py app/callbacks/navigation.py app/callbacks/guide.py app/callbacks/analysis.py app/callbacks/economics.py app/callbacks/wine.py app/layouts/layout_main.py app/layouts/analysis.py app/layouts/economics.py app/layouts/wine.py app/layouts/analysis_shared.py app/layouts/layout_404.py app/utils/guide_figures.py app/utils/analysis_figures.py app/utils/economics_figures.py app/utils/wine_figures.py app/utils/restaurant_cards.py app/utils/star_filters.py app/utils/wine_prompts.py app/utils/locationMatcher.py
```

For the supported smoke-test harness:

```bash
pip install -r requirements_dev.txt
python -m pytest
```

`pytest.ini` limits test discovery to `tests/`. The current suite imports the app, checks route shells, verifies central data objects load, and constructs the Analysis/Economics/Wine layouts without OpenAI credentials, browser automation, or visual regression checks.

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

- Keep documentation, styling, layout, callback, data loading, and deployment changes separate where possible.
- Avoid broad CSS rewrites unless the task is explicitly a styling-system cleanup.
- Leave unrelated local changes alone.
- Do not stage untracked bytecode.
- Treat `assets/data/wine_regions_simplified.geojson` as local/untracked unless the user explicitly asks to add it.
