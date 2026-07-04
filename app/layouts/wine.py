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
                            "Explore France’s ",
                            html.A(
                                "Appellations d’Origine Contrôlée (AOC)",
                                href="https://www.inao.gouv.fr/en/aop-appellation-origine-protegee",
                                target="_blank",
                                rel="noopener noreferrer",
                            ),
                            " on the map. Overlay Michelin-starred restaurants to see which restaurants "
                            "sit within or near each appellation.",
                        ],
                        className="wine-text-paragraph editorial-page-description",
                    )
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
                            html.Div(
                                className='wine-region-selector-container editorial-control-group',
                                children=[
                                    html.H6("Wine Region", className='editorial-control-label'),
                                    dcc.Dropdown(
                                        id='wine-region-selector',
                                        options=[],
                                        value=None,
                                        className='dropdown-region-wine editorial-select',
                                        searchable=True,
                                        clearable=True,
                                        placeholder="Select region...",
                                    )
                                ],
                            ),
                            html.Div(
                                className='wine-appellation-search-container editorial-control-group',
                                children=[
                                    html.H6("Search Appellation", className='editorial-control-label'),
                                    dcc.Dropdown(
                                        id='wine-appellation-search',
                                        options=[],
                                        value=None,
                                        className='dropdown-appellation-wine editorial-select',
                                        searchable=True,
                                        clearable=True,
                                        placeholder="Search by appellation...",
                                    )
                                ],
                            ),
                            html.Div(
                                className='wine-map-outlines editorial-control-group',
                                children=[
                                    dbc.Button(
                                        "Regional outlines",
                                        id='toggle-regional-outlines-wine',
                                        n_clicks=0,
                                        active=False,
                                        className='button-show-details editorial-action-button editorial-toggle-button',
                                    ),
                                ],
                                style={'width': '20%'},
                            ),
                            html.Div(
                                className='toggle-details-container-wine editorial-control-group',
                                children=[
                                    dbc.Button(
                                        "Starred restaurants",
                                        id='toggle-show-details-wine',
                                        n_clicks=0,
                                        active=False,
                                        className='button-show-details editorial-action-button editorial-toggle-button',
                                    )
                                ],
                            ),
                            # Star filter specific to wine page
                            html.Div(
                                className='star-filter-container editorial-control-group',
                                id='star-filter-container-wine',
                                children=[
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
                            dcc.Graph(
                                id='wine-map-graph',
                                clear_on_unhover=True,
                                config={'displayModeBar': False},
                                style={'height': '700px'},
                            ),
                            html.Div(
                                id='wine-map-hover-overlay',
                                className='wine-map-hover-overlay',
                                hidden=True,
                                children=[
                                    html.Div(
                                        id='wine-map-hover-appellation',
                                        className='wine-map-hover-appellation',
                                    ),
                                    html.Div(
                                        id='wine-map-hover-region',
                                        className='wine-map-hover-region',
                                    ),
                                ],
                            ),
                            dcc.Store(id='map-view-store', data={}),    # Store to hold map view parameters
                            dcc.Store(id='wine-map-ready', data=False),
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
                                    html.H5(
                                        [
                                            html.I("Appellation d'origine contrôlée"),
                                            " (AOC)",
                                        ],
                                        className='wine-title',
                                    ),
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
                                                                        This content is generated by GPT-4.1 mini 
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
