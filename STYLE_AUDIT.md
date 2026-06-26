# Styling Audit: Analysis, Economics, and Wine

## Scope

This audit is a documentation snapshot for the next styling phase. It does not prescribe code changes to make immediately, and it intentionally avoids changing layouts, callbacks, routes, component IDs, or dependencies.

Primary files inspected:

- `assets/styles.css`
- `assets/scroll-script.js`
- `app/layouts/analysis.py`
- `app/layouts/economics.py`
- `app/layouts/wine.py`
- `app/layouts/analysis_shared.py`
- `app/components/shared.py`
- `app/pages/analysis.py`
- `app/pages/economics.py`
- `app/pages/wine.py`
- `app/callbacks/navigation.py`

## Current CSS Organisation

`assets/styles.css` has 1,993 lines. The active sections are broadly ordered as:

- global styles
- header/nav
- Guide city search and footer
- Guide map/sidebar, restaurant details, and star filters
- Analysis page shell and sections
- Analysis dropdown and star-button styles
- ranking section
- Economics/Demographics section
- Wine section
- responsive styles
- large commented Wine work-in-progress block

The file is not random, but it is also not yet a styling system. It mostly grew around page sections and feature work. The next cleanup should preserve behaviour while grouping shared rules, design tokens, page-specific rules, and responsive overrides more deliberately.

## Repeated Values and Patterns

### Colours

Active and commented colour usage includes:

- Michelin red: `#C2282D`
- darker red hover: `#A01F25`
- Bootstrap/link blue: `#007bff`, `#0056b3`
- neutral greys: `#ddd`, `#ccc`, `#555`, `#666`, `#f0f0f0`, `#f5f5f5`, `#f7f7f7`, `#f8f8f8`
- Michelin selected grey: `#808080`
- many commented pastel/debug colours: `#fdf5e6`, `#d9edf7`, `#c8e6c9`, `#ffebee`, `#d9f7be`, `#ffe4e1`, `#cce5ff`

The pastel/debug palette appears mostly in comments, but it still signals the old mental model and makes the stylesheet feel less mature. The active Economics selected dropdown styling uses blue and is the clearest live colour conflict with the Michelin-led palette.

### Spacing

Common values repeat across pages:

- side gutters: `50px`, reduced to `30px` at the `1250px` breakpoint
- section gaps: `20px`, `30px`, `40px`
- control gaps: `20px`, `40px`
- button padding: `5px`, `10px 20px`

These should become named spacing conventions or at least documented CSS variables before visual redesign begins.

### Typography

Current type scale is informal:

- header title: `60px`, then `50px`
- section/page headers: `25px`
- subsection headers: `20px`
- lead/description text: `18px`, reduced to `16px` at tablet width
- controls: `16px`
- footer/disclaimer text: `9px`, `10px`, `12px`

There is no dedicated editorial hierarchy for page title, section title, lead copy, control labels, chart notes, and empty states.

### Borders, Shadows, Radii

- Borders are mostly `1px solid #ddd`, `1px solid black`, or `1px solid #ccc`.
- Active star controls use `box-shadow: 0 0 5px 2px rgba(0, 0, 0, 0.2)`.
- Header dropdown uses `box-shadow: 0 4px 8px rgba(0,0,0,0.1)`.
- Radii are usually `5px` or `8px`.

The black section rules and heavy active-control shadow are likely contributors to a less refined visual feel.

## Shared Class Groups

These are broadly shared or structural:

- `.main-layout`
- `.header`
- `.header-container`
- `.title-section`
- `.year-text`
- `.hamburger-menu`
- `.nav-dropdown`
- `.nav-link`
- `.footer-main`
- `.info-container`
- `.content-container`
- `.analysis-container`
- `.button-show-details`
- `.michelin-star`, `.bib-image`, `.green-star`
- `.star-button-*`
- `.star-filter-section-*`
- `.star-filter-buttons-*`

These should be treated carefully because changes may affect more than one page.

## Page-Specific Class Groups

### Guide

Mostly uses:

- `.main-content`
- `.map-sidebar-container`
- `.map-section`
- `.sidebar-container`
- `.city-match-*`
- `.dropdowns-container-main`
- `.star-filter-section`
- `.restaurant-details-container`
- `.star-ratings-container-main`

The Guide page is not the target of the next redesign except for shared regressions.

### Analysis

Mostly uses:

- `.michelin-text-container`
- `.distribution-header`
- `.distribution-section-header`
- `.region-*`
- `.department-*`
- `.arrondissement-*`
- `.ranking-*`
- `.dropdown-region-analysis`
- `.dropdown-department-analysis`
- `.dropdown-arrondissement-analysis`
- `.dropdown-granularity`
- `.dropdown-ranking`
- `.dropdown-star-ranking`

The repeated region/department/arrondissement class families are candidates for shared section/control/visual wrapper rules.

### Economics

Mostly uses:

- `.demographics-container`
- `.demographics-text-container`
- `.demographics-header`
- `.demographics-filter-container`
- `.demographics-dropdown-container`
- `.dropdown-category-demographics-selector`
- `.dropdown-granularity-demographics`
- `.dropdown-category-demographics`
- `.demographics-restaurants-controls`
- `.demographics-content-wrapper`
- `.weighted-mean-explanation`

Only `.dropdown-category-demographics` has detailed selected-value styling. `.dropdown-category-demographics-selector` and `.dropdown-granularity-demographics` appear in layout code but have no obvious dedicated CSS rules.

### Wine

Mostly uses:

- `.wine-container`
- `.wine-text-container`
- `.wine-header`
- `.wine-text-paragraph`
- `.wine-tagline-paragraph`
- `.wine-restaurants-controls`
- `.wine-map-outlines`
- `.dropdown-granularity-wine`
- `.wine-content-wrapper`
- `.wine-map`
- `.wine-llm-output`
- `.wine-llm-text`
- `.wine-title`
- `.region-name-placeholder`
- `.LLM-output`
- `.disclaimer-content`
- `.openai-logo`
- `.disclaimer-text-ai`

`.wine-map-outlines` has a CSS rule, but `.dropdown-granularity-wine`, `.wine-map`, and `.wine-llm-text` have no obvious active dedicated CSS rules beyond surrounding wrappers and inline layout styles.

## Obsolete, Unused, or Questionable Selectors

Candidates to verify in browser/static inspection before deleting:

- `.dropdown-container` and `.ratings-container` appear in CSS but are not obvious in current target layout code.
- `.dropdowns-container` appears as CSS but does not obviously match current Analysis ranking markup.
- `.star-button-cuisine` and `.star-filter-section-cuisine` are included in shared star-button CSS groups but do not appear in current layout code.
- `.header-button` appears in the 404 layout but has no obvious CSS rule.
- `.footer-inline` appears in shared footer markup but has no obvious CSS rule.
- `.restaurant-cards-container` appears in ranking utility output but has no obvious CSS rule.
- `.default-message`, `.match-details`, `.city-match-container`, and `.no-match-message` appear in Guide callback output but have no obvious CSS rule.
- `.restaurant-cuisine`, `.restaurant-price`, `.restaurant-address`, `.details-address`, `.details-location`, and `.details-website` appear in card markup but are mostly styled through parent/detail classes.
- The final commented Wine WIP block duplicates active Wine selectors and should be removed or converted into intentional rules during cleanup.

Do not delete these solely from static search; some may be generated only after callback interactions.

## Conflicts and Inconsistencies

- `.container-style` is defined twice.
- `.dropdown-style` is defined twice.
- `.region-filter-title` is defined twice.
- Guide and Analysis-style star filters use separate helper functions and overlapping concepts.
- Layout files use inline `style` props for key dimensions, including 50/50 graph/map splits, hidden star filters, and Wine graph height.
- Callback-returned styles also control visibility and graph dimensions, especially in Analysis, Economics, and Wine.
- Analysis selected dropdown values use red; Economics selected dropdown values use blue.
- Page sections use a mixture of `width: calc(100% - 50px)`, `padding-right: 50px`, and container-level padding.
- Some layout comments still explain implementation history rather than current design intent.

## Media Query Findings

Active breakpoints:

- `max-width: 1400px`: header height/title size, body padding, Analysis top margin, Guide description and restaurant title sizes.
- `max-width: 1250px`: Guide layout stacks sidebar above map, adjusts gutters, dropdown wrapping, Guide details/filter row, and reduces Analysis/Economics/Wine paragraph sizes.

No active smaller mobile breakpoint was found. The current `1250px` breakpoint is more tablet/medium-screen focused than mobile-focused.

Responsive risks:

- Analysis graph/map pairs stay side-by-side unless Plotly or callback styles override them.
- Economics map/chart is fixed at `height: 750px` and side-by-side.
- Wine graph is inline `height: 700px` and paired side-by-side with the generated summary.
- Control rows use fixed assumptions such as `width: 50%`, `width: 30%`, and `width: 20%`.
- Fixed header/footer with content `calc(...)` heights should be tested on mobile browser chrome.

## Visual Inconsistency by Page

### Analysis

Analysis is now the pilot for the mature editorial data-report style.

Established decisions:

- Use a white paper sheet with very pale grey gutters, internal indentation, and a centered max-width content area.
- Do not use cream/yellow paper tones, dashboard cards, shadows, rounded chart boxes, or tinted evidence containers.
- Begin directly with “Restaurant Distributions Across France”; the Michelin preamble and rating-system explainer are removed.
- Keep copy plain and direct. Avoid “patterns,” “clusters,” “insights,” “recognition,” and “geography level.”
- Controls use outline/accent styling; data visualizations may use filled colour.
- Rating colours should be recognisable but controlled, neither garish nor muddy.
- Restaurant cards should carry Guide-page identity in a denser Analysis form.
- The footer should remain in normal document flow, not fixed over content.

Remaining audit concern: responsive and media-query behaviour for the Analysis pattern should be consolidated before carrying the pattern to Economics and Wine.

### Economics

- Blue dropdown selected-state styling competes with the Michelin palette.
- The metric explanation deserves a quieter, more credible note style.
- The control area has several equally weighted elements, which weakens hierarchy.
- Fixed height and split layout need responsive review.

### Wine

- Copy has a refined tone, but the controls and generated-summary panel are still plain.
- Inline 50/50 layout and fixed map height may not produce a polished responsive experience.
- The OpenAI disclaimer is useful but visually utilitarian.
- The large commented WIP block makes it harder to see the intended current Wine styling.

## Likely Causes of the Too-Colourful or Childish Feel

- Michelin rating buttons use saturated fills as the primary filter affordance.
- Blue Economics dropdown styling introduces a second strong accent system.
- Comments and old debug pastel blocks make future changes likely to continue section-by-section colour thinking.
- Active button shadows are relatively heavy.
- Repeated icon rows and bright filter states compete with chart/map content.
- Section spacing and typography are functional rather than editorial.

## High-Value, Low-Risk Changes

Good early styling tasks:

- Add a CSS token section for colours, spacing, type sizes, radii, borders, and shadows.
- Reorganise `styles.css` into current-state sections without changing selectors.
- Remove verified-dead commented debug/WIP blocks, especially the final Wine block.
- Harmonise selected dropdown value styling across Analysis/Economics/Wine.
- Soften active filter shadows and button borders.
- Standardise section headings, lead paragraphs, and body copy sizing.
- Style the weighted mean explanation as a quiet note.
- Add consistent wrappers for chart/map areas using existing class names.
- Add mobile stacking rules for Analysis graph/map, Economics map/chart, and Wine map/summary.
- Next implementation step: consolidate responsive/media-query behaviour for the established Analysis paper-sheet pattern before extending it to Wine and Economics.

## Changes That Should Wait for Layout or Content Decisions

Defer these until the user approves page-level direction:

- Renaming CSS classes.
- Moving inline Dash layout styles into CSS.
- Reintroducing the Analysis Michelin preamble or rating-system explainer.
- Changing page copy substantially outside the approved plain/direct Analysis direction.
- Combining repeated region/department/arrondissement builders.
- Changing Plotly figure colour palettes or map trace ordering.
- Redesigning the Guide page.
- Changing Wine generated-summary prompt wording.
- Changing callback-driven visibility contracts.
