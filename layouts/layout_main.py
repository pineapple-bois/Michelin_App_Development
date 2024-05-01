import json
from dash import html, dcc
import dash_bootstrap_components as dbc

color_map = {
    0.5: "#640A64",
    1: "#FFB84D",
    2: "#FE6F64",
    3: "#C2282D"
}

star_placeholder = [0.5, 1, 2, 3]

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


def get_info_div():
    return html.Div(
        children=[
            html.Img(src="assets/Images/github-mark.png", className='info-image', style={'width': '30px'}),
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


def get_main_layout(unique_regions):
    title_section = html.Div(children=[
        html.H1(["Michelin Guide to France. ", html.Span("2024", className='year-text')], className='title-section')
    ], className='container-style')

    ratings_layout = html.Div([
        dbc.Row([
            # First Column
            dbc.Col([
                html.P(michelin_stars(3), className='star-description-title'),
                html.P('Exceptional cuisine', className='star-description-title'),
                html.P('Worth a special journey', className='star-description-text'),

                html.P(michelin_stars(1), className='star-description-title'),
                html.P('High-quality cooking', className='star-description-title'),
                html.P('Worth a stop', className='star-description-text'),
            ], width=6),
            # Second Column
            dbc.Col([
                html.P(michelin_stars(2), className='star-description-title'),
                html.P('Excellent cooking', className='star-description-title'),
                html.P('Worth a detour', className='star-description-text'),

                html.P([bib_gourmand()], className='star-description-title'),
                html.P('Bib Gourmand', className='star-description-title'),
                html.P('Exceptionally good food at moderate prices', className='star-description-text'),
            ], width=6)
        ])
    ], className='ratings-container')

    # Sidebar content, includes all controls and additional information
    star_button_row = star_filter_section(star_placeholder)
    sidebar_content = html.Div([
        html.Div([
            html.H5("Explore the finest culinary destinations in France, as reviewed by Michelin.", className='site-description')
        ], className='description-container'),

        html.Div([
            html.P("France is divided administratively into regions and departments. Select a region to see the Michelin-rated restaurants by department.", className='instructions')
        ], className='instructions-container'),

        html.Div([
            html.H6("Select a Region", className='dropdown-title'),
            dcc.Dropdown(id='region-dropdown', options=[{'label': region, 'value': region} for region in unique_regions], value=unique_regions[0], className='dropdown-style', clearable=False),
            html.H6("Select a Department", className='dropdown-title'),
            dcc.Dropdown(id='department-dropdown', className='dropdown-style')
        ], className='dropdown-container'),

        # Buttons
        star_button_row,

        html.Div(id='restaurant-details', children=[
        ], className='restaurant-details-container'),
        ratings_layout
    ], className='sidebar-container')

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

    # Footer Section
    footer_section = html.Div(children=[
        get_info_div()
    ], className='footer-section', style={'width': '100%'})

    # Combine all sections into the main layout
    return html.Div([
        title_section,
        sidebar_content,  # Sidebar contains top section and ratings details
        map_section,
        footer_section
    ], className='main-layout')
