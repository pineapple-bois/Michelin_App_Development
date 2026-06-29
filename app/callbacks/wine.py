import dash
from dash import Patch, dcc, html, no_update
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate
from flask import session

from app.utils.star_filters import update_button_active_state_helper
from app.utils.wine_figures import (
    RESTAURANT_STAR_ORDER,
    RESTAURANT_TRACE_INDICES,
    REGIONAL_OUTLINE_LAYER_INDEX,
    plot_wine_choropleth_plotly,
)
from app.utils.wine_prompts import generate_optimized_prompt


def resolve_wine_feature(click_data, feature_lookup):
    """Resolve an AOC click by stable feature ID, or fail closed."""
    if not isinstance(click_data, dict):
        return None

    points = click_data.get("points")
    if not isinstance(points, list) or not points or not isinstance(points[0], dict):
        return None

    feature_id = points[0].get("location")
    if not isinstance(feature_id, str):
        return None

    return feature_lookup.get(feature_id)


def regional_outlines_visible(selected_granularity):
    return selected_granularity == "region"


def regional_outline_visibility_patch(selected_granularity):
    patched_figure = Patch()
    patched_figure["layout"]["map"]["layers"][REGIONAL_OUTLINE_LAYER_INDEX]["visible"] = (
        regional_outlines_visible(selected_granularity)
    )
    return patched_figure


def restaurant_overlay_visible(n_clicks_rest):
    return bool(n_clicks_rest and n_clicks_rest % 2 == 1)


def selected_restaurant_stars(n_clicks_stars, ids):
    if not n_clicks_stars or not ids:
        return set(RESTAURANT_STAR_ORDER)

    return {
        button_id["index"]
        for n_clicks, button_id in zip(n_clicks_stars, ids)
        if n_clicks % 2 == 0
    }


def restaurant_filter_style(show_restaurants):
    return (
        {'width': '30%', 'display': 'block'}
        if show_restaurants
        else {'width': '30%', 'display': 'none'}
    )


def restaurant_visibility_patch(n_clicks_rest, n_clicks_stars=None, ids=None):
    show_restaurants = restaurant_overlay_visible(n_clicks_rest)
    active_stars = selected_restaurant_stars(n_clicks_stars, ids)

    patched_figure = Patch()
    for star in RESTAURANT_STAR_ORDER:
        trace_index = RESTAURANT_TRACE_INDICES[star]
        patched_figure["data"][trace_index]["visible"] = (
            show_restaurants and star in active_stars
        )
    return patched_figure


def build_wine_info_response(
    click_data,
    feature_lookup,
    cache,
    openai_client,
    is_request_limit_exceeded,
    prompt_builder=generate_optimized_prompt,
):
    """Build the Wine information panel from semantic AOC click data."""
    if not click_data:
        return "Click on a wine region to get more information.", {"display": "none"}, no_update, {"display": "none"}

    wine_feature = resolve_wine_feature(click_data, feature_lookup)
    if wine_feature is None:
        return no_update, no_update, no_update, no_update

    wine_region = wine_feature["region"]
    appellation = wine_feature["app"]

    cache_key = f"wine_info_{appellation}_{wine_region}"
    cached_content = cache.get(cache_key)
    if cached_content:
        region_name_content = html.H3(wine_region, style={'color': cached_content['color']})
        print(f"Cached Information retrieved for {appellation}: {wine_region}")
        return dcc.Markdown(cached_content['content']), {"display": "block"}, region_name_content, {"display": "block"}

    if is_request_limit_exceeded():
        error_message = "You have reached the maximum number of requests."
        styled_error = html.Div(error_message, style={"color": "red", "font-weight": "bold", "text-align": "center"})
        return styled_error, {"display": "none"}, no_update, {"display": "none"}

    region_color = wine_feature["colour"]

    prompt = prompt_builder(wine_region, appellation)
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        content = response.choices[0].message.content.strip()

        cache.set(cache_key, {'content': content, 'color': region_color})

        region_name_content = html.H3(wine_region, style={'color': region_color})
        return dcc.Markdown(content), {"display": "block"}, region_name_content, {"display": "block"}

    except Exception as e:
        return f"Error fetching region details: {str(e)}", {"display": "none"}, no_update, {"display": "none"}


def register_wine_callbacks(app, data, config, cache, openai_client):
    all_france = data.all_france
    wine_df = data.wine_df
    region_df = data.region_df
    wine_feature_lookup = (
        wine_df.set_index("feature_id")[["region", "app", "colour"]]
        .to_dict("index")
    )

    def is_request_limit_exceeded():
        # Request limit for OpenAi API calls
        request_limit = config.openai_request_limit

        # Check if request_count exists in session
        if 'request_count' not in session:
            session['request_count'] = 0  # Initialize if not present

        session['request_count'] += 1  # Increment request count

        if session['request_count'] > request_limit:
            return True
        return False

    @app.callback(
        Output('wine-map-graph', 'figure'),
        Input('url', 'pathname'),
        State('map-view-store', 'data'),
    )
    def update_wine_map(pathname, map_view_data):
        if pathname != '/wine':
            raise PreventUpdate

        return plot_wine_choropleth_plotly(
            wine_df=wine_df,
            zoom_data=map_view_data,
            regional_outline_df=region_df,
            restaurants_df=all_france,
        )

    @app.callback(
        Output('wine-map-graph', 'figure', allow_duplicate=True),
        Input('granularity-dropdown-wine', 'value'),
        prevent_initial_call=True,
    )
    def update_wine_regional_outlines(selected_granularity):
        return regional_outline_visibility_patch(selected_granularity)

    @app.callback(
        [Output('wine-map-graph', 'figure', allow_duplicate=True),
         Output('star-filter-container-wine', 'style')],
        [Input('toggle-show-details-wine', 'n_clicks'),
         Input({'type': 'filter-button-wine', 'index': ALL}, 'n_clicks')],
        [State({'type': 'filter-button-wine', 'index': ALL}, 'id')],
        prevent_initial_call=True,
    )
    def update_wine_restaurant_visibility(n_clicks_rest, n_clicks_stars, ids):
        show_restaurants = restaurant_overlay_visible(n_clicks_rest)
        return (
            restaurant_visibility_patch(n_clicks_rest, n_clicks_stars, ids),
            restaurant_filter_style(show_restaurants),
        )

    @app.callback(
        Output('map-view-store', 'data'),
        [Input('wine-map-graph', 'relayoutData')],
        [State('map-view-store', 'data')]
    )
    def store_map_view(relayout_data, existing_data):
        # Initialize existing_data if it's None
        if existing_data is None:
            existing_data = {}

        # If relayoutData is None or empty, do not update the store
        if not relayout_data:
            raise dash.exceptions.PreventUpdate

        # Define the keys that indicate a user interaction
        user_interaction_keys = {'map.zoom', 'map.center'}

        # Check if relayoutData contains any of the user interaction keys
        if user_interaction_keys.intersection(relayout_data.keys()):
            # Extract zoom and center from relayoutData
            zoom = relayout_data.get('map.zoom', existing_data.get('zoom'))
            center = relayout_data.get('map.center', existing_data.get('center'))

            if zoom is not None and center is not None:
                # Update the existing_data with new zoom and center
                existing_data['zoom'] = zoom
                existing_data['center'] = center

                return existing_data

        # If no user interaction keys are present, prevent updating the store
        raise dash.exceptions.PreventUpdate

    @app.callback(
        [Output({'type': 'filter-button-wine', 'index': ALL}, 'className'),
         Output({'type': 'filter-button-wine', 'index': ALL}, 'style')],
        [Input({'type': 'filter-button-wine', 'index': ALL}, 'n_clicks')],
        [State({'type': 'filter-button-wine', 'index': ALL}, 'id')]
    )
    def update_wine_button_active_state(n_clicks_list, ids):
        if not n_clicks_list:
            raise PreventUpdate
        return update_button_active_state_helper(n_clicks_list, ids, 'wine')

    @app.callback(
        [Output('llm-output-container', 'children'),
         Output('disclaimer-container', 'style'),
         Output('region-name-container', 'children'),
         Output('region-name-container', 'style')],
        Input('wine-map-graph', 'clickData')
    )
    def update_wine_info(clickData):
        return build_wine_info_response(
            click_data=clickData,
            feature_lookup=wine_feature_lookup,
            cache=cache,
            openai_client=openai_client,
            is_request_limit_exceeded=is_request_limit_exceeded,
        )
