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

star_placeholder = [0.5, 1, 2, 3]

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


def create_star_button(value, label, filter_type):
    # Generate color with reduced opacity for active state
    normal_bg_color = color_map[value]
    return dbc.Button(
        label,
        id={
            'type': f'filter-button-{filter_type}',  # Dynamic ID based on filter type
            'index': value,
        },
        className=f"me-1 star-button-{filter_type} active",  # Dynamic class name
        outline=True,
        style={
            'display': 'inline-block',
            'backgroundColor': normal_bg_color,
            'width': '100%',
            'opacity': 1
        },
        n_clicks=0,
    )


def star_filter_row(available_stars, filter_type, exclude_stars=None):
    """
    Create a button for each available star rating, optionally excluding specific stars.

    Args:
        available_stars (list): List of available stars to create buttons for.
        filter_type (str): Type of filter (used for dynamic class names).
        exclude_stars (list): Optional list of stars to exclude from the filter.

    Returns:
        html.Div: Div containing buttons for the stars.
    """
    # Exclude specified stars if exclude_stars is provided
    if exclude_stars:
        available_stars = [star for star in available_stars if star not in exclude_stars]
    # Create a button for each available star rating
    buttons = [create_star_button(star, inverted_michelin_stars(star) if star != 0.5 else inverted_bib_gourmand(), filter_type) for star in available_stars]
    return html.Div(buttons, className=f'star-filter-buttons-{filter_type}')  # Dynamic class


def star_filter_section(available_stars=star_placeholder, filter_type="analysis", exclude_stars=None):
    """
    Create a star filter section, optionally excluding specific star ratings.

    Args:
        available_stars (list): List of available stars to create buttons for.
        filter_type (str): Type of filter (used for dynamic class names).
        exclude_stars (list): Optional list of stars to exclude from the filter.

    Returns:
        html.Div: Div containing the star filter section.
    """
    star_buttons = star_filter_row(available_stars, filter_type, exclude_stars=exclude_stars)
    return html.Div([
        html.H6(f"Filter by Michelin Rating", className=f'star-select-title-{filter_type}'),  # Dynamic title
        star_buttons
    ], className=f'star-filter-section-{filter_type}', id=f'star-filter-{filter_type}')  # Dynamic ID and class


def get_department_region_section():
    return html.Div(
        children=[
            # Placeholder text section (common for both regions and departments)
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
                            html.Div(
                                children=[
                                    html.H5("How do Michelin rated restaurants vary across regions?")
                                ], className="region-description"
                            ),
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
                                    star_filter_section(star_placeholder, filter_type="analysis"),
                                ]
                            ),
                        ],
                        style={'width': '30%', 'float': 'left'}
                    ),
                    # Main content for regions - 70% width
                    html.Div(
                        className='region-main-content',
                        children=[
                            html.Div(
                                className='region-visuals',
                                children=[
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
                        style={'width': '70%', 'float': 'right'}
                    )
                ]
            ),
            # Department Section (both sidebar and main content)
            html.Div(
                className='department-content-wrapper',
                children=[
                    html.Div(
                        className='department-sidebar',
                        children=[
                            html.Div(
                                children=[
                                    html.H5("Select a region to view restaurants by department")
                                ], className="department-description"
                            ),
                            html.Div(
                                className='department-filter-container',
                                children=[
                                    dcc.Dropdown(
                                        id='department-dropdown-analysis',
                                        options=[{'label': region, 'value': region} for region in unique_regions],
                                        className='dropdown-department-analysis',
                                        multi=False,  # Single selection enabled
                                        clearable=True
                                    ),
                                ]
                            ),
                            # Star filter specific to department page
                            html.Div(
                                className='star-filter-container-wrapper',
                                children=[
                                    html.Div(
                                        className='star-filter-container',
                                        children=[
                                            dcc.Store(id='selected-stars-department', data=[]),
                                            star_filter_section(star_placeholder, filter_type="department"),
                                        ],
                                    ),
                                ],
                                id='star-filter-wrapper-department',
                            ),
                        ],
                        style={'width': '30%', 'float': 'left'}
                    ),
                    # Main content for departments - 70% width
                    html.Div(
                        className='department-main-content',
                        children=[
                            html.Div(
                                className='department-visuals',
                                children=[
                                    html.Div(
                                        className='department-graph',
                                        children=[
                                            dcc.Graph(
                                                id='department-analysis-graph',
                                                config={'displayModeBar': False}
                                            )
                                        ],
                                        style={'display': 'inline-block'}
                                    ),
                                    html.Div(
                                        className='department-map',
                                        children=[
                                            dcc.Graph(
                                                id='department-map',
                                                config={'displayModeBar': False}
                                            )
                                        ],
                                        style={'display': 'inline-block'}
                                    )
                                ]
                            )
                        ],
                        style={'width': '70%', 'float': 'right'}
                    )
                ]
            )
        ]
    )


def get_top_ranking_section():
    return html.Div(
            className='ranking-content-wrapper',  # Wrapper for both sidebar and content
                children=[
                    # Sidebar - 30% width
                    html.Div(
                        className='ranking-sidebar',
                        children=[
                            # Description for ranking analysis
                            html.Div(
                                children=[
                                    html.H5(
                                        children=[
                                            "Regions/Departments with the Most ",
                                            *michelin_stars(2),  # Unpack the list of images for 2 stars
                                            " and ",
                                            *michelin_stars(3),  # Unpack the list of images for 3 stars
                                            " Restaurants"
                                        ],
                                        className="ranking-description"
                                    )
                                ]
                            ),

                            # Granularity dropdown (Region/Department)
                            html.Div(
                                className='granularity-filter-container',
                                children=[
                                    html.H6("Select Granularity"),
                                    dcc.Dropdown(
                                        id='granularity-dropdown',
                                        options=[
                                            {'label': 'Regions', 'value': 'region'},
                                            {'label': 'Departments', 'value': 'department'}
                                        ],
                                        className='dropdown-granularity',  # Class for styling
                                        multi=False,  # Single selection
                                        clearable=True
                                    )
                                ]
                            ),

                            # Top 3 or Top 5 dropdown
                            html.Div(
                                className='top-ranking-filter-container',
                                children=[
                                    dcc.Dropdown(
                                        id='ranking-dropdown',
                                        options=[
                                            {'label': 'Top 3 (excluding Paris)', 'value': 3},
                                            {'label': 'Top 5 (excluding Paris)', 'value': 5},
                                            {'label': 'Paris', 'value': 1}  # New option for Paris
                                        ],
                                        value=3,  # Default to Top 3
                                        className='dropdown-ranking',  # Class for styling
                                        multi=False,  # Single selection
                                        clearable=False
                                    )
                                ]
                            ),

                            # Dropdown for selecting either 2- or 3-star restaurants
                            html.Div(
                                className='rating-filter-container',
                                children=[
                                    html.H6("Filter by Michelin Stars"),
                                    dcc.Dropdown(
                                        id='star-dropdown-ranking',
                                        options=[
                                            {'label': '2 Stars', 'value': 2},
                                            {'label': '3 Stars', 'value': 3}
                                        ],
                                        value=2,  # Default selection
                                        className='dropdown-star-ranking',
                                        multi=False,  # Single selection
                                        clearable=False
                                    )
                                ]
                            ),

                            # Toggle to show restaurant details
                            html.Div(
                                className='toggle-details-container',
                                children=[
                                    dbc.Button(
                                        "Show Restaurant Details",
                                        id='toggle-show-details',
                                        n_clicks=0,
                                        className='button-show-details'
                                    )
                                ]
                            ),
                        ],
                        style={'width': '30%', 'float': 'left'}  # Sidebar styling
                    ),

                    # Main content - 70% width
                    html.Div(
                        className='ranking-main-content',
                        children=[
                            # Placeholder for ranking output (either restaurant details or ranking summary)
                            html.Div(
                                id='ranking-output',
                                children=[
                                    html.H6("Top Michelin-rated restaurants will be displayed here")
                                ],
                                className='ranking-output-container'
                            )
                        ],
                        style={'width': '70%', 'float': 'right'}  # Main content styling
                    ),
                ]
            )


def get_demographics_content():
    return html.Div(
        className='demographics-container',
        id='demographics-content-top',
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
            ),

            # Demographics dropdowns
            html.Div(
                className='demographics-filter-container',
                children=[
                    # Demographics dropdown
                    html.Div(
                        className='demographics-dropdown-container',
                        children=[
                            html.H6("Select a Socio-Economic Metric"),
                            dcc.Dropdown(
                                id='category-dropdown-demographics',
                                options=[
                                    {'label': 'GDP (millions of €)', 'value': 'GDP_millions(€)'},
                                    {'label': 'GDP (per capita) (€)', 'value': 'GDP_per_capita(€)'},
                                    {'label': 'Poverty Rate (%)', 'value': 'poverty_rate(%)'},
                                    {'label': 'Average Unemployment Rate (%)', 'value': 'average_annual_unemployment_rate(%)'},
                                    {'label': 'Average Hourly Net Wage (€)', 'value': 'average_net_hourly_wage(€)'},
                                    {'label': 'Municipal Population', 'value': 'municipal_population'},
                                    {'label': 'Population Density (inhabitants/km²)', 'value': 'population_density(inhabitants/sq_km)'}
                                ],
                                className='dropdown-category-demographics-selector',
                                multi=False,
                                clearable=True
                            )
                        ],
                    ),
                    # Region dropdown
                    html.Div(
                        className='demographics-dropdown-container',
                        children=[
                            html.H6("Select Region to Show Selected Metrics By Department"),
                            dcc.Dropdown(
                                id='granularity-dropdown-demographics',
                                options=[{'label': 'All France', 'value': 'All France'}] + [
                                    {'label': region, 'value': region} for region in unique_regions],
                                value='All France',  # Default selection
                                className='dropdown-granularity-demographics',
                                multi=False,
                                clearable=False
                            )
                        ],
                    ),
                    # Add or Remove Regions
                    html.Div(
                        className='filter-container',
                        children=[
                            html.Div(
                                id='demographics-add-remove',
                                children=[
                                    html.H5("Add or Remove Regions of France", className='region-filter-title'),
                                    dcc.Dropdown(
                                        id='demographics-dropdown-analysis',
                                        options = [{'label': 'Select All', 'value': 'all'}] +
                                                  [{'label': region, 'value': region} for region in unique_regions],
                                        value=unique_regions,  # All regions selected by default
                                        className='dropdown-category-demographics',
                                        multi=True,  # Multi-select enabled
                                        clearable=True
                                    ),
                                ]
                            )
                        ],
                    ),
                ],
            ),

            # Restaurant selection div
            html.Div(
                className='demographics-restaurants-wrapper',
                children=[
                    # Wrapper for both button and star filter
                    html.Div(
                        className='demographics-restaurants-controls',
                        # Flexbox for side-by-side layout
                        children=[
                            # Toggle to show restaurant details
                            html.Div(
                                className='toggle-details-container',
                                children=[
                                    dbc.Button(
                                        "Show Starred Restaurants",
                                        id='toggle-show-details-demographics',
                                        n_clicks=0,
                                        className='button-show-details'
                                    )
                                ],
                            ),
                            # Star filter specific to analysis page
                            html.Div(
                                className='star-filter-container',
                                children=[
                                    dcc.Store(id='selected-stars-demographics', data=[]),
                                    star_filter_section(star_placeholder, filter_type="demographics", exclude_stars=[0.5]),
                                ],
                                style={'width': '30%'}  # Set filter width to 30% of parent div
                            ),
                        ]
                    )
                ]
            ),

            # Main Content for demographics (Map + Bar Chart)
            html.Div(
                className='demographics-content-wrapper',
                children=[
                    # Map section
                    html.Div(
                        className='demographics-map',
                        children=[
                            dcc.Graph(
                                id='demographics-map-graph',
                                config={'displayModeBar': False}
                            )
                        ],
                        style={'width': '50%', 'display': 'inline-block'}
                    ),
                    # Bar chart section
                    html.Div(
                        className='demographics-chart-mean',
                        id='demographics-chart-math',
                        children=[
                            html.Div(
                                className='demographics-bar-chart',
                                children=[
                                    dcc.Graph(
                                        id='demographics-bar-chart-graph',
                                        config={'displayModeBar': False}
                                    )
                                ],
                            ),
                            html.Div(
                                className='weighted-mean-explanation',
                                children=[
                                    dcc.Markdown(
                                        '''
                                        The French mean is weighted and provides a better sense of trends across France by giving more weight to areas with larger populations.
                                        
                                        $\\text{Weighted Mean} = \\frac{\\sum_{i} (\\text{value}_{i} \\times \\text{population}_i)}{\\sum_{i} \\text{population}_i}$
                                        '''
                                    , mathjax=True)
                                ],
                            ),
                        ],
                    )
                ],
            )
        ]
    )


def get_wine_content():
    return html.Div(
        className='wine-container',
        id='wine-content-top',
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
            ),

            # Restaurant selection div
            html.Div(
                className='wine-restaurants-wrapper',
                children=[
                    # Wrapper for both button and star filter
                    html.Div(
                        className='wine-restaurants-controls',
                        # Flexbox for side-by-side layout
                        children=[
                            # Region dropdown
                            html.Div(
                                className='wine-map-outlines',
                                children=[
                                    html.H6("Show Regions or Departments"),
                                    dcc.Dropdown(
                                        id='granularity-dropdown-wine',
                                        options=[
                                            {'label': 'Regions', 'value': 'region'},
                                            {'label': 'Departments', 'value': 'department'}
                                        ],
                                        value=None,  # Default selection
                                        className='dropdown-granularity-wine',
                                        multi=False,
                                        clearable=True
                                    )
                                ],
                                style={'width': '20%'}
                            ),
                            # Toggle to show restaurant details
                            html.Div(
                                className='toggle-details-container',
                                children=[
                                    dbc.Button(
                                        "Show Starred Restaurants",
                                        id='toggle-show-details-wine',
                                        n_clicks=0,
                                        className='button-show-details'
                                    )
                                ],
                            ),
                            # Star filter specific to wine page
                            html.Div(
                                className='star-filter-container',
                                children=[
                                    dcc.Store(id='selected-stars-wine', data=[]),
                                    star_filter_section(star_placeholder, filter_type="wine", exclude_stars=[0.5]),
                                ],
                                style={'width': '30%'}  # Set filter width to 30% of parent div
                            ),
                        ]
                    )
                ]
            ),

            # Main Content for wine (Map + LLM Section)
            html.Div(
                className='wine-content-wrapper',
                children=[
                    # Map section
                    html.Div(
                        className='wine-map',
                        children=[
                            dcc.Graph(
                                id='wine-map-graph',
                                config={'displayModeBar': False}
                            )
                        ],
                        style={'width': '50%', 'display': 'inline-block'}
                    ),
                    # LLM output section
                    html.Div(
                        className='wine-llm-output',
                        children=[
                            html.Div(
                                className='wine-llm-text',
                                children=[
                                    html.H5("Wine Region Information"),
                                    html.P(
                                        """
                                        Select a wine region on the map to get interactive descriptions, 
                                        grape varieties, and wine pairing recommendations.
                                        """
                                    ),
                                    html.Div(
                                        id='llm-output-container',
                                        children=[
                                            # Placeholder for future LLM content
                                            dcc.Markdown(
                                                """
                                                This is where recommendations and details will appear.
                                                Interact with the map to start exploring wine regions.
                                                """
                                            )
                                        ],
                                    ),
                                ],
                            )
                        ],
                        style={'width': '50%', 'display': 'inline-block'}
                    ),
                ],
            )
        ]
    )


def get_analysis_content():
    return html.Div(
        className='analysis-container',
        id='analysis-content-top',
        children=[
            get_department_region_section(),  # Department and Region Section
            get_top_ranking_section(),        # Top Ranking Section
            get_demographics_content(),       # Demographics Section
            get_wine_content(),               # Wine section
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
            get_analysis_content(),
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
