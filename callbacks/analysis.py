import plotly.graph_objects as go
from dash import html
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate

from utils.appFunctions import (
    create_michelin_bar_chart,
    plot_single_choropleth_plotly,
    top_restaurants,
    update_button_active_state_helper,
)


def register_analysis_callbacks(app, data):
    all_france = data.all_france
    region_df = data.region_df
    department_df = data.department_df
    arron_df = data.arron_df
    paris_df = data.paris_df
    star_placeholder = (0.5, 1, 2, 3)
    unique_regions = data.unique_regions

    # REGION content

    @app.callback(
        [Output('restaurant-analysis-graph', 'figure'),
         Output('region-map', 'figure')],
        [Input('region-dropdown-analysis', 'value'),
         Input({'type': 'filter-button-analysis', 'index': ALL}, 'n_clicks')]
    )
    def update_analysis_chart_and_map(selected_regions, star_clicks):
        # Check if "Select All" is chosen
        if 'all' in selected_regions:
            selected_regions = unique_regions  # Reset to all available regions

        if not selected_regions:
            raise PreventUpdate

        # Default to all star levels if none selected
        select_stars = [0.5, 1, 2, 3]

        if star_clicks:
            select_stars = [star_placeholder[i] for i, n in enumerate(star_clicks) if n % 2 == 0]

        filtered_df = region_df[region_df['region'].isin(selected_regions)].copy()
        filtered_df.sort_values('region', inplace=True)

        fig_bar = create_michelin_bar_chart(
            filtered_df,
            select_stars,
            granularity='region',
            title="Selected regions of France."
        )

        map_fig = plot_single_choropleth_plotly(
            df=filtered_df,
            selected_stars=select_stars,
            granularity='region',
            show_labels=False
        )

        return fig_bar, map_fig

    @app.callback(
        Output('region-dropdown-analysis', 'value'),
        Input('region-dropdown-analysis', 'value')
    )
    def handle_select_all(selected_regions):
        # If "Select All" is selected, replace the selection with all regions
        if 'all' in selected_regions:
            return unique_regions  # Return all available regions

        # Otherwise, return the current selection
        return selected_regions

    @app.callback(
        [Output({'type': 'filter-button-analysis', 'index': ALL}, 'className'),
         Output({'type': 'filter-button-analysis', 'index': ALL}, 'style')],
        [Input({'type': 'filter-button-analysis', 'index': ALL}, 'n_clicks')],
        [State({'type': 'filter-button-analysis', 'index': ALL}, 'id')]
    )
    def update_region_button_active_state(n_clicks_list, ids):
        if not n_clicks_list:
            raise PreventUpdate
        return update_button_active_state_helper(n_clicks_list, ids, 'analysis')

    # DEPARTMENT content

    @app.callback(
        [Output('star-filter-container-department', 'style'),
         Output('department-analysis-graph', 'figure'),
         Output('department-map', 'figure'),
         Output('department-analysis-graph', 'style'),
         Output('department-map', 'style'),
         Output('departments-store', 'data'),
         Output('arrondissement-filter-title', 'children')],
        [Input('department-dropdown-analysis', 'value'),
         Input({'type': 'filter-button-department', 'index': ALL}, 'n_clicks')]
    )
    def update_department_chart_and_map(selected_region, star_clicks):
        hide_style = {'display': 'none'}
        show_style = {'display': 'inline-block', 'height': '100%', 'width': '100%'}

        if not selected_region:
            empty_fig = go.Figure()
            return hide_style, empty_fig, empty_fig, hide_style, hide_style, [], ""

        arrondissements_title = f"Select a Department within {selected_region}"

        # Default to all star levels if none selected
        select_stars = [0.5, 1, 2, 3]

        if star_clicks:
            select_stars = [star_placeholder[i] for i, n in enumerate(star_clicks) if n % 2 == 0]

        filtered_df = department_df[department_df['region'] == selected_region].copy()
        filtered_df.sort_values('department', inplace=True)

        fig_bar = create_michelin_bar_chart(
            filtered_df,
            select_stars,
            granularity='department',
            title=f"{selected_region}"
        )

        map_fig = plot_single_choropleth_plotly(
            df=filtered_df,
            selected_stars=select_stars,
            granularity='department',
            show_labels=False
        )

        # Extract unique departments and create a list of options for the store
        department_options = [{'label': dept, 'value': dept} for dept in filtered_df['department'].unique()]

        return show_style, fig_bar, map_fig, show_style, show_style, department_options, arrondissements_title

    @app.callback(
        [Output({'type': 'filter-button-department', 'index': ALL}, 'className'),
         Output({'type': 'filter-button-department', 'index': ALL}, 'style')],
        [Input({'type': 'filter-button-department', 'index': ALL}, 'n_clicks')],
        [State({'type': 'filter-button-department', 'index': ALL}, 'id')]
    )
    def update_department_button_active_state(n_clicks_list, ids):
        if not n_clicks_list:
            raise PreventUpdate
        return update_button_active_state_helper(n_clicks_list, ids, 'department')

    # ARRONDISSEMENT content

    @app.callback(
        Output('arrondissement-content-wrapper', 'className'),
        Input('department-dropdown-analysis', 'value')
    )
    def toggle_arrondissement_section(selected_region):
        if selected_region:
            return 'visible-section'  # Show the section
        else:
            return 'hidden-section'  # Hide the section

    @app.callback(
        [Output('arrondissement-dropdown-analysis', 'options'),
         Output('arrondissement-dropdown-analysis', 'placeholder')],
        Input('departments-store', 'data')
    )
    def update_arrondissement_dropdown(department_data):
        if department_data:
            return department_data, "Select a Department"
        return [], "Please select a region first"

    @app.callback(
        [Output('star-filter-container-arrondissement', 'style'),
         Output('arrondissement-analysis-graph', 'figure'),
         Output('arrondissement-map', 'figure'),
         Output('arrondissement-analysis-graph', 'style'),
         Output('arrondissement-map', 'style')],
        [Input('arrondissement-dropdown-analysis', 'value'),
         Input({'type': 'filter-button-arrondissement', 'index': ALL}, 'n_clicks')]
    )
    def update_arrondissement_chart_and_map(selected_department, star_clicks):
        hide_style = {'display': 'none'}
        show_style = {'display': 'inline-block', 'height': '100%', 'width': '100%'}

        if not selected_department:
            empty_fig = go.Figure()
            return hide_style, empty_fig, empty_fig, hide_style, hide_style

        # Default to all star levels if none selected
        select_stars = [0.5, 1, 2, 3]

        if star_clicks:
            select_stars = [star_placeholder[i] for i, n in enumerate(star_clicks) if n % 2 == 0]

        if selected_department == 'Paris':
            filtered_df = paris_df
        else:
            filtered_df = arron_df[arron_df['department'] == selected_department].copy()
            filtered_df.sort_values('arrondissement', inplace=True)

        fig_bar = create_michelin_bar_chart(
            filtered_df,
            select_stars,
            granularity='arrondissement',
            title=f"{selected_department}"
        )

        map_fig = plot_single_choropleth_plotly(
            df=filtered_df,
            selected_stars=select_stars,
            granularity='arrondissement',
            show_labels=False
        )

        return show_style, fig_bar, map_fig, show_style, show_style

    @app.callback(
        [Output({'type': 'filter-button-arrondissement', 'index': ALL}, 'className'),
         Output({'type': 'filter-button-arrondissement', 'index': ALL}, 'style')],
        [Input({'type': 'filter-button-arrondissement', 'index': ALL}, 'n_clicks')],
        [State({'type': 'filter-button-arrondissement', 'index': ALL}, 'id')]
    )
    def update_demographics_button_active_state(n_clicks_list, ids):
        if not n_clicks_list:
            raise PreventUpdate
        return update_button_active_state_helper(n_clicks_list, ids, 'arrondissement')

    # RANKING content

    @app.callback(
        [Output('ranking-output', 'children'),
         Output('toggle-show-details', 'n_clicks'),
         Output('toggle-show-details', 'children')],  # Reset the click state
        [Input('granularity-dropdown', 'value'),
         Input('star-dropdown-ranking', 'value'),
         Input('ranking-dropdown', 'value'),
         Input('toggle-show-details', 'n_clicks')],
    )
    def update_ranking_output(granularity, star_rating, top_n, n_clicks):
        # If granularity is not selected, show a message
        if granularity is None:
            return html.Div(
                "Please select a granularity to display rankings.",
                style={
                    "font-style": "italic",
                    "font-size": "16px",
                    "color": "grey",
                    "text-align": "center",
                    "align-items": "center",  # Vertically center
                }
            ), 0, "Show Restaurant Details"

        display_restaurants = n_clicks % 2 == 1  # Toggle restaurant visibility based on button state

        # Set the button label based on the toggle state
        button_label = "Hide Restaurant Details" if display_restaurants else "Show Restaurant Details"

        # Handle the 'Paris' case explicitly
        if top_n == 1 and granularity == 'department':
            # Focus on Paris for department granularity
            filtered_data = all_france[all_france['department_num'] == '75']  # Only Paris restaurants
        elif top_n == 1 and granularity == 'region':
            # Focus on Île-de-France for region granularity
            filtered_data = all_france[all_france['region'] == 'Île-de-France']  # Only Île-de-France restaurants
        elif top_n == 1 and granularity == 'arrondissement':
            # Focus on Paris arrondissements for 'arrondissement' granularity
            filtered_data = all_france[all_france['department_num'] == '75']  # Only Paris restaurants
            top_n = 5  # Force top_n to be 5 for Paris arrondissements
        else:
            # General case: filter out Île-de-France if not Paris
            filtered_data = all_france[all_france['region'] != 'Île-de-France']
            if granularity == 'department' and top_n in [3, 5]:
                filtered_data = filtered_data[filtered_data['department_num'] != '75']  # Exclude Paris

        # Call the top_restaurants function to get the components
        ranking_components = top_restaurants(filtered_data, granularity, star_rating, top_n, display_restaurants)

        return ranking_components, n_clicks, button_label
