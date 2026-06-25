import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
import uuid
from openai import OpenAI
from dash import dcc, html, no_update
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State, ALL
from flask import Flask, session, request, redirect
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix

from app_data import DATA
from app_config import CONFIG
from callbacks.analysis import register_analysis_callbacks
from callbacks.guide import register_guide_callbacks
from callbacks.navigation import register_navigation_callbacks
from utils.appFunctions import (update_button_active_state_helper, plot_demographic_choropleth_plotly,
                                calculate_weighted_mean, plot_demographics_barchart, plot_wine_choropleth_plotly,
                                generate_optimized_prompt)

all_france = DATA.all_france
region_df = DATA.region_df
department_df = DATA.department_df
wine_df = DATA.wine_df
star_placeholder = (0.5, 1, 2, 3)
unique_regions = DATA.unique_regions


# Initialize openai with API key
client = OpenAI(
    api_key=CONFIG.openai_api_key
)

# -----------------> App and server setup

server = Flask(__name__)
server.wsgi_app = ProxyFix(server.wsgi_app, x_proto=1, x_host=1)
server.secret_key = CONFIG.flask_secret_key
app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP,
                          "https://fonts.googleapis.com/css2?family=Kaisei+Decol&family=Libre+Franklin:"
                          "ital,wght@0,100..900;1,100..900&display=swap"],
    external_scripts=['https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.js'],
    server=server)


@server.before_request
def enforce_https_redirect():
    if CONFIG.force_https and not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)


@server.before_request
def ensure_session():
    # Ensure every session has a user_id,
    if 'user_id' not in session:
        # Regular users get a dynamically generated session ID
        session['user_id'] = str(uuid.uuid4())
        session['request_count'] = 0  # Initialize request count for new session


def is_request_limit_exceeded():
    # Request limit for OpenAi API calls
    request_limit = CONFIG.openai_request_limit

    # Check if request_count exists in session
    if 'request_count' not in session:
        session['request_count'] = 0  # Initialize if not present

    session['request_count'] += 1  # Increment request count

    if session['request_count'] > request_limit:
        return True
    return False


# App set up
app.title = 'Gastronomic Guide to France - pineapple-bois'
app.index_string = CONFIG.asset_path("custom_header.html").read_text(encoding="utf-8")
app.layout = html.Div([
    dcc.Store(id='selected-stars', data=[]),
    dcc.Store(id='available-stars', data=[]),  # will populate with star rating by department
    dcc.Store(id='department-centroid-store', data={}),
    dcc.Store(id='paris-arrondissement-centroid', data={}),
    dcc.Store(id='region-demographics-centroid', data={}),
    dcc.Location(id='url', refresh=False),  # Tracks the url
    dash.page_container
])

# Initialize the cache (Maybe Redis or filesystem-based caching for production...?)
cache = Cache(app.server, config=CONFIG.cache_config)

register_navigation_callbacks(app)


# -----------------------> "Guide Page"

register_guide_callbacks(app, DATA)


# -----------------------> "Analysis Page"

register_analysis_callbacks(app, DATA)


# DEMOGRAPHICS content

@app.callback(
    [Output('demographics-dropdown-analysis', 'value'),
     Output('demographics-map-graph', 'figure'),
     Output('demographics-bar-chart-graph', 'figure'),
     Output('demographics-add-remove', 'style'),
     Output('demographics-chart-math', 'style'),
     Output('weighted-mean', 'style'),
     Output('star-filter-demographics', 'style')],
    [Input('category-dropdown-demographics', 'value'),
     Input('granularity-dropdown-demographics', 'value'),
     Input('demographics-dropdown-analysis', 'value'),
     Input('toggle-show-details-demographics', 'n_clicks'),  # Button to toggle restaurants
     Input({'type': 'filter-button-demographics', 'index': ALL}, 'n_clicks')],
    [State('map-view-store-demo', 'data')]
)
def update_demographics_map(selected_metric, selected_dropdown, selected_regions, n_clicks_rest, n_clicks_stars,
                            mapview_data):
    # Handle "Select All"
    if 'all' in selected_regions:
        selected_regions = unique_regions  # Select all regions if "Select All" is chosen

    # Ensure `selected_regions` is not None
    if not selected_regions:
        selected_regions = unique_regions  # Default to all regions when none are selected

    # Set granularity based on whether a region is selected in the dropdown
    if selected_dropdown != 'All France':
        selected_granularity = 'department'  # If a region is selected, use department granularity
        region_selector_style = {'visibility': 'hidden'}  # Hide the region selector
    else:
        selected_granularity = 'region'  # Default granularity is region
        region_selector_style = {'visibility': 'visible'}  # Show the region selector

    if selected_granularity == 'region':
        df = region_df.sort_values('region').copy()  # Use region-level data
        df = df[df['region'].isin(selected_regions)].copy()
        filtered_restaurants = all_france[all_france['region'].isin(selected_regions)].copy()
    else:
        df = department_df.copy()
        # If a region is selected in the dropdown, filter to that region
        if selected_dropdown != 'All France':
            df = df[df['region'] == selected_dropdown].copy()
            filtered_restaurants = all_france.copy()

    # Show or hide the star filter based on button press
    if n_clicks_rest % 2 == 1:
        star_filter_style = {'display': 'block'}
        show_restaurants = True
    else:
        star_filter_style = {'display': 'none'}
        show_restaurants = False

    stars = [1, 2, 3]
    if n_clicks_stars:
        selected_stars = [stars[i] for i, n in enumerate(n_clicks_stars) if n % 2 == 0]  # Only keep active stars
    else:
        selected_stars = stars

    # **Check if any restaurants exist for the selected stars in the region**
    available_stars = filtered_restaurants['stars'].unique().tolist()
    selected_stars = [star for star in selected_stars if star in available_stars]

    # **Handle the case where no stars are selected**
    if not selected_stars:
        show_restaurants = False  # No stars to show
        filtered_restaurants = filtered_restaurants.iloc[0:0]  # Empty DataFrame to avoid plotting

    # If no metric is selected, just show map boundaries without data coloring
    if not selected_metric:
        fig_map = plot_demographic_choropleth_plotly(
            df,
            filtered_restaurants,
            metric=None,  # Pass None to indicate no metric is selected
            granularity=selected_granularity,
            show_labels=False,
            cmap='Blues',
            restaurants=show_restaurants,  # Show restaurants based on button press
            selected_stars=selected_stars,  # Filter based on selected stars
            zoom_data=mapview_data
        )
        empty_fig = go.Figure()  # Return empty figure for bar chart
        return (selected_regions, fig_map, empty_fig, region_selector_style,
                {'display': 'none'}, {'display': 'none'}, star_filter_style)

    if selected_granularity == 'region':
        dataframe = region_df
    else:
        dataframe = department_df

    # List of metrics to exclude from weighted mean
    excluded_metrics = ['municipal_population', 'population_density(inhabitants/sq_km)']

    # Only calculate weighted mean if the metric is not in the excluded list
    if selected_metric not in excluded_metrics:
        weighted_mean = calculate_weighted_mean(dataframe, selected_metric, weight_column='municipal_population')
        weighted_mean_style = {'display': 'block'}  # Show the weighted mean section
    else:
        weighted_mean = None  # No weighted mean calculation
        weighted_mean_style = {'display': 'none'}  # Hide the weighted mean section

    fig_map = plot_demographic_choropleth_plotly(
        df,
        filtered_restaurants,
        selected_metric,
        granularity=selected_granularity,
        show_labels=False,
        cmap='Blues',
        restaurants=show_restaurants,
        selected_stars=selected_stars,
        zoom_data=mapview_data
    )

    fig_bar = plot_demographics_barchart(
        df,
        selected_metric,
        granularity=selected_granularity,
        weighted_mean=weighted_mean
    )

    return (selected_regions, fig_map, fig_bar, region_selector_style,
            {'display': 'block'}, weighted_mean_style, star_filter_style)


@app.callback(
    Output('map-view-store-demo', 'data'),
    [Input('demographics-map-graph', 'relayoutData'),
     Input('granularity-dropdown-demographics', 'value')],
    [State('map-view-store-demo', 'data')]
)
def store_map_view_demo(relayout_data, region_dropdown, existing_data):
    # Initialize existing_data if it's None
    if existing_data is None:
        existing_data = {}

    # Reset zoom data when region or department changes
    ctx = dash.callback_context
    triggered_input = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    if triggered_input == 'granularity-dropdown-demographics':
        return {}  # Clear zoom data when region dropdown changes

    # If relayoutData is None or empty, do not update the store
    if not relayout_data:
        raise dash.exceptions.PreventUpdate

    # Define the keys that indicate a user interaction
    user_interaction_keys = {'map.zoom', 'map.center'}

    # Check if relayoutData contains any of the user interaction keys
    if user_interaction_keys.intersection(relayout_data.keys()):
        zoom = relayout_data.get('map.zoom', existing_data.get('zoom'))
        center = relayout_data.get('map.center', existing_data.get('center'))

        if zoom and center:
            existing_data['zoom'] = zoom
            existing_data['center'] = center
            return existing_data

    raise dash.exceptions.PreventUpdate


@app.callback(
    [Output({'type': 'filter-button-demographics', 'index': ALL}, 'className'),
     Output({'type': 'filter-button-demographics', 'index': ALL}, 'style')],
    [Input({'type': 'filter-button-demographics', 'index': ALL}, 'n_clicks')],
    [State({'type': 'filter-button-demographics', 'index': ALL}, 'id')]
)
def update_demographics_button_active_state(n_clicks_list, ids):
    if not n_clicks_list:
        raise PreventUpdate
    return update_button_active_state_helper(n_clicks_list, ids, 'demographics')


# WINE content

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
        response = client.chat.completions.create(
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


if __name__ == '__main__':
    app.run_server(debug=CONFIG.debug)
