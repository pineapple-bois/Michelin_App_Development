import dash
import plotly.graph_objects as go
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate

from app.utils.economics_figures import (
    ECONOMICS_WEIGHTED_MEAN_EXCLUDED_METRICS,
    calculate_weighted_mean,
    plot_demographic_choropleth_plotly,
    plot_demographics_barchart,
)
from app.utils.star_filters import update_button_active_state_helper


def restaurant_overlay_active(n_clicks):
    return bool(n_clicks and n_clicks % 2 == 1)


def demographics_chart_hidden(selected_metric):
    return not bool(selected_metric)


def demographics_region_selector_style(selected_region):
    return (
        {'display': 'block'}
        if selected_region == 'All France'
        else {'display': 'none'}
    )


def reset_demographics_star_clicks(n_clicks_rest, ids):
    """Reset star-filter parity when the restaurant overlay closes."""
    if restaurant_overlay_active(n_clicks_rest) or not ids:
        return None
    return [0] * len(ids)


def map_view_for_demographics_update(mapview_data, triggered_input):
    """Ignore persisted camera state when the geography selector changes."""
    if triggered_input == 'granularity-dropdown-demographics':
        return {}
    return mapview_data or {}


def register_economics_callbacks(app, data):
    all_france = data.all_france
    region_df = data.region_df
    department_df = data.department_df
    unique_regions = data.unique_regions

    @app.callback(
        [Output('demographics-dropdown-analysis', 'value'),
         Output('demographics-map-graph', 'figure'),
         Output('demographics-bar-chart-graph', 'figure'),
         Output('demographics-add-remove', 'style'),
         Output('demographics-chart-math', 'hidden'),
         Output('weighted-mean', 'style'),
         Output('star-filter-demographics', 'style')],
        [Input('category-dropdown-demographics', 'value'),
         Input('granularity-dropdown-demographics', 'value'),
         Input('demographics-dropdown-analysis', 'value'),
         Input('toggle-show-details-demographics', 'n_clicks'),  # Button to toggle restaurants
         Input({'type': 'filter-button-demographics', 'index': ALL}, 'n_clicks')],
        [State('map-view-store-demo', 'data')]
    )
    def update_demographics_map(selected_metric, selected_dropdown, selected_regions, n_clicks_rest, n_clicks_stars,
                                mapview_data):
        ctx = dash.callback_context
        triggered_input = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        active_mapview_data = map_view_for_demographics_update(mapview_data, triggered_input)

        # Handle "Select All"
        if 'all' in selected_regions:
            selected_regions = unique_regions  # Select all regions if "Select All" is chosen

        # Ensure `selected_regions` is not None
        if not selected_regions:
            selected_regions = unique_regions  # Default to all regions when none are selected

        # Set granularity based on whether a region is selected in the dropdown
        if selected_dropdown != 'All France':
            selected_granularity = 'department'  # If a region is selected, use department granularity
        else:
            selected_granularity = 'region'  # Default granularity is region
        region_selector_style = demographics_region_selector_style(selected_dropdown)

        if selected_granularity == 'region':
            df = region_df.sort_values('region').copy()  # Use region-level data
            df = df[df['region'].isin(selected_regions)].copy()
            filtered_restaurants = all_france[all_france['region'].isin(selected_regions)].copy()
        else:
            df = department_df.copy()
            # If a region is selected in the dropdown, filter to that region
            if selected_dropdown != 'All France':
                df = df[df['region'] == selected_dropdown].copy()
                filtered_restaurants = all_france.copy()

        # Show or hide the star filter based on button press
        if restaurant_overlay_active(n_clicks_rest):
            star_filter_style = {'display': 'block'}
            show_restaurants = True
        else:
            star_filter_style = {'display': 'none'}
            show_restaurants = False

        stars = [1, 2, 3]
        if n_clicks_stars:
            selected_stars = [stars[i] for i, n in enumerate(n_clicks_stars) if n % 2 == 0]  # Only keep active stars
        else:
            selected_stars = stars

        # **Check if any restaurants exist for the selected stars in the region**
        available_stars = filtered_restaurants['stars'].unique().tolist()
        selected_stars = [star for star in selected_stars if star in available_stars]

        # **Handle the case where no stars are selected**
        if not selected_stars:
            show_restaurants = False  # No stars to show
            filtered_restaurants = filtered_restaurants.iloc[0:0]  # Empty DataFrame to avoid plotting

        # If no metric is selected, just show map boundaries without data coloring
        if not selected_metric:
            fig_map = plot_demographic_choropleth_plotly(
                df,
                filtered_restaurants,
                metric=None,  # Pass None to indicate no metric is selected
                granularity=selected_granularity,
                show_labels=False,
                cmap='Blues',
                restaurants=show_restaurants,  # Show restaurants based on button press
                selected_stars=selected_stars,  # Filter based on selected stars
                zoom_data=active_mapview_data
            )
            empty_fig = go.Figure()  # Return empty figure for bar chart
            return (selected_regions, fig_map, empty_fig, region_selector_style,
                    demographics_chart_hidden(selected_metric), {'display': 'none'}, star_filter_style)

        if selected_granularity == 'region':
            dataframe = region_df
        else:
            dataframe = department_df

        # Only calculate weighted mean if the metric is not in the excluded list
        if selected_metric not in ECONOMICS_WEIGHTED_MEAN_EXCLUDED_METRICS:
            weighted_mean = calculate_weighted_mean(dataframe, selected_metric, weight_column='municipal_population')
            weighted_mean_style = {'display': 'block'}  # Show the weighted mean section
        else:
            weighted_mean = None  # No weighted mean calculation
            weighted_mean_style = {'display': 'none'}  # Hide the weighted mean section

        fig_map = plot_demographic_choropleth_plotly(
            df,
            filtered_restaurants,
            selected_metric,
            granularity=selected_granularity,
            show_labels=False,
            cmap='Blues',
            restaurants=show_restaurants,
            selected_stars=selected_stars,
            zoom_data=active_mapview_data
        )

        fig_bar = plot_demographics_barchart(
            df,
            selected_metric,
            granularity=selected_granularity,
            weighted_mean=weighted_mean
        )

        return (selected_regions, fig_map, fig_bar, region_selector_style,
                demographics_chart_hidden(selected_metric), weighted_mean_style, star_filter_style)

    @app.callback(
        Output('toggle-show-details-demographics', 'active'),
        Input('toggle-show-details-demographics', 'n_clicks'),
    )
    def update_restaurant_overlay_active_state(n_clicks):
        return restaurant_overlay_active(n_clicks)

    @app.callback(
        Output({'type': 'filter-button-demographics', 'index': ALL}, 'n_clicks'),
        Input('toggle-show-details-demographics', 'n_clicks'),
        State({'type': 'filter-button-demographics', 'index': ALL}, 'id'),
        prevent_initial_call=True,
    )
    def reset_demographics_restaurant_star_filters(n_clicks_rest, ids):
        reset_clicks = reset_demographics_star_clicks(n_clicks_rest, ids)
        if reset_clicks is None:
            raise PreventUpdate
        return reset_clicks

    @app.callback(
        Output('map-view-store-demo', 'data'),
        [Input('demographics-map-graph', 'relayoutData'),
         Input('granularity-dropdown-demographics', 'value')],
        [State('map-view-store-demo', 'data')]
    )
    def store_map_view_demo(relayout_data, region_dropdown, existing_data):
        # Initialize existing_data if it's None
        if existing_data is None:
            existing_data = {}

        # Reset zoom data when region or department changes
        ctx = dash.callback_context
        triggered_input = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        if triggered_input == 'granularity-dropdown-demographics':
            return {}  # Clear zoom data when region dropdown changes

        # If relayoutData is None or empty, do not update the store
        if not relayout_data:
            raise dash.exceptions.PreventUpdate

        # Define the keys that indicate a user interaction
        user_interaction_keys = {'map.zoom', 'map.center'}

        # Check if relayoutData contains any of the user interaction keys
        if user_interaction_keys.intersection(relayout_data.keys()):
            zoom = relayout_data.get('map.zoom', existing_data.get('zoom'))
            center = relayout_data.get('map.center', existing_data.get('center'))

            if zoom and center:
                existing_data['zoom'] = zoom
                existing_data['center'] = center
                return existing_data

        raise dash.exceptions.PreventUpdate

    @app.callback(
        [Output({'type': 'filter-button-demographics', 'index': ALL}, 'className'),
         Output({'type': 'filter-button-demographics', 'index': ALL}, 'style')],
        [Input({'type': 'filter-button-demographics', 'index': ALL}, 'n_clicks')],
        [State({'type': 'filter-button-demographics', 'index': ALL}, 'id')]
    )
    def update_demographics_button_active_state(n_clicks_list, ids):
        if not n_clicks_list:
            raise PreventUpdate
        return update_button_active_state_helper(n_clicks_list, ids, 'demographics')
