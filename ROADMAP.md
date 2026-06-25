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
- `app/app_config.py`: runtime configuration, repo-root/package paths, cache settings, Flask secret handling, debug/HTTPS flags, and Dash Pages folder path.
- `app/app_data.py`: central restaurant/GeoJSON loading, schema checks, and existing derived dropdown/map lookup values.
- `app/components/shared.py`: shared header, footer, visible nav metadata, Michelin icon helpers, and rating colours.
- `app/callbacks/navigation.py`: global hamburger/menu and active-route callbacks registered by `michelin_app.py`.
- `app/callbacks/guide.py`: Guide/Home page callbacks registered by `michelin_app.py`.
- `app/callbacks/analysis.py`: core Analysis page callbacks registered by `michelin_app.py`.
- `app/callbacks/economics.py`: Economics/Demographics page callbacks registered by `michelin_app.py`.
- `app/callbacks/wine.py`: Wine/OpenAI page callbacks registered by `michelin_app.py`.
- `app/pages/`: thin Dash Pages route modules for Guide, `/home` compatibility, Analysis, Economics, Wine, and the 404 fallback.
- `app/layouts/layout_main.py`: Guide page layout plus main-page star filters.
- `app/layouts/analysis.py`: Analysis page section builders and page layout.
- `app/layouts/economics.py`: Economics page section builder and page layout.
- `app/layouts/wine.py`: Wine page section builder and page layout.
- `app/layouts/analysis_shared.py`: shared page shell and star-filter helpers for the analysis-style pages.
- `app/layouts/layout_404.py`: 404 layout.
- `app/utils/guide_figures.py`: Guide/Home map figure builders and outline helpers.
- `app/utils/analysis_figures.py`: core Analysis figure builders and ranking helper.
- `app/utils/economics_figures.py`: Economics/Demographics map, bar, and weighted-mean helpers.
- `app/utils/wine_figures.py`: Wine-region map figure builder.
- `app/utils/restaurant_cards.py`: restaurant detail/card rendering helper.
- `app/utils/star_filters.py`: star-filter active-state helper.
- `app/utils/wine_prompts.py`: Wine/OpenAI prompt construction helper.
- `app/utils/locationMatcher.py`: fuzzy location lookup used by the Guide page.
- `assets/`: CSS, client JS, custom Dash index template, images, CSV/GeoJSON data, and a tile style JSON.
- `Procfile`: Heroku web command, `gunicorn michelin_app:server`.
- `Aptfile`: native GIS packages, currently `gdal-bin` and `libgdal-dev`.
- `requirements.txt`: pinned Python dependencies for Dash, Flask, GeoPandas/Pyogrio, Plotly, OpenAI, and related libraries.

Dash Pages now owns the routing shell. Analysis, Economics, and Wine are now separate public routes, and Phase 5 callback ownership is split by page callback module.

Runtime application modules now live under the `app/` package. The root `michelin_app.py` entrypoint remains in place for Heroku and passes `CONFIG.pages_dir` to Dash so page discovery uses `app/pages/`. Root `assets/` and `assets/data/` remain unchanged.

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
| `app/app_config.py` | Runtime config, repo/package paths, cache/debug/HTTPS/OpenAI settings, and Dash Pages folder path. | Keep repo-root path calculation stable after the package move. |
| `app/app_data.py` | Loads app data and builds existing derived lookup values. | Keep as the data boundary when callbacks move into page modules. |
| `app/components/shared.py` | Shared header/footer, visible nav metadata, icon helpers, and rating colours. | Keep active-route metadata aligned with page modules. |
| `app/callbacks/navigation.py` | Current hamburger/menu and active-route callbacks registered by `michelin_app.py`. | Keep as the navigation callback owner unless routing behavior changes. |
| `app/callbacks/guide.py` | Current Guide/Home callbacks registered by `michelin_app.py`. | Keep as the Guide callback owner during later page splits. |
| `app/callbacks/analysis.py` | Current core Analysis callbacks registered by `michelin_app.py`. | Keep as the Analysis callback owner; split figure helpers later. |
| `app/callbacks/economics.py` | Current Economics/Demographics callbacks registered by `michelin_app.py`. | Keep as the Economics callback owner; split figure helpers later. |
| `app/callbacks/wine.py` | Current Wine/OpenAI callbacks registered by `michelin_app.py`. | Keep as the Wine callback owner; split prompt/cache/service helpers later. |
| `app/pages/*` | Dash Pages route wrappers for the current layouts. | Keep wrappers thin; move callback ownership later. |
| `app/layouts/layout_main.py` | Guide layout plus main-page star filter. | Keep Guide-specific layout here until a dedicated layout split is worthwhile. |
| `app/layouts/analysis.py` | Analysis page layout and section builders. | Keep IDs/classes stable; split figure helpers later. |
| `app/layouts/economics.py` | Economics page layout and section builder. | Keep IDs/classes stable; split figure helpers later. |
| `app/layouts/wine.py` | Wine page layout and section builder. | Keep IDs/classes stable; split wine service/prompt helpers later. |
| `app/layouts/analysis_shared.py` | Shared page shell and star-filter helpers for Analysis/Economics/Wine layouts. | Keep as a small shared layout helper inside the app package. |
| `app/layouts/layout_404.py` | 404 layout. | Convert to Dash Pages fallback or keep as not-found page. |
| `app/utils/guide_figures.py` | Guide/Home map figure builders and outline helpers. | Keep behaviour stable; direct callback imports can move here next. |
| `app/utils/analysis_figures.py` | Core Analysis figures and ranking helper. | Keep behaviour stable; direct callback imports can move here next. |
| `app/utils/economics_figures.py` | Economics/Demographics map, bar chart, and weighted-mean helpers. | Keep behaviour stable; direct callback imports can move here next. |
| `app/utils/wine_figures.py` | Wine-region map figure builder. | Keep behaviour stable; direct callback imports can move here next. |
| `app/utils/restaurant_cards.py` | Restaurant detail/card rendering helper. | Keep card markup and classes stable. |
| `app/utils/star_filters.py` | Shared star-filter active-state helper. | Keep callback output shape stable. |
| `app/utils/wine_prompts.py` | Wine/OpenAI prompt construction helper. | Preserve prompt wording unless changing Wine behavior intentionally. |
| `app/utils/locationMatcher.py` | Fuzzy city/department lookup. | Move or keep as service; add tests around accent/case matching. |
| `assets/styles.css` | Main styling. | Preserve class names and avoid broad styling changes during routing migration. |
| `assets/scroll-script.js` | Analysis/Economics/Wine nav scroll helper. | Revisit after page/callback ownership settles. |
| `assets/custom_header.html` | Dash index template. | Keep unless route-specific meta tags become required. |
| `assets/basicTileMap.json` | Custom map tile style with embedded tile key. | Decide whether key remains public/restricted or moves to config. |
| `assets/data/*` | Deployed CSV/GeoJSON data. | Keep stable; centralize schema validation and dtype normalization. |
| `assets/images/*` | Static images and demo GIFs. | Keep filenames lowercase and update app references with asset renames. |
| `LICENSE.md` | Project license. | No expected change. |

## Current Page Model

Current public routes are registered with Dash Pages:

- `/` and `/home`: Guide layout from `get_main_layout()`.
- `/analysis`: restaurant distribution and rankings from `app/layouts/analysis.py`.
- `/economics`: socioeconomic and demographic maps/charts from `app/layouts/economics.py`.
- `/wine`: wine regions and generated wine-region notes from `app/layouts/wine.py`.
- anything else: `get_404_layout()` through `app/pages/not_found_404.py`.

Page titles can change later, but the route split now reflects the three distinct callback domains.

## Current Package Architecture

Use Dash Pages because the repo already uses Dash `2.18.1`, which supports first-class page registration. Keep the Heroku-facing `server` export stable so the current `Procfile` can continue to work.

Current structure:

```text
michelin_app.py
app/
  __init__.py
  app_config.py
  app_data.py
  pages/
    guide.py
    analysis.py
    economics.py
    wine.py
    not_found_404.py
  callbacks/
    navigation.py
    guide.py
    analysis.py
    economics.py
    wine.py
  components/
    shared.py
  layouts/
    layout_main.py
    analysis.py
    economics.py
    wine.py
    analysis_shared.py
    layout_404.py
  utils/
    guide_figures.py
    analysis_figures.py
    economics_figures.py
    wine_figures.py
    restaurant_cards.py
    star_filters.py
    wine_prompts.py
    locationMatcher.py
assets/
  data/
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
- Avoid committing generated bytecode. Local `__pycache__/` folders should remain ignored and disposable.
- Treat the modified `assets/styles.css` WIP wine CSS as existing local work unless explicitly cleaned up.
- Keep `Procfile` compatibility until the final deployment test passes.

### Phase 1: App Factory, Config, and Data Boundary

- Extract Flask/Dash creation into a small app factory or initializer.
- Move environment handling into `app/app_config.py`.
- Keep the environment-aware HTTPS redirect contract intact. Local development should not require commenting code out.
- Move `OPENAI_API_KEY`, `FLASK_SECRET_KEY`, cache settings, and request limits into config.
- Keep CSV/GeoJSON loading in `app/app_data.py`.
- Preserve explicit string-like identifier checks for `department_num` and geographic `code` columns.
- Use repository-relative `Path` objects rather than relying on the process working directory.

### Phase 2: Shared Components

- Header/footer, visible nav metadata, Michelin icon helpers, and rating colours now live in `app/components/shared.py`.
- Visible navigation now includes Guide, Analysis, Economics, and Wine.
- `/home` remains an active Guide alias.
- `assets/scroll-script.js` maps the visible Analysis/Economics/Wine links to their current page anchors.
- Keep CSS class names stable where possible to avoid unnecessary styling work.

### Phase 3: True Multipage Routing

- Dash Pages routing shell is in place:
  - `dash.Dash(..., use_pages=True, ...)`
  - `dash.register_page(...)` in `app/pages/`
  - `dash.page_container` in the root layout
- The old `display_page` callback has been removed.
- Keep shared stores only when they are genuinely cross-page.
- Move page-specific stores into the relevant page layout.
- Preserve `/home` with the current compatibility page until external links are updated.
- Decide whether `suppress_callback_exceptions=True` is still needed after page registration. Keep it only if callbacks are registered before page layouts are available.

### Phase 4: Guide Page Extraction

Guide page callbacks now live in `app/callbacks/guide.py` and are registered from `michelin_app.py` with `register_guide_callbacks(app, DATA)`:

- search collapse and city matching
- department dropdown population
- main-page star filter state
- restaurant sidebar detail updates
- Paris arrondissement visibility
- main map updates
- centroid and map-view stores

Keep Monaco handling explicit. It is currently included for the Guide page when the selected region is `Provence-Alpes-Côte d'Azur`.

Navigation callbacks now live in `app/callbacks/navigation.py` and are registered from `michelin_app.py` with `register_navigation_callbacks(app)`. Visible navigation includes Guide, Analysis, Economics, and Wine, with `/home` still treated as a Guide active path.

`suppress_callback_exceptions=True` was inspected during the navigation extraction and left enabled because callbacks are still registered separately from Dash Pages layout mounting.

Core Analysis callbacks now live in `app/callbacks/analysis.py` and are registered from `michelin_app.py` with `register_analysis_callbacks(app, DATA)`. Economics callbacks now live in `app/callbacks/economics.py` and are registered from `michelin_app.py` with `register_economics_callbacks(app, DATA)`. Wine/OpenAI callbacks now live in `app/callbacks/wine.py` and are registered from `michelin_app.py` with `register_wine_callbacks(app, DATA, CONFIG, cache, client)`.

### Phase 5: Split the Current Analysis Page

`/analysis`, `/economics`, and `/wine` are real Dash Pages routes composed from page-specific layout modules:

- `app/layouts/analysis.py`: `build_analysis_sections()`
- `app/layouts/economics.py`: `build_economics_section()`
- `app/layouts/wine.py`: `build_wine_section()`
- `app/layouts/analysis_shared.py`: shared page shell and star-filter helpers

The old combined `/analysis` public page was removed rather than retained as a compatibility route. `build_combined_analysis_content()` was removed because no public page or internal code uses the combined composition helper.

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

The layout-module cleanup is also complete: the old large `app/layouts/layout_analysis.py` module has been removed rather than retained as a compatibility shim. This cleanup did not move callbacks; callback ownership remains in the dedicated `app/callbacks/*` modules.

### Phase 6: Figure and Service Refactor

Phase 6 utility cleanup is complete. The old mixed `app/utils/appFunctions.py` implementation is separated by purpose:

- `app/utils/guide_figures.py`: Guide/Home map figure builders and outline helpers.
- `app/utils/analysis_figures.py`: core Analysis figure builders and ranking helper.
- `app/utils/economics_figures.py`: demographic/economic map, bar, and weighted-mean helpers.
- `app/utils/wine_figures.py`: wine map helper.
- `app/utils/restaurant_cards.py`: restaurant detail/card renderer.
- `app/utils/star_filters.py`: star-filter active-state helper.
- `app/utils/wine_prompts.py`: OpenAI/wine prompt helper.

Callback modules now import directly from these purpose-specific modules. `app/utils/appFunctions.py` was removed because no code imports it after the direct-import cleanup.

A good callback should mostly validate inputs, select data, call a figure/service helper, and return Dash outputs.

### Phase 6.5: Package Move

Package-level cleanup is complete:

- Runtime modules now live under `app/`.
- Root `michelin_app.py` remains the Heroku entrypoint for `gunicorn michelin_app:server`.
- Dash Pages discovers `app/pages/` through `pages_folder=str(CONFIG.pages_dir)`.
- `app/app_config.py` calculates the repository root from inside the package and keeps `assets/` plus `assets/data/` at the repository root.
- Application imports use `app.*` paths rather than root-level `callbacks/`, `components/`, `layouts/`, `pages/`, or `utils/` packages.

The next cleanup should revisit `suppress_callback_exceptions=True` and app-factory extraction if route/layout smoke tests remain stable.

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
| Dash Pages shell | `app/pages/*`, root layout in `michelin_app.py` | `app/pages/*` plus app setup |
| Navigation | `app/callbacks/navigation.py` | `app/callbacks/navigation.py` |
| Guide page | `app/callbacks/guide.py` | `app/callbacks/guide.py` |
| Analysis distributions | `app/callbacks/analysis.py` | `app/callbacks/analysis.py` |
| Rankings | `app/callbacks/analysis.py` | `app/callbacks/analysis.py` |
| Economics/demographics | `app/callbacks/economics.py` | `app/callbacks/economics.py` |
| Wine | `app/callbacks/wine.py` | `app/callbacks/wine.py` |

Section-level layout builders for these pages now live in `app/layouts/analysis.py`, `app/layouts/economics.py`, and `app/layouts/wine.py`. Shared analysis-style layout helpers live in `app/layouts/analysis_shared.py`.

## Known Risks and Decisions

- Analysis, Economics, and Wine layout builders are split by module, but the sections still share CSS classes and star-filter conventions. Clean names only when visual behavior is covered by targeted checks.
- `app/callbacks/wine.py` preserves the existing OpenAI client, cache, request-limit, and curve-number lookup behavior by dependency injection rather than recreating those services.
- Several callbacks assume list inputs are never `None`. Clearing multi-select dropdowns can expose this.
- `department_num` is compared as a string in several places. `app/app_data.py` now reads both restaurant CSVs with `dtype={"department_num": str}`; defer deeper normalization so leading-zero and Corsican code semantics remain unchanged.
- Flask `before_request` hooks now have distinct names for HTTPS enforcement and session setup. Keep this clarity during later app-factory work.
- There are duplicate Python callback function names. Dash has already registered the decorated callables, but this makes debugging harder.
- `Flask-Caching` is configured as `simple`, which is per-process memory. Multiple Gunicorn workers or dynos will not share cache entries.
- The wine callback uses both `@cache.memoize` and manual cache keys. Prefer one service-level cache keyed by wine region.
- The wine map stores Plotly curve numbers and later maps them back to `wine_df` rows. Multi-polygon wine regions can make this fragile unless trace metadata is added.
- The OpenAI client is created at import time. Missing `OPENAI_API_KEY` should degrade gracefully on the Wine page rather than failing unexpectedly.
- `assets/basicTileMap.json` contains an embedded tile-service key. Decide whether this is intentionally public and restricted, or move it to config.
- Local HTTPS behavior is now config-driven. Keep this contract intact during later routing work.
- Fiona has been removed as a direct dependency; Pyogrio is the intended GeoPandas file I/O path. Keep `Aptfile` until Heroku build evidence shows native GDAL packages are unnecessary.
- Data loading now lives in `app/app_data.py`; defer deeper data normalization so map/chart semantics stay unchanged.
- Package-level cleanup is complete. Keep root `michelin_app.py` as the Heroku entrypoint unless the `Procfile` changes in the same deployment-focused PR.
- Utility imports now target the purpose-specific `app/utils/*` modules directly. The old `app/utils/appFunctions.py` shim has been removed.

## Definition of Done

The migration is complete when:

- `/`, `/analysis`, `/economics`, and `/wine` can be loaded directly, refreshed, and navigated through the header.
- Existing Guide behavior still works, including city matching, Paris arrondissement handling, Monaco inclusion, star filtering, map zoom persistence, and restaurant detail clicks.
- Analysis, Economics, and Wine pages preserve their current functional behavior after being split.
- Local development does not require editing source code to disable HTTPS redirects.
- Heroku still starts with Gunicorn and exposes the Flask `server`.
- README and AGENTS documentation match the new structure.
- No generated bytecode or local scratch files are committed.
