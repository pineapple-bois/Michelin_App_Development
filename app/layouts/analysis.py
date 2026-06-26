from dash import html, dcc
import dash_bootstrap_components as dbc

from app.layouts.analysis_shared import (
    get_analysis_page_layout,
    star_filter_section,
    star_placeholder,
    unique_regions,
)

def michelin_star_header(count):
    return [
        html.Img(
            src="assets/images/michelin_star.png",
            className='michelin-star-header',
            style={'width': '25px', 'vertical-align': 'middle'}
        )
        for _ in range(int(count))
    ]


def green_star_header():
    return html.Img(
            src="assets/images/michelin_green_star.png",
            className='green-star-header',
            style={'width': '27px', 'vertical-align': 'middle'}
        )


def get_regions_section():
    return html.Div(
        className='region-content-wrapper clearfix editorial-section',  # Wrapper to couple sidebar and content for regions
        children=[
            # Description section (100% width)
            html.Div(
                children=[
                    html.Div(
                        className='distribution-header editorial-page-title',
                        children=[
                        "Restaurant Distributions Across France"
                        ],
                    ),
                    html.Div(
                        className='distribution-section-header',
                        children=[
                            "Regions"
                        ],
                    ),
                    html.Div(
                        className='region-description editorial-page-description',
                        children=[
                            "France is divided into 13 metropolitan regions, each with its own unique culinary heritage. "
                            "Use the controls below to subset France into regions like ‘North & South’, compare neighboring regions, or remove outliers. "
                            "How do Michelin-rated restaurants vary across regions?"
                        ],
                    )
                ]
            ),

            # Dropdown and star filter section (50% width each)
            html.Div(
                className='region-controls editorial-control-row',
                children=[
                    html.Div(
                        className='region-filter-container editorial-control-group',
                        children=[
                            html.P("Add or Remove Regions of France", className='region-filter-title editorial-control-label'),
                            dcc.Dropdown(
                                id='region-dropdown-analysis',
                                options=[{'label': 'Select All', 'value': 'all'}] +
                                        [{'label': region, 'value': region} for region in unique_regions],
                                value=unique_regions,  # All regions selected by default
                                className='dropdown-region-analysis editorial-select editorial-chip-select',
                                multi=True,  # Multi-select enabled
                                clearable=True
                            ),
                        ],
                    ),
                    # Star filter specific to analysis page
                    html.Div(
                        className='star-filter-container-region editorial-control-group',
                        children=[
                            dcc.Store(id='selected-stars-analysis', data=[]),
                            star_filter_section(star_placeholder, filter_type="analysis"),
                        ],
                    )
                ],
            ),
            # Main content for regions
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
                                style={'width': '50%', 'display': 'inline-block'}
                            ),
                            html.Div(
                                className='region-map',
                                children=[
                                    dcc.Graph(
                                        id='region-map',
                                        config={'displayModeBar': False}
                                    )
                                ],
                                style={'width': '50%', 'display': 'inline-block'}
                            )
                        ]
                    )
                ],
            )
        ]
    )


def get_departments_section():
    return html.Div(
        className='department-content-wrapper clearfix editorial-section',
        children=[
            html.Div(
                children=[
                    html.Div(
                        className='distribution-section-header',
                        children=[
                            "Departments"
                        ],
                    ),
                    html.Div(
                        className='department-description editorial-section-description',
                        children=[
                            "France is further divided into 96 departments, which are smaller administrative regions. "
                            "Use the dropdown to filter the data by a particular region and analyse how the distribution of Michelin-rated restaurants varies across that region's departments."
                        ]
                    ),
                ]
            ),


            # Dropdown and star filter section (50% width each)
            html.Div(
                className='department-controls editorial-control-row',
                children=[
                    html.Div(
                        className='department-filter-container editorial-control-group',
                        children=[
                            html.P("Select a Region of France", className='region-filter-title editorial-control-label'),
                            dcc.Store(id='departments-store', data=[]),    # will serve the arrondissements filter
                            dcc.Dropdown(
                                id='department-dropdown-analysis',
                                options=[{'label': region, 'value': region} for region in unique_regions],
                                className='dropdown-department-analysis editorial-select',
                                multi=False,  # Single selection enabled
                                clearable=True
                            ),
                        ],
                    ),
                    # Star filter specific to department page
                    html.Div(
                        className='star-filter-container-department editorial-control-group',
                        id='star-filter-container-department',
                        children=[
                            dcc.Store(id='selected-stars-department', data=[]),
                            star_filter_section(star_placeholder, filter_type="department"),
                        ],
                    )
                ],
            ),
            # Main content for departments
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
                            ),
                            html.Div(
                                className='department-map',
                                children=[
                                    dcc.Graph(
                                        id='department-map',
                                        config={'displayModeBar': False}
                                    )
                                ],
                            )
                        ]
                    )
                ],
            )
        ]
    )


def get_arrondissements_section():
    return html.Div(
        id='arrondissement-content-wrapper',
        className='hidden-section clearfix editorial-section',  # Starts as hidden, becomes visible when needed
        children=[
            # Description section (100% width)
            html.Div(
                children=[
                    html.Div(
                        className='distribution-section-header',
                        children=[
                            "Arrondissements"
                        ],
                    ),
                    html.Div(
                        className='arrondissement-description editorial-section-description',
                        children=[
                            "France's departments are then divided into arrondissements which could represent a neighbourhood in a large city, a medium to large conurbation or a larger rural area. "
                            "Use the dropdown to filter by department and analyse how Michelin-starred restaurants are distributed across arrondissements."
                        ]
                    ),
                ]
            ),

            # Dropdown and star filter section (50% width each)
            html.Div(
                className='arrondissement-controls editorial-control-row',
                children=[
                    html.Div(
                        className='arrondissement-filter-container editorial-control-group',
                        children=[
                            html.P(
                                id='arrondissement-filter-title',
                                children="Select a Department of France",  # Default display
                                className='region-filter-title editorial-control-label'),
                            dcc.Dropdown(
                                id='arrondissement-dropdown-analysis',
                                placeholder="Please select a region first",  # Placeholder
                                options=[],  # Will be populated dynamically
                                className='dropdown-arrondissement-analysis editorial-select',
                                multi=False,  # Single selection enabled
                                clearable=True
                            ),
                        ],
                    ),
                    # Star filter specific to arrondissement page
                    html.Div(
                        className='star-filter-container-arrondissement editorial-control-group',
                        id='star-filter-container-arrondissement',
                        children=[
                            dcc.Store(id='selected-stars-arrondissement', data=[]),
                            star_filter_section(star_placeholder, filter_type="arrondissement"),
                        ],
                    )
                ],
            ),

            # Main content for arrondissements (graph and map, 50% each)
            html.Div(
                className='arrondissement-main-content',
                children=[
                    html.Div(
                        className='arrondissement-visuals',
                        children=[
                            html.Div(
                                className='arrondissement-graph',
                                children=[
                                    dcc.Graph(
                                        id='arrondissement-analysis-graph',
                                        config={'displayModeBar': False}
                                    )
                                ],
                                style={'width': '50%', 'display': 'inline-block'}
                            ),
                            html.Div(
                                className='arrondissement-map',
                                children=[
                                    dcc.Graph(
                                        id='arrondissement-map',
                                        config={'displayModeBar': False}
                                    )
                                ],
                                style={'width': '50%', 'display': 'inline-block'}
                            )
                        ]
                    )
                ],
            )
        ]
    )


def build_region_distribution_section():
    return get_regions_section()


def build_department_distribution_section():
    return get_departments_section()


def build_arrondissement_distribution_section():
    return get_arrondissements_section()


def build_restaurant_distribution_section():
    return html.Div(
        children=[
            # Region Section (both sidebar and main content)
            build_region_distribution_section(),

            # Department Section (both sidebar and main content)
            build_department_distribution_section(),

            # Arrondissement Section (both sidebar and main content)
            build_arrondissement_distribution_section()
        ]
    )


def get_analysis_section():
    return build_restaurant_distribution_section()


def get_top_ranking_section():
    return html.Div(
        className='ranking-content-wrapper editorial-section',  # Wrapper for the entire section
        children=[
            html.Div(
                "Where are France’s top Michelin awards?",
                className="ranking-header",
            ),
            html.Div(
                className="ranking-description editorial-section-description",
                children=[
                    "Compare regions, departments, and arrondissements by three-star, two-star, or Green Star restaurants.",
                    html.Br(),
                    "Choose a view and rating to update the list.",
                ],
            ),

            # Dropdown and filter selection section (100% width, split between dropdowns)
            html.Div(
                className='ranking-controls editorial-control-row',
                children=[
                    # Granularity dropdown (Region/Department/Arrondissement)
                    html.Div(
                        className='granularity-filter-container editorial-control-group',
                        children=[
                            html.H6("Select Granularity", className='editorial-control-label'),
                            dcc.Dropdown(
                                id='granularity-dropdown',
                                options=[
                                    {'label': 'Regions', 'value': 'region'},
                                    {'label': 'Departments', 'value': 'department'},
                                    {'label': 'Arrondissements', 'value': 'arrondissement'}
                                ],
                                className='dropdown-granularity editorial-select',  # Class for styling
                                multi=False,  # Single selection
                                clearable=True
                            )
                        ],
                    ),
                    # Top 3 or Top 5 dropdown
                    html.Div(
                        className='top-ranking-filter-container editorial-control-group',
                        children=[
                            html.H6("Select 'Top 3' or 'Top 5'", className='editorial-control-label'),
                            dcc.Dropdown(
                                id='ranking-dropdown',
                                options=[
                                    {'label': 'Top 3 (excluding Paris)', 'value': 3},
                                    {'label': 'Top 5 (excluding Paris)', 'value': 5},
                                    {'label': 'Paris', 'value': 1}  # Option for Paris
                                ],
                                value=3,  # Default to Top 3
                                className='dropdown-ranking editorial-select',  # Class for styling
                                multi=False,  # Single selection
                                clearable=False
                            )
                        ],
                    ),
                    # Dropdown for selecting greenstar, 2- or 3-star restaurants
                    html.Div(
                        className='rating-filter-container editorial-control-group',
                        children=[
                            html.H6("Filter by Michelin Rating", className='editorial-control-label'),
                            dcc.Dropdown(
                                id='star-dropdown-ranking',
                                options=[
                                    {'label': 'Two Stars', 'value': 2},
                                    {'label': 'Three Stars', 'value': 3},
                                    {'label': 'Green Star', 'value': 'green'}
                                ],
                                value=2,  # Default selection
                                className='dropdown-star-ranking editorial-select',
                                multi=False,  # Single selection
                                clearable=False
                            )
                        ]
                    ),
                    # Toggle to show restaurant details
                    html.Div(
                        className='toggle-details-container editorial-control-group',
                        children=[
                            dbc.Button(
                                "Show Restaurant Details",
                                id='toggle-show-details',
                                n_clicks=0,
                                className='button-show-details editorial-action-button'
                            )
                        ]
                    ),
                ],
            ),

            # Main content for rankings (results section)
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
                ]
            )
        ]
    )


def build_rankings_section():
    return get_top_ranking_section()


def build_analysis_sections():
    return [
        build_restaurant_distribution_section(),
        build_rankings_section(),
    ]


def build_analysis_page_content():
    return html.Div(
        className='analysis-container editorial-sheet editorial-page',
        id='analysis-content-top',
        children=build_analysis_sections()
    )


def get_analysis_content():
    return build_analysis_page_content()


def get_analysis_layout():
    return get_analysis_page_layout(get_analysis_content())
