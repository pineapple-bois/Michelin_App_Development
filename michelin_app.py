import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
import logging
from dash import dcc, html, callback_context, no_update
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State, ALL
from flask import Flask, redirect, request
from layouts.layout_main import get_main_layout, color_map, star_filter_row, star_filter_section
from appFunctions import (plot_regional_outlines, plot_department_outlines, plot_interactive_department,
                          get_restaurant_details)


# # FOR LOCAL DEVELOPMENT ONLY - RISK OF MAN-IN-MIDDLE ATTACKS
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context


# Load restaurant data
all_france = pd.read_csv("assets/Data/all_restaurants(arrondissements).csv")
# Load departmental GeoJSON data
geo_df = gpd.read_file("assets/Data/department_restaurants.geojson")
# Load regional GeoJSON data
region_df = gpd.read_file("assets/Data/region_restaurants.geojson")


# Get unique department numbers with restaurants
departments_with_restaurants = all_france['department_num'].unique()
# Filter geo_df
geo_df = geo_df[geo_df['code'].isin(departments_with_restaurants)]


# Use geo_df to get unique regions and departments for the initial dropdowns
unique_regions = sorted(geo_df['region'].unique())
initial_departments = geo_df[geo_df['region'] == unique_regions[0]][['department', 'code']].drop_duplicates().to_dict('records')
initial_options = [{'label': f"{dept['department']} ({dept['code']})", 'value': dept['department']} for dept in initial_departments]
dept_to_code = geo_df.drop_duplicates(subset='department').set_index('department')['code'].to_dict()
region_to_name = {region: region for region in geo_df['region'].unique()}


# Initialize the Dash app
server = Flask(__name__)
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP,
                          "https://fonts.googleapis.com/css2?family=Kaisei+Decol&family=Libre+Franklin:"
                          "ital,wght@0,100..900;1,100..900&display=swap"],
    server=server)


# Comment out to launch locally (development)
@server.before_request
def before_request():
    if not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)


# App set up
app.title = 'Michelin Guide to France - pineapple-bois'
app.index_string = open('assets/custom_header.html', 'r').read()
app.layout = html.Div([
    dcc.Store(id='selected-stars', data=[]),
    dcc.Store(id='error-state', data=False),  # Initialize with no error
    dcc.Store(id='available-stars', data=[]),  # will populate with star rating by department
    dcc.Location(id='url', refresh=False),  # Tracks the url
    html.Div(id='page-content', children=get_main_layout(unique_regions))  # Set initial content
])

# Set up basic configuration for logging/debug
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


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
    if department_row['3_star'] > 0:
        available_stars.append(3)
    if department_row['2_star'] > 0:
        available_stars.append(2)
    if department_row['1_star'] > 0:
        available_stars.append(1)
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
def update_map(selected_department, selected_region, selected_stars, error_state):  # add selected stars
    #logging.debug(f"Updating map: {selected_department}, {selected_region}, Stars: {selected_stars}, Error: {error_state}")
    ctx = callback_context
    triggered_id, _ = ctx.triggered[0]['prop_id'].split('.') if ctx.triggered else (None, None)
    #logging.debug(f"Triggered by: {triggered_id}")

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


# For local development, debug=True
if __name__ == '__main__':
    app.run_server(debug=False)
