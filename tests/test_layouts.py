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
    component_ids = collect_component_ids(get_wine_layout())

    assert {
        "wine-content-top",
        "granularity-dropdown-wine",
        "toggle-show-details-wine",
        "selected-stars-wine",
        "wine-map-graph",
        "region-name-container",
        "llm-output-container",
        "disclaimer-container",
    }.issubset(component_ids)
    assert "wine-region-curve-numbers" not in component_ids
