from dash import html, dcc
import dash_bootstrap_components as dbc


def michelin_star():
    return html.Img(src="https://upload.wikimedia.org/wikipedia/commons/a/ad/MichelinStar.svg",
                    className='michelin-star',
                    style={'width': '20px', 'vertical-align': 'middle', 'margin-right': '3px'})


def bib_gourmand():
    return html.Img(src="https://upload.wikimedia.org/wikipedia/commons/6/6e/Michelin_Bib_Gourmand.png",
                    className='bib-image',
                    style={'width': '20px', 'vertical-align': 'middle'})


def get_info_div():
    return html.Div(
        children=[
            html.Img(src="assets/github-mark.png", className='info-image', style={'width': '30px'}),
            html.Div(
                children=[
                    html.Span("The Michelin Guide to France was built from this ", className='info-text'),
                    dcc.Link("GitHub Repository", href="https://github.com/pineapple-bois/Michelin_Rated_Restaurants",
                             target="_blank", className='info-link'),
                    html.Div("© pineapple-bois 2024", className='info-footer')
                ],
                style={'flexDirection': 'column'}  # This will stack the text and the new line on top of each other
            )
        ],
        className='info-container',
        style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-start', 'padding': '1rem'}
    )


def get_main_layout(unique_regions):
    # Title Section with Container Style
    title_section = html.Div(children=[
        html.H1(["Michelin Guide to France. ", html.Span("2024", className='year-text')], className='title-section')
    ], className='container-style')

    # Footer Section
    footer_section = html.Div(children=[
        get_info_div()
    ], className='footer-section', style={'width': '100%'})

    ratings_layout = html.Div([
        dbc.Row([
            # First Column
            dbc.Col([
                html.P([michelin_star(), michelin_star(), michelin_star()], className='star-description-title'),
                html.P('Exceptional cuisine', className='star-description-title'),
                html.P('Worth a special journey', className='star-description-text'),
                html.Br(),
                html.P(michelin_star(), className='star-description-title'),
                html.P('High-quality cooking', className='star-description-title'),
                html.P('Worth a stop', className='star-description-text'),
            ], width=6),
            # Second Column
            dbc.Col([
                html.P([michelin_star(), michelin_star()], className='star-description-title'),
                html.P('Excellent cooking', className='star-description-title'),
                html.P('Worth a detour', className='star-description-text'),
                html.Br(),
                html.P([bib_gourmand()], className='star-description-title'),
                html.P('Bib Gourmand', className='star-description-title'),
                html.P('Exceptionally good food at moderate prices', className='star-description-text'),
            ], width=6)
        ], className='ratings-row')
    ], className='ratings-container')

    # New Container Section with Map and Star Ratings Side by Side
    map_and_star_section = html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(
                id='map-display',
                responsive=True,
                className='map-display',
                config={
                    'displayModeBar': True,
                    'scrollZoom': True,
                    'modeBarButtonsToRemove': ['pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d',
                                               'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian',
                                               'toggleSpikelines', 'toImage'],
                    'modeBarButtonsToAdd': ['zoom2d', 'resetScale2d']}
            ), width=8),  # Set width as needed
            dbc.Col([
                # Container for Site Description
                html.Div([
                    html.H5("Explore the finest culinary destinations in France, as reviewed by Michelin.",
                            className='site-description')
                ], className='description-container'),

                # Container for Instructions
                html.Div([
                    html.P("France is divided administratively into regions and departments. "
                           "Select a region to see the Michelin-rated restaurants by department.",
                           className='instructions')
                ], className='instructions-container'),

                # Container for Region Dropdown
                html.Div([
                    html.H6("Select a Region", className='dropdown-title'),
                    dcc.Dropdown(
                        id='region-dropdown',
                        options=[{'label': region, 'value': region} for region in unique_regions],
                        value=unique_regions[0],  # Default value
                        className='dropdown-style',
                        clearable=False
                    )
                ], className='dropdown-container'),

                # Container for Department Dropdown
                html.Div([
                    html.H6("Select a Department", className='dropdown-title'),
                    dcc.Dropdown(
                        id='department-dropdown',
                        className='dropdown-style'
                    )
                ], className='dropdown-container'),

                # Placeholder container for restaurant details
                html.Div(id='restaurant-details', children=[
                    html.P("Select a restaurant on the map to view details here.", className='placeholder-text'),
                ], className='restaurant-details-container'),

                ratings_layout
            ], className='sidebar-container', width=4)
        ])
    ], className='sidebar-container')

    # Combine all sections into the main layout
    return html.Div([
        title_section,
        map_and_star_section,  # Replace map_display_section with map_and_star_section
        footer_section
    ])
