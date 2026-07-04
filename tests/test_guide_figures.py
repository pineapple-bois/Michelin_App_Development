from app.utils.guide_figures import (
    GUIDE_FRANCE_MAP_BOUNDS,
    default_map_figure,
    plot_arrondissement_outlines,
    plot_department_outlines,
    plot_interactive_department,
    plot_paris_arrondissement,
    plot_regional_outlines,
)


def _assert_guide_bounds(fig):
    assert fig.layout.map.bounds.to_plotly_json() == GUIDE_FRANCE_MAP_BOUNDS


def test_default_guide_map_has_native_france_bounds():
    fig = default_map_figure()

    _assert_guide_bounds(fig)
    assert fig.layout.map.center.lat == 46.603354
    assert fig.layout.map.center.lon == 1.888334
    assert fig.layout.map.zoom == 5


def test_all_guide_map_rebuild_paths_keep_native_bounds(data_boundary):
    region = data_boundary.region_df.iloc[0]["region"]
    department_code = data_boundary.geo_df.iloc[0]["code"]
    arrondissement = data_boundary.paris_df.iloc[0]["arrondissement"]
    persisted_view = {
        "center": {"lat": 46.2, "lon": 2.4},
        "zoom": 8.25,
    }

    figures = [
        plot_regional_outlines(data_boundary.region_df, region),
        plot_department_outlines(
            data_boundary.geo_df,
            department_code,
            persisted_view,
        ),
        plot_arrondissement_outlines(
            data_boundary.paris_df,
            arrondissement,
            persisted_view,
        ),
        plot_interactive_department(
            data_boundary.all_france,
            data_boundary.geo_df,
            department_code,
            [0.25, 0.5, 1, 2, 3],
            persisted_view,
        ),
        plot_paris_arrondissement(
            data_boundary.all_france,
            data_boundary.paris_df,
            arrondissement,
            [0.25, 0.5, 1, 2, 3],
            persisted_view,
        ),
    ]

    for fig in figures:
        _assert_guide_bounds(fig)

    for fig in figures[1:]:
        assert fig.layout.map.center.lat == persisted_view["center"]["lat"]
        assert fig.layout.map.center.lon == persisted_view["center"]["lon"]
        assert fig.layout.map.zoom == persisted_view["zoom"]
