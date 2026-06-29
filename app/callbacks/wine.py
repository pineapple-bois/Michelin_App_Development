import dash
from dash import dcc, html, no_update
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate
from flask import session

from app.utils.star_filters import update_button_active_state_helper
from app.utils.wine_figures import plot_wine_choropleth_plotly
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
        return "Please click on a wine appellation.", {"display": "none"}, no_update, {"display": "none"}

    wine_region = wine_feature["region"]

    cache_key = f"wine_info_{wine_region}"
    cached_content = cache.get(cache_key)
    if cached_content:
        region_name_content = html.H3(wine_region, style={'color': cached_content['color']})
        print(f"Cached Information retrieved for {wine_region}")
        return dcc.Markdown(cached_content['content']), {"display": "block"}, region_name_content, {"display": "block"}

    if is_request_limit_exceeded():
        error_message = "You have reached the maximum number of requests."
        styled_error = html.Div(error_message, style={"color": "red", "font-weight": "bold", "text-align": "center"})
        return styled_error, {"display": "none"}, no_update, {"display": "none"}

    region_color = wine_feature["colour"]

    prompt = prompt_builder(wine_region)
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
    wine_df = data.wine_df
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
