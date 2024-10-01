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

def michelin_star_header(count):
    # Returns a list of image components for each star
    return [html.Img(src="assets/Images/Michelin_star.png",
                     className='michelin-star',
                     style={'width': '25px', 'vertical-align': 'middle', 'margin-right': '4px'}) for _ in range(int(count))]


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


def get_intro_section():
    return html.Div(
        className='michelin-text-container',
        children=[
            html.Div(
                [
                    "Michelin introduced its ",
                    html.A("star ranking system for restaurants",
                           href="https://guide.michelin.com/gb/en/about-us", target="_blank"),
                    " to France in 1936. Today, over 40 countries are represented in a Michelin Guide, and globally, approximately 3,500 restaurants have been awarded one, two, or three stars. Of these, over 600 are in France, the spiritual home of ",
                    html.I("Le Guide Rouge"),
                    "."
                ],
                className='michelin-title-paragraph'
            ),
            html.Div(
                [
                    "Earning a Michelin Star can be the pinnacle of a chef’s career. Keeping one requires drive, determination, and consistency. The pressures of maintaining a third star can be overwhelming, as tragically illustrated by the story of ",
                    html.A("Bernard Loiseau",
                           href="https://www.newyorker.com/magazine/2003/05/12/death-of-a-chef",
                           target="_blank"),
                    ". In contrast, in 2017, Sébastien Bras made the unprecedented decision to voluntarily ",
                    html.A("hand back his three-star rating",
                           href="https://www.theguardian.com/world/2017/sep/20/sebastien-bras-french-chef-three-michelin-stars-le-suquet-laguiole",
                           target="_blank"),
                    ", choosing freedom from the intense expectations that come with such an award. "
                    "Chefs in France affectionately refer to Michelin Stars as 'macarons', a fitting simile for the elusive nature of perfection—much like the delicate art of baking the perfect macaron."
                ],
                className='michelin-text-paragraph'
            ),

            html.Div(
                className='star-ratings-container',  # Class for the parent container
                children=[
                    html.Div(
                        children=[
                            html.P([bib_gourmand()], className='star-description-title'),
                            html.P('Bib Gourmand', className='star-description-title'),
                            html.P('Exceptionally good food at moderate prices',
                                   className='star-description-text'),
                        ], className='bib-child'
                    ),
                    html.Div(
                        children=[
                            html.P(michelin_stars(1), className='star-description-title'),
                            html.P('High-quality cooking', className='star-description-title'),
                            html.P('Worth a stop', className='star-description-text'),
                        ], className='one-child'
                    ),
                    html.Div(
                        children=[
                            html.P(michelin_stars(2), className='star-description-title'),
                            html.P('Excellent cooking', className='star-description-title'),
                            html.P('Worth a detour', className='star-description-text'),
                        ], className='two-child'
                    ),
                    html.Div(
                        children=[
                            html.P(michelin_stars(3), className='star-description-title'),
                            html.P('Exceptional cuisine', className='star-description-title'),
                            html.P('Worth a special journey', className='star-description-text'),
                        ], className='three-child'
                    ),
                ]
            ),
        ],
    )


def get_regions_section():
    return html.Div(
        className='region-content-wrapper clearfix',  # Wrapper to couple sidebar and content for regions
        children=[
            # Description section (100% width)
            html.Div(
                children=[
                    html.Div(
                        className='distribution-header',
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
                        className='region-description',
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
                className='region-controls',
                children=[
                    html.Div(
                        className='region-filter-container',
                        children=[
                            html.P("Add or Remove Regions of France", className='region-filter-title'),
                            dcc.Dropdown(
                                id='region-dropdown-analysis',
                                options=[{'label': 'Select All', 'value': 'all'}] +
                                        [{'label': region, 'value': region} for region in unique_regions],
                                value=unique_regions,  # All regions selected by default
                                className='dropdown-region-analysis',
                                multi=True,  # Multi-select enabled
                                clearable=True
                            ),
                        ],
                    ),
                    # Star filter specific to analysis page
                    html.Div(
                        className='star-filter-container-region',
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
        className='department-content-wrapper clearfix',
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
                        className='department-description',
                        children=[
                            "France is further divided into 96 departments, which are smaller administrative regions. "
                            "Use the dropdown to filter the data by a particular region and analyse how the distribution of Michelin-rated restaurants varies across that region's departments."
                        ]
                    ),
                ]
            ),


            # Dropdown and star filter section (50% width each)
            html.Div(
                className='department-controls',
                children=[
                    html.Div(
                        className='department-filter-container',
                        children=[
                            html.P("Select a Region of France", className='region-filter-title'),
                            dcc.Store(id='departments-store', data=[]),    # will serve the arrondissements filter
                            dcc.Dropdown(
                                id='department-dropdown-analysis',
                                options=[{'label': region, 'value': region} for region in unique_regions],
                                className='dropdown-department-analysis',
                                multi=False,  # Single selection enabled
                                clearable=True
                            ),
                        ],
                    ),
                    # Star filter specific to department page
                    html.Div(
                        className='star-filter-container-department',
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
        className='hidden-section clearfix',  # Starts as hidden, becomes visible when needed
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
                        className='arrondissement-description',
                        children=[
                            "France's departments are then divided into arrondissements which could represent a neighbourhood in a large city, a medium to large conurbation or a larger rural area. "
                            "Use the dropdown to filter by department and analyse how Michelin-starred restaurants are distributed across arrondissements."
                        ]
                    ),
                ]
            ),

            # Dropdown and star filter section (50% width each)
            html.Div(
                className='arrondissement-controls',
                children=[
                    html.Div(
                        className='arrondissement-filter-container',
                        children=[
                            html.P(
                                id='arrondissement-filter-title',
                                children="Select a Department of France",  # Default display
                                className='region-filter-title'),
                            dcc.Dropdown(
                                id='arrondissement-dropdown-analysis',
                                placeholder="Please select a region first",  # Placeholder
                                options=[],  # Will be populated dynamically
                                className='dropdown-arrondissement-analysis',
                                multi=False,  # Single selection enabled
                                clearable=True
                            ),
                        ],
                    ),
                    # Star filter specific to arrondissement page
                    html.Div(
                        className='star-filter-container-arrondissement',
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


def get_analysis_section():
    return html.Div(
        children=[
            # Michelin Blurb section (common for both regions and departments)
            get_intro_section(),

            # Region Section (both sidebar and main content)
            get_regions_section(),

            # Department Section (both sidebar and main content)
            get_departments_section(),

            # Arrondissement Section (both sidebar and main content)
            get_arrondissements_section()
        ]
    )


def get_top_ranking_section():
    return html.Div(
        className='ranking-content-wrapper',  # Wrapper for the entire section
        children=[
            html.Div(
                className='ranking-header',
                children=[
                    "Most ",
                    *michelin_star_header(2),  # Unpack the list of images for 2 stars
                    " & ",
                    *michelin_star_header(3),  # Unpack the list of images for 3 stars
                    " Restaurants",
                ]
            ),
            # Description section (100% width)
            html.Div(
                className='ranking-description',
                children=[
                    "Which regions, departments, and arrondissements have the highest concentration of two and three star restaurants?",
                    html.Br(),
                    "Select the granularity and ranking criteria below to see the top culinary destinations in France."
                ]
            ),

            # Dropdown and filter selection section (100% width, split between dropdowns)
            html.Div(
                className='ranking-controls',
                children=[
                    # Granularity dropdown (Region/Department/Arrondissement)
                    html.Div(
                        className='granularity-filter-container',
                        children=[
                            html.H6("Select Granularity"),
                            dcc.Dropdown(
                                id='granularity-dropdown',
                                options=[
                                    {'label': 'Regions', 'value': 'region'},
                                    {'label': 'Departments', 'value': 'department'},
                                    {'label': 'Arrondissements', 'value': 'arrondissement'}
                                ],
                                className='dropdown-granularity',  # Class for styling
                                multi=False,  # Single selection
                                clearable=True
                            )
                        ],
                    ),
                    # Top 3 or Top 5 dropdown
                    html.Div(
                        className='top-ranking-filter-container',
                        children=[
                            html.H6("Select 'Top 3' or 'Top 5'"),
                            dcc.Dropdown(
                                id='ranking-dropdown',
                                options=[
                                    {'label': 'Top 3 (excluding Paris)', 'value': 3},
                                    {'label': 'Top 5 (excluding Paris)', 'value': 5},
                                    {'label': 'Paris', 'value': 1}  # Option for Paris
                                ],
                                value=3,  # Default to Top 3
                                className='dropdown-ranking',  # Class for styling
                                multi=False,  # Single selection
                                clearable=False
                            )
                        ],
                    ),
                    # Dropdown for selecting 2- or 3-star restaurants
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


def get_demographics_content():
    return html.Div(
        className='demographics-container',
        id='demographics-content-top',
        children=[
            html.Div(
                className='demographics-text-container',
                children=[
                    html.Div(
                        [
                            "Michelin Stars and the Economic Health of France"
                        ],
                        className='demographics-header'
                    ),
                    html.Div(
                        [
                            "We now turn our attention to key economic health metrics such as 'GDP per capita', 'poverty rate', and 'population density', with data sourced from the ",
                            html.A("National Institute of Statistics and Economic Studies (INSEE)",
                                   href="https://www.insee.fr/fr/accueil", target="_blank"),
                            ". While these metrics offer insights into the economic fabric of each region, they are just one part of a much larger picture. "
                            "Across France, patterns emerge that are influenced by a complex mix of factors—regional culture, economic conditions, and local identity to name a few. The observations that follow provide a starting point for deeper exploration."
                        ],
                        className='demographics-text-paragraph'
                    ),
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
                            html.H6("Select a Region to Show Selected Metric by Department"),
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
                                className='toggle-details-container-demographics',
                                children=[
                                    dbc.Button(
                                        "Overlay Starred Restaurants",
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
                                id='weighted-mean',
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
            html.Div(
                className='wine-text-container',
                children=[
                    html.Div(
                        [
                            "French Wine & Gastronomy"
                        ],
                        className='wine-header'
                    ),
                    html.Div(
                        [
                            "France’s wine regions are as diverse and storied as its cuisine. Each one tells a different tale through its vineyards, grape varieties, and winemaking traditions. "
                            "This tool offers a window into these regions, allowing you to explore their cultural significance and contribution to French gastronomy. "
                            "By overlaying Michelin-starred restaurants, you can explore how the relationship between food and wine plays out across the country, adding new layers to your understanding of French culinary excellence."
                        ],
                        className='wine-text-paragraph'
                    ),
                    html.Div(
                        [
                            html.I("Nunc est bibendum... À votre santé!"),
                        ],
                        className='wine-tagline-paragraph'
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
                                    html.H6("Show Regional Outlines"),
                                    dcc.Dropdown(
                                        id='granularity-dropdown-wine',
                                        options=[
                                            {'label': 'Regional Outlines', 'value': 'region'},
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
                                className='toggle-details-container-wine',
                                children=[
                                    dbc.Button(
                                        "Overlay Starred Restaurants",
                                        id='toggle-show-details-wine',
                                        n_clicks=0,
                                        className='button-show-details'
                                    )
                                ],
                            ),
                            # Star filter specific to wine page
                            html.Div(
                                className='star-filter-container',
                                id='star-filter-container-wine',
                                children=[
                                    dcc.Store(id='selected-stars-wine', data=[]),
                                    star_filter_section(star_placeholder, filter_type="wine", exclude_stars=[0.5]),
                                ],
                                style={'width': '30%', 'display': 'none'}  # Hidden by default
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
                            dcc.Graph(id='wine-map-graph',
                                      config={'displayModeBar': False},
                                       style={'height': '700px'}
                                      ),
                            dcc.Store(id='wine-region-curve-numbers'),  # Store for wine region curve numbers
                            dcc.Store(id='map-view-store', data={}),    # Store to hold map view parameters
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
                                    html.H5("Wine Region Information", className='wine-title'),
                                    dcc.Loading(
                                        id="loading-llm",
                                        type="circle",
                                        children=[
                                            # Placeholder for region name
                                            html.Div(id='region-name-container', className='region-name-placeholder'),
                                            # LLM content container
                                            html.Div(id='llm-output-container', className='LLM-output'),
                                            # Disclaimer div
                                            html.Div(
                                                id="disclaimer-container",  # ID for the disclaimer div
                                                children=[
                                                    # Wrapper to hold the logo and the disclaimer text side by side
                                                    html.Div(
                                                        className="disclaimer-content",
                                                        children=[
                                                            html.Img(
                                                                src="/assets/Images/openai-lockup.svg",
                                                                # Path to OpenAI logo
                                                                className="openai-logo"
                                                            ),
                                                            html.Div(
                                                                className="disclaimer-text-wrapper",
                                                                children=[
                                                                    html.P(
                                                                        """
                                                                        This content is generated by GPT-3.5 turbo and may not be 100% accurate. 
                                                                        """,
                                                                        className="disclaimer-text"
                                                                    ),
                                                                ]
                                                            )
                                                        ],
                                                    ),
                                                ],
                                            )
                                        ],
                                    ),
                                ],
                            ),
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
            get_analysis_section(),           # Department and Region Section
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
