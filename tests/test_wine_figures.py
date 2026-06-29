from app.utils.wine_figures import plot_wine_choropleth_plotly


def test_wine_figure_uses_one_feature_based_geography_trace(data_boundary):
    fig = plot_wine_choropleth_plotly(data_boundary.wine_df)
    expected_count = len(data_boundary.wine_df)

    assert len(fig.data) == 1
    trace = fig.data[0]
    assert trace.type == "choroplethmap"
    assert trace.subplot == "map"
    assert trace.featureidkey == "properties.feature_id"
    assert len(trace.locations) == expected_count
    assert len(set(trace.locations)) == expected_count
    assert list(trace.locations) == data_boundary.wine_df["feature_id"].tolist()
    assert list(trace.ids) == list(trace.locations)
    assert trace.showscale is False


def test_wine_figure_exposes_semantic_hover_data(data_boundary):
    fig = plot_wine_choropleth_plotly(data_boundary.wine_df)
    trace = fig.data[0]
    expected_count = len(data_boundary.wine_df)

    assert len(trace.customdata) == expected_count
    assert list(trace.customdata[0]) == data_boundary.wine_df.iloc[0][
        ["region", "app", "feature_id"]
    ].tolist()
    assert "Appellation:" in trace.hovertemplate
    assert "%{customdata[1]}" in trace.hovertemplate
    assert "Parent region:" in trace.hovertemplate
    assert "%{customdata[0]}" in trace.hovertemplate

    features = trace.geojson["features"]
    assert len(features) == expected_count
    assert {
        feature["properties"]["feature_id"]
        for feature in features
    } == set(trace.locations)


def test_wine_figure_preserves_map_contract(data_boundary):
    fig = plot_wine_choropleth_plotly(data_boundary.wine_df)

    assert fig.layout.map.style == "carto-positron"
    assert fig.layout.map.zoom == 5
    assert fig.layout.map.center.lat == 46.603354
    assert fig.layout.map.center.lon == 1.888334
    assert fig.layout.map.uirevision == "wine-aoc-map-v1"
