from dash import html, dcc
import dash_bootstrap_components as dbc

from app.layouts.analysis_shared import (
    get_analysis_page_layout,
    star_filter_section,
    star_placeholder,
)


def get_wine_content():
    return html.Div(
        className='wine-container editorial-page',
        id='wine-content-top',
        children=[
            html.Div(
                className='wine-text-container editorial-section',
                children=[
                    html.Div(
                        [
                            "French Wine & Gastronomy"
                        ],
                        className='wine-header editorial-page-title'
                    ),
                    html.Div(
                        [
                            "Explore France’s wine regions on the map. Click a region to learn about its wines, grapes, and food traditions. ",
                            "Overlay Michelin-starred restaurants to see which restaurants sit within or near each region."
                        ],
                        className='wine-text-paragraph editorial-page-description'
                    ),
                ],
            ),
            # Restaurant selection div
            html.Div(
                className='wine-restaurants-wrapper',
                children=[
                    # Wrapper for both button and star filter
                    html.Div(
                        className='wine-restaurants-controls editorial-control-row',
                        # Flexbox for side-by-side layout
                        children=[
                            # Region dropdown
                            html.Div(
                                className='wine-map-outlines editorial-control-group',
                                children=[
                                    html.H6("Show Regional Outlines", className='editorial-control-label'),
                                    dcc.Dropdown(
                                        id='granularity-dropdown-wine',
                                        options=[
                                            {'label': 'Regional Outlines', 'value': 'region'},
                                        ],
                                        value=None,  # Default selection
                                        className='dropdown-granularity-wine editorial-select',
                                        multi=False,
                                        clearable=True,
                                    )
                                ],
                                style={'width': '20%'},
                            ),
                            # Toggle to show restaurant details
                            html.Div(
                                className='toggle-details-container-wine editorial-control-group',
                                children=[
                                    dbc.Button(
                                        "Overlay Starred Restaurants",
                                        id='toggle-show-details-wine',
                                        n_clicks=0,
                                        className='button-show-details editorial-action-button',
                                        disabled=True,
                                    )
                                ],
                                title='Restaurant overlays will return in the next Wine map phase.',
                            ),
                            # Star filter specific to wine page
                            html.Div(
                                className='star-filter-container editorial-control-group',
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
                className='wine-content-wrapper editorial-evidence editorial-evidence--map-led',
                children=[
                    # Map section
                    html.Div(
                        className='wine-map editorial-map',
                        children=[
                            dcc.Graph(id='wine-map-graph',
                                      config={'displayModeBar': False},
                                       style={'height': '700px'}
                                      ),
                            dcc.Store(id='map-view-store', data={}),    # Store to hold map view parameters
                        ],
                        style={'width': '50%', 'display': 'inline-block'}
                    ),
                    # LLM output section
                    html.Div(
                        className='wine-llm-output editorial-info-panel',
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
                                                className="editorial-note",
                                                children=[
                                                    # Wrapper to hold the logo and the disclaimer text side by side
                                                    html.Div(
                                                        className="disclaimer-content",
                                                        children=[
                                                            html.Img(
                                                                src="/assets/images/openai-lockup.svg",
                                                                # Path to OpenAI logo
                                                                className="openai-logo"
                                                            ),
                                                            html.Div(
                                                                className="disclaimer-text-wrapper",
                                                                children=[
                                                                    html.P(
                                                                        """
                                                                        This content is generated by GPT-4o mini and may not be 100% accurate. 
                                                                        """,
                                                                        className="disclaimer-text-ai"
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


def build_wine_section():
    return get_wine_content()


def build_wine_page_content():
    return html.Div(
        className='analysis-container editorial-sheet',
        children=[
            build_wine_section(),
        ]
    )


def get_wine_layout():
    return get_analysis_page_layout(build_wine_page_content())
