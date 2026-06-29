from app.layouts.analysis import get_analysis_layout
from app.layouts.economics import get_economics_layout
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


def test_economics_layout_contains_expected_component_ids():
    component_ids = collect_component_ids(get_economics_layout())

    assert {
        "demographics-content-top",
        "category-dropdown-demographics",
        "granularity-dropdown-demographics",
        "demographics-dropdown-analysis",
        "demographics-map-graph",
        "demographics-bar-chart-graph",
        "weighted-mean",
    }.issubset(component_ids)


def test_wine_layout_contains_expected_component_ids():
    layout = get_wine_layout()
    component_ids = collect_component_ids(layout)

    assert {
        "wine-content-top",
        "wine-region-selector",
        "wine-appellation-search",
        "granularity-dropdown-wine",
        "toggle-show-details-wine",
        "wine-map-graph",
        "region-name-container",
        "llm-output-container",
        "disclaimer-container",
    }.issubset(component_ids)
    assert "selected-stars-wine" not in component_ids
    assert "wine-region-curve-numbers" not in component_ids

    region_selector = find_component_by_id(layout, "wine-region-selector")
    appellation_search = find_component_by_id(layout, "wine-appellation-search")
    outline_dropdown = find_component_by_id(layout, "granularity-dropdown-wine")
    restaurant_button = find_component_by_id(layout, "toggle-show-details-wine")
    star_filter_container = find_component_by_id(layout, "star-filter-container-wine")

    assert getattr(region_selector, "searchable", False) is True
    assert getattr(region_selector, "clearable", False) is True
    assert region_selector.placeholder == "Select region..."
    assert getattr(appellation_search, "searchable", False) is True
    assert getattr(appellation_search, "clearable", False) is True
    assert appellation_search.placeholder == "Search by appellation..."
    assert getattr(outline_dropdown, "disabled", False) is False
    assert getattr(restaurant_button, "disabled", False) is False
    assert star_filter_container.style == {'width': '30%', 'display': 'none'}
