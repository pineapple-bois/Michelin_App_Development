import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
import os
import uuid
from openai import OpenAI
from dotenv import load_dotenv
from dash import dcc, html, callback_context, no_update
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State, ALL
from flask import Flask, session, request, redirect
from flask_caching import Cache

from layouts.layout_main import get_main_layout, color_map, star_filter_section
from layouts.layout_analysis import get_analysis_layout
from layouts.layout_404 import get_404_layout

from utils.locationMatcher import LocationMatcher
from utils.appFunctions import (plot_regional_outlines, plot_department_outlines, plot_interactive_department,
                                plot_paris_arrondissement, plot_arrondissement_outlines, default_map_figure,
                                get_restaurant_details, create_michelin_bar_chart, update_button_active_state_helper,
                                plot_single_choropleth_plotly, top_restaurants, plot_demographic_choropleth_plotly,
                                calculate_weighted_mean, plot_demographics_barchart, plot_wine_choropleth_plotly,
                                generate_optimized_prompt)

# Load restaurant data
all_france = pd.read_csv("assets/Data/all_restaurants(arrondissements).csv")
# Load Monaco data (department_num is inferred 'int' by Pandas)
all_monaco = pd.read_csv("assets/Data/monaco_restaurants.csv", dtype={'department_num': str})

# Load regional GeoJSON data
region_df = gpd.read_file("assets/Data/region_restaurants.geojson")
# Load departmental GeoJSON data
department_df = gpd.read_file("assets/Data/department_restaurants.geojson")
# Load arrondissement GeoJSON data
arron_df = gpd.read_file("assets/Data/arrondissement_restaurants.geojson")
# Load Paris GeoJSON data
paris_df = gpd.read_file("assets/Data/paris_restaurants.geojson")
# Load Monaco GeoJSON data (departmental aggregation)
monaco_df = gpd.read_file("assets/Data/monaco_restaurants.geojson")
# Load wine GeoJSON data
wine_df = gpd.read_file("assets/Data/wine_regions_cleaned.geojson")


# Create France + Monaco for guide
def get_combined_restaurant_data(include_monaco=False):
    if include_monaco:
        return pd.concat([all_france, all_monaco], ignore_index=True)
    return all_france


# Create Departmental France + Monaco geojson for guide
def get_geo_df(include_monaco=False):
    combined = all_france if not include_monaco else pd.concat([all_france, all_monaco], ignore_index=True)
    dept_codes = combined['department_num'].unique()

    if not include_monaco:
        return department_df[department_df['code'].isin(dept_codes)]

    # Concatenate and cast to GeoDataFrame
    merged_df = pd.concat([department_df, monaco_df], ignore_index=True)
    merged_gdf = gpd.GeoDataFrame(merged_df, geometry='geometry', crs=department_df.crs)
    return merged_gdf


# Get unique department numbers with restaurants
departments_with_restaurants = all_france['department_num'].unique()
# Filter geo_df
geo_df = department_df[department_df['code'].isin(departments_with_restaurants)]
star_placeholder = (0.25, 0.5, 1, 2, 3)


# Use geo_df to get unique regions and departments for the initial dropdowns
unique_regions = sorted(geo_df['region'].unique())
initial_departments = geo_df[geo_df['region'] == unique_regions[0]][['department', 'code']].drop_duplicates().to_dict('records')
initial_options = [{
    'label': f"{dept['department']} ({dept['code']})",
    'value': dept['department']
} for dept in initial_departments]
dept_to_code = geo_df.drop_duplicates(subset='department').set_index('department')['code'].to_dict()
region_to_name = {region: region for region in geo_df['region'].unique()}


load_dotenv()
# Initialize openai with API key
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# -----------------> App and server setup

server = Flask(__name__)
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP,
                          "https://fonts.googleapis.com/css2?family=Kaisei+Decol&family=Libre+Franklin:"
                          "ital,wght@0,100..900;1,100..900&display=swap"],
    external_scripts=['https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.js'],
    server=server)


# Comment out to launch locally (development)
@server.before_request
def before_request():
    if not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)


@server.before_request
def before_request():
    # Ensure every session has a user_id,
    if 'user_id' not in session:
        # Regular users get a dynamically generated session ID
        session['user_id'] = str(uuid.uuid4())
        session['request_count'] = 0  # Initialize request count for new session


def is_request_limit_exceeded():
    # Request limit for OpenAi API calls
    REQUEST_LIMIT = 5

    # Check if request_count exists in session
    if 'request_count' not in session:
        session['request_count'] = 0  # Initialize if not present

    session['request_count'] += 1  # Increment request count

    if session['request_count'] > REQUEST_LIMIT:
        return True
    return False


# Retrieve the Flask secret key from .env, or assign a default one
secret_key = os.getenv('FLASK_SECRET_KEY', str(uuid.uuid4()))  # Generate a random key if none is found
server.secret_key = secret_key  # Assign secret key for sessions


# App set up
app.title = 'Gastronomic Guide to France - pineapple-bois'
app.index_string = open('assets/custom_header.html', 'r').read()
app.layout = html.Div([
    dcc.Store(id='selected-stars', data=[]),
    dcc.Store(id='available-stars', data=[]),  # will populate with star rating by department
    dcc.Store(id='department-centroid-store', data={}),
    dcc.Store(id='paris-arrondissement-centroid', data={}),
    dcc.Store(id='region-demographics-centroid', data={}),
    dcc.Location(id='url', refresh=False),  # Tracks the url
    html.Div(id='page-content', children=get_main_layout())  # Set initial content
])

# Initialize the cache (Maybe Redis or filesystem-based caching for production...?)
cache = Cache(app.server, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 3600  # Cache timeout in seconds (1 hour)
})


# Define callback to handle page navigation
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/analysis':
        return get_analysis_layout()
    elif pathname == '/home':
        return get_main_layout()
    else:
        return get_main_layout() if pathname == '/' else get_404_layout()


# Callback to update the button classes based on the current page
@app.callback(
    [Output('home-button', 'className'),
     Output('analysis-button', 'className')],
    [Input('url', 'pathname')]
)
def update_button_classes(pathname):
    # Define active and inactive classes
    active_class = 'header-button active'
    inactive_class = 'header-button inactive'

    # Check the current URL path and apply the active class to the corresponding button
    if pathname == '/' or pathname == '/home':
        return active_class, inactive_class  # Home button active
    elif pathname == '/analysis':
        return inactive_class, active_class  # Analysis button active
    else:
        return inactive_class, inactive_class  # Default case, both inactive


# -----------------------> "Guide Page"


# Get rid of the 'hand' when hovering over restaurants
app.clientside_callback(
    """
    function(hoverData) {
        if (hoverData) {
            document.getElementById('map-display').style.cursor = 'pointer';
        } else {
            document.getElementById('map-display').style.cursor = 'default';
        }
    }
    """,
    Output('dummy-output', 'children'),
    Input('map-display', 'hoverData')
)


"""New version with Enter key functionality"""
@app.callback(
    [Output('info-collapse', 'is_open'),
     Output('city-input-mainpage', 'value'),
     Output('matched-city-output-mainpage', 'children'),
     Output('matched-city-output-mainpage', 'className'),
     Output('region-dropdown', 'value'),
     Output('department-dropdown', 'value')],
    [Input('info-toggle-button', 'n_clicks'),
     Input('submit-city-button-mainpage', 'n_clicks'),
     Input('clear-city-button-mainpage', 'n_clicks'),
     Input('city-input-mainpage', 'n_submit')],  # Add `n_submit` for Enter key
    [State('info-collapse', 'is_open'),
     State('city-input-mainpage', 'value')]
)
def toggle_collapse_and_handle_search(n_info_clicks, n_submit_clicks, n_clear_clicks, n_submit, is_open, city_input):
    """
    Callback function to manage the information collapse section and handle city search functionality.

    This function handles user interactions:
    - Toggling the information collapse visibility with the info button.
    - Processing city search via submit button or pressing Enter.
    - Clearing input and resetting outputs with the clear button.
    """
    # Ensure clicks are initialized
    n_info_clicks = n_info_clicks or 0
    n_submit_clicks = n_submit_clicks or 0
    n_clear_clicks = n_clear_clicks or 0
    n_submit = n_submit or 0

    # Collapse logic: only triggered by the toggle button
    ctx = dash.callback_context
    if ctx.triggered[0]['prop_id'] == 'info-toggle-button.n_clicks':
        if is_open:
            # Collapse: clear input and match result
            return False, '', html.Div([html.P("", className='default-message')]), \
                   'city-match-output-container-mainpage', dash.no_update, dash.no_update
        else:
            # Expand the collapse without resetting input/output
            return (True, dash.no_update, dash.no_update, 'city-match-output-container-mainpage',
                    dash.no_update, dash.no_update)

    # Handle clearing the input and resetting the output when clear is clicked
    if ctx.triggered[0]['prop_id'] == 'clear-city-button-mainpage.n_clicks':
        return dash.no_update, '', html.Div([html.P("", className='default-message')]), \
               'city-match-output-container-mainpage', dash.no_update, dash.no_update

    # Handle the search functionality triggered by the submit button or Enter key
    if ctx.triggered[0]['prop_id'] in {'submit-city-button-mainpage.n_clicks', 'city-input-mainpage.n_submit'}:
        if not city_input:
            # Fallback for invalid or empty input
            return dash.no_update, '', html.Div([html.P("Enter a valid location.", className='default-message')]), \
                'city-match-output-container-mainpage', dash.no_update, dash.no_update

        # Add Monaco to dataset
        plus_monaco = get_combined_restaurant_data(include_monaco=True)
        matcher = LocationMatcher(plus_monaco)
        result = matcher.find_region_department(city_input)
        if isinstance(result, dict):
            # Valid result, update outputs
            city_details = [
                html.P(
                    f"Match:  {result.get('Matched Location', 'Unknown')},  "
                    f"Region:  {result.get('Region', 'Unknown')},  "
                    f"Department:  {result.get('Department', 'Unknown')}",
                    className='match-details'
                ),
            ]
            return dash.no_update, dash.no_update, html.Div(city_details, className='city-match-container'), \
                'city-match-output-container-mainpage visible', result.get('Region'), result.get('Department')
        else:
            # No match found
            return dash.no_update, dash.no_update, html.Div([
                html.P(f"No match found. '{city_input}' is not represented in the Michelin Guide",
                       className='no-match-message')
            ]), 'city-match-output-container-mainpage visible', dash.no_update, dash.no_update

    # Default to no update if no actions were triggered
    return (dash.no_update, dash.no_update, dash.no_update, 'city-match-output-container-mainpage',
            dash.no_update, dash.no_update)


@app.callback(
        [Output('department-dropdown', 'options'),
        Output('star-filter', 'children'),
        Output('star-filter', 'style'),
        Output('available-stars', 'data')],
       [Input('region-dropdown', 'value'),
        Input('department-dropdown', 'value'),
        Input('arrondissement-dropdown', 'value')]
)
def update_department_and_filters(selected_region, selected_department, selected_arrondissement):
    # Use dynamic geo_df based on region
    geo_df_dynamic = get_geo_df(include_monaco=(selected_region == "Provence-Alpes-Côte d'Azur"))

    # Fetch department options based on the selected region.
    departments = geo_df_dynamic[geo_df_dynamic['region'] == selected_region][['department', 'code']].drop_duplicates().to_dict('records')
    department_options = [{'label': f"{dept['department']} ({dept['code']})", 'value': dept['department']} for dept in departments]

    if not selected_department:
        # No department selected, hide star filter and clear buttons
        return department_options, star_filter_section().children, {'display': 'none'}, []

    # Handle the case when the department is Paris
    if selected_department == 'Paris':
        # Determine available stars based on arrondissement selection
        if selected_arrondissement and selected_arrondissement != 'all':
            # Filter all_france for the selected arrondissement
            filtered_data = all_france[
                (all_france['department'] == 'Paris') &
                (all_france['arrondissement'] == selected_arrondissement)
            ]
        else:
            # No specific arrondissement selected, use all of Paris
            filtered_data = all_france[
                (all_france['department'] == 'Paris')
            ]

        # Determine available stars from the filtered data
        available_stars = sorted(filtered_data['stars'].unique(), reverse=True)

        # Only show the filter if there are stars available
        if available_stars:
            star_filter = star_filter_section(available_stars)
            return department_options, star_filter.children, {'display': 'block'}, available_stars
        else:
            return department_options, star_filter_section().children, {'display': 'none'}, []

    else:
        # For departments other than Paris
        # Fetch the row for the selected department
        department_row = geo_df_dynamic[geo_df_dynamic['department'] == selected_department]

        if department_row.empty:
            # Handle the case where the department is not found
            return department_options, star_filter_section().children, {'display': 'none'}, []

        department_row = department_row.iloc[0]

        # Determine which star ratings are present in the department
        available_stars = []
        for star_level in [3, 2, 1]:  # Ensure all levels are checked
            if department_row[f'{int(star_level)}_star'] > 0:
                available_stars.append(star_level)
        if department_row['bib_gourmand'] > 0:
            available_stars.append(0.5)
        if department_row['selected'] > 0:
            available_stars.append(0.25)

        # Only show the filter if there are stars available
        if available_stars:
            star_filter = star_filter_section(available_stars)
            return department_options, star_filter.children, {'display': 'block'}, available_stars
        else:
            return department_options, star_filter_section().children, {'display': 'none'}, []


@app.callback(
    [Output({'type': 'filter-button-mainpage', 'index': ALL}, 'className'),
     Output({'type': 'filter-button-mainpage', 'index': ALL}, 'style'),
     Output('selected-stars', 'data'),
     Output('toggle-selected-btn', 'className'),
     Output('toggle-selected-btn', 'style')],
    [Input({'type': 'filter-button-mainpage', 'index': ALL}, 'n_clicks'),
     Input('toggle-selected-btn', 'n_clicks')],
    [State({'type': 'filter-button-mainpage', 'index': ALL}, 'id'),
     State('selected-stars', 'data'),
     State('available-stars', 'data')]
)
def update_button_active_state(n_clicks_list, toggle_selected_clicks, ids,
                               current_stars, available_stars):
    # Handle cases where not all data is available, especially at initialization
    if (not n_clicks_list or not available_stars or len(available_stars) == 0) and available_stars != [0.25]:
        raise PreventUpdate

    # Initialize empty lists to store class names and styles
    class_names = []
    styles = []

    # Initialize the new list of active stars from current state filtered by available stars
    new_stars = [star for star in current_stars if star in available_stars and star != 0.25]

    for i, button_id in enumerate(ids):
        index = button_id['index']
        n_clicks = n_clicks_list[i] if i < len(n_clicks_list) else 0  # fallback to 0

        if index not in available_stars:
            # Still return something so Dash output lengths match
            class_names.append("me-1 star-button-filter-button-mainpage inactive")
            styles.append({
                "display": "inline-block",
                "width": "100%",
                "backgroundColor": "#cccccc"
            })
            continue

        # Determine if the button is active (even number of clicks means active)
        is_active = n_clicks % 2 == 0

        if is_active:
            if index not in new_stars:
                new_stars.append(index)
            background_color = color_map[index]
        else:
            if index in new_stars:
                new_stars.remove(index)
            background_color = (
                f"rgba({int(color_map[index][1:3], 16)},"
                f"{int(color_map[index][3:5], 16)},"
                f"{int(color_map[index][5:7], 16)},0.6)"
            )

        class_name = f"me-1 star-button-{button_id['type']}" + (" active" if is_active else "")
        color_style = {
            "display": "inline-block",
            "width": "100%",
            "backgroundColor": background_color,
        }
        class_names.append(class_name)
        styles.append(color_style)

    # ---- Toggle Selected Button Logic ----
    selected_active = toggle_selected_clicks % 2 == 0
    if selected_active and 0.25 not in new_stars:
        new_stars.append(0.25)
    elif not selected_active and 0.25 in new_stars:
        new_stars.remove(0.25)

    selected_class = "selected-toggle-button" + (" active" if selected_active else " inactive")
    # Compute display: show the toggle button only if 0.25 is an available star rating
    toggle_display = "block" if 0.25 in available_stars else "none"
    selected_style = {
        "display": toggle_display,
    }

    return class_names, styles, new_stars, selected_class, selected_style


@app.callback(
    Output('restaurant-details', 'children'),
    [Input('map-display', 'clickData'),
     Input('department-dropdown', 'value'),
     Input('region-dropdown', 'value'),
     Input('selected-stars', 'data')],
)
def update_sidebar(clickData, selected_department, selected_region, selected_stars):
    ctx = dash.callback_context

    # Placeholder messages
    restaurant_placeholder = html.Div(
        "Select a restaurant on the map to see more details",
        className='placeholder-text'
    )

    select_stars_placeholder = html.Div(
        "Select a star rating to see restaurants.",
        className='placeholder-text',
        style={'color': 'red'}
    )

    select_department_placeholder = html.Div(
        "Select a department to view restaurants.",
        className='placeholder-text'
    )

    # If no department is selected, prompt the user
    if not selected_department:
        return select_department_placeholder

    # If no stars are selected, prompt the user to select stars
    if not selected_stars:
        return select_stars_placeholder

    include_monaco = selected_region == "Provence-Alpes-Côte d'Azur"
    combined_data = get_combined_restaurant_data(include_monaco)

    # Determine which input triggered the callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Handle map clicks
    if triggered_id == 'map-display':
        if clickData and 'points' in clickData and len(clickData['points']) > 0:
            point = clickData['points'][0]
            restaurant_index = point.get('meta') or point.get('customdata')

            if restaurant_index in combined_data.index:
                restaurant_info = combined_data.loc[restaurant_index]
                # Check if the restaurant's star rating is in selected_stars
                if restaurant_info['stars'] in selected_stars:
                    return get_restaurant_details(restaurant_info)
        return restaurant_placeholder

    # For any other triggers, clear the restaurant details
    return restaurant_placeholder


@app.callback(
    [Output('arrondissement-dropdown-container', 'className'),
     Output('arrondissement-dropdown', 'options'),
     Output('arrondissement-dropdown', 'value')],
    [Input('department-dropdown', 'value')]
)
def update_arrondissement_visibility(selected_department):
    if selected_department == 'Paris':
        # Fetch arrondissements from paris_df
        arrondissement_list = paris_df['arrondissement'].unique()
        arrondissement_options = [{'label': arr, 'value': arr} for arr in arrondissement_list]
        # Add 'All Arrondissements' option at the top
        arrondissement_options.insert(0, {'label': 'All Arrondissements', 'value': 'all'})
        return 'visible-paris-section', arrondissement_options, 'all'
    else:
        # Hide the arrondissement section by setting class to 'hidden-section'
        return 'hidden-paris-section', [], None


@app.callback(
    Output('map-display', 'figure'),
    [Input('department-dropdown', 'value'),
     Input('region-dropdown', 'value'),
     Input('selected-stars', 'data'),
     Input('arrondissement-dropdown', 'value')],
    [State('map-view-store-mainpage', 'data'),
     State('department-centroid-store', 'data'),
     State('paris-arrondissement-centroid', 'data')]
)
def update_map(selected_department, selected_region, selected_stars, paris_arrondissement,
               mapview_data, dept_viewdata, arron_viewdata):
    ctx = callback_context
    triggered_id, _ = ctx.triggered[0]['prop_id'].split('.') if ctx.triggered else (None, None)

    # Use combined restaurant + geo data for PACA
    include_monaco = selected_region == "Provence-Alpes-Côte d'Azur"
    restaurant_data = get_combined_restaurant_data(include_monaco=include_monaco)
    geo_df_dynamic = get_geo_df(include_monaco=include_monaco)
    dept_to_code_dynamic = geo_df_dynamic.drop_duplicates(subset='department').set_index('department')['code'].to_dict()

    # Set view_data once, then reuse it
    view_data = mapview_data if mapview_data else dept_viewdata

    # Handle Paris-specific logic first
    if selected_department == 'Paris':
        department_code = dept_to_code.get('Paris')

        # Handle arrondissement case
        if paris_arrondissement and paris_arrondissement != 'all':
            view_data = mapview_data if mapview_data else arron_viewdata
            if triggered_id == 'selected-stars':
                # Plot selected arrondissement with stars
                if selected_stars:
                    return plot_paris_arrondissement(restaurant_data, paris_df, paris_arrondissement, selected_stars, view_data)
                return plot_arrondissement_outlines(paris_df, paris_arrondissement, view_data)

        # Plot entire Paris department when no arrondissement selected
        view_data = mapview_data if mapview_data else dept_viewdata
        if triggered_id == 'selected-stars':
            if selected_stars:
                return plot_interactive_department(restaurant_data, geo_df_dynamic, department_code, selected_stars, view_data)
            return plot_department_outlines(geo_df_dynamic, department_code, view_data)

    # Case 1: Department selected (non-Paris)
    if triggered_id == 'department-dropdown' and selected_department:
        department_code = dept_to_code_dynamic.get(selected_department)
        return plot_department_outlines(geo_df_dynamic, department_code, view_data)

    # Case 2: Handle stars selection
    if triggered_id == 'selected-stars' and selected_department:
        department_code = dept_to_code_dynamic.get(selected_department)
        if selected_stars:
            return plot_interactive_department(restaurant_data, geo_df_dynamic, department_code, selected_stars, view_data)
        else:
            return plot_department_outlines(geo_df_dynamic, department_code, view_data)

    # Case 3: Handle region selection
    if selected_region or triggered_id == 'region-dropdown':
        region_name = region_to_name.get(selected_region)
        if region_name:
            return plot_regional_outlines(region_df, region_name)

    # Default fallback case: Show entire country map if no specific input
    return default_map_figure()


@app.callback(
Output('department-centroid-store', 'data'),
[Input('department-dropdown', 'value'),
 Input('region-dropdown', 'value')]
)
def calculate_department_centroid(selected_department, selected_region):
    if not selected_department:
        return {}

    # Dynamically include Monaco for PACA
    include_monaco = selected_region == "Provence-Alpes-Côte d'Azur"
    geo_df_dynamic = get_geo_df(include_monaco=include_monaco)

    # Generate dept_to_code dynamically from the active geo_df
    dept_to_code_dynamic = geo_df_dynamic.drop_duplicates(subset='department').set_index('department')[
        'code'].to_dict()
    department_code = dept_to_code_dynamic.get(selected_department)

    if not department_code:
        return {}

    filtered_geo = geo_df_dynamic[geo_df_dynamic['code'] == str(department_code)]
    if filtered_geo.empty:
        return {}

    specific_geometry = filtered_geo['geometry'].iloc[0]
    centroid = specific_geometry.centroid

    # Adjust zoom level
    if department_code == '75':
        zoom_level = 11  # Paris
    elif department_code == '98':
        zoom_level = 13.5  # Monaco
    else:
        zoom_level = 8

    return {
        'zoom': zoom_level,
        'center': {
            'lat': centroid.y,
            'lon': centroid.x
        }
    }


@app.callback(
    Output('paris-arrondissement-centroid', 'data'),
    [Input('arrondissement-dropdown', 'value')]
)
def calculate_arrondissement_centroid(selected_arrondissement):
    if not selected_arrondissement:
        return {}

    # Find the geometry for the selected arrondissement
    filtered_geo = paris_df[paris_df['arrondissement'] == selected_arrondissement]

    if filtered_geo.empty:
        return {}  # Return empty if the arrondissement is not found

    # Calculate the centroid of the selected arrondissement's geometry
    specific_geometry = filtered_geo['geometry'].iloc[0]
    centroid = specific_geometry.centroid

    # Set a zoom level for Paris arrondissements
    zoom_level = 13

    # Create the dictionary to store
    stored_data = {
        'zoom': zoom_level,
        'center': {
            'lat': centroid.y,
            'lon': centroid.x
        }
    }

    return stored_data


@app.callback(
    Output('map-view-store-mainpage', 'data'),
    [Input('map-display', 'relayoutData'),
     Input('region-dropdown', 'value'),
     Input('department-dropdown', 'value'),
     Input('arrondissement-dropdown', 'value')],
    [State('map-view-store-mainpage', 'data')]
)
def store_map_view_mainpage(relayout_data, selected_region, selected_department, selected_arrondissement, existing_data):
    # Initialize existing_data if it's None
    if existing_data is None:
        existing_data = {}

    # Reset zoom data when region or department changes
    ctx = dash.callback_context
    triggered_input = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    if triggered_input in ['region-dropdown', 'department-dropdown', 'arrondissement-dropdown']:
        return {}

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
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=400
        )
        content = response.choices[0].message.content.strip()

        # Cache the response for future requests
        cache.set(cache_key, {'content': content, 'color': region_color})

        region_name_content = html.H3(wine_region, style={'color': region_color})
        return dcc.Markdown(content), {"display": "block"}, region_name_content, {"display": "block"}

    except Exception as e:
        return f"Error fetching region details: {str(e)}", {"display": "none"}, no_update, {"display": "none"}


# For local development, debug=True
if __name__ == '__main__':
    app.run_server(debug=False)
