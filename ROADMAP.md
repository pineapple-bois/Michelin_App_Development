# Michelin App Styling Roadmap

## Current Baseline

The Dash Pages multipage app is the stable architecture baseline. The initial page-specific styling phase for Analysis, Wine, and Economics is substantially complete: all three pages now point toward the same mature editorial/report language, while Guide remains outside the redesign scope unless shared styling creates a specific regression.

Current implementation is still mostly page-scoped. The visual direction is shared, but many wrappers and selectors remain specific to Analysis, Economics, or Wine. The next major work is therefore not another page-by-page visual pass; it is a careful shared-class and responsive/media-query consolidation phase.

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

## Next Phase: Shared Class and Responsive Consolidation

Goal: identify common page primitives, reduce duplicated page-specific responsive CSS, and make future Analysis/Wine/Economics changes safer.

This phase should be incremental. Do not rename classes broadly, move callbacks, or reorganise layouts in one large sweep. Prefer one primitive at a time, with before/after visual checks on all affected pages.

Candidate primitives to investigate:

- page sheet / page frame
- page intro / title block
- section block
- control row
- dropdown/select styling
- rating filter buttons
- evidence area / map-chart pairing
- map-led layout
- restaurant card / guide-entry card
- notes and disclaimers
- normal-flow footer

These are candidates for consolidation, not a claim that shared classes already exist for each primitive.

## Proposed Work Phases

### Phase 1: Current Selector Inventory

- Audit active class names in `assets/styles.css` and the Analysis, Wine, and Economics layouts.
- Identify which visual decisions are already shared by class and which are only repeated through page-specific selectors.
- Record inline Dash `style={...}` values that constrain widths, heights, hidden states, or responsive behavior.
- Keep component IDs, routes, callback signatures, Plotly figure logic, and data loading unchanged.

### Phase 2: Shared Primitive Plan

- Choose a small shared naming scheme for editorial page primitives.
- Map existing page-specific selectors to the proposed primitives before changing markup.
- Decide where CSS-only grouping is enough and where a minimal layout class addition would reduce risk.
- Keep Guide-specific styling separate unless a shared selector already affects it.

### Phase 3: Responsive and Media-Query Consolidation

- Consolidate toward a small documented breakpoint system while preserving current desktop appearance.
- Reduce duplicated Analysis/Economics/Wine responsive rules where the layout behavior is the same.
- Preserve the white sheet, pale gutters, and internal padding at laptop, tablet, and phone widths.
- Ensure chart/map pairs, Wine map/details, dropdowns, chips, rating filters, and restaurant card grids stack cleanly.
- Avoid viewport-width font scaling and avoid brittle Plotly CSS overrides.

### Phase 4: Browser and Visual QA

- Check `/analysis`, `/economics`, and `/wine` at desktop, laptop, tablet, and phone widths.
- Check `/`, `/home`, `/guide` if available, and `/missing` for shared header/footer or shell regressions.
- Verify dropdown open/selected states, rating filter active/inactive states, map/chart rendering, Wine map clicks, and footer placement.
- Use screenshots for visual comparison whenever practical.

### Phase 5: Deployment Checklist

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
