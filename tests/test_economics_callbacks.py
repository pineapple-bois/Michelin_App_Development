import pytest

from app.callbacks.economics import (
    demographics_chart_hidden,
    demographics_region_selector_style,
    map_view_for_demographics_update,
    reset_demographics_star_clicks,
    restaurant_overlay_active,
)


@pytest.mark.parametrize(
    ("n_clicks", "expected"),
    [
        (None, False),
        (0, False),
        (1, True),
        (2, False),
    ],
)
def test_restaurant_overlay_active_tracks_toggle_clicks(n_clicks, expected):
    assert restaurant_overlay_active(n_clicks) is expected


@pytest.mark.parametrize(
    ("selected_metric", "expected"),
    [(None, True), ("", True), ("gdp_per_capita_eur", False)],
)
def test_demographics_chart_hidden_tracks_metric_selection(selected_metric, expected):
    assert demographics_chart_hidden(selected_metric) is expected


def test_demographics_region_selector_is_removed_for_department_view():
    assert demographics_region_selector_style("All France") == {'display': 'block'}
    assert demographics_region_selector_style("Bourgogne-Franche-Comté") == {
        'display': 'none'
    }


def test_demographics_star_clicks_reset_only_when_overlay_closes():
    ids = [
        {"type": "filter-button-demographics", "index": 1},
        {"type": "filter-button-demographics", "index": 2},
        {"type": "filter-button-demographics", "index": 3},
    ]

    assert reset_demographics_star_clicks(1, ids) is None
    assert reset_demographics_star_clicks(2, ids) == [0, 0, 0]
    assert reset_demographics_star_clicks(2, []) is None


def test_demographics_region_change_ignores_persisted_map_view():
    persisted_view = {"zoom": 7, "center": {"lat": 48.0, "lon": 2.0}}

    assert map_view_for_demographics_update(
        persisted_view,
        "granularity-dropdown-demographics",
    ) == {}
    assert map_view_for_demographics_update(
        persisted_view,
        "category-dropdown-demographics",
    ) == persisted_view
