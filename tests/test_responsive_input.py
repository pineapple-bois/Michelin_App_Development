import inspect

from dash import dcc

from app.callbacks.responsive import (
    RESPONSIVE_DROPDOWN_IDS,
    RESPONSIVE_INPUT_MODE_STORE_ID,
    SMALL_SCREEN_MAX_WIDTH,
    initial_responsive_input_mode,
    register_responsive_input_callbacks,
)
from app.layouts.analysis import get_analysis_layout
from app.layouts.economics import get_economics_layout
from app.layouts.layout_main import get_main_layout, unique_regions
from app.layouts.wine import get_wine_layout


def _walk(component):
    stack = [component]
    while stack:
        item = stack.pop()
        if item is None:
            continue
        if isinstance(item, (list, tuple)):
            stack.extend(item)
            continue
        yield item
        children = getattr(item, "children", None)
        if isinstance(children, (list, tuple)):
            stack.extend(children)
        elif children is not None:
            stack.append(children)


def _by_id(layout, component_id):
    return next(
        component for component in _walk(layout)
        if getattr(component, "id", None) == component_id
    )


def test_responsive_store_is_root_scoped_with_safe_initial_mode(app_module):
    store = _by_id(app_module.app.layout, RESPONSIVE_INPUT_MODE_STORE_ID)

    assert isinstance(store, dcc.Store)
    assert getattr(store, "storage_type", "memory") == "memory"
    assert store.data == initial_responsive_input_mode() == {
        "ready": False,
        "is_small_screen": True,
        "max_width": 1250,
    }


def test_responsive_policy_reuses_the_existing_small_layout_breakpoint():
    assert SMALL_SCREEN_MAX_WIDTH == 1250


def test_all_dropdowns_start_non_searchable_without_changing_their_contracts():
    layouts = {
        "guide": get_main_layout(),
        "analysis": get_analysis_layout(),
        "economics": get_economics_layout(),
        "wine": get_wine_layout(),
    }
    dropdowns = {
        page: {
            component.id: component
            for component in _walk(layout)
            if isinstance(component, dcc.Dropdown)
        }
        for page, layout in layouts.items()
    }

    assert {
        page: set(page_dropdowns)
        for page, page_dropdowns in dropdowns.items()
    } == {
        page: set(dropdown_ids)
        for page, dropdown_ids in RESPONSIVE_DROPDOWN_IDS.items()
    }
    assert all(
        component.searchable is False
        for page_dropdowns in dropdowns.values()
        for component in page_dropdowns.values()
    )

    expected_contracts = {
        "region-dropdown": ("Auvergne-Rhône-Alpes", False, False),
        "department-dropdown": (None, False, True),
        "arrondissement-dropdown": (None, False, False),
        "region-dropdown-analysis": (unique_regions, True, True),
        "department-dropdown-analysis": (None, False, True),
        "arrondissement-dropdown-analysis": (None, False, True),
        "granularity-dropdown": (None, False, True),
        "ranking-dropdown": (3, False, False),
        "star-dropdown-ranking": (2, False, False),
        "category-dropdown-demographics": (None, False, True),
        "granularity-dropdown-demographics": ("All France", False, False),
        "demographics-dropdown-analysis": (unique_regions, True, True),
        "wine-region-selector": (None, False, True),
        "wine-appellation-search": (None, False, True),
    }
    for page_dropdowns in dropdowns.values():
        for component_id, component in page_dropdowns.items():
            assert (
                getattr(component, "value", None),
                getattr(component, "multi", False),
                getattr(component, "clearable", True),
            ) == expected_contracts[component_id]

    expected_option_values = {
        "region-dropdown": unique_regions,
        "department-dropdown": None,
        "arrondissement-dropdown": None,
        "region-dropdown-analysis": ["all", *unique_regions],
        "department-dropdown-analysis": unique_regions,
        "arrondissement-dropdown-analysis": [],
        "granularity-dropdown": ["region", "department", "arrondissement"],
        "ranking-dropdown": [3, 5, 1],
        "star-dropdown-ranking": [2, 3, "green"],
        "category-dropdown-demographics": [
            "gdp_current_prices_million_eur",
            "gdp_per_capita_eur",
            "poverty_rate_percent",
            "census_unemployment_rate_15_64_percent",
            "average_net_monthly_wage_fte_eur",
            "median_living_standard_eur",
            "municipal_population",
            "population_density_per_sq_km",
            "area_sq_km",
        ],
        "granularity-dropdown-demographics": ["All France", *unique_regions],
        "demographics-dropdown-analysis": ["all", *unique_regions],
        "wine-region-selector": [],
        "wine-appellation-search": [],
    }
    for page_dropdowns in dropdowns.values():
        for component_id, component in page_dropdowns.items():
            options = getattr(component, "options", None)
            option_values = (
                [option["value"] for option in options]
                if options is not None
                else None
            )
            assert option_values == expected_option_values[component_id]


def test_guide_location_search_remains_a_text_input():
    city_input = _by_id(get_main_layout(), "city-input-mainpage")

    assert isinstance(city_input, dcc.Input)
    assert city_input.type == "text"


def test_responsive_callbacks_govern_every_dropdown_on_its_page(app_module):
    expected_dropdown_ids = {
        dropdown_id
        for dropdown_ids in RESPONSIVE_DROPDOWN_IDS.values()
        for dropdown_id in dropdown_ids
    }
    searchable_outputs = {
        dropdown_id
        for output in app_module.app.callback_map
        if ".searchable" in output
        for dropdown_id in expected_dropdown_ids
        if f"{dropdown_id}.searchable" in output
    }

    assert searchable_outputs == expected_dropdown_ids


def test_viewport_callback_tracks_layout_changes_without_device_detection():
    source = inspect.getsource(register_responsive_input_callbacks)

    assert 'addEventListener("resize"' in source
    assert 'addEventListener("orientationchange"' in source
    assert 'removeEventListener("resize"' in source
    assert 'removeEventListener("orientationchange"' in source
    assert "window.innerWidth" in source
    assert "set_props" in source
    assert "pointer" not in source.lower()
    assert "hover" not in source.lower()
    assert "touch" not in source.lower()


def test_wine_search_value_callback_remains_registered(app_module):
    option_callbacks = [
        metadata
        for output, metadata in app_module.app.callback_map.items()
        if output == "wine-appellation-search.options"
    ]

    assert len(option_callbacks) == 1
    assert {
        "id": "wine-appellation-search",
        "property": "search_value",
    } in option_callbacks[0]["inputs"]
