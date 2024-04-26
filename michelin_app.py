import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
from flask import Flask, redirect, request
from layouts.layout_main import get_main_layout
from appFunctions import plot_interactive_department


# # FOR LOCAL DEVELOPMENT ONLY - RISK MAN-IN-MIDDLE ATTACKS
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


# Load restaurant data
url = ("https://raw.githubusercontent.com/pineapple-bois/Michelin_Rated_Restaurants"
       "/main/Years/2024/data/France/all_restaurants(arrondissements).csv")
all_france = pd.read_csv(url)

# Load GeoJSON departmental data
geojson_url = ("https://raw.githubusercontent.com/pineapple-bois/Michelin_Rated_Restaurants/"
               "main/Years/2024/data/France/geodata/department_restaurants.geojson")
geo_df = gpd.read_file(geojson_url)

# Get unique department numbers with restaurants
departments_with_restaurants = all_france['department_num'].unique()

# Filter geo_df
geo_df = geo_df[geo_df['code'].isin(departments_with_restaurants)]

star_descriptions = {
    3: "⭐⭐⭐ - Exceptional cuisine, worth a special journey",
    2: "⭐⭐ - Excellent cooking, worth a detour",
    1: "⭐ - High-quality cooking, worth a stop",
    0.5: "- Bib Gourmand - Exceptionally good food at moderate prices"
}

# Use geo_df to get unique regions and departments for the initial dropdowns
unique_regions = geo_df['region'].unique()
initial_departments = geo_df[geo_df['region'] == unique_regions[0]][['department', 'code']].drop_duplicates().to_dict('records')
initial_options = [{'label': f"{dept['department']} ({dept['code']})", 'value': dept['department']} for dept in initial_departments]
dept_to_code = geo_df.drop_duplicates(subset='department').set_index('department')['code'].to_dict()


# Initialize the Dash app
server = Flask(__name__)
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
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
    [Input('department-dropdown', 'value')]
)
def update_map(selected_department):
    # Show all stars by default
    selected_stars = [0.5, 1, 2, 3]
    if selected_department is None:
        # Create an empty figure with map centered around France
        fig = go.Figure(go.Scattermapbox())

        fig.update_layout(
            plot_bgcolor='black',
            paper_bgcolor='black',
            title="Michelin Guide to France 2024",
            font=dict(
                family="Courier New, monospace",
                size=18,
                color="white"
            ),
            width=1000,
            height=800,
            mapbox_style="carto-positron",
            mapbox_zoom=5,
            mapbox_center_lat=46.603354,  # Approximate latitude for France center
            mapbox_center_lon=1.888334  # Approximate longitude for France center
        )
        return fig
    department_code = dept_to_code[selected_department]
    fig = plot_interactive_department(all_france, geo_df, department_code, selected_stars)
    return fig


# For local development, debug=True
if __name__ == '__main__':
    app.run_server(debug=True)
