from dash import html, dcc
import dash_bootstrap_components as dbc


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


#  wikipedia image links:
# https://upload.wikimedia.org/wikipedia/commons/a/ad/MichelinStar.svg
# https://upload.wikimedia.org/wikipedia/commons/6/6e/Michelin_Bib_Gourmand.png


# Standard michelin images
def michelin_stars(count):
    # Returns a list of image components for each star
    return [html.Img(src="assets/Images/Michelin_star.png",
                     className='michelin-star',
                     style={'width': '20px', 'vertical-align': 'middle', 'margin-right': '3px'}) for _ in range(int(count))]


def bib_gourmand():
    return html.Img(src="assets/Images/Michelin_Bib.png",
                    className='bib-image',
                    style={'width': '20px', 'vertical-align': 'middle'})


# Inverted michelin images
def inverted_michelin_stars(count):
    # Returns a list of Michelin star image components each with inverted colors
    return [html.Img(src="assets/Images/Michelin_star.png",
                     className='michelin-star',
                     style={'width': '16px', 'vertical-align': 'middle', 'margin-right': '2px', 'filter': 'brightness(0) invert(1)'}) for _ in range(int(count))]


def inverted_bib_gourmand():
    # Returns the Bib Gourmand image component with inverted colors
    return html.Img(src="assets/Images/Michelin_Bib.png",
                    className='bib-image',
                    style={'width': '16px', 'vertical-align': 'middle', 'filter': 'brightness(0) invert(1)'})


def get_header_with_buttons():
    return html.Div(
        children=[
            html.Div([
                html.H1(["Michelin Guide to France. ", html.Span("2024", className='year-text')],
                        className='title-section'),
                ], className='header-title'
            ),
            html.Div(
                [
                    dbc.Button("Guide", href='/', id='home-button', className='header-button', color='primary'),
                    dbc.Button("Analysis", href='/analysis', id='analysis-button', className='header-button', color='secondary')
                ],
                className='header-buttons'
            )
        ], className='header-container'
    )


def get_city_match_section():
    return html.Div(
            className='city-match-content-wrapper-mainpage clearfix',
            # Wrapper to couple sidebar and content for the city match section
            children=[
                # Sidebar for city input - 30% width
                html.Div(
                    className='city-match-sidebar-mainpage',
                    children=[
                        html.Div(
                            children=[
                                "Search for a location in France",
                            ], className="city-match-description-mainpage"
                        ),
                        # Text entry field for city input
                        html.Div(
                            className='city-input-container-mainpage',
                            children=[
                                dcc.Input(
                                    id='city-input-mainpage',
                                    type='text',
                                    placeholder='Enter a city or location',
                                    className='city-input-field'
                                ),
                                # Submit button
                                html.Button('Submit', id='submit-city-button-mainpage', n_clicks=0,
                                            className='submit-city-button-mainpage'),
                                # Clear button
                                html.Button('Clear', id='clear-city-button-mainpage', n_clicks=0,
                                            className='clear-city-button-mainpage', style={'margin-left': '10px'})
                            ]
                        ),
                    ],
                    style={'width': '30%', 'float': 'left'}
                ),

                # Main content for matched results - 70% width
                html.Div(
                    className='city-match-main-content-mainpage',
                    children=[
                        # Placeholder for the matched city content
                        html.Div(
                            id='matched-city-output-mainpage',
                            children=[
                                "Matched city details will be displayed here.",
                            ],
                            className='city-match-output-container-mainpage'
                        )
                    ],
                    style={'width': '70%', 'float': 'right'}
                )
            ]
        )


def get_footer():
    return html.Div(
        children=[
            html.Div(
                children=[
                    html.Img(src="assets/Images/github-mark.png", className='info-image'),
                    html.Div(
                        children=[
                            html.Span("The Michelin Guide to France was built from this ", className='info-text'),
                            dcc.Link("GitHub Repository", href="https://github.com/pineapple-bois/Michelin_Rated_Restaurants",
                                     target="_blank", className='info-link'),
                            html.Div("© pineapple-bois 2024", className='info-footer')
                        ],
                        style={'flexDirection': 'column'}  # Stack the text and the new line on top of each other
                    )
                ],
                className='info-container'  # Inner container
            )
        ],
        className='footer-main'  # Main div for debug coloring
    )


# Define the row with buttons logic as functions
def create_star_button(value, label):
    # Generate color with reduced opacity for active state
    normal_bg_color = color_map[value]
    return dbc.Button(
        label,
        id={
            'type': 'filter-button',
            'index': value,
        },
        className="me-1 star-button",
        outline=True,
        style={
            'display': 'inline-block',
            'backgroundColor': normal_bg_color,
            'width': '100%',
            'opacity': 1
        },
        n_clicks=0,
    )


def star_filter_row(available_stars):
    # Create a button for each available star rating
    buttons = [create_star_button(star, inverted_michelin_stars(star) if star != 0.5 else inverted_bib_gourmand()) for star in available_stars]
    return html.Div(buttons, className='star-filter-buttons')


def star_filter_section(available_stars=star_placeholder):
    star_buttons = star_filter_row(available_stars)
    return html.Div([
        html.H6("Filter by Michelin Rating", className='star-select-title'),
        star_buttons
    ], className='star-filter-section', id='star-filter', style={'display': 'none'})


def get_main_content_with_city_match(unique_regions):
    # City match section
    city_match_section = get_city_match_section()

    # Sidebar content (existing sidebar)
    sidebar_content = html.Div([
        html.Div([
                html.H5("Explore the finest culinary destinations in France, as reviewed by Michelin.", className='site-description')
            ], className='description-container'
        ),

        html.Div([
                html.P("France is divided administratively into regions and departments. Select a region to see the Michelin-rated restaurants by department.", className='instructions')
            ], className='instructions-container'
        ),

        html.Div([
                html.H6("Select a Region", className='dropdown-title'),
                dcc.Dropdown(id='region-dropdown', options=[{'label': region, 'value': region} for region in unique_regions], value=unique_regions[0], className='dropdown-style', clearable=False),
                html.H6("Select a Department", className='dropdown-title'),
                dcc.Dropdown(id='department-dropdown', className='dropdown-style')
            ], className='dropdown-container'
        ),
        # Arrondissement dropdown container (initially hidden)
        html.Div(
            id='arrondissement-dropdown-container',
            className='hidden-paris-section',
            children=[
                html.H6("Select an Arrondissement", className='dropdown-title'),
                dcc.Dropdown(
                    id='arrondissement-dropdown',
                    className='dropdown-style',
                    clearable=False
                )
            ],
        ),

        # Buttons
        star_filter_section(star_placeholder),

        html.Div(id='restaurant-details', children=[], className='restaurant-details-container'),
    ], className='sidebar-container')

    # Map section (existing map)
    map_section = html.Div([
        dcc.Graph(
            id='map-display',
            responsive=True,
            className='map-display',
            config={
                'displayModeBar': True,
                'scrollZoom': True,
                'modeBarButtonsToRemove': ['pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d',
                                           'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian',
                                           'toggleSpikelines', 'toImage'],
                'modeBarButtonsToAdd': ['zoom2d', 'resetScale2d']
            }
        )
    ], className='map-section')

    # Star Ratings Section (below map and sidebar)
    star_ratings_section = html.Div(
        className='star-ratings-container-main',  # Class for the parent container
        children=[
            html.Div(
                children=[
                    html.P(michelin_stars(3), className='star-description-title'),
                    html.P('Exceptional cuisine', className='star-description-title'),
                    html.P('Worth a special journey', className='star-description-text'),
                ], className='three-child'
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
                    html.P(michelin_stars(1), className='star-description-title'),
                    html.P('High-quality cooking', className='star-description-title'),
                    html.P('Worth a stop', className='star-description-text'),
                ], className='one-child'
            ),
            html.Div(
                children=[
                    html.P([bib_gourmand()], className='star-description-title'),
                    html.P('Bib Gourmand', className='star-description-title'),
                    html.P('Exceptionally good food at moderate prices', className='star-description-text'),
                ], className='bib-child'
            ),
        ],
    )

    # Combine all sections into the main content layout
    return html.Div([
        city_match_section,
        html.Div([
            map_section,
            sidebar_content,
        ], className='map-sidebar-container'),
        star_ratings_section
    ], className='main-content')


def get_main_layout():
    # Header with buttons
    header = html.Div(
        children=[
            get_header_with_buttons()
        ],
        className='header'
    )

    body = html.Div(
        children=[
            get_main_content_with_city_match(unique_regions)
        ],
        className='body'
    )

    footer = get_footer()

    # Combine all sections into the main layout
    return html.Div([
        header,
        body,
        footer
    ], className='main-layout')
