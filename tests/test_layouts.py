from app.components.shared import get_footer
from app.layouts.analysis import get_analysis_layout
from app.layouts.economics import get_economics_layout
from app.layouts.layout_main import get_main_layout
from app.layouts.wine import get_wine_layout


def collect_component_ids(component):
    ids = set()
    stack = [component]

    while stack:
        item = stack.pop()

        if item is None:
            continue

        if isinstance(item, (list, tuple)):
            stack.extend(item)
            continue

        component_id = getattr(item, "id", None)
        if component_id is not None:
            ids.add(str(component_id))

        children = getattr(item, "children", None)
        if isinstance(children, (list, tuple)):
            stack.extend(children)
        elif children is not None:
            stack.append(children)

    return ids


def find_component_by_id(component, target_id):
    stack = [component]

    while stack:
        item = stack.pop()

        if item is None:
            continue

        if isinstance(item, (list, tuple)):
            stack.extend(item)
            continue

        if getattr(item, "id", None) == target_id:
            return item

        children = getattr(item, "children", None)
        if isinstance(children, (list, tuple)):
            stack.extend(children)
        elif children is not None:
            stack.append(children)

    return None


def test_shared_footer_contains_only_credit_and_linked_github_image():
    footer = get_footer()
    content = footer.children
    credit, github_link = content.children
    github_image = github_link.children

    assert footer.className == "footer-main"
    assert content.className == "footer-content"
    assert credit.children == "pineapple-bois 2026"
    assert github_link.href == (
        "https://github.com/pineapple-bois/Michelin_Rated_Restaurants"
    )
    assert github_link.target == "_blank"
    assert github_link.rel == "noopener noreferrer"
    assert github_link.title == "Open GitHub repository"
    assert github_link.className == "footer-github-link"
    assert github_image.src == "/assets/images/github-mark.png"
    assert github_image.className == "footer-github-image"


def test_analysis_layout_contains_expected_component_ids():
    component_ids = collect_component_ids(get_analysis_layout())

    assert {
        "analysis-content-top",
        "restaurant-analysis-graph",
        "region-map",
        "department-analysis-graph",
        "department-map",
        "arrondissement-analysis-graph",
        "arrondissement-map",
        "ranking-output",
    }.issubset(component_ids)


def test_guide_layout_uses_editorial_shell_without_changing_component_ids():
    layout = get_main_layout()
    component_ids = collect_component_ids(layout)
    _, body, _ = layout.children
    guide_sheet = body.children[0]
    main_content = guide_sheet.children[0]
    map_sidebar, _ = main_content.children
    map_section, sidebar = map_sidebar.children
    _, match_overlay, _ = map_section.children
    search_section, _, _ = sidebar.children
    search_toggle = find_component_by_id(layout, "info-toggle-button")
    search_input = find_component_by_id(layout, "city-input-mainpage")
    region_select = find_component_by_id(layout, "region-dropdown")
    department_select = find_component_by_id(layout, "department-dropdown")
    arrondissement_select = find_component_by_id(layout, "arrondissement-dropdown")
    star_filter = find_component_by_id(layout, "star-filter")
    restaurant_panel = find_component_by_id(layout, "restaurant-details")
    rating_row = star_filter.children[1]
    rating_button = rating_row.children[0]

    assert {
        "info-toggle-button",
        "info-collapse",
        "city-input-mainpage",
        "submit-city-button-mainpage",
        "clear-city-button-mainpage",
        "matched-city-output-mainpage",
        "region-dropdown",
        "department-dropdown",
        "arrondissement-dropdown-container",
        "arrondissement-dropdown",
        "star-filter",
        "toggle-selected-btn",
        "restaurant-details",
        "map-display",
        "map-view-store-mainpage",
    }.issubset(component_ids)
    assert "guide-page-frame" in body.className
    assert "editorial-page-frame" in body.className
    assert "guide-page-sheet" in guide_sheet.className
    assert "editorial-sheet" in guide_sheet.className
    assert main_content.className == "main-content"
    assert "guide-sidebar-search" in search_section.className
    assert "guide-map-match-overlay" in match_overlay.className
    assert match_overlay.children[0].id == "matched-city-output-mainpage"
    assert "editorial-action-button" in search_toggle.className
    assert "guide-search-input" in search_input.className
    for select in (region_select, department_select, arrondissement_select):
        assert "editorial-select" in select.className
        assert "guide-select" in select.className
    assert "editorial-rating-filters" in star_filter.className
    assert "editorial-rating-button" in rating_button.className
    assert "guide-rating-button" in rating_button.className
    assert "editorial-info-panel" in restaurant_panel.className
    assert "guide-restaurant-panel" in restaurant_panel.className


def test_economics_layout_contains_expected_component_ids():
    layout = get_economics_layout()
    component_ids = collect_component_ids(layout)

    assert {
        "demographics-content-top",
        "category-dropdown-demographics",
        "granularity-dropdown-demographics",
        "demographics-dropdown-analysis",
        "demographics-map-graph",
        "demographics-bar-chart-graph",
        "weighted-mean",
        "toggle-show-details-demographics",
    }.issubset(component_ids)

    restaurant_toggle = find_component_by_id(
        layout,
        "toggle-show-details-demographics",
    )
    demographics_chart = find_component_by_id(layout, "demographics-chart-math")
    region_filter = find_component_by_id(layout, "demographics-add-remove")
    assert restaurant_toggle.children == "Starred restaurants"
    assert restaurant_toggle.n_clicks == 0
    assert restaurant_toggle.active is False
    assert "editorial-toggle-button" in restaurant_toggle.className
    assert demographics_chart.hidden is True
    assert "filter-container" in region_filter.className


def test_wine_layout_contains_expected_component_ids():
    layout = get_wine_layout()
    component_ids = collect_component_ids(layout)

    assert {
        "wine-content-top",
        "wine-region-selector",
        "wine-appellation-search",
        "toggle-regional-outlines-wine",
        "toggle-show-details-wine",
        "wine-map-graph",
        "wine-map-hover-overlay",
        "wine-map-hover-appellation",
        "wine-map-hover-region",
        "region-name-container",
        "llm-output-container",
        "disclaimer-container",
    }.issubset(component_ids)
    assert "selected-stars-wine" not in component_ids
    assert "wine-region-curve-numbers" not in component_ids

    region_selector = find_component_by_id(layout, "wine-region-selector")
    appellation_search = find_component_by_id(layout, "wine-appellation-search")
    outline_toggle = find_component_by_id(layout, "toggle-regional-outlines-wine")
    restaurant_button = find_component_by_id(layout, "toggle-show-details-wine")
    star_filter_container = find_component_by_id(layout, "star-filter-container-wine")
    wine_map = find_component_by_id(layout, "wine-map-graph")
    hover_overlay = find_component_by_id(layout, "wine-map-hover-overlay")

    assert getattr(region_selector, "searchable", False) is True
    assert getattr(region_selector, "clearable", False) is True
    assert region_selector.placeholder == "Select region..."
    assert getattr(appellation_search, "searchable", False) is True
    assert getattr(appellation_search, "clearable", False) is True
    assert appellation_search.placeholder == "Search by appellation..."
    assert outline_toggle.children == "Regional outlines"
    assert outline_toggle.n_clicks == 0
    assert outline_toggle.active is False
    assert "editorial-toggle-button" in outline_toggle.className
    assert restaurant_button.children == "Starred restaurants"
    assert restaurant_button.n_clicks == 0
    assert restaurant_button.active is False
    assert "editorial-toggle-button" in restaurant_button.className
    assert getattr(restaurant_button, "disabled", False) is False
    assert star_filter_container.style == {'width': '30%', 'display': 'none'}
    assert wine_map.clear_on_unhover is True
    assert hover_overlay.hidden is True
