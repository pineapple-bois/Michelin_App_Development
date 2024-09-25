import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
import dash
import dash_bootstrap_components as dbc
import os
import uuid
from openai import OpenAI
from dotenv import load_dotenv
from dash import dcc, html, callback_context, no_update
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State, MATCH, ALL
from flask import Flask, redirect, request, session
from flask_caching import Cache

from layouts.layout_main import get_main_layout, color_map, star_filter_row, star_filter_section
from layouts.layout_analysis import get_analysis_layout
from layouts.layout_404 import get_404_layout

from locationMatcher import LocationMatcher
from appFunctions import (plot_regional_outlines, plot_department_outlines, plot_interactive_department,
                          get_restaurant_details, create_michelin_bar_chart, update_button_active_state_helper,
                          plot_single_choropleth_plotly, top_restaurants, plot_demographic_choropleth_plotly,
                          calculate_weighted_mean, plot_demographics_barchart, plot_wine_choropleth_plotly,
                          generate_optimized_prompt)


# Load restaurant data
all_france = pd.read_csv("assets/Data/all_restaurants(arrondissements).csv")
# Load regional GeoJSON data
region_df = gpd.read_file("assets/Data/region_restaurants.geojson")
# Load departmental GeoJSON data
department_df = gpd.read_file("assets/Data/department_restaurants.geojson")
# Load arrondissement GeoJSON data
arron_df = gpd.read_file("assets/Data/arrondissement_restaurants.geojson")
# Load wine GeoJSON data
wine_df = gpd.read_file("assets/Data/wine_regions_cleaned.geojson")


# Get unique department numbers with restaurants
departments_with_restaurants = all_france['department_num'].unique()
# Filter geo_df
geo_df = department_df[department_df['code'].isin(departments_with_restaurants)]
star_placeholder = (0.5, 1, 2, 3)


# Use geo_df to get unique regions and departments for the initial dropdowns
unique_regions = sorted(geo_df['region'].unique())
initial_departments = geo_df[geo_df['region'] == unique_regions[0]][['department', 'code']].drop_duplicates().to_dict('records')
initial_options = [{'label': f"{dept['department']} ({dept['code']})", 'value': dept['department']} for dept in initial_departments]
dept_to_code = geo_df.drop_duplicates(subset='department').set_index('department')['code'].to_dict()
region_to_name = {region: region for region in geo_df['region'].unique()}


load_dotenv()
# Initialize OpenAI client with API key
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
    REQUEST_LIMIT = 7

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
app.title = 'Michelin Guide to France - pineapple-bois'
app.index_string = open('assets/custom_header.html', 'r').read()
app.layout = html.Div([
    dcc.Store(id='selected-stars', data=[]),
    dcc.Store(id='error-state', data=False),  # Initialize with no error
    dcc.Store(id='available-stars', data=[]),  # will populate with star rating by department
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
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/analysis':
        return get_analysis_layout()
    elif pathname == '/home':
        return get_main_layout()
    else:
        return get_main_layout() if pathname == '/' else get_404_layout()


# Callback to update the button colors based on the current page
@app.callback(
    [Output('home-button', 'style'),
     Output('analysis-button', 'style')],
    [Input('url', 'pathname')]
)
def update_button_styles(pathname):
    # Define the active and inactive button styles
    active_button_style = {
        'background-color': '#C2282D',
        'color': 'white',
        'border': 'none',
        'padding': '10px 20px',
        'border-radius': '5px',
        'cursor': 'pointer',
    }
    inactive_button_style = {
        'background-color': 'lightcoral',
        'color': 'white',
        'border': 'none',
        'padding': '10px 20px',
        'border-radius': '5px',
        'cursor': 'pointer',
    }

    # Check the current URL path and apply the active style to the corresponding button
    if pathname == '/' or pathname == '/home':
        return active_button_style, inactive_button_style  # Home button active
    elif pathname == '/analysis':
        return inactive_button_style, active_button_style  # Analysis button active
    else:
        return inactive_button_style, inactive_button_style  # Default case, both inactive


# -----------------------> "Guide Page"

@app.callback(
    [
        Output('department-dropdown', 'options'),
        Output('star-filter', 'children'),
        Output('star-filter', 'style'),
        Output('available-stars', 'data')],
    [Input('region-dropdown', 'value'),
     Input('department-dropdown', 'value')]
)
def update_department_and_filters(selected_region, selected_department):
    # Fetch department options based on the selected region.
    departments = geo_df[geo_df['region'] == selected_region][['department', 'code']].drop_duplicates().to_dict(
        'records')
    department_options = [{'label': f"{dept['department']} ({dept['code']})", 'value': dept['department']} for dept in
                          departments]

    if not selected_department:
        # No department selected, hide star filter and clear buttons
        return department_options, star_filter_section().children, {'display': 'none'}, []

    # Fetch the row for the selected department
    department_row = geo_df[geo_df['department'] == selected_department].iloc[0]

    # Determine which star ratings are present
    available_stars = []
    for star_level in [3, 2, 1]:  # Ensure all levels are checked
        if department_row[f'{int(star_level)}_star'] > 0:
            available_stars.append(star_level)
    if department_row['bib_gourmand'] > 0:
        available_stars.append(0.5)

    # Only show the filter if there are stars available
    if available_stars:
        star_filter = star_filter_section(available_stars)
        return department_options, star_filter.children, {'display': 'block'}, available_stars
    else:
        return department_options, star_filter_section.children, {'display': 'none'}, []


@app.callback(
    [Output({'type': 'filter-button', 'index': ALL}, 'className'),
     Output({'type': 'filter-button', 'index': ALL}, 'style'),
     Output('selected-stars', 'data'),  # This output updates the list of active stars
     Output('error-state', 'data')],
    [Input({'type': 'filter-button', 'index': ALL}, 'n_clicks')],
    [State({'type': 'filter-button', 'index': ALL}, 'id'),
     State('selected-stars', 'data'),
     State('available-stars', 'data')]
)
def update_button_active_state(n_clicks_list, ids, current_stars, available_stars):
    # Handle cases where not all data is available, especially at initialization
    if not n_clicks_list or not available_stars:
        raise PreventUpdate

    # Initialize empty lists to store class names and styles
    class_names = []
    styles = []

    # Initialize the new list of active stars
    new_stars = [star for star in current_stars if star in available_stars]

    # Initialize error state
    error_state = False     # default to no error

    for n_clicks, button_id in zip(n_clicks_list, ids):
        index = button_id['index']
        if index not in available_stars:
            continue  # Skip processing for stars not available

        # Determine if the button is currently active
        is_active = n_clicks % 2 == 0  # Even clicks means 'active'
        if is_active:
            if index not in new_stars:
                new_stars.append(index)  # Add if not already in the list
            background_color = color_map[index]  # Full color for active state
        else:
            if index in new_stars:
                new_stars.remove(index)  # Remove if in the list but not active
            background_color = (f"rgba({int(color_map[index][1:3], 16)},"
                                f"{int(color_map[index][3:5], 16)},"
                                f"{int(color_map[index][5:7], 16)},"
                                f"0.6)")  # Lighter color for inactive

        class_name = "me-1 star-button" + (" active" if is_active else "")
        color_style = {
            "display": 'inline-block',
            "width": '100%',
            'backgroundColor': background_color,
        }
        class_names.append(class_name)
        styles.append(color_style)

    if not new_stars:
        error_state = True  # Set error if no stars are active
    return class_names, styles, new_stars, error_state


@app.callback(
    Output('restaurant-details', 'children'),
    [Input('map-display', 'clickData'),
     Input('department-dropdown', 'value'),
     Input('error-state', 'data')]  # Listen to the error state
)
def update_sidebar(clickData, selected_department, error_state):
    ctx = dash.callback_context

    if error_state:
        return html.Div("Please select at least one category to display restaurants.",
                        className='placeholder-text',
                        style={'color': '#C2282D'})

    # Check if the callback was triggered by a department change and if it's cleared
    if not selected_department:
        return html.Div("Select a department to view restaurants.", className='placeholder-text')

    # If there's a map click and it contains valid data, update the details
    if ctx.triggered[0]['prop_id'] == 'map-display.clickData' and clickData:
        if 'points' in clickData and clickData['points']:
            restaurant_index = clickData['points'][0]['customdata']
            restaurant_info = all_france.loc[restaurant_index]
            return get_restaurant_details(restaurant_info)

    # Default message if no restaurant is selected yet
    return html.Div("Select a restaurant on the map to see more details", className='placeholder-text')


@app.callback(
    Output('map-display', 'figure'),
    [Input('department-dropdown', 'value'),
     Input('region-dropdown', 'value'),
     Input('selected-stars', 'data'),
     Input('error-state', 'data')],
)
def update_map(selected_department, selected_region, selected_stars, error_state):
    ctx = callback_context
    triggered_id, _ = ctx.triggered[0]['prop_id'].split('.') if ctx.triggered else (None, None)

    # Check for error state first - highest priority
    if error_state:
        return handle_error_condition(selected_department)

    # Check if the callback was specifically triggered by a department or star selection
    if triggered_id in ['department-dropdown', 'selected-stars']:
        if selected_department:
            department_code = dept_to_code.get(selected_department)
            if department_code:
                if not selected_stars:
                    return plot_department_outlines(geo_df, department_code)
                else:
                    return plot_interactive_department(all_france, geo_df, department_code, selected_stars)

    # Handle region selection separately
    if selected_region or triggered_id == 'region-dropdown':
        region_name = region_to_name.get(selected_region)
        if region_name:  # Ensure region name exists
            return plot_regional_outlines(region_df, region_name)

    # Default case - no specific input or cleared inputs
    return default_map_figure()


def handle_error_condition(selected_department):
    if selected_department:
        department_code = dept_to_code.get(selected_department, None)
        if department_code:
            return plot_department_outlines(geo_df, department_code)
    return default_map_figure()


def default_map_figure():
    return go.Figure(go.Scattermapbox()).update_layout(
            font=dict(
                family="Courier New, monospace",
                size=18,
                color="white"
            ),
            width=800,
            height=600,
            mapbox_style="carto-positron",
            mapbox_zoom=5,
            mapbox_center_lat=46.603354,
            mapbox_center_lon=1.888334,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )


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


# LOCATION MATCHING content

@app.callback(
    Output('matched-city-output', 'children'),
    [Input('submit-city-button', 'n_clicks'),
     Input('clear-city-button', 'n_clicks')],
    [State('city-input', 'value')]
)
def update_city_match_output(n_submit_clicks, n_clear_clicks, city_input):
    if n_submit_clicks > 0 or n_clear_clicks > 0:
        if city_input == '' or n_clear_clicks >= n_submit_clicks:
            # Clear the output when the 'Clear' button is clicked or empty input
            return html.Div(
                children=[html.P("Please enter a location and click 'Submit'.", className='default-message')]
            )
        else:
            matcher = LocationMatcher(all_france)
            result = matcher.find_region_department(city_input)

            if isinstance(result, dict):
                city_details = [
                    html.P(f"Matched Location: {result.get('Matched Location', 'Unknown')}", className='match-title'),
                    html.P(f"Region: {result.get('Region', 'Unknown')}", className='match-details'),
                    html.P(f"Department: {result.get('Department', 'Unknown')}", className='match-details')
                ]
                # Only add Capital Status if it's not an empty string
                if result.get('Is Capital'):
                    city_details.append(html.P(f"Capital Status: {result['Is Capital']}", className='match-details'))

                return html.Div(city_details, className='city-match-container')

            elif isinstance(result, str):
                return html.Div([
                    html.P(f"No match found for '{city_input}'", className='no-match-message')
                ])

    return html.Div([
        html.H5("Please enter a location and click 'Submit'.", className='default-message')
    ])


@app.callback(
    Output('city-input', 'value'),
    Input('clear-city-button', 'n_clicks')
)
def clear_input(n_clicks):
    if n_clicks > 0:
        return ''  # Return an empty string to clear the input field
    return dash.no_update  # Keep the current value if the clear button is not clicked


# DEPARTMENT content

@app.callback(
    [Output('star-filter-wrapper-department', 'style'),
     Output('department-analysis-graph', 'figure'),
     Output('department-map', 'figure'),
     Output('department-analysis-graph', 'style'),
     Output('department-map', 'style'),
     Output('departments-store', 'data')],
    [Input('department-dropdown-analysis', 'value'),
     Input({'type': 'filter-button-department', 'index': ALL}, 'n_clicks')]
)
def update_department_chart_and_map(selected_region, star_clicks):
    hide_style = {'display': 'none'}
    show_style = {'display': 'inline-block', 'height': '100%', 'width': '100%'}

    if not selected_region:
        empty_fig = go.Figure()
        return hide_style, empty_fig, empty_fig, hide_style, hide_style, []

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

    return show_style, fig_bar, map_fig, show_style, show_style, department_options


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
    [Output('arrondissement-analysis-graph', 'figure'),
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
        return empty_fig, empty_fig, hide_style, hide_style

    # Default to all star levels if none selected
    select_stars = [0.5, 1, 2, 3]

    if star_clicks:
        select_stars = [star_placeholder[i] for i, n in enumerate(star_clicks) if n % 2 == 0]

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

    return fig_bar, map_fig, show_style, show_style


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
     Output('toggle-show-details', 'n_clicks')], # Reset the click state
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
                "font-size": "20px",
                "color": "grey",
                "text-align": "center",
                "align-items": "center",  # Vertically center
            }
        ), 0

    display_restaurants = n_clicks % 2 == 1  # Toggle restaurant visibility based on button state

    # If 'Paris' is selected in the Top N dropdown
    if top_n == 1 and granularity == 'department':
        filtered_data = all_france[all_france['department_num'] == '75']  # Only Paris restaurants
    elif top_n == 1 and granularity == 'region':
        filtered_data = all_france[all_france['region'] == 'Île-de-France']  # Only Île-de-France restaurants
    else:
        # Filter out Paris if department is selected and not 'Paris'
        filtered_data = all_france[all_france['region'] != 'Île-de-France']
        if granularity == 'department' and top_n in [3, 5]:
            filtered_data = filtered_data[filtered_data['department_num'] != '75']  # Exclude Paris

    # Call the top_restaurants function to get the components
    ranking_components = top_restaurants(filtered_data, granularity, star_rating, top_n, display_restaurants)

    return ranking_components, n_clicks


# DEMOGRAPHICS content

@app.callback(
    [Output('demographics-map-graph', 'figure'),
     Output('demographics-bar-chart-graph', 'figure'),
     Output('demographics-add-remove', 'style'),
     Output('demographics-dropdown-analysis', 'value'),
     Output('demographics-chart-math', 'style'),
     Output('star-filter-demographics', 'style')],
    [Input('category-dropdown-demographics', 'value'),
     Input('granularity-dropdown-demographics', 'value'),
     Input('demographics-dropdown-analysis', 'value'),
     Input('toggle-show-details-demographics', 'n_clicks'),  # Button to toggle restaurants
     Input({'type': 'filter-button-demographics', 'index': ALL}, 'n_clicks')]  # Selected star ratings
)
def update_demographics_map(selected_metric, selected_dropdown, selected_regions, n_clicks_rest, n_clicks_stars):
    # Handle "Select All"
    if 'all' in selected_regions:
        selected_regions = unique_regions  # Select all regions if "Select All" is chosen

    # Set granularity based on whether a region is selected in the dropdown
    if selected_dropdown != 'All France':
        selected_granularity = 'department'  # If a region is selected, use department granularity
        region_selector_style = {'display': 'none'}  # Hide the region selector
    else:
        selected_granularity = 'region'  # Default granularity is region
        region_selector_style = {'display': 'block'}  # Show the region selector

    if selected_granularity == 'region':
        df = region_df.sort_values('region')  # Use region-level data
        if selected_regions:
            df = df[df['region'].isin(selected_regions)]
            filtered_restaurants = all_france[all_france['region'].isin(selected_regions)]
    else:
        df = department_df
        # If a region is selected in the dropdown, filter to that region
        if selected_dropdown != 'All France':
            df = df[df['region'] == selected_dropdown]
            filtered_restaurants = all_france

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
            selected_stars=selected_stars  # Filter based on selected stars
        )
        empty_fig = go.Figure()  # Return empty figure for bar chart
        return fig_map, empty_fig, region_selector_style, selected_regions, {'display': 'none'}, star_filter_style

    if selected_granularity == 'region':
        dataframe = region_df
    else:
        dataframe = department_df

    weighted_mean = calculate_weighted_mean(dataframe, selected_metric, weight_column='municipal_population')

    fig_map = plot_demographic_choropleth_plotly(
        df,
        filtered_restaurants,
        selected_metric,
        granularity=selected_granularity,
        show_labels=False,
        cmap='Blues',
        restaurants=show_restaurants,
        selected_stars=selected_stars
    )

    fig_bar = plot_demographics_barchart(
        df,
        selected_metric,
        granularity=selected_granularity,
        weighted_mean=weighted_mean
    )

    return fig_map, fig_bar, region_selector_style, selected_regions, {'display': 'block'}, star_filter_style


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
     Input({'type': 'filter-button-wine', 'index': ALL}, 'n_clicks')]
)
def update_wine_map(outline_type, n_clicks_rest, n_clicks_stars):
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
        selected_stars=selected_stars
    )

    return fig, wine_region_curve_numbers, filter_style


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
