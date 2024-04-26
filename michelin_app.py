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


# # FOR LOCAL DEVELOPMENT ONLY - RISK MAN-IN-MIDDLE ATTACKS
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context


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


def plot_interactive_department(data_df, geo_df, department_code, selected_stars):
    # Initialize a blank figure
    fig = go.Figure()
    fig.update_layout(autosize=True)

    # Get the specific geometry
    specific_geometry = geo_df[geo_df['code'] == str(department_code)]['geometry'].iloc[0]

    # Plot the geometry's boundaries
    if specific_geometry.geom_type == 'Polygon':
        x, y = specific_geometry.exterior.xy
        fig.add_trace(go.Scattermapbox(
            lat=list(y),
            lon=list(x),
            mode='lines',
            line=dict(width=0.5, color='black'),  # Making line thicker and black for visibility
            hoverinfo='none',
            showlegend=False  # Hide from legend
        ))
    elif specific_geometry.geom_type == 'MultiPolygon':
        for polygon in specific_geometry.geoms:
            if polygon.geom_type == 'Polygon':  # Ensure we're dealing with a Polygon
                x, y = polygon.exterior.xy
                fig.add_trace(go.Scattermapbox(
                    lat=list(y),
                    lon=list(x),
                    mode='lines',
                    line=dict(width=0.5, color='black'),
                    hoverinfo='none',
                    showlegend=False
                ))

    # Define custom color map based on stars, including Bibs
    color_map = {0.5: "green", 1: "yellow", 2: "orange", 3: "red"}
    dept_data = data_df[(data_df['department_num'] == str(department_code)) & (data_df['stars'].isin(selected_stars))].copy()
    dept_data['color'] = dept_data['stars'].map(color_map)

    # Modify the hover text function
    dept_data['hover_text'] = dept_data.apply(
        lambda row: f"<span style='font-family: Courier New, monospace;'><b>{row['name']}</b><br>{'⭐' * int(row['stars']) if row['stars'] != 0.5 else 'Bib Gourmand'}<br>"
                    f"Address: {row['address']}<br>Location: {row['location']}<br>Cuisine: {row['cuisine']}<br>"
                    f"<a href='{row['url']}' target='_blank' style='font-family: Courier New, monospace;'>Visit website</a><br>"
                    f"Price: {row['price']}</span>",
        axis=1
    )

    # Overlay restaurant points
    for star, color in color_map.items():
        subset = dept_data[dept_data['stars'] == star]

        # Adjust hover text for Bib Gourmand
        if star == 0.5:
            label_name = 'Bib Gourmand'
        else:
            label_name = f"{'⭐' * int(star)}"

        fig.add_trace(go.Scattermapbox(lat=subset['latitude'],
                                       lon=subset['longitude'],
                                       mode='markers',
                                       marker=go.scattermapbox.Marker(size=10, color=color),
                                       text=subset['hover_text'],
                                       hovertemplate='%{text}<br>Coordinates: (%{lat}, %{lon})',
                                       name=label_name))

    # Adjusting layout
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
        mapbox_zoom=8,
        mapbox_center_lat=dept_data['latitude'].mean(),
        mapbox_center_lon=dept_data['longitude'].mean()
    )

    return fig


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

# Use geo_df to get unique regions and departments for the initial dropdowns
unique_regions = geo_df['region'].unique()
initial_departments = geo_df[geo_df['region'] == unique_regions[0]][['department', 'code']].drop_duplicates().to_dict('records')
initial_options = [{'label': f"{dept['department']} ({dept['code']})", 'value': dept['department']} for dept in initial_departments]
dept_to_code = geo_df.drop_duplicates(subset='department').set_index('department')['code'].to_dict()

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='region-dropdown',
                options=[{'label': region, 'value': region} for region in unique_regions],
                value=unique_regions[0],  # default value
                style={"fontFamily": "Courier New, monospace"}
            )
        ]),
        dbc.Col([
            dcc.Dropdown(
                id='department-dropdown',
                style={"fontFamily": "Courier New, monospace"}
            )
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='map-display',
                responsive=True,
                style={"height": "80vh"},
                config={
                    'displayModeBar': True,
                    'scrollZoom': True,
                    'modeBarButtonsToRemove': ['pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d',
                                               'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian',
                                               'toggleSpikelines', 'toImage'],
                    'modeBarButtonsToAdd': ['zoom2d', 'resetScale2d']
                }
            )
        ])
    ]),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div([
                    # For the Bib Gourmand, combine logo and description inside a Div
                    html.Div([
                        html.Img(
                            src="https://upload.wikimedia.org/wikipedia/commons/6/6e/Michelin_Bib_Gourmand.png",
                            style={"width": "20px", "verticalAlign": "middle", "marginRight": "10px", "display": "inline-block"}
                        ),
                        html.H6(star_descriptions[key],
                                style={"fontFamily": "Courier New, monospace",
                                       "fontSize": "18px", "display": "inline-block",
                                       "margin": "5px 0"})
                    ], style={"display": "inline-block"})
                    if key == 0.5 else
                    html.H6(star_descriptions[key],
                            style={"fontFamily": "Courier New, monospace", "fontSize": "18px"})
                ]) for key in star_descriptions
            ], style={'marginTop': '20px'})
        ])
    ])
], fluid=True)


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
    app.run_server(debug=False)
