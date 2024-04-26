from dash import html, dcc
import dash_bootstrap_components as dbc


def get_main_layout(unique_regions, star_descriptions):
    # Title Section
    title_section = html.Div(
        html.H1("Michelin Guide to France 2024"),
        className='title-section'
    )

    # Dropdown Section
    dropdown_section = html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id='region-dropdown',
                    options=[{'label': region, 'value': region} for region in unique_regions],
                    value=unique_regions[0],  # Default value
                    className='dropdown-style'
                ),
                dcc.Dropdown(
                    id='department-dropdown',
                    className='dropdown-style'
                )
            ])
        ])
    ], className='dropdown-style')

    # Map Display Section
    map_display_section = html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Graph(
                    id='map-display',
                    responsive=True,
                    className='map-display',
                    config={
                        'displayModeBar': True,
                        'scrollZoom': True,
                        'modeBarButtonsToRemove': ['pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d',
                                                   'autoScale2d', 'resetScale2d', 'hoverClosestCartesian',
                                                   'hoverCompareCartesian', 'toggleSpikelines', 'toImage'],
                        'modeBarButtonsToAdd': ['zoom2d', 'resetScale2d']
                    }
                )
            ])
        ])
    ], className='map-display')

    # Star Descriptions Section
    star_descriptions_section = html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Img(src="https://upload.wikimedia.org/wikipedia/commons/6/6e/Michelin_Bib_Gourmand.png",
                                 className='star-image'),
                        html.Span(star_descriptions[key], className='star-description-text')  # Use Span for inline text
                    ], className='star-description-item')  # This is a new class for the flex container
                    if key == 0.5 else
                    html.H6(star_descriptions[key], className='star-description')
                ]) for key in star_descriptions
            ])
        ])
    ], className='star-descriptions-container')

    # Combine all sections into the main layout
    return html.Div([
        title_section,
        dropdown_section,
        map_display_section,
        star_descriptions_section
    ])
