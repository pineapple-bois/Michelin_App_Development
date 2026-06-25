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

- `michelin_app.py`: application entrypoint, data loading, Flask server setup, Dash setup, pseudo-router, cache setup, OpenAI client setup, and all callbacks.
- `layouts/layout_main.py`: Guide page layout plus shared header, footer, Michelin icon helpers, and main-page star filters.
- `layouts/layout_analysis.py`: one large combined Analysis layout containing the future Analysis, Economics, and Wine page sections.
- `layouts/layout_404.py`: 404 layout.
- `utils/appFunctions.py`: Plotly map/chart builders, restaurant card rendering, star-button helper logic, wine prompt generation, and other mixed presentation/data helpers.
- `utils/locationMatcher.py`: fuzzy location lookup used by the Guide page.
- `assets/`: CSS, client JS, custom Dash index template, images, CSV/GeoJSON data, and a tile style JSON.
- `Procfile`: Heroku web command, `gunicorn michelin_app:server`.
- `Aptfile`: native GIS packages, currently `gdal-bin` and `libgdal-dev`.
- `requirements.txt`: pinned Python dependencies for Dash, Flask, GeoPandas, Plotly, OpenAI, and related libraries.

There is no true Dash Pages setup yet. The current router is a manual callback over `dcc.Location(id="url")` and `html.Div(id="page-content")`.

## Repository Change Map

| Path | Current role | Migration action |
| --- | --- | --- |
| `.python-version` | Declares Python `3.12`. | Keep or change deliberately, then align README and Heroku runtime expectations. |
| `.gitignore` | Ignores `.env`, IDE files, `Development/`, and master wine GeoJSON. | Add bytecode/cache ignores before cleanup work. |
| `.gitattributes` | Text normalization only. | No expected change. |
| `Procfile` | Heroku web process, `gunicorn michelin_app:server`. | Keep stable unless the deployment module is intentionally renamed. |
| `Aptfile` | Installs GDAL/native GIS packages for GeoPandas/Fiona. | Keep; re-check when dependency versions move. |
| `requirements.txt` | Pins Dash, Flask, GeoPandas, Plotly, OpenAI, and runtime packages. | Review only after architecture split; avoid dependency upgrades mixed with routing changes. |
| `README.md` | Product and local setup docs. | Update after refactor; current Python and local HTTPS instructions are stale. |
| `michelin_app.py` | Monolithic app, data loading, routing, callbacks, services. | Shrink to deployment entrypoint plus app creation/registration. |
| `layouts/layout_main.py` | Guide layout plus shared header/footer/icons/star filter. | Split Guide layout from shared components. |
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

Current public routes:

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

- Decide the supported Python runtime and make it consistent. The repo currently has `.python-version` set to `3.12`, while `README.md` tells local developers to use Python `3.9`.
- Add a repeatable local smoke command before refactoring. At minimum, verify import, route layout creation, and callback registration.
- Avoid committing generated bytecode. Local `__pycache__/` folders are currently visible as untracked files.
- Treat the modified `assets/styles.css` WIP wine CSS as existing local work unless explicitly cleaned up.
- Keep `Procfile` compatibility until the final deployment test passes.

### Phase 1: App Factory, Config, and Data Boundary

- Extract Flask/Dash creation into a small app factory or initializer.
- Move environment handling into `app/config.py`.
- Replace the unconditional HTTPS redirect with an environment-aware production setting. Local development should not require commenting code out.
- Move `OPENAI_API_KEY`, `FLASK_SECRET_KEY`, cache settings, and request limits into config.
- Move CSV/GeoJSON loading into `app/data.py`.
- Normalize key data types at load time, especially `department_num` and geographic `code` columns.
- Use repository-relative `Path` objects rather than relying on the process working directory.

### Phase 2: Shared Components

- Move header/footer and Michelin icon helpers out of `layout_main.py` into shared components.
- Convert navigation links to include Guide, Analysis, Economics, and Wine.
- Update active nav state for the new routes.
- Update or remove `assets/scroll-script.js`, which currently assumes the single Analysis page and `analysis-content-top`.
- Keep CSS class names stable where possible to avoid unnecessary styling work.

### Phase 3: True Multipage Routing

- Replace the `display_page` callback with Dash Pages:
  - `dash.Dash(..., use_pages=True, ...)`
  - `dash.register_page(...)` in each page module
  - `dash.page_container` in the root layout
- Keep shared stores only when they are genuinely cross-page.
- Move page-specific stores into the relevant page layout.
- Preserve `/home` with a redirect or alias until external links are updated.
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
| Pseudo-router and nav | 164-199 | `app/callbacks/navigation.py` or Dash Pages metadata |
| Guide page | 212-733 | `app/callbacks/guide.py` |
| Analysis distributions | 735-947 | `app/callbacks/analysis.py` |
| Rankings | 948-999 | `app/callbacks/analysis.py` |
| Economics/demographics | 1001-1174 | `app/callbacks/economics.py` |
| Wine | 1176-1328 | `app/callbacks/wine.py` |

## Known Risks and Decisions

- `layout_analysis.py` already contains the future page split, but the sections share helper names, CSS classes, and star-filter conventions. Split layout first, then clean names.
- Several callbacks assume list inputs are never `None`. Clearing multi-select dropdowns can expose this.
- `department_num` is compared as a string in several places, but France restaurant data is read without an explicit dtype while Monaco data is read with `dtype={"department_num": str}`.
- There are two Flask `before_request` functions with the same Python name. Flask registers both, but this is confusing and should be consolidated or renamed.
- There are duplicate Python callback function names. Dash has already registered the decorated callables, but this makes debugging harder.
- `Flask-Caching` is configured as `simple`, which is per-process memory. Multiple Gunicorn workers or dynos will not share cache entries.
- The wine callback uses both `@cache.memoize` and manual cache keys. Prefer one service-level cache keyed by wine region.
- The wine map stores Plotly curve numbers and later maps them back to `wine_df` rows. Multi-polygon wine regions can make this fragile unless trace metadata is added.
- The OpenAI client is created at import time. Missing `OPENAI_API_KEY` should degrade gracefully on the Wine page rather than failing unexpectedly.
- `assets/basicTileMap.json` contains an embedded tile-service key. Decide whether this is intentionally public and restricted, or move it to config.
- The README currently asks developers to manually comment out production HTTPS behavior for local development. This should become config-driven.

## Definition of Done

The migration is complete when:

- `/`, `/analysis`, `/economics`, and `/wine` can be loaded directly, refreshed, and navigated through the header.
- Existing Guide behavior still works, including city matching, Paris arrondissement handling, Monaco inclusion, star filtering, map zoom persistence, and restaurant detail clicks.
- Analysis, Economics, and Wine pages preserve their current functional behavior after being split.
- Local development does not require editing source code to disable HTTPS redirects.
- Heroku still starts with Gunicorn and exposes the Flask `server`.
- README and AGENTS documentation match the new structure.
- No generated bytecode or local scratch files are committed.
