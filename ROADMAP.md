# Michelin App Styling and Content Modernisation Roadmap

## Current Baseline

The multipage Dash refactor is complete and deployed. Treat the current repository as the stable baseline:

- `michelin_app.py` remains the Heroku/Gunicorn entrypoint and exports `server`.
- Dash Pages owns routing through thin modules in `app/pages/`.
- `/`, `/home`, `/analysis`, `/economics`, `/wine`, and the Dash Pages 404 fallback are current supported routes.
- Guide, navigation, Analysis, Economics, and Wine callbacks live in dedicated modules under `app/callbacks/`.
- Analysis, Economics, and Wine layouts live in `app/layouts/analysis.py`, `app/layouts/economics.py`, and `app/layouts/wine.py`.
- Shared Analysis/Economics/Wine shell helpers live in `app/layouts/analysis_shared.py`.
- Shared header, footer, nav metadata, and Michelin icon helpers live in `app/components/shared.py`.
- `assets/styles.css` is the primary styling surface and should remain behaviour-preserving until the styling phase begins.

The next phase is visual and content modernisation for the Analysis, Economics, and Wine pages. Preserve the Guide page unless shared styling changes expose a specific Guide issue.

For detailed selector and CSS findings, see `STYLE_AUDIT.md`.

## Design Direction

The target tone is mature, restrained, editorial, and coherent while still feeling connected to Michelin, French geography, restaurants, and wine.

- Use Michelin red as a disciplined accent rather than a dominant or repeated fill.
- Reduce competing blue, pastel, and section-specific accent treatments.
- Prefer warmer neutrals, quiet borders, restrained shadows, and consistent spacing.
- Make text hierarchy feel editorial: clear page heading, section lead, controls, then chart/map output.
- Make chart and map surroundings feel like analysis surfaces, not playful widgets.
- Use subtler cards and panels only where they support scanning or grouping.
- Keep filter and button states consistent across Analysis, Economics, and Wine.
- Give Wine a refined atmosphere without novelty styling or gimmicks.

Established Analysis direction:

- Analysis uses a clean white paper sheet with very pale grey gutters, internal indentation, and a centered max-width content area.
- Avoid cream/yellow paper tones, dashboard cards, shadows, rounded chart boxes, and tinted evidence containers.
- Analysis begins directly with “Restaurant Distributions Across France”; the Michelin history preamble and rating explainer are intentionally removed.
- Copy should be plain and direct. Avoid analyst-speak such as “patterns,” “clusters,” “insights,” “recognition,” and “geography level.”
- Controls use outline/accent styling. Data visualizations may use filled colour.
- Rating colours should stay recognisable but controlled: neither garish nor muddy.
- Analysis restaurant cards should carry Guide-page identity in a denser Analysis form.
- The shared footer should remain in normal document flow, not fixed over page content.

## Styling/CSS Audit Findings

`assets/styles.css` is organised roughly by global styles, header/nav, Guide, Analysis, Economics, Wine, responsive rules, then a commented Wine work-in-progress block. It is readable, but not yet a design system.

High-level findings:

- Repeated spacing values include `20px`, `30px`, `40px`, and `50px`, often applied page by page.
- Repeated border radii include `5px` and `8px`, with no documented rule for when each is used.
- Repeated shadows are limited but strong enough to make active controls feel heavier than the surrounding editorial layout.
- Colour usage mixes Michelin red, Bootstrap blue, greys, and many commented pastel/debug colours.
- Dropdown selected-value styles are page-specific: Analysis uses red while Economics uses blue.
- Star filter button styling is duplicated across Guide and Analysis-style pages with dynamic class names.
- Many Analysis/Economics/Wine containers use distinct class families even when they perform the same structural role.
- Several active class names have no obvious CSS rule, and several CSS rules target classes that are currently absent or only present in commented WIP code.
- There are many inline Dash `style={...}` widths and heights in the three target layouts; future styling work should either preserve them deliberately or migrate them into CSS in a behaviour-covered pass.

The first styling PR should introduce organisation and shared conventions before changing the look aggressively.

## Responsive/Media Query Findings

There are two active breakpoints:

- `@media screen and (max-width: 1400px)`
- `@media screen and (max-width: 1250px)`

These mostly adjust header height, header spacing, Guide layout, and some text sizes for Analysis-style pages. There is no dedicated small-mobile breakpoint.

Important responsive issues to inspect visually before implementation:

- Analysis graph/map pairs remain side-by-side by default and rely on fixed 50/50 widths.
- Economics map/chart uses a fixed `750px` content height and 50/50 layout.
- Wine map/LLM uses a 50/50 layout and the graph has inline `height: 700px`.
- Controls often use 50/50 or 25/25/50 assumptions that may not stack gracefully on narrow screens.
- The fixed header/footer plus `calc(100vh - ...)` layout may leave cramped vertical space on tablets and phones.
- Several dropdown menus use z-index fixes that should be retested after any responsive changes.

Responsive cleanup should consolidate breakpoints, define page-shell rules for tablet/mobile stacking, and only then tune page-specific exceptions.

## Page-Level Findings

### Analysis

The Analysis page is the pilot for the mature editorial data-report pattern.

Findings:

- The page now starts directly with “Restaurant Distributions Across France.”
- Region, department, arrondissement, and ranking sections should keep the current paper-sheet, plain-copy, and restrained-control direction.
- Graph/map areas should stay open and editorial; do not reintroduce dashboard cards, tinted evidence boxes, shadows, or rounded chart containers.
- Ranking controls, result headings, and restaurant cards now define the denser Analysis form of the Guide identity.
- Inline widths on graph/map containers should be audited before CSS changes.

Desired next outcome: consolidate responsive and media-query behaviour for this Analysis pattern before carrying the pattern to Economics and Wine.

### Economics

The Economics page has credible subject matter but the current styling does not yet support that credibility consistently.

Findings:

- The explanatory text is strong enough to serve as a serious lead section, but typography and spacing should make it feel more authoritative.
- Metric, granularity, add/remove, overlay, and star-filter controls need a clearer hierarchy.
- Economics dropdown selected values use Bootstrap blue, which visually competes with the Michelin palette and separates the page from Analysis.
- The weighted mean explanation is functionally useful but visually plain and should become a quiet explanatory note.
- Map and bar chart sections use fixed height and side-by-side assumptions that need mobile/tablet review.

Desired next outcome: a calm analytical page where demographic context feels rigorous, clear, and connected to the Michelin data.

### Wine

The Wine page should feel refined and atmospheric, but the current implementation is mostly utilitarian with a commented WIP styling block still present.

Findings:

- The page copy sets a refined tone, but controls, map, and generated-summary panel do not yet share a coherent visual language.
- Wine controls combine outline selection, overlay toggle, and star filters in one row with inline widths.
- The map/LLM split uses fixed 50/50 assumptions and an inline `700px` graph height.
- Region summary output and generated-content disclaimer need a more polished, trustworthy treatment.
- The commented WIP block at the end of `styles.css` should be deleted or revived intentionally during the styling cleanup, not left as background noise.

Desired next outcome: a restrained, wine-editorial page with a polished map/summary relationship and subtle generated-content disclosure.

## Proposed Work Phases

### Phase 1: Styling Inventory and Safety Baseline

- Keep behaviour unchanged.
- Confirm direct route loads for `/analysis`, `/economics`, and `/wine`.
- Capture desktop, tablet, and mobile screenshots before making style changes.
- Decide the target viewport set for visual QA.
- Record the current Guide screenshots so shared styling changes can be checked against regressions.
- Identify unused or obsolete CSS selectors using static search and browser inspection.

### Phase 2: CSS Organisation and Design Tokens

- Reorganise `assets/styles.css` into documented sections without changing visual output where practical.
- Add a small token section for colours, spacing, radii, typography scale, borders, and shadows.
- Keep existing class names and component IDs.
- Remove or archive obsolete commented debug/WIP blocks after confirming they are not needed.
- Normalise comments so they describe current intent rather than past debugging.

### Phase 3: Shared Analysis-Style Page Shell

- Consolidate shared page-shell spacing, section headers, lead paragraphs, control rows, map/chart wrappers, and filter button states.
- Keep layout modules and callbacks stable.
- Prefer CSS changes over Python layout changes unless a layout assumption blocks responsive behaviour.
- Preserve Guide-specific styling unless a shared selector currently affects it.

### Phase 4: Analysis Page Modernisation

- Create a calmer editorial rhythm for the intro and distribution sections.
- Make section dividers and descriptions consistent.
- Reduce visual busyness in the Michelin rating explainer.
- Standardise graph/map container treatment.
- Improve ranking empty state, controls, and result spacing.
- Verify that arrondissement reveal/hide behaviour still reads correctly.

### Phase 5: Economics Page Modernisation

- Wait until the Analysis responsive/media-query pattern is consolidated.
- Make the lead explanation visually credible and concise.
- Unify dropdown and filter styling with the Analysis page.
- Replace blue selected-value styling with a restrained system accent.
- Improve weighted-mean note styling.
- Review map/chart stacking and height behaviour across tablet and mobile.

### Phase 6: Wine Page Modernisation

- Wait until the Analysis responsive/media-query pattern is consolidated.
- Establish a refined palette and atmospheric but quiet typography treatment.
- Improve the map and generated summary panel relationship.
- Style the OpenAI/generated-content disclosure as a subtle trust note.
- Review the overlay controls and hidden star filter state.
- Remove the obsolete commented Wine WIP CSS block once its useful ideas have been captured or rejected.

### Phase 7: Responsive Consolidation

- Treat this as the next implementation step before extending the Analysis pattern to Wine and Economics.
- Consolidate breakpoints into a small documented set.
- Add mobile-first or clearly layered rules for Analysis/Economics/Wine.
- Stack graph/map and map/summary pairs gracefully on smaller viewports.
- Verify dropdown menus, filter rows, the fixed header, and the normal-flow footer.
- Avoid viewport-width font scaling; use stable type sizes and line heights.

### Phase 8: Browser and Visual QA

- Run the existing smoke tests if any Python, callback, route, or layout code changes.
- Use browser screenshots for `/analysis`, `/economics`, `/wine`, and a Guide regression check.
- Test desktop, tablet, and mobile widths.
- Check first load, route navigation, dropdown open states, filter active/inactive states, map/chart rendering, Wine generated-content loading/error states, and 404 shell.
- Compare screenshots against the pre-change baseline.

### Phase 9: Deployment Checklist

- Confirm `python -m pytest` passes if code was touched.
- Confirm no component IDs, routes, callback signatures, dependencies, or deployment files changed unless explicitly intended.
- Confirm `assets/styles.css` changes are scoped and documented.
- Confirm direct route loads after deployment:
  - `/`
  - `/home`
  - `/analysis`
  - `/economics`
  - `/wine`
  - `/missing`
- Confirm Heroku still starts through `gunicorn michelin_app:server`.
- Confirm no untracked scratch files, generated bytecode, or accidental data files are staged.

## Non-Goals

- Do not redesign or reorganise the Guide page without a specific issue.
- Do not change routes.
- Do not change callbacks.
- Do not change component IDs.
- Do not change data loading.
- Do not change dependencies.
- Do not move packages or modules.
- Do not alter deployment configuration.
- Do not mix data/model/service rewrites with visual modernisation.
- Do not introduce a new frontend framework.

## Risks/Gotchas

- Many callbacks return inline styles to hide/show sections and graphs; styling changes must not fight those returned styles.
- Dynamic star-filter classes are used across Analysis, Department, Arrondissement, Demographics, and Wine.
- Some page controls are hidden until callbacks reveal them; QA must cover hidden and visible states.
- `assets/scroll-script.js` scrolls nav clicks to `analysis-content-top`, `demographics-content-top`, and `wine-content-top`.
- Dropdown selectors use Dash/React-Select class names such as `.Select-value`; test after changing selected-value styling.
- The header remains fixed; the footer should stay in normal document flow and must not overlay content.
- Wine click handling remains curve-number based; visual changes should not change trace ordering or callback assumptions.
- Plotly figures have their own colours and layout defaults in Python helpers; page CSS alone will not fully modernise chart styling.
- `assets/basicTileMap.json` contains an embedded tile-service key; do not treat it as incidental styling.
- `assets/data/wine_regions_simplified.geojson` is currently untracked and should remain untouched unless explicitly requested.

## Validation Checklist

For documentation-only work:

- Confirm Markdown files are readable.
- Confirm no Python, CSS, callback, route, dependency, or deployment files changed.
- No smoke tests are required if only documentation changed.

For styling/content PRs:

- Run `python -m pytest` if any Python code changes.
- Capture before/after screenshots for `/analysis`, `/economics`, `/wine`, and `/`.
- Verify desktop, tablet, and mobile layouts.
- Verify dropdown open/selected states.
- Verify star filter active/inactive states.
- Verify Wine generated-summary loading, cached, missing-key, and request-limit states where practical.
- Confirm direct route refresh works for every public route.
