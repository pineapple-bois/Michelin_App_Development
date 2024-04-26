import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output
from flask import Flask, redirect, request
from layouts.layout_main import get_main_layout
from appFunctions import plot_regional_outlines, plot_interactive_department


# # FOR LOCAL DEVELOPMENT ONLY - RISK MAN-IN-MIDDLE ATTACKS
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context


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


star_descriptions = {
    3: "⭐⭐⭐ - Exceptional cuisine, worth a special journey",
    2: "⭐⭐ - Excellent cooking, worth a detour",
    1: "⭐ - High-quality cooking, worth a stop",
    0.5: "- Bib Gourmand - Exceptionally good food at moderate prices"
}


# Initialize the Dash app
server = Flask(__name__)
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
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
    dcc.Location(id='url', refresh=False),  # Tracks the url
    html.Div(id='page-content', children=get_main_layout(unique_regions, star_descriptions))  # Set initial content
])


@app.callback(
    Output('department-dropdown', 'options'),
    Input('region-dropdown', 'value')
)
def update_department_dropdown(selected_region):
    departments = geo_df[geo_df['region'] == selected_region][['department', 'code']].drop_duplicates().to_dict('records')
    return [{'label': f"{dept['department']} ({dept['code']})", 'value': dept['department']} for dept in departments]


@app.callback(
    Output('map-display', 'figure'),
    [Input('department-dropdown', 'value'),
     Input('region-dropdown', 'value')]
)
def update_map(selected_department, selected_region):
    # Show all stars by default
    selected_stars = [0.5, 1, 2, 3]

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
            margin={"r": 20, "t": 20, "l": 20, "b": 20},  # Remove margins
        )


# For local development, debug=True
if __name__ == '__main__':
    app.run_server(debug=False)
