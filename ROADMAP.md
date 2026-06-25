# Michelin App Modernisation Roadmap

## Purpose

This roadmap describes the work needed to turn the current pseudo-multipage Dash app into a true multipage app on the Heroku 24 deployment path, while preserving the existing visual design as much as possible.

The primary product goal is to split the former combined `Analysis` page into three first-class pages:

- `Analysis`: restaurant distribution, Michelin ranking, region, department, and arrondissement views.
- `Economics`: socioeconomic and demographic exploration.
- `Wine`: wine-region map, restaurant overlay, and OpenAI-powered region summaries.

The first implementation pass should be architectural. Styling work should stay minimal unless a split page exposes a layout defect.

## Current Repository Shape

The deployed application is currently concentrated in a small number of large modules:

- `michelin_app.py`: application entrypoint, Flask server setup, Dash Pages setup, cache setup, OpenAI client setup, and callback registration.
- `app_data.py`: central restaurant/GeoJSON loading, schema checks, and existing derived dropdown/map lookup values.
- `components/shared.py`: shared header, footer, visible nav metadata, Michelin icon helpers, and rating colours.
- `callbacks/navigation.py`: global hamburger/menu and active-route callbacks registered by `michelin_app.py`.
- `callbacks/guide.py`: Guide/Home page callbacks registered by `michelin_app.py`.
- `callbacks/analysis.py`: core Analysis page callbacks registered by `michelin_app.py`.
- `callbacks/economics.py`: Economics/Demographics page callbacks registered by `michelin_app.py`.
- `callbacks/wine.py`: Wine/OpenAI page callbacks registered by `michelin_app.py`.
- `pages/`: thin Dash Pages route modules for Guide, `/home` compatibility, Analysis, Economics, Wine, and the 404 fallback.
- `layouts/layout_main.py`: Guide page layout plus main-page star filters.
- `layouts/layout_analysis.py`: page shell and section-level builders for Analysis, Economics, and Wine pages.
- `layouts/layout_404.py`: 404 layout.
- `utils/appFunctions.py`: Plotly map/chart builders, restaurant card rendering, star-button helper logic, wine prompt generation, and other mixed presentation/data helpers.
- `utils/locationMatcher.py`: fuzzy location lookup used by the Guide page.
- `assets/`: CSS, client JS, custom Dash index template, images, CSV/GeoJSON data, and a tile style JSON.
- `Procfile`: Heroku web command, `gunicorn michelin_app:server`.
- `Aptfile`: native GIS packages, currently `gdal-bin` and `libgdal-dev`.
- `requirements.txt`: pinned Python dependencies for Dash, Flask, GeoPandas/Pyogrio, Plotly, OpenAI, and related libraries.

Dash Pages now owns the routing shell. Analysis, Economics, and Wine are now separate public routes, and Phase 5 callback ownership is split by page callback module.

## Repository Change Map

| Path | Current role | Migration action |
| --- | --- | --- |
| `.python-version` | Declares Python `3.12`. | Keep aligned with README and Heroku runtime expectations. |
| `.gitignore` | Ignores `.env`, IDE files, `Development/`, and master wine GeoJSON. | Add bytecode/cache ignores before cleanup work. |
| `.gitattributes` | Text normalization only. | No expected change. |
| `Procfile` | Heroku web process, `gunicorn michelin_app:server`. | Keep stable unless the deployment module is intentionally renamed. |
| `Aptfile` | Installs GDAL/native GIS packages for the Heroku geospatial build path. | Keep for now; remove only after dedicated Heroku build verification. |
| `requirements.txt` | Pins Dash, Flask, GeoPandas/Pyogrio, Plotly, OpenAI, and runtime packages. | Keep package changes scoped; avoid unrelated upgrades mixed with routing changes. |
| `README.md` | Product and local setup docs. | Keep current with runtime/config changes as the refactor progresses. |
| `michelin_app.py` | App/server setup, callback registration, service clients, and root layout. | Shrink to deployment entrypoint plus app creation/registration. |
| `app_data.py` | Loads app data and builds existing derived lookup values. | Keep as the data boundary when callbacks move into page modules. |
| `components/shared.py` | Shared header/footer, visible nav metadata, icon helpers, and rating colours. | Keep active-route metadata aligned with page modules. |
| `callbacks/navigation.py` | Current hamburger/menu and active-route callbacks registered by `michelin_app.py`. | Keep as the navigation callback owner unless routing behavior changes. |
| `callbacks/guide.py` | Current Guide/Home callbacks registered by `michelin_app.py`. | Keep as the Guide callback owner during later page splits. |
| `callbacks/analysis.py` | Current core Analysis callbacks registered by `michelin_app.py`. | Keep as the Analysis callback owner; split figure helpers later. |
| `callbacks/economics.py` | Current Economics/Demographics callbacks registered by `michelin_app.py`. | Keep as the Economics callback owner; split figure helpers later. |
| `callbacks/wine.py` | Current Wine/OpenAI callbacks registered by `michelin_app.py`. | Keep as the Wine callback owner; split prompt/cache/service helpers later. |
| `pages/*` | Dash Pages route wrappers for the current layouts. | Keep wrappers thin; move callback ownership later. |
| `layouts/layout_main.py` | Guide layout plus main-page star filter. | Keep Guide-specific layout here until a dedicated layout split is worthwhile. |
| `layouts/layout_analysis.py` | Shared page shell and section-level builders for Analysis, Economics, and Wine. | Keep styling wrappers stable while callbacks move later. |
| `layouts/layout_404.py` | 404 layout. | Convert to Dash Pages fallback or keep as not-found page. |
| `utils/appFunctions.py` | Mixed plotting, Dash components, ranking, wine prompt, helper logic. | Split into figures, components, and services. |
| `utils/locationMatcher.py` | Fuzzy city/department lookup. | Move or keep as service; add tests around accent/case matching. |
| `assets/styles.css` | Main styling. | Preserve class names and avoid broad styling changes during routing migration. |
| `assets/scroll-script.js` | Analysis/Economics/Wine nav scroll helper. | Revisit after page/callback ownership settles. |
| `assets/custom_header.html` | Dash index template. | Keep unless route-specific meta tags become required. |
| `assets/basicTileMap.json` | Custom map tile style with embedded tile key. | Decide whether key remains public/restricted or moves to config. |
| `assets/Data/*` | Deployed CSV/GeoJSON data. | Keep stable; centralize schema validation and dtype normalization. |
| `assets/Images/*` | Static images and demo GIFs. | No expected architecture change. |
| `LICENSE.md` | Project license. | No expected change. |

## Current Page Model

Current public routes are registered with Dash Pages:

- `/` and `/home`: Guide layout from `get_main_layout()`.
- `/analysis`: combined layout from `get_analysis_layout()`.
- anything else: `get_404_layout()`.

Target public routes:

- `/`: Guide.
- `/analysis`: restaurant distribution and rankings.
- `/economics`: socioeconomic and demographic maps/charts.
- `/wine`: wine regions and generated wine-region notes.
- `/home`: compatibility redirect or alias to `/`.

Page titles can change later, but the route split should reflect the three distinct callback domains that already exist inside `layout_analysis.py`.

## Recommended Target Architecture

Use Dash Pages because the repo already uses Dash `2.18.1`, which supports first-class page registration. Keep the Heroku-facing `server` export stable so the current `Procfile` can continue to work.

Recommended structure:

```text
michelin_app.py
app/
  __init__.py
  config.py
  data.py
  cache.py
  pages/
    guide.py
    analysis.py
    economics.py
    wine.py
    not_found.py
  callbacks/
    navigation.py
    guide.py
    analysis.py
    economics.py
    wine.py
  components/
    header.py
    footer.py
    michelin_icons.py
    star_filters.py
    restaurant_cards.py
  figures/
    guide_maps.py
    analysis_figures.py
    economics_figures.py
    wine_figures.py
  services/
    location_matcher.py
    wine_info.py
```

`michelin_app.py` should become the small deployment entrypoint:

- create Flask `server`
- create Dash `app`
- register cache, config, and callbacks
- expose `server` for Gunicorn
- optionally run the app locally under `if __name__ == "__main__"`

The current file name can stay to avoid deployment churn.

## Migration Phases

### Phase 0: Baseline and Guardrails

- Keep the supported Python runtime consistent across `.python-version`, `README.md`, and Heroku expectations.
- Add a repeatable local smoke command before refactoring. At minimum, verify import, route layout creation, and callback registration.
- Avoid committing generated bytecode. Local `__pycache__/` folders are currently visible as untracked files.
- Treat the modified `assets/styles.css` WIP wine CSS as existing local work unless explicitly cleaned up.
- Keep `Procfile` compatibility until the final deployment test passes.

### Phase 1: App Factory, Config, and Data Boundary

- Extract Flask/Dash creation into a small app factory or initializer.
- Move environment handling into `app/config.py`.
- Keep the environment-aware HTTPS redirect contract intact. Local development should not require commenting code out.
- Move `OPENAI_API_KEY`, `FLASK_SECRET_KEY`, cache settings, and request limits into config.
- Keep CSV/GeoJSON loading in `app_data.py` until a package/app-factory structure is introduced.
- Preserve explicit string-like identifier checks for `department_num` and geographic `code` columns.
- Use repository-relative `Path` objects rather than relying on the process working directory.

### Phase 2: Shared Components

- Header/footer, visible nav metadata, Michelin icon helpers, and rating colours now live in `components/shared.py`.
- Visible navigation now includes Guide, Analysis, Economics, and Wine.
- `/home` remains an active Guide alias.
- `assets/scroll-script.js` maps the visible Analysis/Economics/Wine links to their current page anchors.
- Keep CSS class names stable where possible to avoid unnecessary styling work.

### Phase 3: True Multipage Routing

- Dash Pages routing shell is in place:
  - `dash.Dash(..., use_pages=True, ...)`
  - `dash.register_page(...)` in `pages/`
  - `dash.page_container` in the root layout
- The old `display_page` callback has been removed.
- Keep shared stores only when they are genuinely cross-page.
- Move page-specific stores into the relevant page layout.
- Preserve `/home` with the current compatibility page until external links are updated.
- Decide whether `suppress_callback_exceptions=True` is still needed after page registration. Keep it only if callbacks are registered before page layouts are available.

### Phase 4: Guide Page Extraction

Guide page callbacks now live in `callbacks/guide.py` and are registered from `michelin_app.py` with `register_guide_callbacks(app, DATA)`:

- search collapse and city matching
- department dropdown population
- main-page star filter state
- restaurant sidebar detail updates
- Paris arrondissement visibility
- main map updates
- centroid and map-view stores

Keep Monaco handling explicit. It is currently included for the Guide page when the selected region is `Provence-Alpes-Côte d'Azur`.

Navigation callbacks now live in `callbacks/navigation.py` and are registered from `michelin_app.py` with `register_navigation_callbacks(app)`. Visible navigation includes Guide, Analysis, Economics, and Wine, with `/home` still treated as a Guide active path.

`suppress_callback_exceptions=True` was inspected during the navigation extraction and left enabled because callbacks are still registered separately from Dash Pages layout mounting.

Core Analysis callbacks now live in `callbacks/analysis.py` and are registered from `michelin_app.py` with `register_analysis_callbacks(app, DATA)`. Economics callbacks now live in `callbacks/economics.py` and are registered from `michelin_app.py` with `register_economics_callbacks(app, DATA)`. Wine/OpenAI callbacks now live in `callbacks/wine.py` and are registered from `michelin_app.py` with `register_wine_callbacks(app, DATA, CONFIG, cache, client)`.

### Phase 5: Split the Current Analysis Page

`/analysis`, `/economics`, and `/wine` are now real Dash Pages routes composed from `layouts/layout_analysis.py` builders:

- `build_analysis_sections()`
- `build_economics_section()`
- `build_wine_section()`
- `build_combined_analysis_content()`

The old combined `/analysis` public page was removed rather than retained as a compatibility route. `build_combined_analysis_content()` remains available internally as a reference/composition helper, but it is not currently exposed by a public page.

Current page composition:

- `Analysis` page:
  - Michelin intro
  - region distribution
  - department distribution
  - arrondissement distribution
  - top restaurant rankings
- `Economics` page:
  - socioeconomic metric selector
  - region/department demographic map
  - demographic bar chart
  - weighted-mean explanation
  - optional starred restaurant overlay
- `Wine` page:
  - wine-region map
  - optional regional outlines
  - optional starred restaurant overlay
  - OpenAI region summary panel
  - generated-content disclaimer

Phase 5 callback ownership is complete. Page-specific callbacks no longer live in `michelin_app.py`.

### Phase 6: Figure and Service Refactor

Split `utils/appFunctions.py` by purpose:

- pure figure builders
- Dash component builders
- restaurant card rendering
- star filter button state helpers
- OpenAI/wine prompt service

This should make callback files thin. A good callback should mostly validate inputs, select data, call a figure/service helper, and return Dash outputs.

### Phase 7: Tests and Verification

Add lightweight checks before larger visual work:

- app import smoke test
- page layout smoke tests for `/`, `/analysis`, `/economics`, `/wine`
- callback registration smoke test
- data loader schema checks for required CSV/GeoJSON columns
- location matcher unit test for accent-insensitive matching
- wine curve-number mapping test
- route smoke checks against a local server

For visual regressions, use browser screenshots only after the routing split is stable.

### Phase 8: Deployment Cleanup

- Keep `gunicorn michelin_app:server` working or update `Procfile` in the same commit as the entrypoint change.
- Document required Heroku config vars:
  - `OPENAI_API_KEY`
  - `FLASK_SECRET_KEY`
  - any map tile key if it is moved out of `assets/basicTileMap.json`
- Confirm native GIS dependencies still build on the Heroku 24 stack.
- Confirm direct-loading each route works after deployment, not just client-side navigation.
- Update `README.md` after the architecture lands.

## Callback Split Reference

Current callback ownership:

| Current area | Current location | Target owner |
| --- | --- | --- |
| Dash Pages shell | `pages/*`, root layout in `michelin_app.py` | `pages/*` plus app setup |
| Navigation | `callbacks/navigation.py` | `callbacks/navigation.py` |
| Guide page | `callbacks/guide.py` 20-539 | `callbacks/guide.py` |
| Analysis distributions | `callbacks/analysis.py` | `callbacks/analysis.py` |
| Rankings | `callbacks/analysis.py` | `callbacks/analysis.py` |
| Economics/demographics | `callbacks/economics.py` | `callbacks/economics.py` |
| Wine | `callbacks/wine.py` | `callbacks/wine.py` |

Section-level layout builders for these pages still live in `layouts/layout_analysis.py`; rename or split that layout module in a later cleanup PR.

## Known Risks and Decisions

- `layout_analysis.py` has page-level layout builders, but the sections still share helper names, CSS classes, and star-filter conventions. Clean names only when callback ownership is clearer.
- `callbacks/wine.py` preserves the existing OpenAI client, cache, request-limit, and curve-number lookup behavior by dependency injection rather than recreating those services.
- Several callbacks assume list inputs are never `None`. Clearing multi-select dropdowns can expose this.
- `department_num` is compared as a string in several places. `app_data.py` now reads both restaurant CSVs with `dtype={"department_num": str}`; defer deeper normalization so leading-zero and Corsican code semantics remain unchanged.
- Flask `before_request` hooks now have distinct names for HTTPS enforcement and session setup. Keep this clarity during later app-factory work.
- There are duplicate Python callback function names. Dash has already registered the decorated callables, but this makes debugging harder.
- `Flask-Caching` is configured as `simple`, which is per-process memory. Multiple Gunicorn workers or dynos will not share cache entries.
- The wine callback uses both `@cache.memoize` and manual cache keys. Prefer one service-level cache keyed by wine region.
- The wine map stores Plotly curve numbers and later maps them back to `wine_df` rows. Multi-polygon wine regions can make this fragile unless trace metadata is added.
- The OpenAI client is created at import time. Missing `OPENAI_API_KEY` should degrade gracefully on the Wine page rather than failing unexpectedly.
- `assets/basicTileMap.json` contains an embedded tile-service key. Decide whether this is intentionally public and restricted, or move it to config.
- Local HTTPS behavior is now config-driven. Keep this contract intact during later routing work.
- Fiona has been removed as a direct dependency; Pyogrio is the intended GeoPandas file I/O path. Keep `Aptfile` until Heroku build evidence shows native GDAL packages are unnecessary.
- Data loading now lives in `app_data.py`; defer deeper data normalization so map/chart semantics stay unchanged.

## Definition of Done

The migration is complete when:

- `/`, `/analysis`, `/economics`, and `/wine` can be loaded directly, refreshed, and navigated through the header.
- Existing Guide behavior still works, including city matching, Paris arrondissement handling, Monaco inclusion, star filtering, map zoom persistence, and restaurant detail clicks.
- Analysis, Economics, and Wine pages preserve their current functional behavior after being split.
- Local development does not require editing source code to disable HTTPS redirects.
- Heroku still starts with Gunicorn and exposes the Flask `server`.
- README and AGENTS documentation match the new structure.
- No generated bytecode or local scratch files are committed.
