# Agent Guide

## Purpose

This file is for future agents working on the Michelin Dash app. It documents the current architecture, dependencies, runtime assumptions, and gotchas that matter before refactoring the pseudo-multipage app into a true multipage app.

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

`michelin_app.py` currently does almost everything:

- binds data frames and derived lookup values from `app_data.py`
- creates the Flask `server`
- creates the Dash `app`
- imports runtime/path configuration from `app_config.py`
- creates the OpenAI client
- configures Flask session handling
- configures `Flask-Caching`
- defines root `dcc.Store` components
- defines the pseudo-router callback
- defines all page callbacks
- exposes `server` for Gunicorn

This file should be reduced over time, but preserve the `server` export until deployment is intentionally changed.

`app_data.py`

- Loads the two restaurant CSVs and deployed GeoJSON files from `CONFIG.data_path(...)`.
- Uses `geopandas.read_file(..., engine="pyogrio")` for GeoJSON I/O.
- Keeps `department_num` string-like in restaurant CSVs so values such as `06`, `2A`, `2B`, and `75` continue to match existing callback logic.
- Checks required columns for restaurants, aggregate geography, demographics, Paris, Monaco, and wine data at import time.
- Builds the existing derived values used by callbacks: `geo_df`, `unique_regions`, `initial_options`, `dept_to_code`, and `region_to_name`.
- Provides `get_combined_restaurant_data(...)` and `get_geo_df(...)` methods to preserve current France/Monaco behavior.

### Layout Modules

`layouts/layout_main.py`

- Guide page layout.
- Shared header/footer.
- Michelin icon helpers.
- Main Guide star-filter layout.
- Header currently has only `Guide` and `Analysis` links.

`layouts/layout_analysis.py`

- One combined layout for several conceptual pages.
- Contains the future Analysis page sections:
  - Michelin intro
  - region distribution
  - department distribution
  - arrondissement distribution
  - ranking section
- Contains the future Economics page:
  - demographic metric selector
  - demographic map
  - demographic bar chart
  - weighted mean explanation
- Contains the future Wine page:
  - wine map
  - restaurant overlay controls
  - LLM output panel
  - generated-content disclaimer

`layouts/layout_404.py`

- Small 404 page using shared header/footer.

### Utility Modules

`utils/appFunctions.py`

- Plotly map and chart builders.
- Restaurant detail card renderer.
- Michelin star hover text helpers.
- Star-button active-state helper.
- Ranking component builder.
- Demographic weighted mean and plots.
- Wine map builder.
- Wine prompt builder.

This module mixes pure plotting, Dash component rendering, and service prompt logic. Split by purpose during refactor.

`utils/locationMatcher.py`

- `LocationMatcher` uses `fuzzywuzzy`, `python-Levenshtein`, and `unidecode`.
- It normalizes accents and casing, splits the restaurant `location` field, and returns matched region/department data.

### Geospatial Dependencies

- `app_data.py` uses `geopandas.read_file(...)` for local GeoJSON files and `geopandas.GeoDataFrame(...)` for Monaco/France geometry combination.
- `utils/appFunctions.py` uses GeoPandas CRS helpers and Shapely geometry objects. It does not read or write files.
- Pyogrio is the intended GeoPandas I/O backend. Do not re-add Fiona unless a future feature requires Fiona-specific behavior.
- `Aptfile` remains conservative for Heroku 24 builds. Pyogrio wheels include GDAL on supported platforms, but remove `gdal-bin`/`libgdal-dev` only after a dedicated deployment/build verification.

### Assets

`assets/styles.css`

- Primary styling file.
- Currently has local modified WIP commented Wine CSS at the bottom. Do not overwrite casually.

`assets/scroll-script.js`

- Adds a click listener to `analysis-button` and scrolls to `analysis-content-top`.
- This will become stale after splitting Analysis, Economics, and Wine.

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

The app is pseudo-multipage:

- Root layout contains `dcc.Location(id="url")`.
- Root layout contains `html.Div(id="page-content")`.
- `display_page(pathname)` returns a layout based on the URL.

Current routes:

- `/` -> Guide
- `/home` -> Guide
- `/analysis` -> combined Analysis/Economics/Wine page
- anything else -> 404

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

Many of these are page-specific and should move into page layouts during true multipage migration.

## Callback Ownership

Current callbacks live in `michelin_app.py`.

Recommended ownership after refactor:

- `app/callbacks/navigation.py`: active nav, hamburger menu, redirects or aliases.
- `app/callbacks/guide.py`: Guide search, filters, map, restaurant details, centroids, main map-view store.
- `app/callbacks/analysis.py`: region, department, arrondissement, and ranking callbacks.
- `app/callbacks/economics.py`: demographic map, bar chart, weighted mean, economics map-view store.
- `app/callbacks/wine.py`: wine map, wine map-view store, wine star buttons, OpenAI summary callback.

Use `dash.callback` in page callback modules where practical, or register callbacks through explicit `register_callbacks(app, deps)` functions. Avoid importing the app object into every module.

## Gotchas

- The app has no Dash Pages setup yet. There is no `dash.register_page`, `dash.page_container`, or `use_pages=True`.
- `suppress_callback_exceptions=True` currently hides missing component problems caused by pseudo-routing. Revisit it after pages are split.
- Flask `before_request` hooks are split between `enforce_https_redirect` and `ensure_session`. Keep the HTTPS hook before session work.
- HTTPS redirect is environment-aware and proxy-aware through `app_config.py` and `ProxyFix`. Keep it that way during later refactors.
- Session request counts limit OpenAI calls to 10 per session by default. Local-only generated `FLASK_SECRET_KEY` fallback resets sessions on restart.
- `Flask-Caching` uses `CACHE_TYPE="simple"`, which is per-process memory. It is not shared across Gunicorn workers or Heroku dynos.
- The Wine callback uses both `@cache.memoize` and manual `cache.get/cache.set`. Prefer one cache boundary keyed by wine region.
- The OpenAI client is created at import time. Missing or invalid `OPENAI_API_KEY` should be handled gracefully by the Wine page.
- Fiona is no longer installed directly. If it reappears transitively, verify why before accepting the dependency.
- `Aptfile` may eventually be removable, but that is a Heroku build/deployment validation task, not part of page-routing work.
- `department_num` is now explicitly read as string-like for both France and Monaco. Do not normalize department codes further without checking leading-zero and Corsican `2A`/`2B` behavior.
- The Guide page includes Monaco only when the selected region is `Provence-Alpes-Côte d'Azur`. Analysis, Economics, and Wine currently use France data only unless explicitly changed.
- `layout_main.py` and `layout_analysis.py` both define star-filter helpers with overlapping names but different ID conventions.
- Some callback function names are duplicated or misleading. Dash registers the decorated function object, but duplicate names are painful for debugging.
- Some callbacks assume dropdown values are lists and can fail if a multi-select is cleared to `None`.
- `plot_single_choropleth_plotly` mutates its input frame by writing `total_restaurants`. Pass copies or make the helper copy internally.
- Plotly map usage mixes `Scattermap`, `Choroplethmap`, `Choropleth`, and an older `mapbox_style` property in one fallback figure. Be careful when upgrading Plotly.
- Wine-region click handling maps Plotly curve numbers back through list positions. Multi-polygon regions can make this fragile. Prefer storing the wine region name in trace `customdata` or `meta`.
- `assets/scroll-script.js` targets the old single Analysis page and should be updated or removed after routing changes.
- `Development/` is ignored scratch/reference material, not deployed code.
- Do not commit `__pycache__/` artifacts. They are currently present as untracked local files.
- `assets/Data/wine_regions_simplified.geojson` is currently untracked and unrelated to the deployed `wine_regions_cleaned.geojson` path.

## Safe Refactor Order

1. Stabilize runtime/config and add smoke checks.
2. Extract data loading with dtype normalization.
3. Extract shared header/footer/icon/star-filter components.
4. Introduce Dash Pages while keeping existing layouts intact.
5. Move Guide callbacks.
6. Split the combined Analysis layout into Analysis, Economics, and Wine pages.
7. Move callbacks page by page.
8. Split figure/service helpers.
9. Update README and deployment notes.

## Quick Local Checks

After changing architecture, run at least:

```bash
python -m py_compile michelin_app.py layouts/layout_main.py layouts/layout_analysis.py layouts/layout_404.py utils/appFunctions.py utils/locationMatcher.py
```

If dependencies are installed:

```bash
python michelin_app.py
```

Then verify direct route loads in a browser:

```text
http://127.0.0.1:8050/
http://127.0.0.1:8050/analysis
http://127.0.0.1:8050/economics
http://127.0.0.1:8050/wine
```

The current app will not have `/economics` or `/wine` until the routing migration lands.

## Commit Hygiene

- Keep docs, routing, data loading, and visual styling changes separate where possible.
- Avoid broad CSS rewrites during the architecture migration.
- Leave unrelated local changes alone.
- Do not stage untracked bytecode.
- Treat `assets/Data/wine_regions_simplified.geojson` as local/untracked unless the user explicitly asks to add it.
