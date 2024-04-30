import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback_context, no_update
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State, ALL
from flask import Flask, redirect, request
from layouts.layout_main import get_main_layout, color_map, star_filter_row, star_filter_section
from appFunctions import plot_regional_outlines, plot_interactive_department, get_restaurant_details


# # FOR LOCAL DEVELOPMENT ONLY - RISK MAN-IN-MIDDLE ATTACKS
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


# Load restaurant data
url = ("https://raw.githubusercontent.com/pineapple-bois/Michelin_Rated_Restaurants"
       "/main/Years/2024/data/France/all_restaurants(arrondissements).csv")
all_france = pd.read_csv(url)

# Load GeoJSON departmental data
deptjson_url = ("https://raw.githubusercontent.com/pineapple-bois/Michelin_Rated_Restaurants/"
                "main/Years/2024/data/France/geodata/department_restaurants.geojson")
geo_df = gpd.read_file(deptjson_url)

# Load GeoJSON regional data
regionjson_url = ("https://raw.githubusercontent.com/pineapple-bois/Michelin_Rated_Restaurants/"
                  "main/Years/2024/data/France/geodata/region_restaurants.geojson")
region_df = gpd.read_file(regionjson_url)


# Get unique department numbers with restaurants
departments_with_restaurants = all_france['department_num'].unique()
# Filter geo_df
geo_df = geo_df[geo_df['code'].isin(departments_with_restaurants)]


# Use geo_df to get unique regions and departments for the initial dropdowns
unique_regions = geo_df['region'].unique()
initial_departments = geo_df[geo_df['region'] == unique_regions[0]][['department', 'code']].drop_duplicates().to_dict('records')
initial_options = [{'label': f"{dept['department']} ({dept['code']})", 'value': dept['department']} for dept in initial_departments]
dept_to_code = geo_df.drop_duplicates(subset='department').set_index('department')['code'].to_dict()
region_to_name = {region: region for region in geo_df['region'].unique()}


# Initialize the Dash app
server = Flask(__name__)
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP,
                          "https://fonts.googleapis.com/css2?family=Kaisei+Decol&display=swap",
                          "https://fonts.googleapis.com/css2?family=Kaisei+Decol&family=Libre+Franklin:ital,wght@0,100..900;1,100..900&display=swap"],
    server=server)


# Comment out to launch locally (development)
# @server.before_request
# def before_request():
#     if not request.is_secure:
#         url = request.url.replace('http://', 'https://', 1)
#         return redirect(url, code=301)


# App set up
app.title = 'Michelin Guide to France - pineapple-bois'
app.index_string = open('assets/custom_header.html', 'r').read()
app.layout = html.Div([
    dcc.Store(id='selected-stars', data=[0.5, 1, 2, 3]),  # Initialized with all stars selected
    dcc.Location(id='url', refresh=False),  # Tracks the url
    html.Div(id='page-content', children=get_main_layout(unique_regions))  # Set initial content
])


@app.callback(
    [Output({'type': 'filter-button', 'index': ALL}, 'className'),
     Output({'type': 'filter-button', 'index': ALL}, 'style'),
     Output('selected-stars', 'data')],  # This output updates the list of active stars
    [Input({'type': 'filter-button', 'index': ALL}, 'n_clicks')],
    [State({'type': 'filter-button', 'index': ALL}, 'id'),
     State('selected-stars', 'data')]
)
def update_button_active_state(n_clicks_list, ids, current_stars):
    # if all(n_clicks == 0 for n_clicks in n_clicks_list):  # Check if all n_clicks are zero
    #     return no_update, no_update, no_update  # Avoid processing on initial load

    class_names = []
    styles = []
    new_stars = current_stars.copy()  # Start with current active stars

    for n_clicks, button_id in zip(n_clicks_list, ids):
        index = button_id['index']
        is_active = n_clicks % 2 == 0  # Toggle active state - Even clicks means 'active'
        if is_active:
            if index not in new_stars:
                new_stars.append(index)  # Add if not already in the list
            background_color = color_map[index]  # Full color for active state
        else:
            if index in new_stars:
                new_stars.remove(index)  # Remove if in the list but not active
            background_color = f"rgba({int(color_map[index][1:3], 16)}, {int(color_map[index][3:5], 16)}, {int(color_map[index][5:7], 16)}, 0.6)"  # Lighter color for inactive

        class_name = "me-1 star-button" + (" active" if is_active else "")
        color_style = {
            "display": 'inline-block',
            "width": '100%',
            'backgroundColor': background_color,
        }
        class_names.append(class_name)
        styles.append(color_style)

        # Debugging output
        # print(f"Button {index}: Active state: {is_active}, Color: {background_color}")
        # print(f"Updated active stars: {new_stars}")
        # print(f"Previous stars data: {current_stars}")

    return class_names, styles, new_stars


@app.callback(
    [
        Output('department-dropdown', 'options'),
        Output('star-filter', 'children'),
        Output('star-filter', 'style')],
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
        return department_options, star_filter_section().children, {'display': 'none'}

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
        return department_options, star_filter.children, {'display': 'block'}
    else:
        return department_options, star_filter_section.children, {'display': 'none'}


@app.callback(
    Output('map-display', 'figure'),
    [Input('department-dropdown', 'value'),
     Input('region-dropdown', 'value'),
     Input('selected-stars', 'data')]
)
def update_map(selected_department, selected_region, selected_stars):  # add selected stars
    # Determine which input triggered the callback
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if selected_department:
        # If a department is selected, show specific department information
        department_code = dept_to_code[selected_department]
        return plot_interactive_department(all_france, geo_df, department_code, selected_stars)
    elif selected_region or trigger_id == 'region-dropdown':
        # If a region is selected (and it's the trigger), show regional outlines
        region_name = region_to_name[selected_region]
        return plot_regional_outlines(region_df, region_name)
    else:
        # No specific region or department selected, or department cleared
        # Create an empty figure with map centered around France
        return go.Figure(go.Scattermapbox()).update_layout(
            font=dict(
                family="Courier New, monospace",
                size=18,
                color="white"
            ),
            width=800,
            height=600,
            mapbox_style="carto-positron",
            mapbox_center_lat=46.603354,  # Approximate latitude for France center
            mapbox_center_lon=1.888334,  # Approximate longitude for France center
            margin={"r": 0, "t": 0, "l": 0, "b": 0},  # Remove margins
        )


@app.callback(
    Output('restaurant-details', 'children'),
    [Input('map-display', 'clickData'),
     Input('department-dropdown', 'value')]  # Include department dropdown as a trigger
)
def update_sidebar(clickData, selected_department):
    ctx = dash.callback_context

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


# For local development, debug=True
if __name__ == '__main__':
    app.run_server(debug=True)
