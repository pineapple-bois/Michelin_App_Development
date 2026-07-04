import pytest

from app.utils.analysis_figures import (
    ANALYSIS_FRANCE_MAP_ZOOM,
    plot_single_choropleth_plotly,
)
from app.utils.economics_figures import (
    ECONOMICS_FRANCE_MAP_ZOOM,
    ECONOMICS_SPLIT_MAP_ZOOM,
    plot_demographic_choropleth_plotly,
)
from app.utils.map_constraints import (
    FRANCE_OVERVIEW_MAP_BOUNDS,
    FRANCE_SPLIT_MAP_BOUNDS,
    METROPOLITAN_FRANCE_MAP_BOUNDS,
)
from app.utils.wine_figures import plot_wine_choropleth_plotly


def _assert_france_bounds(fig, expected_bounds=METROPOLITAN_FRANCE_MAP_BOUNDS):
    assert fig.layout.map.bounds.to_plotly_json() == expected_bounds


@pytest.mark.parametrize(
    ("granularity", "frame_name"),
    (
        ("region", "region_df"),
        ("department", "department_df"),
        ("arrondissement", "paris_df"),
    ),
)
def test_analysis_maps_use_maplibre_france_bounds(
    data_boundary,
    granularity,
    frame_name,
):
    frame = getattr(data_boundary, frame_name).copy()
    if granularity == "department":
        frame = frame[frame["region"] == "Île-de-France"].copy()

    fig = plot_single_choropleth_plotly(
        frame,
        [0.5, 1, 2, 3],
        granularity=granularity,
        show_labels=False,
    )

    assert fig.data[0].type == "choroplethmap"
    assert fig.layout.geo.to_plotly_json() == {}
    _assert_france_bounds(fig, FRANCE_SPLIT_MAP_BOUNDS)
    if granularity == "region":
        assert fig.layout.map.zoom == ANALYSIS_FRANCE_MAP_ZOOM


def test_economics_map_uses_shared_france_bounds_and_preserves_view(data_boundary):
    persisted_view = {
        "center": {"lat": 47.1, "lon": 2.6},
        "zoom": 6.25,
    }

    fig = plot_demographic_choropleth_plotly(
        data_boundary.region_df.copy(),
        data_boundary.all_france,
        metric="municipal_population",
        show_labels=False,
        zoom_data=persisted_view,
    )

    _assert_france_bounds(fig, FRANCE_SPLIT_MAP_BOUNDS)
    assert fig.layout.map.center.lat == persisted_view["center"]["lat"]
    assert fig.layout.map.center.lon == persisted_view["center"]["lon"]
    assert fig.layout.map.zoom == persisted_view["zoom"]


def test_economics_default_view_fits_metropolitan_france(data_boundary):
    fig = plot_demographic_choropleth_plotly(
        data_boundary.region_df.copy(),
        data_boundary.all_france,
        metric=None,
        show_labels=False,
    )

    _assert_france_bounds(fig, FRANCE_OVERVIEW_MAP_BOUNDS)
    assert fig.layout.map.zoom == ECONOMICS_FRANCE_MAP_ZOOM


def test_economics_metric_view_uses_split_layout_framing(data_boundary):
    fig = plot_demographic_choropleth_plotly(
        data_boundary.region_df.copy(),
        data_boundary.all_france,
        metric="municipal_population",
        show_labels=False,
    )

    _assert_france_bounds(fig, FRANCE_SPLIT_MAP_BOUNDS)
    assert fig.layout.map.zoom == ECONOMICS_SPLIT_MAP_ZOOM


def test_wine_map_uses_shared_france_bounds_and_preserves_view(data_boundary):
    persisted_view = {
        "center": {"lat": 44.9, "lon": 4.8},
        "zoom": 7.5,
    }

    fig = plot_wine_choropleth_plotly(
        data_boundary.wine_df,
        zoom_data=persisted_view,
        regional_outline_df=data_boundary.region_df,
        restaurants_df=data_boundary.all_france,
    )

    _assert_france_bounds(fig)
    assert fig.layout.map.center.lat == persisted_view["center"]["lat"]
    assert fig.layout.map.center.lon == persisted_view["center"]["lon"]
    assert fig.layout.map.zoom == persisted_view["zoom"]
