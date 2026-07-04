from app.callbacks.guide import (
    available_ratings_for_department,
    guide_geography_key,
    resolve_guide_view_data,
    updated_guide_view_store,
)
from app.layouts.layout_main import GUIDE_HIDDEN_RATING_BUTTON_CLASS, star_filter_section


def _find_component_by_id(component, component_id):
    if getattr(component, "id", None) == component_id:
        return component
    children = getattr(component, "children", None)
    if children is None:
        return None
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        found = _find_component_by_id(child, component_id)
        if found is not None:
            return found
    return None


def test_bib_only_filter_keeps_required_selected_control_hidden():
    rating_filter = star_filter_section([0.5])

    selected_control = _find_component_by_id(rating_filter, "toggle-selected-btn")

    assert selected_control is not None
    assert GUIDE_HIDDEN_RATING_BUTTON_CLASS in selected_control.className


def test_department_available_ratings_match_restaurant_ratings_globally(data_boundary):
    geo_df = data_boundary.get_geo_df(include_monaco=True)
    restaurants = data_boundary.get_combined_restaurant_data(include_monaco=True)

    for _, department in geo_df.iterrows():
        department_restaurants = restaurants[
            restaurants["department_num"] == str(department["code"])
        ]
        ratings_present = set(department_restaurants["stars"].unique())
        ratings_available = set(available_ratings_for_department(department))

        assert ratings_available == ratings_present, (
            f"{department['department']} ({department['code']}) exposes "
            f"{sorted(ratings_available)} but contains {sorted(ratings_present)}"
        )


def test_geographic_selection_reset_overrides_stale_stored_view():
    stale_view = {
        "center": {"lat": 46.603354, "lon": 1.888334},
        "zoom": 5,
    }
    selected_department_view = {
        "center": {"lat": 46.35, "lon": 3.15},
        "zoom": 8,
    }
    selected_geography = guide_geography_key(
        "Auvergne-Rhône-Alpes",
        "Allier",
        None,
    )

    resolved = resolve_guide_view_data(
        {"selected-stars", "department-dropdown"},
        stale_view,
        selected_department_view,
        selected_geography,
    )

    assert resolved == selected_department_view
    assert resolved is not selected_department_view


def test_non_geographic_update_preserves_manual_stored_view():
    selected_geography = guide_geography_key(
        "Auvergne-Rhône-Alpes",
        "Allier",
        None,
    )
    manual_view = {
        "center": {"lat": 46.1, "lon": 2.75},
        "zoom": 9.25,
        "geography": selected_geography,
    }
    selected_department_view = {
        "center": {"lat": 46.35, "lon": 3.15},
        "zoom": 8,
    }

    resolved = resolve_guide_view_data(
        {"selected-stars"},
        manual_view,
        selected_department_view,
        selected_geography,
    )

    assert resolved == manual_view
    assert resolved is not manual_view


def test_delayed_rating_update_rejects_view_from_previous_department():
    previous_geography = guide_geography_key(
        "Auvergne-Rhône-Alpes",
        "Allier",
        None,
    )
    selected_geography = guide_geography_key(
        "Auvergne-Rhône-Alpes",
        "Cantal",
        None,
    )
    stale_view = {
        "center": {"lat": 46.35, "lon": 3.15},
        "zoom": 9,
        "geography": previous_geography,
    }
    selected_department_view = {
        "center": {"lat": 45.05, "lon": 2.68},
        "zoom": 8,
    }

    resolved = resolve_guide_view_data(
        {"selected-stars"},
        stale_view,
        selected_department_view,
        selected_geography,
    )

    assert resolved == selected_department_view


def test_geographic_change_clears_view_but_records_new_owner():
    previous_geography = guide_geography_key(
        "Auvergne-Rhône-Alpes",
        "Allier",
        None,
    )
    selected_geography = guide_geography_key(
        "Auvergne-Rhône-Alpes",
        "Cantal",
        None,
    )
    stale_view = {
        "center": {"lat": 46.35, "lon": 3.15},
        "zoom": 9,
        "geography": previous_geography,
    }

    next_view = updated_guide_view_store(
        {"department-dropdown"},
        {"map.zoom": 9, "map.center": stale_view["center"]},
        selected_geography,
        stale_view,
    )

    assert next_view == {"geography": selected_geography}


def test_manual_relayout_is_persisted_for_current_geography():
    geography = guide_geography_key(
        "Auvergne-Rhône-Alpes",
        "Allier",
        None,
    )
    manual_center = {"lat": 46.1, "lon": 2.75}

    next_view = updated_guide_view_store(
        {"map-display"},
        {"map.zoom": 9.25, "map.center": manual_center},
        geography,
        {"geography": geography},
    )

    assert next_view == {
        "zoom": 9.25,
        "center": manual_center,
        "geography": geography,
    }
