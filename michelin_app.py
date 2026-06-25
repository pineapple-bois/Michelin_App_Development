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
from callbacks.guide import register_guide_callbacks
from components.shared import nav_link_class
from utils.appFunctions import (create_michelin_bar_chart, update_button_active_state_helper,
                                plot_single_choropleth_plotly, top_restaurants, plot_demographic_choropleth_plotly,
                                calculate_weighted_mean, plot_demographics_barchart, plot_wine_choropleth_plotly,
                                generate_optimized_prompt)

all_france = DATA.all_france
all_monaco = DATA.all_monaco
region_df = DATA.region_df
department_df = DATA.department_df
arron_df = DATA.arron_df
paris_df = DATA.paris_df
monaco_df = DATA.monaco_df
wine_df = DATA.wine_df
geo_df = DATA.geo_df
star_placeholder = (0.5, 1, 2, 3)
unique_regions = DATA.unique_regions
initial_options = DATA.initial_options
dept_to_code = DATA.dept_to_code
region_to_name = DATA.region_to_name
get_combined_restaurant_data = DATA.get_combined_restaurant_data
get_geo_df = DATA.get_geo_df


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


# Toggle nav menu open/closed
@app.callback(
    Output('navigation-menu', 'className'),
    Input('hamburger-icon', 'n_clicks'),
    State('navigation-menu', 'className'),
    prevent_initial_call=True
)
def toggle_menu_class(n_clicks, current_class):
    if current_class == 'nav-dropdown':
        return 'nav-dropdown visible'
    else:
        return 'nav-dropdown'


@app.callback(
    [Output('home-button', 'className'),
     Output('analysis-button', 'className')],
    Input('url', 'pathname')
)
def update_nav_classes(pathname):
    return nav_link_class(pathname, 'home-button'), nav_link_class(pathname, 'analysis-button')


# -----------------------> "Guide Page"

register_guide_callbacks(app, DATA)


# -----------------------> "Analysis Page"

# REGION content

@app.callback(
    [Output('restaurant-analysis-graph', 'figure'),
     Output('region-map', 'figure')],
    [Input('region-dropdown-analysis', 'value'),
     Input({'type': 'filter-button-analysis', 'index': ALL}, 'n_clicks')]
)
def update_analysis_chart_and_map(selected_regions, star_clicks):
    # Check if "Select All" is chosen
    if 'all' in selected_regions:
        selected_regions = unique_regions  # Reset to all available regions

    if not selected_regions:
        raise PreventUpdate

    # Default to all star levels if none selected
    select_stars = [0.5, 1, 2, 3]

    if star_clicks:
        select_stars = [star_placeholder[i] for i, n in enumerate(star_clicks) if n % 2 == 0]

    filtered_df = region_df[region_df['region'].isin(selected_regions)].copy()
    filtered_df.sort_values('region', inplace=True)

    fig_bar = create_michelin_bar_chart(
        filtered_df,
        select_stars,
        granularity='region',
        title="Selected regions of France."
    )

    map_fig = plot_single_choropleth_plotly(
        df=filtered_df,
        selected_stars=select_stars,
        granularity='region',
        show_labels=False
    )

    return fig_bar, map_fig


@app.callback(
    Output('region-dropdown-analysis', 'value'),
    Input('region-dropdown-analysis', 'value')
)
def handle_select_all(selected_regions):
    # If "Select All" is selected, replace the selection with all regions
    if 'all' in selected_regions:
        return unique_regions  # Return all available regions

    # Otherwise, return the current selection
    return selected_regions


@app.callback(
    [Output({'type': 'filter-button-analysis', 'index': ALL}, 'className'),
     Output({'type': 'filter-button-analysis', 'index': ALL}, 'style')],
    [Input({'type': 'filter-button-analysis', 'index': ALL}, 'n_clicks')],
    [State({'type': 'filter-button-analysis', 'index': ALL}, 'id')]
)
def update_region_button_active_state(n_clicks_list, ids):
    if not n_clicks_list:
        raise PreventUpdate
    return update_button_active_state_helper(n_clicks_list, ids, 'analysis')


# DEPARTMENT content

@app.callback(
    [Output('star-filter-container-department', 'style'),
     Output('department-analysis-graph', 'figure'),
     Output('department-map', 'figure'),
     Output('department-analysis-graph', 'style'),
     Output('department-map', 'style'),
     Output('departments-store', 'data'),
     Output('arrondissement-filter-title', 'children')],
    [Input('department-dropdown-analysis', 'value'),
     Input({'type': 'filter-button-department', 'index': ALL}, 'n_clicks')]
)
def update_department_chart_and_map(selected_region, star_clicks):
    hide_style = {'display': 'none'}
    show_style = {'display': 'inline-block', 'height': '100%', 'width': '100%'}

    if not selected_region:
        empty_fig = go.Figure()
        return hide_style, empty_fig, empty_fig, hide_style, hide_style, [], ""

    arrondissements_title = f"Select a Department within {selected_region}"

    # Default to all star levels if none selected
    select_stars = [0.5, 1, 2, 3]

    if star_clicks:
        select_stars = [star_placeholder[i] for i, n in enumerate(star_clicks) if n % 2 == 0]

    filtered_df = department_df[department_df['region'] == selected_region].copy()
    filtered_df.sort_values('department', inplace=True)

    fig_bar = create_michelin_bar_chart(
        filtered_df,
        select_stars,
        granularity='department',
        title=f"{selected_region}"
    )

    map_fig = plot_single_choropleth_plotly(
        df=filtered_df,
        selected_stars=select_stars,
        granularity='department',
        show_labels=False
    )

    # Extract unique departments and create a list of options for the store
    department_options = [{'label': dept, 'value': dept} for dept in filtered_df['department'].unique()]

    return show_style, fig_bar, map_fig, show_style, show_style, department_options, arrondissements_title


@app.callback(
    [Output({'type': 'filter-button-department', 'index': ALL}, 'className'),
     Output({'type': 'filter-button-department', 'index': ALL}, 'style')],
    [Input({'type': 'filter-button-department', 'index': ALL}, 'n_clicks')],
    [State({'type': 'filter-button-department', 'index': ALL}, 'id')]
)
def update_department_button_active_state(n_clicks_list, ids):
    if not n_clicks_list:
        raise PreventUpdate
    return update_button_active_state_helper(n_clicks_list, ids, 'department')


# ARRONDISSEMENT content

@app.callback(
    Output('arrondissement-content-wrapper', 'className'),
    Input('department-dropdown-analysis', 'value')
)
def toggle_arrondissement_section(selected_region):
    if selected_region:
        return 'visible-section'  # Show the section
    else:
        return 'hidden-section'  # Hide the section


@app.callback(
    [Output('arrondissement-dropdown-analysis', 'options'),
     Output('arrondissement-dropdown-analysis', 'placeholder')],
    Input('departments-store', 'data')
)
def update_arrondissement_dropdown(department_data):
    if department_data:
        return department_data, "Select a Department"
    return [], "Please select a region first"


@app.callback(
[Output('star-filter-container-arrondissement', 'style'),
     Output('arrondissement-analysis-graph', 'figure'),
     Output('arrondissement-map', 'figure'),
     Output('arrondissement-analysis-graph', 'style'),
     Output('arrondissement-map', 'style')],
    [Input('arrondissement-dropdown-analysis', 'value'),
     Input({'type': 'filter-button-arrondissement', 'index': ALL}, 'n_clicks')]
)
def update_arrondissement_chart_and_map(selected_department, star_clicks):
    hide_style = {'display': 'none'}
    show_style = {'display': 'inline-block', 'height': '100%', 'width': '100%'}

    if not selected_department:
        empty_fig = go.Figure()
        return hide_style, empty_fig, empty_fig, hide_style, hide_style

    # Default to all star levels if none selected
    select_stars = [0.5, 1, 2, 3]

    if star_clicks:
        select_stars = [star_placeholder[i] for i, n in enumerate(star_clicks) if n % 2 == 0]

    if selected_department == 'Paris':
        filtered_df = paris_df
    else:
        filtered_df = arron_df[arron_df['department'] == selected_department].copy()
        filtered_df.sort_values('arrondissement', inplace=True)

    fig_bar = create_michelin_bar_chart(
        filtered_df,
        select_stars,
        granularity='arrondissement',
        title=f"{selected_department}"
    )

    map_fig = plot_single_choropleth_plotly(
        df=filtered_df,
        selected_stars=select_stars,
        granularity='arrondissement',
        show_labels=False
    )

    return show_style, fig_bar, map_fig, show_style, show_style


@app.callback(
    [Output({'type': 'filter-button-arrondissement', 'index': ALL}, 'className'),
     Output({'type': 'filter-button-arrondissement', 'index': ALL}, 'style')],
    [Input({'type': 'filter-button-arrondissement', 'index': ALL}, 'n_clicks')],
    [State({'type': 'filter-button-arrondissement', 'index': ALL}, 'id')]
)
def update_demographics_button_active_state(n_clicks_list, ids):
    if not n_clicks_list:
        raise PreventUpdate
    return update_button_active_state_helper(n_clicks_list, ids, 'arrondissement')


# RANKING content

@app.callback(
     [Output('ranking-output', 'children'),
     Output('toggle-show-details', 'n_clicks'),
     Output('toggle-show-details', 'children')], # Reset the click state
    [Input('granularity-dropdown', 'value'),
     Input('star-dropdown-ranking', 'value'),
     Input('ranking-dropdown', 'value'),
     Input('toggle-show-details', 'n_clicks')],
)
def update_ranking_output(granularity, star_rating, top_n, n_clicks):
    # If granularity is not selected, show a message
    if granularity is None:
        return html.Div(
            "Please select a granularity to display rankings.",
            style={
                "font-style": "italic",
                "font-size": "16px",
                "color": "grey",
                "text-align": "center",
                "align-items": "center",  # Vertically center
            }
        ), 0, "Show Restaurant Details"

    display_restaurants = n_clicks % 2 == 1  # Toggle restaurant visibility based on button state

    # Set the button label based on the toggle state
    button_label = "Hide Restaurant Details" if display_restaurants else "Show Restaurant Details"

    # Handle the 'Paris' case explicitly
    if top_n == 1 and granularity == 'department':
        # Focus on Paris for department granularity
        filtered_data = all_france[all_france['department_num'] == '75']  # Only Paris restaurants
    elif top_n == 1 and granularity == 'region':
        # Focus on Île-de-France for region granularity
        filtered_data = all_france[all_france['region'] == 'Île-de-France']  # Only Île-de-France restaurants
    elif top_n == 1 and granularity == 'arrondissement':
        # Focus on Paris arrondissements for 'arrondissement' granularity
        filtered_data = all_france[all_france['department_num'] == '75']  # Only Paris restaurants
        top_n = 5  # Force top_n to be 5 for Paris arrondissements
    else:
        # General case: filter out Île-de-France if not Paris
        filtered_data = all_france[all_france['region'] != 'Île-de-France']
        if granularity == 'department' and top_n in [3, 5]:
            filtered_data = filtered_data[filtered_data['department_num'] != '75']  # Exclude Paris

    # Call the top_restaurants function to get the components
    ranking_components = top_restaurants(filtered_data, granularity, star_rating, top_n, display_restaurants)

    return ranking_components, n_clicks, button_label


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
