import dash
from dash import dcc, html, no_update
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate
from flask import session

from app.utils.star_filters import update_button_active_state_helper
from app.utils.wine_figures import plot_wine_choropleth_plotly
from app.utils.wine_prompts import generate_optimized_prompt


def register_wine_callbacks(app, data, config, cache, openai_client):
    all_france = data.all_france
    region_df = data.region_df
    department_df = data.department_df
    wine_df = data.wine_df

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
        [Output('wine-map-graph', 'figure'),
         Output('wine-region-curve-numbers', 'data'),
         Output('star-filter-container-wine', 'style')],
        [Input('granularity-dropdown-wine', 'value'),
         Input('toggle-show-details-wine', 'n_clicks'),
         Input({'type': 'filter-button-wine', 'index': ALL}, 'n_clicks')],
         [State('map-view-store', 'data')]
    )
    def update_wine_map(outline_type, n_clicks_rest, n_clicks_stars, map_view_data):
        # Ensure zoom_data is a dictionary
        if map_view_data is None:
            map_view_data = {}

        # Determine if restaurants should be shown based on button press
        show_restaurants = n_clicks_rest % 2 == 1  # Odd clicks mean show restaurants

        # Determine visibility of star-filter-container based on the button press
        filter_style = {'width': '30%', 'display': 'block'} if show_restaurants else {'width': '30%', 'display': 'none'}

        # Star selection based on button clicks
        stars = [1, 2, 3]
        if n_clicks_stars:
            selected_stars = [stars[i] for i, n in enumerate(n_clicks_stars) if n % 2 == 0]  # Only active stars
        else:
            selected_stars = stars

        if outline_type == 'region':
            df = region_df
        elif outline_type == 'department':
            df = department_df
        else:
            df = None  # No outlines if `outline_type` is None

        fig, wine_region_curve_numbers = plot_wine_choropleth_plotly(
            df=df,
            wine_df=wine_df,
            all_france=all_france,
            outline_type=outline_type,
            show_restaurants=show_restaurants,
            selected_stars=selected_stars,
            zoom_data=map_view_data
        )

        return fig, wine_region_curve_numbers, filter_style

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
        Input('wine-map-graph', 'clickData'),
        State('wine-region-curve-numbers', 'data')
    )
    @cache.memoize(timeout=3600)  # Cache this function's output for 1 hour
    def update_wine_info(clickData, wine_region_curve_numbers):
        if not clickData:
            return "Click on a wine region to get more information.", {"display": "none"}, no_update, {"display": "none"}

        try:
            curve_number = clickData['points'][0]['curveNumber']
            if curve_number not in wine_region_curve_numbers:
                return "Please click on a wine region, not a restaurant.", {"display": "none"}, no_update, {"display": "none"}

            wine_region = wine_df.iloc[wine_region_curve_numbers.index(curve_number)]["region"]

        except (KeyError, IndexError):
            return "Could not retrieve region information.", {"display": "none"}, no_update, {"display": "none"}

        # Check if the response is already cached
        cache_key = f"wine_info_{wine_region}"
        cached_content = cache.get(cache_key)
        if cached_content:
            region_name_content = html.H3(wine_region, style={'color': cached_content['color']})
            print(f"Cached Information retrieved for {wine_region}")
            return dcc.Markdown(cached_content['content']), {"display": "block"}, region_name_content, {"display": "block"}

        # Check if the user has exceeded their request limit
        if is_request_limit_exceeded():
            error_message = "You have reached the maximum number of requests."
            styled_error = html.Div(error_message, style={"color": "red", "font-weight": "bold", "text-align": "center"})
            return styled_error, {"display": "none"}, no_update, {"display": "none"}

        try:
            region_color = wine_df[wine_df['region'] == wine_region]['colour'].values[0]
        except IndexError:
            region_color = 'black'

        prompt = generate_optimized_prompt(wine_region)
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user","content": prompt}],
                max_tokens=400
            )
            content = response.choices[0].message.content.strip()

            # Cache the response for future requests
            cache.set(cache_key, {'content': content, 'color': region_color})

            region_name_content = html.H3(wine_region, style={'color': region_color})
            return dcc.Markdown(content), {"display": "block"}, region_name_content, {"display": "block"}

        except Exception as e:
            return f"Error fetching region details: {str(e)}", {"display": "none"}, no_update, {"display": "none"}
