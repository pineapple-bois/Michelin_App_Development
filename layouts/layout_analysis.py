import json
from dash import html, dcc
import dash_bootstrap_components as dbc

from .layout_main import (michelin_stars, bib_gourmand, inverted_michelin_stars, inverted_bib_gourmand,
                          get_header_with_buttons, get_footer)


color_map = {
    0.5: "#640A64",
    1: "#FFB84D",
    2: "#FE6F64",
    3: "#C2282D"
}

star_placeholder = (0.5, 1, 2, 3)

unique_regions = ['Auvergne-Rhône-Alpes',
                  'Bourgogne-Franche-Comté',
                  'Bretagne',
                  'Centre-Val de Loire',
                  'Corse',
                  'Grand Est',
                  'Hauts-de-France',
                  'Normandie',
                  'Nouvelle-Aquitaine',
                  'Occitanie',
                  'Pays de la Loire',
                  "Provence-Alpes-Côte d'Azur",
                  'Île-de-France'
                  ]


def create_star_button_analysis(value, label):
    # Generate color with reduced opacity for active state
    normal_bg_color = color_map[value]
    return dbc.Button(
        label,
        id={
            'type': 'filter-button-analysis',
            'index': value,
        },
        className="me-1 star-button-analysis active",  # New class specific for analysis page
        outline=True,
        style={
            'display': 'inline-block',
            'backgroundColor': normal_bg_color,
            'width': '100%',
            'opacity': 1
        },
        n_clicks=0,
    )


def star_filter_row_analysis(available_stars):
    # Create a button for each available star rating, specific to analysis page
    buttons = [create_star_button_analysis(star, inverted_michelin_stars(star) if star != 0.5 else inverted_bib_gourmand()) for star in available_stars]
    return html.Div(buttons, className='star-filter-buttons-analysis')  # New class


def star_filter_section_analysis(available_stars=star_placeholder):
    star_buttons = star_filter_row_analysis(available_stars)
    return html.Div([
        html.H6("Filter by Michelin Rating", className='star-select-title-analysis'),  # New class
        star_buttons
    ], className='star-filter-section-analysis', id='star-filter-analysis')  # New id and class


def get_analysis_content():
    return html.Div(
        className='analysis-container',
        children=[
            # New Div for placeholder text (full width)
            html.Div(
                className='placeholder-text-container',
                children=[
                    html.H5(
                        """
                        Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
                        Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. 
                        Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. 
                        Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. 
                        Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
                        """
                    )
                ],
                style={'width': '100%'}  # Set full width
            ),
            # Region Section (both sidebar and main content)
            html.Div(
                className='region-content-wrapper',  # Wrapper to couple sidebar and content for regions
                children=[
                    # Sidebar for regions - 30% width
                    html.Div(
                        className='region-sidebar',
                        children=[
                            # Description related to region analysis
                            html.Div(
                                children=[
                                    html.H5("How do Michelin rated restaurants vary across regions?")
                                ], className="region-description"
                            ),

                            # Title and region dropdown in one div
                            html.Div(
                                className='region-filter-container',
                                children=[
                                    html.H5("Add or Remove Regions of France", className='region-filter-title'),
                                    dcc.Dropdown(
                                        id='region-dropdown-analysis',
                                        options=[{'label': region, 'value': region} for region in unique_regions],
                                        value=unique_regions,  # All regions selected by default
                                        className='dropdown-region-analysis',
                                        multi=True,  # Multi-select enabled
                                        clearable=True
                                    ),
                                ]
                            ),

                            # Star filter specific to analysis page
                            html.Div(
                                className='star-filter-container',
                                children=[
                                    dcc.Store(id='selected-stars-analysis', data=[]),
                                    star_filter_section_analysis(star_placeholder),  # Use new filter section
                                ]
                            ),
                        ],
                        style={'width': '30%', 'float': 'left'}  # Region sidebar
                    ),

                    # Main Content for regions - 70% width
                    html.Div(
                        className='region-main-content',
                        children=[
                            # Row for bar chart and map
                            html.Div(
                                className='region-visuals',
                                children=[
                                    # Bar chart
                                    html.Div(
                                        className='region-graph',
                                        children=[
                                            dcc.Graph(
                                                id='restaurant-analysis-graph',
                                                config={'displayModeBar': False}
                                            )
                                        ],
                                        style={'width': '60%', 'display': 'inline-block'}
                                    ),
                                    # Map
                                    html.Div(
                                        className='region-map',
                                        children=[
                                            dcc.Graph(
                                                id='region-map',
                                                config={'displayModeBar': False}
                                            )
                                        ],
                                        style={'width': '40%', 'display': 'inline-block'}
                                    )
                                ]
                            )
                        ],
                        style={'width': '70%', 'float': 'right'}  # Region main content
                    )
                ]
            ),

            # Department Section Placeholder
            html.Div(
                className='department-content-wrapper',
                children=[
                    # Sidebar for regions - 30% width
                    html.Div(
                        className='department-sidebar',
                        children=[
                            # Description related to region analysis
                            html.Div(
                                children=[
                                    html.H5("Select a region to view restaurants by department")
                                ], className="department-description"
                            ),
                        ],
                        style={'width': '30%', 'float': 'left'} # Department sidebar
                    )
                ]
            ),
        ]
    )

def get_analysis_layout():
    # Header with buttons
    header = html.Div(
        children=[
            get_header_with_buttons()
        ],
        className='header'
    )

    body = html.Div(
        children=[
            get_analysis_content()
        ],
        className='content-container'
    )

    footer = get_footer()

    # Combine all sections into the main layout
    return html.Div([
        header,
        body,
        footer
    ], className='main-layout')