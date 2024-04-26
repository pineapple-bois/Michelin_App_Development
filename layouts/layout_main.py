from dash import html, dcc
import dash_bootstrap_components as dbc


def get_main_layout(unique_regions, star_descriptions):
    # Title Section with Container Style
    title_section = html.Div(children=[
        html.H1("Michelin Guide to France 2024", className='title-section'),
        html.P([
            "Explore the finest culinary destinations in France, as reviewed by Michelin.",
            html.Br(),  # Add a line break
            "France is divided administratively into regions and departments.",
            html.Br(),  # Another line break for spacing if needed
            html.Br(),  # Add as many <br> as needed for desired spacing
            "Select a region to see the Michelin-starred restaurants by department."  # Instructional sentence
        ], className='title-description')],
        className='container-style'
    )

    # Dropdown Section with Container Style
    dropdown_section = html.Div([
        dbc.Row([
            dbc.Col(dcc.Dropdown(
                id='region-dropdown',
                options=[{'label': region, 'value': region} for region in unique_regions],
                value=unique_regions[0],  # Default value
                className='dropdown-style',
                clearable=False
            )),
            dbc.Col(dcc.Dropdown(
                id='department-dropdown',
                className='dropdown-style'
            ))
        ])
    ], className='container-style')

    # Map Display Section with Container Style
    map_display_section = html.Div([
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
                    'modeBarButtonsToAdd': ['zoom2d', 'resetScale2d']
                }
            ))
        ])
    ], className='container-style')

    # Star Descriptions Section with Container Style
    star_descriptions_section = html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([html.Div([
                    html.Img(src="https://upload.wikimedia.org/wikipedia/commons/6/6e/Michelin_Bib_Gourmand.png", className='star-image'),
                    html.Span(star_descriptions[key], className='star-description-text')
                ], className='star-description-item') if key == 0.5 else
                html.H6(star_descriptions[key], className='star-description')
                ]) for key in star_descriptions
            ])
        ])
    ], className='container-style')

    # Combine all sections into the main layout with Container Style
    return html.Div([
        title_section,
        dropdown_section,
        map_display_section,
        star_descriptions_section])

