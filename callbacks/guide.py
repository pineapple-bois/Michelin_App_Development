import dash
from dash import callback_context, html
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate

from components.shared import color_map
from layouts.layout_main import star_filter_section
from utils.appFunctions import (
    default_map_figure,
    get_restaurant_details,
    plot_arrondissement_outlines,
    plot_department_outlines,
    plot_interactive_department,
    plot_paris_arrondissement,
    plot_regional_outlines,
)
from utils.locationMatcher import LocationMatcher


def register_guide_callbacks(app, data):
    all_france = data.all_france
    region_df = data.region_df
    paris_df = data.paris_df
    dept_to_code = data.dept_to_code
    region_to_name = data.region_to_name
    get_combined_restaurant_data = data.get_combined_restaurant_data
    get_geo_df = data.get_geo_df

    # Get rid of the 'hand' when hovering over restaurants (doesn't work with Safari...)
    app.clientside_callback(
        """
        function(hoverData) {
            if (hoverData) {
                document.getElementById('map-display').style.cursor = 'pointer';
            } else {
                document.getElementById('map-display').style.cursor = 'default';
            }
        }
        """,
        Output('dummy-output', 'children'),
        Input('map-display', 'hoverData')
    )

    """New version with Enter key functionality"""
    @app.callback(
        [Output('info-collapse', 'is_open'),
         Output('city-input-mainpage', 'value'),
         Output('matched-city-output-mainpage', 'children'),
         Output('matched-city-output-mainpage', 'className'),
         Output('region-dropdown', 'value'),
         Output('department-dropdown', 'value')],
        [Input('info-toggle-button', 'n_clicks'),
         Input('submit-city-button-mainpage', 'n_clicks'),
         Input('clear-city-button-mainpage', 'n_clicks'),
         Input('city-input-mainpage', 'n_submit')],  # Add `n_submit` for Enter key
        [State('info-collapse', 'is_open'),
         State('city-input-mainpage', 'value')]
    )
    def toggle_collapse_and_handle_search(n_info_clicks, n_submit_clicks, n_clear_clicks, n_submit, is_open,
                                          city_input):
        """
        Callback function to manage the information collapse section and handle city search functionality.

        This function handles user interactions:
        - Toggling the information collapse visibility with the info button.
        - Processing city search via submit button or pressing Enter.
        - Clearing input and resetting outputs with the clear button.
        """
        # Ensure clicks are initialized
        n_info_clicks = n_info_clicks or 0
        n_submit_clicks = n_submit_clicks or 0
        n_clear_clicks = n_clear_clicks or 0
        n_submit = n_submit or 0

        # Collapse logic: only triggered by the toggle button
        ctx = dash.callback_context
        if ctx.triggered[0]['prop_id'] == 'info-toggle-button.n_clicks':
            if is_open:
                # Collapse: clear input and match result
                return False, '', html.Div([html.P("", className='default-message')]), \
                       'city-match-output-container-mainpage', dash.no_update, dash.no_update
            else:
                # Expand the collapse without resetting input/output
                return (True, dash.no_update, dash.no_update, 'city-match-output-container-mainpage',
                        dash.no_update, dash.no_update)

        # Handle clearing the input and resetting the output when clear is clicked
        if ctx.triggered[0]['prop_id'] == 'clear-city-button-mainpage.n_clicks':
            return dash.no_update, '', html.Div([html.P("", className='default-message')]), \
                   'city-match-output-container-mainpage', dash.no_update, dash.no_update

        # Handle the search functionality triggered by the submit button or Enter key
        if ctx.triggered[0]['prop_id'] in {'submit-city-button-mainpage.n_clicks', 'city-input-mainpage.n_submit'}:
            if not city_input:
                # Fallback for invalid or empty input
                return dash.no_update, '', html.Div([html.P("Enter a valid location.", className='default-message')]), \
                    'city-match-output-container-mainpage', dash.no_update, dash.no_update

            # Add Monaco to dataset
            plus_monaco = get_combined_restaurant_data(include_monaco=True)
            matcher = LocationMatcher(plus_monaco)
            result = matcher.find_region_department(city_input)
            if isinstance(result, dict):
                # Valid result, update outputs
                city_details = [
                    html.P(
                        f"Match:  {result.get('Matched Location', 'Unknown')},  "
                        f"Region:  {result.get('Region', 'Unknown')},  "
                        f"Department:  {result.get('Department', 'Unknown')}",
                        className='match-details'
                    ),
                ]
                return dash.no_update, dash.no_update, html.Div(city_details, className='city-match-container'), \
                    'city-match-output-container-mainpage visible', result.get('Region'), result.get('Department')
            else:
                # No match found
                return dash.no_update, dash.no_update, html.Div([
                    html.P(f"No match found. '{city_input}' is not represented in the Michelin Guide",
                           className='no-match-message')
                ]), 'city-match-output-container-mainpage visible', dash.no_update, dash.no_update

        # Default to no update if no actions were triggered
        return (dash.no_update, dash.no_update, dash.no_update, 'city-match-output-container-mainpage',
                dash.no_update, dash.no_update)

    @app.callback(
            [Output('department-dropdown', 'options'),
            Output('star-filter', 'children'),
            Output('star-filter', 'style'),
            Output('available-stars', 'data')],
           [Input('region-dropdown', 'value'),
            Input('department-dropdown', 'value'),
            Input('arrondissement-dropdown', 'value')]
    )
    def update_department_and_filters(selected_region, selected_department, selected_arrondissement):
        # Use dynamic geo_df based on region
        geo_df_dynamic = get_geo_df(include_monaco=(selected_region == "Provence-Alpes-Côte d'Azur"))

        # Fetch department options based on the selected region.
        departments = geo_df_dynamic[geo_df_dynamic['region'] == selected_region][['department', 'code']].drop_duplicates().to_dict('records')
        department_options = [{'label': f"{dept['department']} ({dept['code']})", 'value': dept['department']} for dept in departments]

        if not selected_department:
            # No department selected, hide star filter and clear buttons
            return department_options, star_filter_section().children, {'display': 'none'}, []

        # Handle the case when the department is Paris
        if selected_department == 'Paris':
            # Determine available stars based on arrondissement selection
            if selected_arrondissement and selected_arrondissement != 'all':
                # Filter all_france for the selected arrondissement
                filtered_data = all_france[
                    (all_france['department'] == 'Paris') &
                    (all_france['arrondissement'] == selected_arrondissement)
                ]
            else:
                # No specific arrondissement selected, use all of Paris
                filtered_data = all_france[
                    (all_france['department'] == 'Paris')
                ]

            # Determine available stars from the filtered data
            available_stars = sorted(filtered_data['stars'].unique(), reverse=True)

            # Only show the filter if there are stars available
            if available_stars:
                star_filter = star_filter_section(available_stars)
                return department_options, star_filter.children, {'display': 'block'}, available_stars
            else:
                return department_options, star_filter_section().children, {'display': 'none'}, []

        else:
            # For departments other than Paris
            # Fetch the row for the selected department
            department_row = geo_df_dynamic[geo_df_dynamic['department'] == selected_department]

            if department_row.empty:
                # Handle the case where the department is not found
                return department_options, star_filter_section().children, {'display': 'none'}, []

            department_row = department_row.iloc[0]

            # Determine which star ratings are present in the department
            available_stars = []
            for star_level in [3, 2, 1]:  # Ensure all levels are checked
                if department_row[f'{int(star_level)}_star'] > 0:
                    available_stars.append(star_level)
            if department_row['bib_gourmand'] > 0:
                available_stars.append(0.5)
            if department_row['selected'] > 0:
                available_stars.append(0.25)

            # Only show the filter if there are stars available
            if available_stars:
                star_filter = star_filter_section(available_stars)
                return department_options, star_filter.children, {'display': 'block'}, available_stars
            else:
                return department_options, star_filter_section().children, {'display': 'none'}, []

    @app.callback(
        [Output({'type': 'filter-button-mainpage', 'index': ALL}, 'className'),
         Output({'type': 'filter-button-mainpage', 'index': ALL}, 'style'),
         Output('selected-stars', 'data'),
         Output('toggle-selected-btn', 'className'),
         Output('toggle-selected-btn', 'style')],
        [Input({'type': 'filter-button-mainpage', 'index': ALL}, 'n_clicks'),
         Input('toggle-selected-btn', 'n_clicks')],
        [State({'type': 'filter-button-mainpage', 'index': ALL}, 'id'),
         State('selected-stars', 'data'),
         State('available-stars', 'data')]
    )
    def update_button_active_state(n_clicks_list, toggle_selected_clicks, ids,
                                   current_stars, available_stars):
        # Handle cases where not all data is available, especially at initialization
        if (not n_clicks_list or not available_stars or len(available_stars) == 0) and available_stars != [0.25]:
            raise PreventUpdate

        # Initialize empty lists to store class names and styles
        class_names = []
        styles = []

        # Initialize the new list of active stars from current state filtered by available stars
        new_stars = [star for star in current_stars if star in available_stars and star != 0.25]

        for i, button_id in enumerate(ids):
            index = button_id['index']
            n_clicks = n_clicks_list[i] if i < len(n_clicks_list) else 0  # fallback to 0

            if index not in available_stars:
                # Still return something so Dash output lengths match
                class_names.append("me-1 star-button inactive")
                styles.append({
                    "display": "inline-block",
                    "width": "100%",
                    "backgroundColor": "#cccccc"
                })
                continue

            # Determine if the button is active (even number of clicks means active)
            is_active = n_clicks % 2 == 0

            if is_active:
                if index not in new_stars:
                    new_stars.append(index)
                background_color = color_map[index]
            else:
                if index in new_stars:
                    new_stars.remove(index)
                background_color = (
                    f"rgba({int(color_map[index][1:3], 16)},"
                    f"{int(color_map[index][3:5], 16)},"
                    f"{int(color_map[index][5:7], 16)},0.6)"
                )

            class_name = "me-1 star-button" + (" active" if is_active else "")
            color_style = {
                "display": "inline-block",
                "width": "100%",
                "backgroundColor": background_color,
            }
            class_names.append(class_name)
            styles.append(color_style)

        # ---- Toggle Selected Button Logic ----
        selected_active = toggle_selected_clicks % 2 == 0
        if selected_active and 0.25 not in new_stars:
            new_stars.append(0.25)
        elif not selected_active and 0.25 in new_stars:
            new_stars.remove(0.25)

        selected_class = "selected-toggle-button" + (" active" if selected_active else " inactive")
        # Compute display: show the toggle button only if 0.25 is an available star rating
        toggle_display = "block" if 0.25 in available_stars else "none"
        selected_style = {
            "display": toggle_display,
        }

        return class_names, styles, new_stars, selected_class, selected_style

    @app.callback(
        Output('restaurant-details', 'children'),
        [Input('map-display', 'clickData'),
         Input('department-dropdown', 'value'),
         Input('region-dropdown', 'value'),
         Input('selected-stars', 'data')],
    )
    def update_sidebar(clickData, selected_department, selected_region, selected_stars):
        ctx = dash.callback_context

        # Placeholder messages
        restaurant_placeholder = html.Div(
            "Select a restaurant on the map to see more details",
            className='placeholder-text'
        )

        select_stars_placeholder = html.Div(
            "Select a star rating to see restaurants.",
            className='placeholder-text',
            style={'color': 'red'}
        )

        select_department_placeholder = html.Div(
            "Select a department to view restaurants.",
            className='placeholder-text'
        )

        # If no department is selected, prompt the user
        if not selected_department:
            return select_department_placeholder

        # If no stars are selected, prompt the user to select stars
        if not selected_stars:
            return select_stars_placeholder

        include_monaco = selected_region == "Provence-Alpes-Côte d'Azur"
        combined_data = get_combined_restaurant_data(include_monaco)

        # Determine which input triggered the callback
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # Handle map clicks
        if triggered_id == 'map-display':
            if clickData and 'points' in clickData and len(clickData['points']) > 0:
                point = clickData['points'][0]
                restaurant_index = point.get('meta') or point.get('customdata')

                if restaurant_index in combined_data.index:
                    restaurant_info = combined_data.loc[restaurant_index]
                    # Check if the restaurant's star rating is in selected_stars
                    if restaurant_info['stars'] in selected_stars:
                        return get_restaurant_details(restaurant_info)
            return restaurant_placeholder

        # For any other triggers, clear the restaurant details
        return restaurant_placeholder

    @app.callback(
        [Output('arrondissement-dropdown-container', 'className'),
         Output('arrondissement-dropdown', 'options'),
         Output('arrondissement-dropdown', 'value')],
        [Input('department-dropdown', 'value')]
    )
    def update_arrondissement_visibility(selected_department):
        if selected_department == 'Paris':
            # Fetch arrondissements from paris_df
            arrondissement_list = paris_df['arrondissement'].unique()
            arrondissement_options = [{'label': arr, 'value': arr} for arr in arrondissement_list]
            # Add 'All Arrondissements' option at the top
            arrondissement_options.insert(0, {'label': 'All Arrondissements', 'value': 'all'})
            return 'visible-paris-section', arrondissement_options, 'all'
        else:
            # Hide the arrondissement section by setting class to 'hidden-section'
            return 'hidden-paris-section', [], None

    @app.callback(
        Output('map-display', 'figure'),
        [Input('department-dropdown', 'value'),
         Input('region-dropdown', 'value'),
         Input('selected-stars', 'data'),
         Input('arrondissement-dropdown', 'value')],
        [State('map-view-store-mainpage', 'data'),
         State('department-centroid-store', 'data'),
         State('paris-arrondissement-centroid', 'data')]
    )
    def update_map(selected_department, selected_region, selected_stars, paris_arrondissement,
                   mapview_data, dept_viewdata, arron_viewdata):
        ctx = callback_context
        triggered_id, _ = ctx.triggered[0]['prop_id'].split('.') if ctx.triggered else (None, None)

        # Use combined restaurant + geo data for PACA
        include_monaco = selected_region == "Provence-Alpes-Côte d'Azur"
        restaurant_data = get_combined_restaurant_data(include_monaco=include_monaco)
        geo_df_dynamic = get_geo_df(include_monaco=include_monaco)
        dept_to_code_dynamic = geo_df_dynamic.drop_duplicates(subset='department').set_index('department')['code'].to_dict()

        # Set view_data once, then reuse it
        view_data = mapview_data if mapview_data else dept_viewdata

        # Handle Paris-specific logic first
        if selected_department == 'Paris':
            department_code = dept_to_code.get('Paris')

            # Handle arrondissement case
            if paris_arrondissement and paris_arrondissement != 'all':
                view_data = mapview_data if mapview_data else arron_viewdata
                if triggered_id == 'selected-stars':
                    # Plot selected arrondissement with stars
                    if selected_stars:
                        return plot_paris_arrondissement(restaurant_data, paris_df, paris_arrondissement, selected_stars, view_data)
                    return plot_arrondissement_outlines(paris_df, paris_arrondissement, view_data)

            # Plot entire Paris department when no arrondissement selected
            view_data = mapview_data if mapview_data else dept_viewdata
            if triggered_id == 'selected-stars':
                if selected_stars:
                    return plot_interactive_department(restaurant_data, geo_df_dynamic, department_code, selected_stars, view_data)
                return plot_department_outlines(geo_df_dynamic, department_code, view_data)

        # Case 1: Department selected (non-Paris)
        if triggered_id == 'department-dropdown' and selected_department:
            department_code = dept_to_code_dynamic.get(selected_department)
            return plot_department_outlines(geo_df_dynamic, department_code, view_data)

        # Case 2: Handle stars selection
        if triggered_id == 'selected-stars' and selected_department:
            department_code = dept_to_code_dynamic.get(selected_department)
            if selected_stars:
                return plot_interactive_department(restaurant_data, geo_df_dynamic, department_code, selected_stars, view_data)
            else:
                return plot_department_outlines(geo_df_dynamic, department_code, view_data)

        # Case 3: Handle region selection
        if selected_region or triggered_id == 'region-dropdown':
            region_name = region_to_name.get(selected_region)
            if region_name:
                return plot_regional_outlines(region_df, region_name)

        # Default fallback case: Show entire country map if no specific input
        return default_map_figure()

    @app.callback(
        Output('department-centroid-store', 'data'),
        [Input('department-dropdown', 'value'),
         Input('region-dropdown', 'value')]
    )
    def calculate_department_centroid(selected_department, selected_region):
        if not selected_department:
            return {}

        # Dynamically include Monaco for PACA
        include_monaco = selected_region == "Provence-Alpes-Côte d'Azur"
        geo_df_dynamic = get_geo_df(include_monaco=include_monaco)

        # Generate dept_to_code dynamically from the active geo_df
        dept_to_code_dynamic = geo_df_dynamic.drop_duplicates(subset='department').set_index('department')[
            'code'].to_dict()
        department_code = dept_to_code_dynamic.get(selected_department)

        if not department_code:
            return {}

        filtered_geo = geo_df_dynamic[geo_df_dynamic['code'] == str(department_code)]
        if filtered_geo.empty:
            return {}

        specific_geometry = filtered_geo['geometry'].iloc[0]
        centroid = specific_geometry.centroid

        # Adjust zoom level
        if department_code == '75':
            zoom_level = 11  # Paris
        elif department_code == '98':
            zoom_level = 13.5  # Monaco
        else:
            zoom_level = 8

        return {
            'zoom': zoom_level,
            'center': {
                'lat': centroid.y,
                'lon': centroid.x
            }
        }

    @app.callback(
        Output('paris-arrondissement-centroid', 'data'),
        [Input('arrondissement-dropdown', 'value')]
    )
    def calculate_arrondissement_centroid(selected_arrondissement):
        if not selected_arrondissement:
            return {}

        # Find the geometry for the selected arrondissement
        filtered_geo = paris_df[paris_df['arrondissement'] == selected_arrondissement]

        if filtered_geo.empty:
            return {}  # Return empty if the arrondissement is not found

        # Calculate the centroid of the selected arrondissement's geometry
        specific_geometry = filtered_geo['geometry'].iloc[0]
        centroid = specific_geometry.centroid

        # Set a zoom level for Paris arrondissements
        zoom_level = 13

        # Create the dictionary to store
        stored_data = {
            'zoom': zoom_level,
            'center': {
                'lat': centroid.y,
                'lon': centroid.x
            }
        }

        return stored_data

    @app.callback(
        Output('map-view-store-mainpage', 'data'),
        [Input('map-display', 'relayoutData'),
         Input('region-dropdown', 'value'),
         Input('department-dropdown', 'value'),
         Input('arrondissement-dropdown', 'value')],
        [State('map-view-store-mainpage', 'data')]
    )
    def store_map_view_mainpage(relayout_data, selected_region, selected_department, selected_arrondissement,
                                existing_data):
        # Initialize existing_data if it's None
        if existing_data is None:
            existing_data = {}

        # Reset zoom data when region or department changes
        ctx = dash.callback_context
        triggered_input = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        if triggered_input in ['region-dropdown', 'department-dropdown', 'arrondissement-dropdown']:
            return {}

        # If relayoutData is None or empty, do not update the store
        if not relayout_data:
            raise dash.exceptions.PreventUpdate

        # Define the keys that indicate a user interaction
        user_interaction_keys = {'map.zoom', 'map.center'}

        # Check if relayoutData contains any of the user interaction keys
        if user_interaction_keys.intersection(relayout_data.keys()):
            # Extract zoom and center from relayoutData
            zoom = relayout_data.get('map.zoom', existing_data.get('zoom'))
            center = relayout_data.get('map.center', existing_data.get('center'))

            if zoom is not None and center is not None:
                # Update the existing_data with new zoom and center
                existing_data['zoom'] = zoom
                existing_data['center'] = center

                return existing_data

        # If no user interaction keys are present, prevent updating the store
        raise dash.exceptions.PreventUpdate
