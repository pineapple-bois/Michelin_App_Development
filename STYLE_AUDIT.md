# Style Audit: Editorial Pages

## Scope

This audit reflects the current styling direction after the Analysis, Wine, and Economics editorial passes. It is a documentation snapshot for the next phase: shared class, wrapper, and responsive/media-query consolidation.

Primary files inspected:

- `assets/styles.css`
- `app/layouts/analysis.py`
- `app/layouts/economics.py`
- `app/layouts/wine.py`
- `app/layouts/analysis_shared.py`
- `app/utils/restaurant_cards.py`

This audit does not request app-code changes by itself. Keep callbacks, component IDs, routes, data loading, dependencies, and Plotly behavior stable unless a later task explicitly covers them.

## Current Design Language

The active direction is a mature editorial/report style:

- White paper sheet with very pale grey gutters.
- Internal indentation so content never touches the sheet edge.
- Plain, direct copy.
- Quiet outline/accent controls.
- Filled colour is acceptable for data visualizations, not for broad control slabs.
- Michelin red is reserved for Michelin objects, rating controls, links, and reference accents.
- Economic indicators use restrained slate/blue-grey rather than default bright blue or Michelin red.
- Footer remains in normal document flow, not fixed over content.

Avoid:

- Cream, yellow, parchment, or stained-paper backgrounds.
- Rounded dashboard cards.
- Generic SaaS-style chart cards.
- Drop shadows as hierarchy.
- Tinted evidence panels.
- Page-specific colour noise that competes with the maps and charts.

## Current Implementation Summary

`assets/styles.css` is now a 3,000+ line stylesheet with foundation tokens, global/header/Guide rules, Analysis-style page rules, Economics rules, Wine rules, several responsive blocks, and a deprecated commented Wine block at the end.

The design language is shared visually, but not yet fully shared structurally:

- `app/layouts/analysis_shared.py` provides the common `content-container`, `analysis-container`, header, footer, and dynamic star-filter helpers.
- Analysis uses `#analysis-content-top` as the main page-scoped styling anchor.
- Economics uses `#demographics-content-top` inside `.analysis-container`, with page-frame styling applied through `:has(...)`.
- Wine uses `#wine-content-top` inside `.analysis-container`, with page-frame styling applied through `:has(...)`.
- Many repeated behaviors are still implemented through page-specific selectors rather than shared primitive classes.

Treat this as a consolidation opportunity, not as a reason to rewrite the stylesheet wholesale.

## Current Page State

### Analysis

Current decisions:

- Starts directly with "Restaurant Distributions Across France."
- No Michelin history/rating-system preamble.
- Uses the white sheet, pale grey gutters, internal indentation, and max-width page frame.
- Uses open chart/map evidence areas, not chart cards.
- Uses outline/accent rating filters.
- Uses recognisable but controlled rating colours.
- Restaurant cards carry Guide-page identity in a denser Analysis form.

Implementation notes:

- Primary styling is anchored under `#analysis-content-top`.
- Section families remain page-specific: `region-*`, `department-*`, `arrondissement-*`, and `ranking-*`.
- Chart/map pairs still rely partly on layout-level inline width/display styles.
- Restaurant card markup comes from `app/utils/restaurant_cards.py`; Analysis-specific card styling is scoped under `#analysis-content-top`.

### Wine

Current decisions:

- Wine is map-led; the map should dominate desktop space.
- The region information panel, generated summary, and disclaimer support the map rather than competing with it.
- Wine rating buttons use the same rating colour language as Analysis.
- White sheet, pale gutters, internal indentation, and no dashboard-card treatment apply here too.

Implementation notes:

- Primary styling is anchored through `.content-container:has(#wine-content-top)` and `.analysis-container:has(#wine-content-top)`.
- The active wrapper classes are `wine-container`, `wine-restaurants-controls`, `wine-content-wrapper`, `wine-map`, and `wine-llm-output`.
- The layout still contains inline width/display and graph-height styles that CSS overrides or works around.
- The callback maps Plotly curve numbers back to wine regions. Styling work must not change trace ordering or click behavior.

### Economics

Current decisions:

- Economics follows the Analysis page frame.
- The page uses a civic/statistical colour language for regional indicators.
- Metric choropleth and bar fills use a restrained slate/blue-grey palette.
- Michelin red remains appropriate for links, Michelin/rating controls, and the mean/reference line.
- Economics dropdown selected/hover states should stay slate/neutral rather than red or pink.

Implementation notes:

- Primary styling is anchored through `.content-container:has(#demographics-content-top)` and `.analysis-container:has(#demographics-content-top)`.
- Page-specific classes include `demographics-container`, `demographics-filter-container`, `demographics-restaurants-controls`, `demographics-content-wrapper`, `demographics-map`, and `demographics-chart-mean`.
- The Economics layout still contains inline width/display styles for the map/chart split and inline hidden/width behavior around star filters.
- Plotly palette decisions live in `app/utils/economics_figures.py`; do not assume CSS tokens control the figure colours.

## Styling System Findings

### Tokens

The stylesheet now has foundation tokens for brand red, neutrals, borders, control surfaces, focus rings, rating colours, Analysis page sheet values, and active-control shadow. These tokens are useful, but they are not yet a complete design system.

Watchouts:

- Rating colours are shared through CSS tokens for control styling.
- Economics figure colours are defined in Python, not CSS.
- Page-frame tokens are named with `analysis-*` even though the same sheet pattern is now used by Analysis, Economics, and Wine. Rename only in a dedicated consolidation task.

### Shared and Page-Specific Selectors

Actually shared today:

- `.main-layout`
- `.header`
- `.content-container`
- `.analysis-container`
- `.button-show-details`
- dynamic star-filter classes from `analysis_shared.py`, such as `.star-button-analysis`, `.star-button-demographics`, and `.star-button-wine`
- Michelin icon classes such as `.michelin-star`, `.bib-image`, and related inverted variants

Page-scoped today:

- Analysis: `#analysis-content-top`, `region-*`, `department-*`, `arrondissement-*`, `ranking-*`.
- Economics: `#demographics-content-top`, `demographics-*`, `dropdown-category-demographics-*`.
- Wine: `#wine-content-top`, `wine-*`, `dropdown-granularity-wine`.

Candidate shared primitives should be introduced carefully; do not claim these page-scoped classes are already shared.

### Dropdown and React Select Styling

Dropdown styling remains cascade-sensitive because Dash/React Select generates classes such as:

- `.Select-control`
- `.Select-value`
- `.Select-value-label`
- `.Select-value-icon`
- `.Select-option`
- `.VirtualizedSelectFocusedOption`
- `.VirtualizedSelectSelectedOption`

Current direction:

- Analysis dropdown chips are quiet metadata tags.
- Economics metric/dropdown selected states are slate/neutral.
- Wine dropdown controls use the restrained outline language.

Risk: broad `.analysis-container .Select-*` rules can unintentionally affect all three editorial pages. Keep page-specific overrides until a shared select primitive is tested across open, hover, selected, multi-chip, clear, and keyboard-focus states.

### Footer

The footer should remain in normal document flow. Do not restore fixed or floating footer positioning. If gaps appear on Guide or other pages, fix the page-height/layout cause rather than making the footer overlay content again.

## Intended Shared Primitives to Investigate

These are candidates for future consolidation. Some exist only as repeated visual behavior today, not as shared classes.

- Page sheet / page frame: white sheet, pale gutters, internal padding, max width.
- Page intro / title block: compact title and short explanatory copy.
- Section block: major section spacing and optional fine rule treatment.
- Control row: label scale, compact spacing, wrapping behavior.
- Dropdown/select styling: neutral outline, metadata chips, selected/hover/focus states.
- Rating filter buttons: outline/accent buttons with rating-specific icon/accent colours.
- Evidence area / map-chart pairing: open chart/map placement without cards or shadows.
- Map-led layout: Wine-style map-dominant split with secondary support panel.
- Restaurant card / guide-entry card: compact Guide-related entries for Analysis ranking output.
- Notes and disclaimers: weighted-mean explanation, generated-content disclaimer, placeholder/default notes.
- Normal-flow footer: shared footer placement without fixed positioning.

Consolidation should begin by mapping current selectors to these primitives, then moving one primitive at a time.

## Responsive and Media-Query Findings

Active responsive rules are no longer limited to the old 1400px and 1250px breakpoints. The stylesheet now includes a mix of:

- `max-width: 1400px`
- `max-width: 1250px`
- `max-width: 1200px`
- `max-width: 1050px`
- `max-width: 900px`
- `max-width: 600px`

Current risks:

- Duplicated breakpoint intent across 1250px and 1200px rules.
- Wine has a 1050px stacking breakpoint while Analysis/Economics use 900px for major stacking.
- Sheet gutter and padding variables are updated in several responsive blocks.
- Chart/map pairs can be constrained by inline widths and Plotly figure layout.
- Dropdowns and multi-value chips can overflow if the sheet padding and control widths are too tight.
- Rating button rows need to wrap or stay fixed depending on page context.
- Restaurant card grids need predictable collapse from multi-column to one column.
- Header fixed positioning and footer normal-flow spacing need to be checked together on small screens.
- Plotly graph heights and colourbar/title space can require Python figure changes rather than CSS-only fixes.

The next responsive pass should reduce duplicated page-specific rules only where the behavior is genuinely shared.

## Still-Valid Gotchas

- Cascade risk is high in `assets/styles.css`; prefer scoped edits and final diff review.
- Dash/React Select classes can change visual states beyond the selector that was edited.
- `:has(...)` is currently part of the page-frame strategy. Test browser support and scope before relying on it more broadly.
- Inline Dash `style={...}` props still define widths, display behavior, hidden states, and graph heights in the target layouts.
- Callback-returned styles may override CSS for visibility and sizing.
- Plotly figures have layout, colour, colourbar, and map constraints in Python helpers.
- Wine map click handling is curve-number based and fragile if trace ordering changes.
- The final commented Wine block is deprecated/pending review; do not revive it incidentally.
- Guide is not the styling target, but shared header/footer/control selectors can still affect it.

## High-Value Next Steps

- Inventory actual class usage across `assets/styles.css`, the three target layouts, shared helpers, callbacks that return styles, and restaurant-card output.
- Decide which page-frame selectors can become shared without widening scope to Guide.
- Create or document shared primitive classes one at a time.
- Consolidate responsive breakpoints around observed behavior, not a theoretical system.
- Move repeated control-row and rating-filter behavior only after checking Analysis, Economics, and Wine active/hidden states.
- Document any responsive problems that require layout or Plotly figure changes rather than forcing brittle CSS.

## Changes That Should Wait

- Broad CSS reordering.
- Splitting `assets/styles.css`.
- Renaming many classes at once.
- Removing inline layout styles without visual coverage.
- Changing callbacks or component IDs.
- Changing routes, data loading, dependencies, or deployment config.
- Changing Wine map trace ordering or click behavior.
- Redesigning Guide.
- Reintroducing the Analysis preamble or rating explainer.

## Validation for Consolidation PRs

- Run `git diff --check`.
- Run `python -m pytest` if Python or layout code changes.
- Start the app when practical and inspect `/analysis`, `/economics`, and `/wine`.
- Check `/`, `/home`, `/guide` if available, and `/missing` when shared shell/header/footer selectors change.
- Inspect desktop, laptop, tablet, and phone widths.
- Check for horizontal scroll, sheet padding, dropdown/chip overflow, chart/map stacking, Wine map dominance, restaurant card collapse, footer placement, and React Select hover/selected/focus states.
