import json

import plotly.graph_objects as go

REGIONAL_OUTLINE_LAYER_INDEX = 0
WINE_AOC_TRACE_INDEX = 0
RESTAURANT_STAR_ORDER = (1, 2, 3)
RESTAURANT_TRACE_INDICES = {
    star: index
    for index, star in enumerate(RESTAURANT_STAR_ORDER, start=1)
}
RESTAURANT_STAR_COLORS = {
    1: "#FFB84D",
    2: "#FE6F64",
    3: "#C2282D",
}


def _region_colour_contract(wine_df):
    region_colours = (
        wine_df[["region", "colour"]]
        .drop_duplicates()
        .sort_values("region")
    )
    region_codes = {
        region: code
        for code, region in enumerate(region_colours["region"])
    }

    colour_count = len(region_colours)
    colorscale = []
    for code, colour in enumerate(region_colours["colour"]):
        lower = code / colour_count
        upper = (code + 1) / colour_count
        colorscale.extend(((lower, colour), (upper, colour)))

    return region_codes, colorscale


def _outline_geojson(outline_df):
    outlines = (
        outline_df[["region", "geometry"]]
        .drop_duplicates(subset="region")
        .copy()
    )
    outlines["geometry"] = outlines.geometry.boundary

    return json.loads(outlines.to_json(drop_id=True))


def _regional_outline_layer(outline_df, visible=False):
    return {
        "source": _outline_geojson(outline_df),
        "type": "line",
        "below": "traces",
        "color": "#5f5148",
        "line": {"width": 0.65},
        "opacity": 0.45,
        "visible": visible,
    }


def _restaurant_trace(restaurants_df, star):
    star_data = restaurants_df[restaurants_df["stars"] == star]
    return go.Scattermap(
        lon=star_data["longitude"].tolist(),
        lat=star_data["latitude"].tolist(),
        mode="markers",
        below="",
        marker=go.scattermap.Marker(
            size=8,
            color=RESTAURANT_STAR_COLORS[star],
        ),
        hovertemplate=(
            "<b>Restaurant Name:</b> %{customdata[0]}<br>"
            "<b>Location:</b> %{customdata[1]}<br>"
            "<extra></extra>"
        ),
        customdata=star_data[["name", "location"]].values,
        showlegend=False,
        visible=False,
        name=f"{'★' * star}",
        meta={
            "kind": "restaurant",
            "stars": star,
        },
    )


def plot_wine_choropleth_plotly(
    wine_df,
    zoom_data=None,
    regional_outline_df=None,
    restaurants_df=None,
    show_regional_outlines=False,
):
    """Render the complete AOC FeatureCollection as one MapLibre trace."""
    zoom_data = zoom_data or {}
    regional_outline_df = regional_outline_df if regional_outline_df is not None else wine_df
    region_codes, colorscale = _region_colour_contract(wine_df)
    feature_ids = wine_df["feature_id"].tolist()

    geojson = json.loads(wine_df.to_json(drop_id=True))
    z_values = wine_df["region"].map(region_codes).tolist()
    colour_count = len(region_codes)

    fig = go.Figure(
        go.Choroplethmap(
            subplot="map",
            geojson=geojson,
            featureidkey="properties.feature_id",
            locations=feature_ids,
            ids=feature_ids,
            z=z_values,
            zmin=-0.5,
            zmax=colour_count - 0.5,
            colorscale=colorscale,
            showscale=False,
            customdata=wine_df[["region", "app", "feature_id"]].to_numpy(),
            hovertemplate=(
                "<b>Appellation:</b> %{customdata[1]}<br>"
                "<b>Parent region:</b> %{customdata[0]}"
                "<extra></extra>"
            ),
            marker_line_width=0.5,
            marker_line_color="darkgray",
            name="Wine appellations",
        )
    )
    if restaurants_df is not None:
        for star in RESTAURANT_STAR_ORDER:
            fig.add_trace(_restaurant_trace(restaurants_df, star))

    zoom = zoom_data.get("zoom", 5)
    center = zoom_data.get("center") or {
        "lat": 46.603354,
        "lon": 1.888334,
    }

    fig.update_layout(
        map={
            "style": "carto-positron",
            "zoom": zoom,
            "center": center,
            "uirevision": "wine-aoc-map-v1",
            "layers": [
                _regional_outline_layer(
                    regional_outline_df,
                    visible=show_regional_outlines,
                )
            ],
        },
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        hovermode="closest",
    )

    return fig
