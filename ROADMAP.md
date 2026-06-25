# Michelin App Modernisation Roadmap

## Purpose

This roadmap describes the work needed to turn the current pseudo-multipage Dash app into a true multipage app on the Heroku 24 deployment path, while preserving the existing visual design as much as possible.

The primary product goal is to split the current combined `Analysis` page into three first-class pages:

- `Analysis`: restaurant distribution, Michelin ranking, region, department, and arrondissement views.
- `Economics`: socioeconomic and demographic exploration.
- `Wine`: wine-region map, restaurant overlay, and OpenAI-powered region summaries.

The first implementation pass should be architectural. Styling work should stay minimal unless a split page exposes a layout defect.

## Current Repository Shape

The deployed application is currently concentrated in a small number of large modules:

- `michelin_app.py`: application entrypoint, Flask server setup, Dash Pages setup, cache setup, OpenAI client setup, and all callbacks.
- `app_data.py`: central restaurant/GeoJSON loading, schema checks, and existing derived dropdown/map lookup values.
- `components/shared.py`: shared header, footer, visible nav metadata, Michelin icon helpers, and rating colours.
- `pages/`: thin Dash Pages route modules for Guide, `/home` compatibility, the combined Analysis page, and the 404 fallback.
- `layouts/layout_main.py`: Guide page layout plus main-page star filters.
- `layouts/layout_analysis.py`: one large combined Analysis layout containing the future Analysis, Economics, and Wine page sections.
- `layouts/layout_404.py`: 404 layout.
- `utils/appFunctions.py`: Plotly map/chart builders, restaurant card rendering, star-button helper logic, wine prompt generation, and other mixed presentation/data helpers.
- `utils/locationMatcher.py`: fuzzy location lookup used by the Guide page.
- `assets/`: CSS, client JS, custom Dash index template, images, CSV/GeoJSON data, and a tile style JSON.
- `Procfile`: Heroku web command, `gunicorn michelin_app:server`.
- `Aptfile`: native GIS packages, currently `gdal-bin` and `libgdal-dev`.
- `requirements.txt`: pinned Python dependencies for Dash, Flask, GeoPandas/Pyogrio, Plotly, OpenAI, and related libraries.

Dash Pages now owns the routing shell. The current registered pages still mirror the old public routes, and the Analysis page is still the combined Analysis/Economics/Wine layout.

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
| `michelin_app.py` | Monolithic app, routing, callbacks, and services. | Shrink to deployment entrypoint plus app creation/registration. |
| `app_data.py` | Loads app data and builds existing derived lookup values. | Keep as the data boundary when callbacks move into page modules. |
| `components/shared.py` | Shared header/footer, visible nav metadata, icon helpers, and rating colours. | Add future visible nav links only after their pages exist. |
| `pages/*` | Dash Pages route wrappers for the current layouts. | Split Analysis/Economics/Wine pages here in a later phase. |
| `layouts/layout_main.py` | Guide layout plus main-page star filter. | Keep Guide-specific layout here until Guide callbacks move. |
| `layouts/layout_analysis.py` | Combined Analysis/Economics/Wine layout. | Split into three page modules. |
| `layouts/layout_404.py` | 404 layout. | Convert to Dash Pages fallback or keep as not-found page. |
| `utils/appFunctions.py` | Mixed plotting, Dash components, ranking, wine prompt, helper logic. | Split into figures, components, and services. |
| `utils/locationMatcher.py` | Fuzzy city/department lookup. | Move or keep as service; add tests around accent/case matching. |
| `assets/styles.css` | Main styling. | Preserve class names and avoid broad styling changes during routing migration. |
| `assets/scroll-script.js` | Old Analysis scroll behavior. | Update or remove after pages split. |
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
- Keep visible navigation at Guide and Analysis until Economics and Wine have real routes.
- Update active nav state when new routes are added.
- `assets/scroll-script.js` now uses delegated clicks but still assumes the current combined Analysis anchor, `analysis-content-top`.
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

Move the Guide page callbacks out of `michelin_app.py` into `app/callbacks/guide.py`:

- search collapse and city matching
- department dropdown population
- main-page star filter state
- restaurant sidebar detail updates
- Paris arrondissement visibility
- main map updates
- centroid and map-view stores

Keep Monaco handling explicit. It is currently included for the Guide page when the selected region is `Provence-Alpes-Côte d'Azur`.

### Phase 5: Split the Current Analysis Page

Extract `layouts/layout_analysis.py` by section:

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

Move the matching callbacks into `app/callbacks/analysis.py`, `app/callbacks/economics.py`, and `app/callbacks/wine.py`.

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

Current callback ownership in `michelin_app.py`:

| Current area | Current callback lines | Target owner |
| --- | ---: | --- |
| Dash Pages shell and nav | `pages/*`, 114-134 | `pages/*` plus `app/callbacks/navigation.py` |
| Guide page | 136-658 | `app/callbacks/guide.py` |
| Analysis distributions | 659-873 | `app/callbacks/analysis.py` |
| Rankings | 874-926 | `app/callbacks/analysis.py` |
| Economics/demographics | 927-1101 | `app/callbacks/economics.py` |
| Wine | 1102-1259 | `app/callbacks/wine.py` |

## Known Risks and Decisions

- `layout_analysis.py` already contains the future page split, but the sections share helper names, CSS classes, and star-filter conventions. Split layout first, then clean names.
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
