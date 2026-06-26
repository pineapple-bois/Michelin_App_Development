# Michelin App Styling Roadmap

## Current Baseline

The Dash Pages multipage app is the stable architecture baseline. The initial page-specific styling phase for Analysis, Wine, and Economics is substantially complete: all three pages now point toward the same mature editorial/report language, while Guide remains outside the redesign scope unless shared styling creates a specific regression.

Current implementation now includes shared editorial page-frame hooks, control hooks, evidence/layout hooks, shared responsive rules, corrected header/banner scaling, shared editorial page title scaling, and shared rating filter treatment. The next major work is not another visual styling pass; it is CSS stabilisation and selective cleanup so the new shared hooks can safely replace duplicated page-specific CSS over time.

For detailed selector findings and responsive risks, see `STYLE_AUDIT.md`.

## Locked Design Direction

- Use a mature editorial/report style, not a dashboard or card-grid UI.
- Use a white paper sheet with very pale grey gutters.
- Keep internal indentation so content never touches the sheet edge.
- Keep copy plain, direct, and functional.
- Avoid cream, yellow, beige, parchment, or stained-paper backgrounds.
- Avoid rounded dashboard cards, generic SaaS-style chart cards, tinted evidence panels, and drop shadows as hierarchy.
- Use quiet outline/accent controls.
- Allow data visualizations to use filled colour when the data needs it.
- Reserve Michelin red for Michelin objects, rating controls, links, and reference accents.
- Use restrained slate/blue-grey for economic indicators, not default bright blue and not Michelin red.
- Keep the footer in normal document flow, not fixed over content.

## Current Page Decisions

### Analysis

- Analysis begins directly with "Restaurant Distributions Across France."
- The Michelin history/rating-system preamble has been removed and should not return without an explicit content decision.
- The page uses a white sheet, pale grey gutters, internal indentation, and a centered max-width content area.
- Controls use outline/accent styling; rating filters should remain quieter than charts and maps.
- Rating colours should remain recognisable but controlled: neither garish nor muddy.
- Restaurant cards should keep Guide-page identity in a denser Analysis form.
- Avoid analyst-speak such as "patterns," "clusters," "insights," "recognition," and "geography level" in new Analysis copy.

### Wine

- Wine is map-led: the map is the primary content and should dominate the available desktop space.
- Region details, generated summary text, and disclaimers are secondary support for the map.
- Wine rating controls use the same rating colour language as Analysis.
- Do not change wine map trace ordering or click behavior during styling work.

### Economics

- Economics follows the Analysis page frame: white sheet, pale grey gutters, and internal indentation.
- The page purpose is technical comparison: choose a regional indicator and compare selected regions.
- Economic map and bar chart colours use a restrained slate/blue-grey statistical palette.
- Michelin red remains appropriate for Michelin objects, links, rating controls, and the reference/mean line.
- Economics dropdown selected and hover states should stay slate/neutral, not red or pink.

## Next Phase: CSS Stabilisation and Selective Cleanup

### Purpose

- Stabilise `assets/styles.css` after the editorial redesign and responsive/typography passes.
- Use the shared hooks now available to reduce duplicated Analysis, Economics, and Wine CSS:
  - `editorial-page-frame`, `editorial-sheet`, `editorial-page`, `editorial-page-title`, `editorial-page-description`, `editorial-section`
  - `editorial-control-row`, `editorial-control-group`, `editorial-control-label`, `editorial-select`, `editorial-chip-select`, `editorial-action-button`, `editorial-rating-filters`, `editorial-rating-button`
  - `editorial-evidence`, `editorial-evidence--split`, `editorial-evidence--map-led`, `editorial-chart`, `editorial-map`, `editorial-info-panel`, `editorial-note`, `editorial-card-grid`, `editorial-guide-entry`
- Avoid broad rewrites, large selector moves, and speculative deletion.
- Preserve the current Analysis, Economics, and Wine visuals.
- Treat each cleanup PR as audit-first: identify redundant or conflicting rules before removing them.

### Breakpoint Cleanup

- Audit every `@media` block in `assets/styles.css`.
- Group breakpoints by purpose:
  - global/header
  - editorial page frame
  - Analysis
  - Economics
  - Wine
  - Guide/Home/other
- Identify duplicate or near-duplicate rules, especially around sheet padding, control wrapping, stacked evidence layouts, and mobile title handling.
- Identify old breakpoints that may now be superseded by the shared responsive system around `1366`, `1024`, `768`, `600`, and `480` pixels.
- Keep `1366px` and `1024px` as proper desktop/tablet layouts, not compressed mobile layouts.
- Treat phones as minimal support: readable text, no horizontal overflow, no edge collisions.

### Typography Cleanup

- Audit rules affecting:
  - global app title/header title
  - editorial page titles
  - section headings
  - page descriptions
  - control labels
- Identify rules that fight `.editorial-page-frame .editorial-page-title`.
- Identify page-specific mobile overrides that may reintroduce old title sizes.
- Keep the corrected header/banner scaling and shared editorial page-title scale as the current baseline.
- Remove typography overrides only when visual QA confirms the shared rule already covers the page.

### Rating Filter Cleanup

- Audit selectors affecting rating buttons across Analysis, Economics, and Wine.
- Decide which shared base styles can move under `.editorial-rating-button`.
- Preserve page-specific layout differences where needed:
  - Analysis rating layout and stacked wrapping
  - Economics overlay/rating layout
  - Wine fixed-size horizontal layout on desktop
- Preserve rating colour semantics:
  - Bib Gourmand: deep wine/purple
  - 1 Star: warm gold
  - 2 Stars: coral/salmon
  - 3 Stars: controlled Michelin red
- Keep outline/accent controls. Do not return to filled colour slabs or active shadows.
- Be careful with callback-generated button class names and inline styles from `analysis_shared.py` and `app/utils/star_filters.py`.

### Page Frame and Sheet Cleanup

- Identify duplicate page-frame, sheet, gutter, padding, and max-width rules now covered by `.editorial-page-frame` and `.editorial-sheet`.
- Keep `:has(...)` scoping until there is a clearly safe replacement.
- Do not remove scoping that protects Guide/Home from editorial page rules.
- Do not rename `analysis-*` page-frame tokens until a dedicated token cleanup task covers naming and migration.

### Evidence and Layout Cleanup

- Audit page-specific chart/map/map-led responsive rules now potentially covered by:
  - `.editorial-evidence`
  - `.editorial-evidence--split`
  - `.editorial-evidence--map-led`
  - `.editorial-chart`
  - `.editorial-map`
  - `.editorial-info-panel`
- Identify what can be consolidated and what should remain page-specific.
- Keep Wine map-led behavior distinct from Analysis/Economics split evidence.
- Do not force CSS-only fixes where Plotly sizing, colourbars, or inline Dash styles require a separate layout or figure decision.

### Risk Notes

Cleanup can break:

- Dash/React Select generated classes and their hover, selected, chip, and focus states.
- Callback-generated star buttons and active/inactive class/style returns.
- Wine map click behavior and trace ordering.
- Plotly sizing, map heights, colourbars, and SVG/canvas layout.
- Guide/Home shared cards, header, footer, and normal-flow page height.

### Proposed Cleanup Order

- PR A: remove only clearly superseded typography overrides after checking Analysis, Economics, Wine, Guide/Home, and missing route shells.
- PR B: consolidate rating button base styles under `.editorial-rating-button`, keeping page-specific layout and rating-colour overrides.
- PR C: remove duplicate sheet/page-frame rules where shared hooks safely cover them and `:has(...)` scoping still protects Guide/Home.
- PR D: consolidate evidence responsive rules for split and map-led layouts while preserving Wine map dominance.
- PR E: simplify media queries and remove dead/commented CSS only after visual QA confirms no regressions.

## Ongoing Validation and Deployment Checklist

- Run `python -m pytest` if any Python, callback, route, or layout code changes.
- Run `git diff --check`.
- Confirm no dependencies, deployment config, data files, or callback contracts changed.
- Confirm direct route loads after deployment:
  - `/`
  - `/home`
  - `/analysis`
  - `/economics`
  - `/wine`
  - `/missing`
- Confirm Heroku still starts through `gunicorn michelin_app:server`.
- Confirm no generated bytecode, scratch files, or unrelated data files are staged.

## Non-Goals

- Do not start a new visual redesign of Analysis, Economics, or Wine.
- Do not redesign the Guide page without a specific shared-style regression.
- Do not change callbacks, component IDs, routes, data loading, dependencies, or deployment configuration.
- Do not change Plotly trace ordering or Wine map click behavior.
- Do not split `assets/styles.css` during the responsive consolidation phase unless that becomes a dedicated task.
- Do not remove inline layout styles until the affected behavior is covered by visual QA.

## Risks and Gotchas

- Dash/React Select generated classes are cascade-sensitive; hover, selected, chip, and focus states need browser checks.
- Current editorial framing relies on page-scoped selectors and `:has(...)`; consolidating classes should not accidentally widen scope to Guide.
- Several layout modules still contain inline widths, heights, and hidden states that may override CSS intent.
- Callback-returned styles also control visibility and graph dimensions.
- Plotly figure layout, colourbars, map heights, and SVG/canvas sizing cannot always be solved safely with CSS alone.
- Wine click handling remains curve-number based and is fragile around trace ordering.
- The header is fixed; the footer should remain normal-flow and must not overlay content.
- `assets/data/wine_regions_simplified.geojson` is currently untracked and should remain untouched unless explicitly requested.

## Validation Checklist

For documentation-only work:

- Confirm Markdown files are readable.
- Confirm no app code changed.

For shared-class or responsive work:

- Run `git diff --check`.
- Run the existing test suite when Python or layout code changes.
- Start the app when practical and inspect affected routes.
- Check for horizontal scrolling, sheet padding, dropdown overflow, stacked chart/map pairs, restaurant card collapse, footer position, and Guide regressions.
