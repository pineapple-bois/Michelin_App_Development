from dash import html, dcc
import dash_bootstrap_components as dbc

from app.layouts.analysis_shared import (
    get_analysis_page_layout,
    star_filter_section,
    star_placeholder,
    unique_regions,
)


def get_demographics_content():
    return html.Div(
        className='demographics-container editorial-page',
        id='demographics-content-top',
        children=[
            html.Div(
                className='demographics-text-container editorial-section',
                children=[
                    html.Div(
                        "Michelin Restaurants and Regional Indicators",
                        className='demographics-header editorial-page-title'
                    ),
                    html.Div(
                        [
                            "Compare Michelin restaurants with regional data from ",
                            html.A(
                                "INSEE",
                                href="https://www.insee.fr/fr/accueil",
                                target="_blank"
                            ),
                            ". Choose a metric such as GDP per capita, poverty rate, or population density, then select regions to compare them on the map."
                        ],
                        className='demographics-text-paragraph editorial-page-description'
                    ),
                ],
            ),
            # Demographics dropdowns
            html.Div(
                className='demographics-filter-container editorial-control-row',
                children=[
                    # Demographics dropdown
                    html.Div(
                        className='demographics-dropdown-container editorial-control-group',
                        children=[
                            html.H6("Select a Socio-Economic Metric", className='editorial-control-label'),
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
                                className='dropdown-category-demographics-selector editorial-select',
                                multi=False,
                                clearable=True
                            )
                        ],
                    ),
                    # Region dropdown
                    html.Div(
                        className='demographics-dropdown-container editorial-control-group',
                        children=[
                            html.H6("Select a Region to Show Metric by Department", className='editorial-control-label'),
                            dcc.Dropdown(
                                id='granularity-dropdown-demographics',
                                options=[{'label': 'All France', 'value': 'All France'}] + [
                                    {'label': region, 'value': region} for region in unique_regions],
                                value='All France',  # Default selection
                                className='dropdown-granularity-demographics editorial-select',
                                multi=False,
                                clearable=False
                            )
                        ],
                    ),
                    # Add or Remove Regions
                    html.Div(
                        className='filter-container editorial-control-group',
                        children=[
                            html.Div(
                                id='demographics-add-remove',
                                children=[
                                    html.H5("Add or Remove Regions of France", className='region-filter-title editorial-control-label'),
                                    dcc.Dropdown(
                                        id='demographics-dropdown-analysis',
                                        options=[{'label': 'Select All', 'value': 'all'}] +
                                                [{'label': region, 'value': region} for region in unique_regions],
                                        value=unique_regions,  # All regions selected by default
                                        className='dropdown-category-demographics editorial-select editorial-chip-select',
                                        multi=True,  # Multi-select enabled
                                        clearable=True,
                                    ),
                                ]
                            )
                        ],
                    )
                ],
            ),

            # Restaurant selection div
            html.Div(
                className='demographics-restaurants-wrapper',
                children=[
                    # Wrapper for both button and star filter
                    html.Div(
                        className='demographics-restaurants-controls editorial-control-row',
                        # Flexbox for side-by-side layout
                        children=[
                            # Toggle to show restaurant details
                            html.Div(
                                className='toggle-details-container-demographics editorial-control-group',
                                children=[
                                    dbc.Button(
                                        "Overlay Starred Restaurants",
                                        id='toggle-show-details-demographics',
                                        n_clicks=0,
                                        className='button-show-details editorial-action-button'
                                    )
                                ],
                            ),
                            # Star filter specific to analysis page
                            html.Div(
                                className='star-filter-container editorial-control-group',
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
                            ),
                            dcc.Store(id='map-view-store-demo', data={}),
                            dcc.Store(id='map-view-demo-updated', data={})
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


def build_economics_section():
    return get_demographics_content()


def build_economics_page_content():
    return html.Div(
        className='analysis-container editorial-sheet',
        children=[
            build_economics_section(),
        ]
    )


def get_economics_layout():
    return get_analysis_page_layout(build_economics_page_content())
