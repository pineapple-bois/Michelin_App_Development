from dash import html, dcc
import dash_bootstrap_components as dbc

from app.components.shared import (
    bib_gourmand,
    color_map,
    get_footer,
    get_header_with_buttons,
    green_star,
    inverted_bib_gourmand,
    inverted_michelin_stars,
    michelin_stars,
)

GUIDE_HIDDEN_RATING_BUTTON_CLASS = 'guide-rating-button-hidden'

star_placeholder = (0.25, 0.5, 1, 2, 3)

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


def get_city_match_section():
    return html.Div(
        className='city-match-content-wrapper-mainpage guide-sidebar-search clearfix',
        children=[
            # Info tab to unfold the search bar
            html.Div(
                children=[
                    html.Button(
                        "Search Locations",
                        id="info-toggle-button",
                        className=(
                            'info-toggle-button editorial-action-button '
                            'guide-search-toggle'
                        )
                    )
                ],
                className='info-tab-container'
            ),
            # Collapsible content for the search bar
            dbc.Collapse(
                id='info-collapse',
                is_open=False,  # Initially closed
                children=[
                    html.Div(
                        className='city-match-sidebar-mainpage',
                        children=[
                            html.Div(
                                className='city-input-container-mainpage',
                                children=[
                                    dcc.Input(
                                        id='city-input-mainpage',
                                        type='text',
                                        placeholder='Enter a location in France',
                                        debounce=True,
                                        className='city-input-field guide-search-input'
                                    ),
                                    # Submit button
                                    html.Button('Submit', id='submit-city-button-mainpage', n_clicks=0,
                                                className=(
                                                    'submit-city-button-mainpage editorial-action-button '
                                                    'guide-search-action guide-search-submit'
                                                )),
                                    # Clear button
                                    html.Button('Clear', id='clear-city-button-mainpage', n_clicks=0,
                                                className=(
                                                    'clear-city-button-mainpage editorial-action-button '
                                                    'guide-search-action guide-search-clear'
                                                ))
                                ]
                            ),
                        ],
                    ),
                ]
            )
        ]
    )


# Define the row with buttons logic as functions
def create_star_button(value, label, type_name='filter-button-mainpage'):
    # Generate color with reduced opacity for active state
    normal_bg_color = color_map[value]
    return dbc.Button(
        label,
        id={
            'type': type_name,
            'index': value,
        },
        className=(
            "me-1 star-button editorial-rating-button guide-rating-button"
        ),
        outline=True,
        style={
            'display': 'inline-block',
            'backgroundColor': normal_bg_color,
            'width': '100%',
            'opacity': 1
        },
        n_clicks=0,
    )


def star_filter_section(available_stars=star_placeholder):
    standard_stars = [s for s in available_stars if s != 0.25]
    has_selected = 0.25 in available_stars

    star_buttons = [
        create_star_button(
            star,
            inverted_michelin_stars(star) if star in [1, 2, 3] else inverted_bib_gourmand(),
            type_name='filter-button-mainpage'
        )
        for star in standard_stars
    ]

    toggle_button = html.Button(
        "Selected",
        id="toggle-selected-btn",
        n_clicks=0,
        className=(
            "selected-toggle-button editorial-rating-button "
            "guide-rating-button guide-rating-selected"
        ),
        style={'display': 'block'}
    )

    def hidden_toggle_button():
        return html.Button(
            "",
            id="toggle-selected-btn",
            n_clicks=1,
            className=(
                "selected-toggle-button editorial-rating-button "
                "guide-rating-button guide-rating-selected "
                f"{GUIDE_HIDDEN_RATING_BUTTON_CLASS}"
            ),
            style={"display": "none"}
        )

    # Shared layout title
    title = html.H6(
        "Filter by Michelin Rating",
        className='star-select-title editorial-control-label guide-control-label'
    )

    # Case 1: inline (fits in same row)
    if has_selected and 1 <= len(standard_stars) <= 3:
        star_buttons.append(toggle_button)
        return html.Div([
            title,
            html.Div(
                star_buttons,
                className=(
                    'star-filter-buttons editorial-rating-filter-row '
                    'guide-rating-filter-row'
                )
            )
        ], className=(
            'star-filter-section editorial-rating-filters guide-rating-filters'
        ), id='star-filter', style={'display': 'none'})

    # Case 2: only 0.25 available → show selected on its own row, 50% width
    elif has_selected and not standard_stars:
        return html.Div([
            title,
            html.Div(
                [
                    html.Div(toggle_button, className='selected-toggle-inner'),
                    html.Div(className='selected-toggle-spacer')
                ],
                className='selected-toggle-wrapper'
            )
        ], className=(
            'star-filter-section editorial-rating-filters guide-rating-filters'
        ), id='star-filter', style={'display': 'none'})

    # Case 3: single available bib → show on its own row, 50% width
    elif not has_selected and standard_stars == [0.5]:
        return html.Div([
            title,
            html.Div(
                [
                    html.Div(star_buttons[0], className='selected-toggle-inner'),
                    html.Div(className='selected-toggle-spacer')
                ],
                className='selected-toggle-wrapper'
            ),
            hidden_toggle_button()
        ], className=(
            'star-filter-section editorial-rating-filters guide-rating-filters'
        ), id='star-filter', style={'display': 'none'})

    # Case 4: selected on a new row, wrapped in its own aligned container
    elif has_selected:
        return html.Div([
            title,
            html.Div(
                star_buttons,
                className=(
                    'star-filter-buttons editorial-rating-filter-row '
                    'guide-rating-filter-row'
                )
            ),
            html.Div(
                [
                    html.Div(toggle_button, className='selected-toggle-inner'),
                    html.Div(className='selected-toggle-spacer'),
                    html.Div(className='selected-toggle-spacer'),
                    html.Div(className='selected-toggle-spacer')
                ],
                className='selected-toggle-wrapper'
            )
        ], className=(
            'star-filter-section editorial-rating-filters guide-rating-filters'
        ), id='star-filter', style={'display': 'none'})

    # Case 5: no toggle at all (fallback)
    else:
        return html.Div([
            title,
            html.Div(
                star_buttons,
                className=(
                    'star-filter-buttons editorial-rating-filter-row '
                    'guide-rating-filter-row'
                )
            ),
            hidden_toggle_button()
        ], className=(
            'star-filter-section editorial-rating-filters guide-rating-filters'
        ), id='star-filter', style={'display': 'none'})


def get_main_content_with_city_match(unique_regions):
    # City match section
    city_match_section = get_city_match_section()

    # Sidebar content (existing sidebar)
    sidebar_content = html.Div([
        city_match_section,

        # Dropdown blocks wrapped in a flex container
        html.Div([
            html.Div([
                html.H6(
                    "Select a Region",
                    className='dropdown-title editorial-control-label guide-control-label'
                ),
                dcc.Dropdown(
                    id='region-dropdown',
                    options=[{'label': region, 'value': region} for region in unique_regions],
                    value=unique_regions[0],
                    className='dropdown-style editorial-select guide-select',
                    clearable=False
                )
            ], className='dropdown-block editorial-control-group guide-control-group'),

            html.Div([
                html.H6(
                    "Select a Department",
                    className='dropdown-title editorial-control-label guide-control-label'
                ),
                dcc.Dropdown(
                    id='department-dropdown',
                    className='dropdown-style editorial-select guide-select'
                )
            ], className='dropdown-block editorial-control-group guide-control-group'),

            html.Div(
                id='arrondissement-dropdown-container',
                className=(
                    'dropdown-block editorial-control-group guide-control-group '
                    'hidden-paris-section'
                ),  # Initially hidden
                children=[
                    html.H6(
                        "Select an Arrondissement",
                        className='dropdown-title editorial-control-label guide-control-label'
                    ),
                    dcc.Dropdown(
                        id='arrondissement-dropdown',
                        className='dropdown-style editorial-select guide-select',
                        clearable=False
                    )
                ],
            ),
        ], className='dropdowns-container-main'),  # Flex container for dropdowns

        # Buttons and restaurant details
        html.Div([
            star_filter_section(star_placeholder),
            html.Div(
                id='restaurant-details',
                children=[],
                className=(
                    'restaurant-details-container editorial-info-panel '
                    'guide-restaurant-panel'
                )
            )
        ], className='star-ratings-and-details-container guide-sidebar-results')

    ], className='sidebar-container guide-sidebar')

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
        ),
        html.Div(
            className='city-match-main-content-mainpage guide-map-match-overlay',
            children=[
                html.Div(
                    id='matched-city-output-mainpage',
                    className='city-match-output-container-mainpage'
                )
            ],
        ),
        dcc.Store(id='map-view-store-mainpage', data={}),
    ], className='map-section guide-map-panel')

    # Star Ratings Section (below map and sidebar)
    star_ratings_section = html.Div(
        className=(
            'star-ratings-container-main editorial-note guide-rating-legend'
        ),
        children=[
            html.Div(
                children=[
                    html.P(michelin_stars(3), className='star-description-title'),
                    html.P('Exceptional cuisine', className='star-description-title'),
                    html.P('Worth a special journey', className='star-description-text'),
                ], className='three-child guide-rating-legend-item'
            ),
            html.Div(
                children=[
                    html.P(michelin_stars(2), className='star-description-title'),
                    html.P('Excellent cooking', className='star-description-title'),
                    html.P('Worth a detour', className='star-description-text'),
                ], className='two-child guide-rating-legend-item'
            ),
            html.Div(
                children=[
                    html.P(michelin_stars(1), className='star-description-title'),
                    html.P('High-quality cooking', className='star-description-title'),
                    html.P('Worth a stop', className='star-description-text'),
                ], className='one-child guide-rating-legend-item'
            ),
            html.Div(
                children=[
                    html.P([bib_gourmand()], className='star-description-title'),
                    html.P('Bib Gourmand', className='star-description-title'),
                    html.P('Good food at moderate prices', className='star-description-text'),
                ], className='bib-child guide-rating-legend-item'
            ),
            html.Div(
                children=[
                    html.P([green_star()], className='star-description-title'),
                    html.P('Green Star', className='star-description-title'),
                    html.P('High sustainability standards', className='star-description-text'),
                ], className='green-child guide-rating-legend-item'
            ),
        ],
    )

    # Combine all sections into the main content layout
    return html.Div([
        html.Div([
            map_section,
            sidebar_content,
        ], className='map-sidebar-container guide-responsive-layout'),
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
            html.Div(
                className='guide-page-sheet editorial-sheet',
                children=[
                    get_main_content_with_city_match(unique_regions)
                ]
            )
        ],
        className='body guide-page-frame editorial-page-frame'
    )

    footer = get_footer()

    # Combine all sections into the main layout
    return html.Div([
        header,
        body,
        footer
    ], className='main-layout')
