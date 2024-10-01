import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from shapely.geometry import Point
from dash import html, dcc

from layouts.layout_main import michelin_stars, bib_gourmand, color_map


# Hover-tip text
text_color_map = {
    0.5: "#FFB84D",
    1: "#640A64",
    2: "#640A64",
    3: "#FFB84D"
}


def plot_regional_outlines(region_df, region):
    """
    Plot the outlines of a selected region on a map.

    Args:
        region_df (GeoDataFrame): A GeoDataFrame containing geometries of regions with a 'region' column.
        region (str): The name of the region to plot.

    Returns:
        fig (plotly.graph_objs.Figure): A Plotly Figure object with the region outlines plotted.

    Raises:
        ValueError: If the specified region is not found in region_df.
    """
    fig = go.Figure(go.Scattermap())  # Initialize empty figure with mapbox

    # Filter the GeoDataFrame for the selected region
    filtered_region = region_df[region_df['region'] == region]

    if filtered_region.empty:
        # Handle case when the region is not found
        raise ValueError(f"Region '{region}' not found in the provided GeoDataFrame.")

    # Loop through the filtered GeoDataFrame
    for _, row in filtered_region.iterrows():
        geometry = row['geometry']
        if geometry.geom_type == 'Polygon':
            x, y = geometry.exterior.xy
            fig.add_trace(go.Scattermap(
                lat=list(y),
                lon=list(x),
                mode='lines',
                line=dict(width=1, color='black'),
                hoverinfo='none',
                showlegend=False
            ))
        elif geometry.geom_type == 'MultiPolygon':
            for poly in geometry.geoms:
                x, y = poly.exterior.xy
                fig.add_trace(go.Scattermap(
                    lat=list(y),
                    lon=list(x),
                    mode='lines',
                    line=dict(width=1, color='black'),
                    hoverinfo='none',
                    showlegend=False
                ))

    # Update map layout settings
    fig.update_layout(
        map_style="carto-positron",
        map_zoom=5,  # Zoom level to show all of France
        map_center_lat=46.603354,  # Approximate latitude for France center
        map_center_lon=1.888334,  # Approximate longitude for France center
        margin={"r": 0, "t": 0, "l": 0, "b": 0},  # Remove margins
        showlegend=False
    )
    return fig


def plot_department_outlines(geo_df, department_code, zoom_data=None):
    """
    Plot the outlines of a selected department on a map.

    Args:
        geo_df (GeoDataFrame): A GeoDataFrame containing geometries of departments with a 'code' column.
        department_code (str or int): The code of the department to plot.

    Returns:
        fig (plotly.graph_objs.Figure): A Plotly Figure object with the department outline plotted.

    Raises:
        ValueError: If the specified department code is not found in geo_df.
    """
    # Initialize zoom_data if not provided
    if zoom_data is None:
        zoom_data = {}

    # Extract zoom and center from zoom_data, with defaults for the whole of France
    zoom = zoom_data.get('zoom', 5)  # Default zoom level for France
    center_lat = zoom_data.get('center', {}).get('lat', 46.603354)  # Default latitude for France
    center_lon = zoom_data.get('center', {}).get('lon', 1.888334)  # Default longitude for France

    fig = go.Figure(go.Scattermap())  # Initialize empty figure with mapbox

    # Filter the GeoDataFrame for the selected department
    specific_geometry = geo_df[geo_df['code'] == str(department_code)]['geometry'].iloc[0]

    # Plot the geometry's boundaries
    if specific_geometry.geom_type == 'Polygon':
        x, y = specific_geometry.exterior.xy
        fig.add_trace(go.Scattermap(
            lat=list(y),
            lon=list(x),
            mode='lines',
            line=dict(width=0.5, color='black'),  # Making line thicker and black for visibility
            hoverinfo='none',
            showlegend=False  # Hide from legend
        ))
    elif specific_geometry.geom_type == 'MultiPolygon':
        for polygon in specific_geometry.geoms:
            if polygon.geom_type == 'Polygon':  # Ensure we're dealing with a Polygon
                x, y = polygon.exterior.xy
                fig.add_trace(go.Scattermap(
                    lat=list(y),
                    lon=list(x),
                    mode='lines',
                    line=dict(width=0.5, color='black'),
                    hoverinfo='none',
                    showlegend=False
                ))


    # Update map layout settings
    fig.update_layout(
        map_style="carto-positron",
        map_zoom=zoom,
        map_center_lat=center_lat,
        map_center_lon=center_lon,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},  # Remove margins
        showlegend=False
    )
    return fig


def plot_paris_arrondissement(data_df, paris_df, arrondissement, selected_stars, zoom_data=None):
    """
    Plot an interactive map of a Paris arrondissement, including restaurant points for selected star ratings.

    Args:
        data_df (pd.DataFrame): DataFrame containing restaurant data with 'arrondissement', 'stars', 'latitude', 'longitude', etc.
        paris_df (GeoDataFrame): GeoDataFrame containing geometries of Paris arrondissements with 'arrondissement' and 'geometry'.
        arrondissement (str): The arrondissement to plot.
        selected_stars (list): List of star ratings to include in the plot.
        zoom_data (dict, optional): Contains zoom and center information.

    Returns:
        fig (plotly.graph_objs.Figure): A Plotly Figure object with the arrondissement and restaurants plotted.
    """
    # Initialize a blank figure
    # Initialize zoom_data if not provided
    if zoom_data is None:
        zoom_data = {}

    # Extract zoom and center from zoom_data
    zoom = zoom_data.get('zoom', 13)  # Default zoom level for Paris
    center_lat = zoom_data.get('center', {}).get('lat', None)
    center_lon = zoom_data.get('center', {}).get('lon', None)

    fig = go.Figure()

    # Get the specific geometry
    filtered_geo = paris_df[paris_df['arrondissement'] == arrondissement]
    if filtered_geo.empty:
        raise ValueError(f"Arrondissement '{arrondissement}' not found in the provided GeoDataFrame.")

    specific_geometry = filtered_geo['geometry'].iloc[0]

    # Plot the arrondissement boundary
    if specific_geometry.geom_type == 'Polygon':
        x, y = specific_geometry.exterior.xy
        fig.add_trace(go.Scattermap(
            lat=list(y),
            lon=list(x),
            mode='lines',
            line=dict(width=1, color='black'),
            hoverinfo='none',
            showlegend=False
        ))
    elif specific_geometry.geom_type == 'MultiPolygon':
        for polygon in specific_geometry.geoms:
            x, y = polygon.exterior.xy
            fig.add_trace(go.Scattermap(
                lat=list(y),
                lon=list(x),
                mode='lines',
                line=dict(width=1, color='black'),
                hoverinfo='none',
                showlegend=False
            ))

    # Filter the data for the selected arrondissement and stars
    arr_data = data_df[
        (data_df['arrondissement'] == arrondissement) &
        (data_df['stars'].isin(selected_stars))
    ].copy()

    # Proceed to plot restaurants as in your existing plotting functions
    if not arr_data.empty:
        arr_data['color'] = arr_data['stars'].map(color_map)
        arr_data['hover_text'] = arr_data.apply(generate_hover_text, axis=1)

        for star, color in color_map.items():
            subset = arr_data[arr_data['stars'] == star]

            if subset.empty:
                continue

            label_name = '🍽️' if star == 0.5 else f"{'★' * int(star)}"

            fig.add_trace(go.Scattermap(
                lat=subset['latitude'],
                lon=subset['longitude'],
                mode='markers',
                marker=go.scattermap.Marker(size=11, color=color),
                text=subset['hover_text'],
                customdata=subset.index,
                hovertemplate='%{text}',
                name=label_name,
                showlegend=False
            ))

        # Use restaurant data to calculate map center if no zoom_data center
        if not center_lat or not center_lon:
            map_center_lat = arr_data['latitude'].mean()
            map_center_lon = arr_data['longitude'].mean()
        else:
            map_center_lat = center_lat
            map_center_lon = center_lon
    else:
        # Use arrondissement centroid if no restaurants
        centroid = specific_geometry.centroid
        map_center_lat = centroid.y
        map_center_lon = centroid.x

    # Update map layout
    fig.update_layout(
        map=dict(
            style="carto-positron",
            zoom=zoom,  # Adjust zoom level as needed
            center=dict(lat=map_center_lat, lon=map_center_lon),
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )

    return fig


def plot_arrondissement_outlines(paris_df, arrondissement, zoom_data=None):
    """
    Plot the outlines of a selected Paris arrondissement on a map.

    Args:
        paris_df (GeoDataFrame): A GeoDataFrame containing geometries of Paris arrondissements with 'arrondissement' and 'geometry'.
        arrondissement (str): The name of the arrondissement to plot.
        zoom_data (dict, optional): Contains zoom and center information.

    Returns:
        fig (plotly.graph_objs.Figure): A Plotly Figure object with the arrondissement outline plotted.

    Raises:
        ValueError: If the specified arrondissement is not found in paris_df.
    """
    # Initialize zoom_data if not provided
    if zoom_data is None:
        zoom_data = {}

    # Extract zoom and center from zoom_data, with defaults for Paris
    zoom = zoom_data.get('zoom', 13)  # Default zoom level for Paris arrondissements
    center_lat = zoom_data.get('center', {}).get('lat', 48.8566)  # Default latitude for Paris
    center_lon = zoom_data.get('center', {}).get('lon', 2.3522)  # Default longitude for Paris

    fig = go.Figure(go.Scattermap())  # Initialize empty figure with mapbox

    # Filter the GeoDataFrame for the selected arrondissement
    filtered_geo = paris_df[paris_df['arrondissement'] == arrondissement]
    if filtered_geo.empty:
        raise ValueError(f"Arrondissement '{arrondissement}' not found in the provided GeoDataFrame.")

    specific_geometry = filtered_geo['geometry'].iloc[0]

    # Plot the geometry's boundaries
    if specific_geometry.geom_type == 'Polygon':
        x, y = specific_geometry.exterior.xy
        fig.add_trace(go.Scattermap(
            lat=list(y),
            lon=list(x),
            mode='lines',
            line=dict(width=1, color='black'),  # Making line thicker and black for visibility
            hoverinfo='none',
            showlegend=False  # Hide from legend
        ))
    elif specific_geometry.geom_type == 'MultiPolygon':
        for polygon in specific_geometry.geoms:
            if polygon.geom_type == 'Polygon':  # Ensure we're dealing with a Polygon
                x, y = polygon.exterior.xy
                fig.add_trace(go.Scattermap(
                    lat=list(y),
                    lon=list(x),
                    mode='lines',
                    line=dict(width=1, color='black'),
                    hoverinfo='none',
                    showlegend=False
                ))

    # Update map layout settings
    fig.update_layout(
        map_style="carto-positron",
        map_zoom=zoom,
        map_center_lat=center_lat,
        map_center_lon=center_lon,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},  # Remove margins
        showlegend=False
    )

    return fig


def get_restaurant_details(row):
    """
    Generate an HTML Div containing detailed information about a restaurant.

    Args:
        row (pd.Series or dict): A pandas Series or dictionary containing restaurant information.

    Returns:
        details_layout (dash_html_components.Div): A Dash HTML Div containing the restaurant's details.

    Raises:
        KeyError: If expected keys are missing in the row data.
    """
    try:
        name = row['name']
        stars = row['stars']
        cuisine = row['cuisine']
        price = row['price']
        address = row['address']
        location = row['location']
        arrondissement = row.get('arrondissement', '')
        website_url = row['url']
        department_num = row['department_num']
    except KeyError as e:
        raise KeyError(f"Missing expected key in row data: {e}")

    # Color for the border based on the number of stars
    border_color = color_map.get(stars, '#ccc')  # Default to grey if no stars count matches

    # Create the address information with a conditional for Paris arrondissements
    if department_num == '75':
        location_info = html.Span(f"{arrondissement}, {location}", className='restaurant-location')
    else:
        location_info = html.Span(f"{location}", className='restaurant-location')

    # Determine if it's a Bib Gourmand or how many Michelin stars
    if stars == 0.5:
        star_component = bib_gourmand()
    else:
        star_component = michelin_stars(stars)

    # Create HTML content to display this information, organized in divs
    details_layout = html.Div([
        html.Div([
            html.Div([
                html.Span(name, className='restaurant-name'),
                html.Span(star_component, className='restaurant-stars'),
            ], className='details-header'),
            html.Div([
                html.Span(f"{cuisine}", className='restaurant-cuisine')
            ], className='details-cuisine'),
            html.Div([
                html.Span(f"{price}", className='restaurant-price')
            ], className='details-price'),
        ], className='restaurant-info'),
        html.Div([
            html.Div([
                html.Span(f"{address}", className='restaurant-address')
            ], className='details-address'),
            html.Div([
                location_info
            ], className='details-location'),
        ], className='address-info'),
        html.Div([
            html.A("Visit Website", href=website_url, target='_blank', className='restaurant-website', style={'display': 'block', 'marginTop': '10px'})
        ], className='details-website')
    ], className='restaurant-details', style={'borderColor': border_color})

    return details_layout


def generate_hover_text(row):
    """
    Generate HTML-formatted hover text for a restaurant.

    Args:
        row (pd.Series or dict): A pandas Series or dictionary containing restaurant information.

    Returns:
        hover_text (str): An HTML-formatted string for hover text.

    Raises:
        KeyError: If expected keys are missing in the row data.
    """
    try:
        name = row['name']
        location = row['location']
        stars = row['stars']
    except KeyError as e:
        raise KeyError(f"Missing expected key in row data: {e}")

    text_color = text_color_map.get(stars, '#000')

    hover_text = (
        f"<span style=\"font-family: 'Libre Franklin', sans-serif; font-size: 12px; color: {text_color};\">"
        f"<span style='font-size: 14px;'>{name}</span><br>"
        f"{location}<br>"
    )
    return hover_text


def plot_interactive_department(data_df, geo_df, department_code, selected_stars, zoom_data=None):
    """
    Plot an interactive map of a department, including restaurant points for selected star ratings.

    Args:
        data_df (pd.DataFrame): DataFrame containing restaurant data with 'department_num', 'stars', 'latitude', 'longitude', etc.
        geo_df (GeoDataFrame): GeoDataFrame containing geometries of departments with 'code' and 'geometry'.
        department_code (str or int): The code of the department to plot.
        selected_stars (list): List of star ratings to include in the plot.
        zoom_data (dict): Dictionary containing zoom level and center information.

    Returns:
        fig (plotly.graph_objs.Figure): A Plotly Figure object with the department and restaurants plotted.

    Raises:
        ValueError: If the specified department code is not found in geo_df.
    """
    # Initialize zoom_data if not provided
    if zoom_data is None:
        zoom_data = {}

    # Get the zoom and center from zoom_data or fallback to department defaults
    zoom = zoom_data.get('zoom', 8 if department_code != '75' else 11)  # Default zoom: 11 for Paris, 8 otherwise
    center_lat = zoom_data.get('center', {}).get('lat', None)
    center_lon = zoom_data.get('center', {}).get('lon', None)

    # Initialize a blank figure
    fig = go.Figure()
    fig.update_layout(autosize=True)

    # Get the specific geometry for the department
    filtered_geo = geo_df[geo_df['code'] == str(department_code)]
    if filtered_geo.empty:
        raise ValueError(f"Department code '{department_code}' not found in the provided GeoDataFrame.")

    specific_geometry = filtered_geo['geometry'].iloc[0]

    # Plot department boundaries
    if specific_geometry.geom_type == 'Polygon':
        x, y = specific_geometry.exterior.xy
        fig.add_trace(go.Scattermap(
            lat=list(y),
            lon=list(x),
            mode='lines',
            line=dict(width=0.5, color='black'),
            hoverinfo='none',
            showlegend=False  # Hide from legend
        ))
    elif specific_geometry.geom_type == 'MultiPolygon':
        for polygon in specific_geometry.geoms:
            x, y = polygon.exterior.xy
            fig.add_trace(go.Scattermap(
                lat=list(y),
                lon=list(x),
                mode='lines',
                line=dict(width=0.5, color='black'),
                hoverinfo='none',
                showlegend=False
            ))

    # Filter data for the selected department and stars
    dept_data = data_df[
        (data_df['department_num'] == str(department_code)) &
        (data_df['stars'].isin(selected_stars))
    ].copy()

    # If dept_data is not empty, add restaurant points
    if not dept_data.empty:
        dept_data['color'] = dept_data['stars'].map(color_map)
        dept_data['hover_text'] = dept_data.apply(generate_hover_text, axis=1)

        for star, color in color_map.items():
            subset = dept_data[dept_data['stars'] == star]

            if subset.empty:
                continue  # Skip if no data for this star rating

            label_name = '🍽️' if star == 0.5 else f"{'★' * int(star)}"

            fig.add_trace(go.Scattermap(
                lat=subset['latitude'],
                lon=subset['longitude'],
                mode='markers',
                marker=go.scattermap.Marker(size=11, color=color),
                text=subset['hover_text'],
                customdata=subset.index,
                hovertemplate='%{text}',
                name=label_name,
                showlegend=False
            ))

        # Calculate the center if zoom_data doesn't have it
        if center_lat is None or center_lon is None:
            map_center_lat = dept_data['latitude'].mean()
            map_center_lon = dept_data['longitude'].mean()
        else:
            map_center_lat = center_lat
            map_center_lon = center_lon
    else:
        # If no restaurant data, center based on geometry's centroid
        centroid = specific_geometry.centroid
        map_center_lat = centroid.y
        map_center_lon = centroid.x

    # Update the layout with the correct zoom and center
    fig.update_layout(
        font=dict(
            family="Courier New, monospace",
            size=18,
            color="white"
        ),
        width=800,
        height=600,
        hovermode='closest',
        hoverdistance=10,
        map_style="carto-positron",
        map_zoom=zoom,  # Zoom level from zoom_data or default
        map_center_lat=map_center_lat,
        map_center_lon=map_center_lon,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},  # Remove margins
    )

    return fig


def default_map_figure():
    """
    Generate a default map figure centered on France.

    Returns:
        - fig (plotly.graph_objs.Figure): A Plotly Figure object with default map settings.
    """
    return go.Figure(go.Scattermap()).update_layout(
            font=dict(
                family="Courier New, monospace",
                size=18,
                color="white"
            ),
            width=800,
            height=600,
            mapbox_style="carto-positron",
            map_zoom=5,
            map_center_lat=46.603354,
            map_center_lon=1.888334,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )


# -------------------> Analysis Functions

def create_michelin_bar_chart(filtered_df, select_stars, granularity, title):
    """
    Create a stacked bar chart of Michelin restaurants for the given data and star levels.

    Args:
        filtered_df (pandas.DataFrame): The filtered DataFrame based on region/department.
        select_stars (list): The selected star ratings to display.
        granularity (str): The level of granularity ('region', 'department' or 'arrondissement').
        title (str): The title of the bar chart.

    Returns:
        go.Figure: A Plotly figure representing the stacked bar chart.
    """
    traces = []

    if 0.5 in select_stars:
        traces.append(go.Bar(
            y=filtered_df[granularity],
            x=filtered_df['bib_gourmand'],
            name="Bib Gourmand",
            marker_color=color_map[0.5],
            orientation='h',
            hovertemplate='<b>Restaurants:</b> %{x}<extra></extra>',
        ))
    if 1 in select_stars:
        traces.append(go.Bar(
            y=filtered_df[granularity],
            x=filtered_df['1_star'],
            name="1 Star",
            marker_color=color_map[1],
            orientation='h',
            hovertemplate='<b>Restaurants:</b> %{x}<extra></extra>',
        ))
    if 2 in select_stars:
        traces.append(go.Bar(
            y=filtered_df[granularity],
            x=filtered_df['2_star'],
            name="2 Stars",
            marker_color=color_map[2],
            orientation='h',
            hovertemplate='<b>Restaurants:</b> %{x}<extra></extra>',
        ))
    if 3 in select_stars:
        traces.append(go.Bar(
            y=filtered_df[granularity],
            x=filtered_df['3_star'],
            name="3 Stars",
            marker_color=color_map[3],
            orientation='h',
            hovertemplate='<b>Restaurants:</b> %{x}<extra></extra>',
        ))

    fig_bar = go.Figure(data=traces)
    fig_bar.update_layout(
        barmode='stack',
        title=title,
        xaxis_title="Number of Restaurants",
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(title_standoff=15),
        yaxis=dict(ticklabelposition="outside", automargin=True, autorange='reversed')
    )

    return fig_bar


def update_button_active_state_helper(n_clicks_list, ids, filter_type):
    """
    Generalized function to update the button states for different filter types (e.g., analysis, department, etc.).

    Args:
        n_clicks_list (list): List of n_clicks from the buttons.
        ids (list): List of button ids.
        filter_type (str): The type of filter (analysis, department, demographics, wine).

    Returns:
        list: Class names for each button.
        list: Styles for each button.
    """
    # Initialize empty lists to store class names and styles
    class_names = []
    styles = []

    for n_clicks, button_id in zip(n_clicks_list, ids):
        index = button_id['index']

        # Determine if the button is currently active
        is_active = n_clicks % 2 == 0  # Even clicks mean 'active'
        if is_active:
            background_color = color_map[index]  # Full color for active state
        else:
            background_color = (f"rgba({int(color_map[index][1:3], 16)},"
                                f"{int(color_map[index][3:5], 16)},"
                                f"{int(color_map[index][5:7], 16)},"
                                f"0.6)")  # Lighter color for inactive

        # Update class name and style based on the active/inactive state
        class_name = f"me-1 star-button-{filter_type}" + (" active" if is_active else "")
        color_style = {
            "display": 'inline-block',
            "width": '100%',
            'backgroundColor': background_color,
        }

        class_names.append(class_name)
        styles.append(color_style)

    return class_names, styles


def plot_single_choropleth_plotly(df, selected_stars, granularity='region', show_labels=True, cmap='Reds'):
    """
    Plot a single choropleth map using Plotly.

    Args:
        df (GeoDataFrame): The DataFrame containing the data.
        selected_stars (list): List of selected star levels (e.g., [0.5, 1, 2, 3]).
        granularity (str): Level of granularity - 'department', or 'region'. Default is 'region'.
        show_labels (bool): Whether to show the labels. Default is True.
        cmap (str): The colormap to use. Default is 'Reds'.

    Returns:
        fig (Plotly Figure): The plotly figure object.
    """

    # Prepare the figure
    fig = go.Figure()

    # Calculate the total number of restaurants for the selected stars
    df['total_restaurants'] = 0
    if 0.5 in selected_stars:
        df['total_restaurants'] += df['bib_gourmand']
    if 1 in selected_stars:
        df['total_restaurants'] += df['1_star']
    if 2 in selected_stars:
        df['total_restaurants'] += df['2_star']
    if 3 in selected_stars:
        df['total_restaurants'] += df['3_star']

    # Set the hover template and custom data based on granularity
    if granularity == 'region':
        hovertemplate = (
            '<b>Region:</b> %{customdata[0]}<br>'
            '<b>Total Restaurants:</b> %{z}<extra></extra>'
        )
        customdata = df[['region']].values
    elif granularity == 'department':
        hovertemplate = (
            '<b>Department:</b> %{customdata[0]}<br>'
            '<b>Code:</b> %{customdata[1]}<br>'
            '<b>Total Restaurants:</b> %{z}<extra></extra>'
        )
        customdata = df[['department', 'code']].values
    elif granularity == 'arrondissement':
        hovertemplate = (
            '<b>Arrondissement:</b> %{customdata[0]}<br>'
            '%{customdata[1]}, (%{customdata[2]})<br>'
            '<b>Total Restaurants:</b> %{z}<extra></extra>'
        )
        customdata = df[['arrondissement', 'department', 'department_num']].values
    else:
        raise ValueError(f"Invalid granularity: {granularity}. Choose from ['region', 'department', 'arrondissement'].")

    # Add the choropleth map with hover info based on granularity
    fig.add_trace(
        go.Choropleth(
            geojson=df.__geo_interface__,  # GeoJSON representation of the dataframe
            z=df['total_restaurants'],  # Use total restaurants for coloring
            locations=df.index,  # Match the locations via index
            colorscale=cmap,
            colorbar_title='Restaurants',
            marker_line_width=0.5,
            marker_line_color='darkgray',
            hovertemplate=hovertemplate,  # Use the dynamic hovertemplate
            customdata=customdata  # Pass the custom data for hover
        )
    )

    # If show_labels is True, add labels to the map based on granularity
    if show_labels:
        if granularity == 'region':
            label_column = 'region'
        elif granularity == 'department':
            label_column = 'code'
        elif granularity == 'arrondissement':
            label_column = 'arrondissement'
        else:
            raise ValueError(f"Invalid granularity: {granularity}. Choose from ['region', 'department', 'arrondissement'].")

        # Add text labels (centroid labels)
        centroids = df.geometry.centroid
        for x, y, label in zip(centroids.x, centroids.y, df[label_column]):
            fig.add_trace(
                go.Scattergeo(
                    lon=[x],
                    lat=[y],
                    text=label,
                    mode='text',
                    textposition='top center',
                    showlegend=False
                )
            )

    # Determine custom centering and zoom level
    if granularity == 'department':
        selected_region = df['region'].unique()[0]  # Extract the region from the dataframe

        # Re-project to Web Mercator (EPSG:3857) for accurate centroid calculation
        df_projected = df.to_crs(epsg=3857)

        if selected_region == 'Île-de-France':
            # Custom centering for Île-de-France
            centroids = df_projected.geometry.centroid
            avg_x, avg_y = centroids.x.mean(), centroids.y.mean()
            zoom_level = 30
        else:
            # General case for other departments
            centroids = df_projected.geometry.centroid
            avg_x, avg_y = centroids.x.mean(), centroids.y.mean()
            zoom_level = 11

        # Convert the projected centroids back to geographic CRS (EPSG:4326)
        centroids_geo = gpd.GeoSeries([Point(avg_x, avg_y)], crs='EPSG:3857').to_crs(epsg=4326)
        avg_lat, avg_lon = centroids_geo[0].y, centroids_geo[0].x

    elif granularity == 'arrondissement':
        # Re-project to Web Mercator (EPSG:3857) for accurate centroid calculation
        df_projected = df.to_crs(epsg=3857)

        # Handle arrondissement-level zoom and center
        centroids = df_projected.geometry.centroid
        avg_x, avg_y = centroids.x.mean(), centroids.y.mean()

        if df['department_num'].unique()[0] == '75':  # Check if it's Paris
            zoom_level = 300  # High zoom for Paris arrondissements
        elif df['region'].unique()[0] == 'Île-de-France':
            zoom_level = 125
        else:
            zoom_level = 25  # Default zoom for other arrondissements

        # Convert the projected centroids back to geographic CRS (EPSG:4326)
        centroids_geo = gpd.GeoSeries([Point(avg_x, avg_y)], crs='EPSG:3857').to_crs(epsg=4326)
        avg_lat, avg_lon = centroids_geo[0].y, centroids_geo[0].x

    else:
        # Default centering on France
        avg_lat, avg_lon = 46.603354, 1.888334
        zoom_level = 6  # Default zoom for region-level map

    # Update the layout for the figure, centering on France and adjusting size
    fig.update_layout(
        geo=dict(
            scope='europe',  # Set the scope to Europe
            resolution=50,
            showcoastlines=False,
            showland=True,
            landcolor="lightgray",
            center=dict(lat=avg_lat, lon=avg_lon),  # Custom center
            projection_scale=zoom_level,  # Custom zoom
        ),
        margin=dict(l=10, r=10, t=30, b=10),  # Reduce margins to reduce white space
    )

    return fig


def top_restaurants(data, granularity, star_rating, top_n, display_restaurants=True):
    """
    Returns a list of Dash components for top_n regions, departments, or arrondissements with the highest count of
    'star_rating' restaurants. Tied areas outside the top N are grouped separately.

    Args:
        data (pandas.DataFrame): The dataset containing restaurant info.
        granularity (str): Either 'region', 'department', or 'arrondissement'.
        star_rating (int): The Michelin star rating (2 or 3).
        top_n (int): The number of top (granularity) to consider.
        display_restaurants (bool): Whether to display individual restaurants. Default is True.

    Returns:
        list: Dash components containing the ranking or restaurant details, with ties grouped separately.
    """
    # Ensure the data contains necessary columns based on granularity
    if granularity not in data.columns:
        raise ValueError(f"Data must contain '{granularity}' column.")

    # Filter the data to include only the restaurants with the specified star rating
    filtered_data = data[data['stars'] == star_rating]

    # Special handling for Paris department or Île-de-France region
    if top_n == 'paris':
        if granularity == 'department':
            filtered_data = filtered_data[filtered_data['department_num'] == '75']  # Focus on Paris department
        elif granularity == 'region':
            filtered_data = filtered_data[filtered_data['region'] == 'Île-de-France']  # Focus on Île-de-France region
        # Calculate restaurant counts for each area
        restaurant_counts = filtered_data[granularity].value_counts()
        top_areas = restaurant_counts.nlargest(top_n)

    else:
        # General case for other regions, departments, or arrondissements
        restaurant_counts = filtered_data[granularity].value_counts()
        top_areas = restaurant_counts.nlargest(top_n)

    # Detect if there are any tied areas outside the top N
    all_tied_areas = restaurant_counts[restaurant_counts == top_areas.iloc[-1]]  # All areas tied for last place
    is_tied = len(all_tied_areas) > len(top_areas)

    components = []
    for area, restaurant_count in top_areas.items():
        restaurant_word = "Restaurant" if restaurant_count == 1 else "Restaurants"

        # Format the display based on the granularity
        if granularity == 'department':
            department_info = filtered_data[filtered_data['department'] == area].iloc[0]
            department_code = department_info['department_num']
            region_name = department_info['region']
            display_area = f"{area} ({department_code}): {region_name}"
        elif granularity == 'arrondissement':
            arrondissement_info = filtered_data[filtered_data['arrondissement'] == area].iloc[0]
            department_name = arrondissement_info['department']
            department_code = arrondissement_info['department_num']
            region_name = arrondissement_info['region']
            display_area = f"{area}, {department_name} ({department_code}), {region_name}"
        else:
            display_area = area

        # Add area name and restaurant count
        area_component = html.Div([
            html.Div(display_area, style={"font-weight": "bold", "font-size": "20px"}),
            html.Div([
                f"{restaurant_count} ",
                html.Span(michelin_stars(star_rating), style={"vertical-align": "middle"}),
                f" {restaurant_word}"
            ], style={"margin-left": "10px", "display": "inline-block"})
        ], style={"margin-bottom": "40px", "text-align": "center"})

        components.append(area_component)

        # Display restaurant details for this area if required
        if display_restaurants:
            restaurants_in_area = filtered_data[filtered_data[granularity] == area]
            restaurant_cards = [get_restaurant_details(row) for _, row in restaurants_in_area.iterrows()]

            components.append(html.Div(
                children=restaurant_cards,
                className='restaurant-cards-container',
                style={'display': 'flex', 'flex-wrap': 'wrap', 'gap': '20px', 'margin-bottom': '40px',
                       'justify-content': 'center'}
            ))

    # Handle tied areas, ensuring restaurant details are shown for all tied areas
    if is_tied:
        tied_components = []  # A separate section for tied areas
        for area, restaurant_count in all_tied_areas.items():
            if area not in top_areas.index:  # Only include tied areas outside top N
                restaurant_word = "Restaurant" if restaurant_count == 1 else "Restaurants"

                # Format the tied area in the same style as the top areas
                if granularity == 'department':
                    department_info = filtered_data[filtered_data['department'] == area].iloc[0]
                    department_code = department_info['department_num']
                    region_name = department_info['region']
                    display_area = f"{area} ({department_code}): {region_name}"
                elif granularity == 'arrondissement':
                    arrondissement_info = filtered_data[filtered_data['arrondissement'] == area].iloc[0]
                    department_name = arrondissement_info['department']
                    department_code = arrondissement_info['department_num']
                    region_name = arrondissement_info['region']
                    display_area = f"{area}, {department_name} ({department_code}), {region_name}"
                else:
                    display_area = area

                tied_area_component = html.Div([
                    html.Div(display_area, style={"font-weight": "bold", "font-size": "20px"}),
                    html.Div([
                        f"{restaurant_count} ",
                        html.Span(michelin_stars(star_rating), style={"vertical-align": "middle"}),
                        f" {restaurant_word}"
                    ], style={"margin-left": "10px", "display": "inline-block"})
                ], style={"margin-bottom": "40px", "text-align": "center"})

                tied_components.append(tied_area_component)

                # Show detailed restaurant info for the tied areas if required
                if display_restaurants:
                    restaurants_in_area = filtered_data[filtered_data[granularity] == area]
                    restaurant_cards = [get_restaurant_details(row) for _, row in restaurants_in_area.iterrows()]

                    tied_components.append(html.Div(
                        children=restaurant_cards,
                        className='restaurant-cards-container',
                        style={'display': 'flex', 'flex-wrap': 'wrap', 'gap': '20px', 'margin-bottom': '40px',
                               'justify-content': 'center'}
                    ))

        # Add a header for the tied areas
        components.append(html.Div("Tied Areas:", style={"font-weight": "bold", "font-size": "22px"}))
        components.extend(tied_components)  # Add the tied areas to the main components

    return components


def plot_demographic_choropleth_plotly(df, all_france, metric=None, granularity='region', show_labels=True, cmap='Blues', restaurants=False, selected_stars=[1, 2, 3]):
    """
    Plot a choropleth map for demographic metrics using Plotly. Optionally, plot restaurant locations from 'all_france'.

    Args:
        df (GeoDataFrame): The DataFrame containing the geographic data.
        all_france (pd.DataFrame): DataFrame containing restaurant data with latitude and longitude.
        metric (str): The demographic metric to visualize. Default is None.
        granularity (str): The level of granularity - 'department' or 'region'. Default is 'region'.
        show_labels (bool): Whether to show labels. Default is True.
        cmap (str): The colormap to use. Default is 'Blues'.
        restaurants (bool): Whether to plot restaurant locations. Default is False.
        selected_stars (list): List of selected star ratings (e.g., [1, 2, 3]).

    Returns:
        fig (Plotly Figure): The Plotly figure object.
    """
    # Dictionary for metric titles
    metric_titles = {
        'GDP_millions(€)': 'GDP (Millions €)',
        'GDP_per_capita(€)': 'GDP per Capita (€)',
        'poverty_rate(%)': 'Poverty Rate (%)',
        'average_annual_unemployment_rate(%)': 'Unemployment Rate (%)',
        'average_net_hourly_wage(€)': 'Hourly Net Wage (€)',
        'municipal_population': 'Municipal Population',
        'population_density(inhabitants/sq_km)': 'Population Density (inhabitants/km²)'
    }

    # Color mapping for star ratings
    star_colors = {
        0.5: "#640A64",  # Bib Gourmand
        1: "#FFB84D",    # 1 star
        2: "#FE6F64",    # 2 stars
        3: "#C2282D"     # 3 stars
    }

    # all_france has some English region names -> easy way to solve
    region_mapping = {
        'Brittany': 'Bretagne',
        'Corsica': 'Corse',
        'Normandy': 'Normandie'
    }

    # Initialize Plotly figure
    fig = go.Figure()

    # Plot the choropleth map if a metric is provided
    if metric:
        hovertemplate = (
            f'<b>Region:</b> %{{customdata[0]}}<br>'
            f'<b>{metric_titles.get(metric, metric)}:</b> %{{z:.2f}}<extra></extra>'
        )
        customdata = df[['region']].values if granularity == 'region' else df[['department', 'code']].values

        # Add choropleth trace
        fig.add_trace(
            go.Choropleth(
                geojson=df.__geo_interface__,
                z=df[metric],
                locations=df.index,
                colorscale=cmap,
                colorbar_title=metric_titles.get(metric, metric),
                marker_line_width=0.5,
                marker_line_color='darkgray',
                hovertemplate=hovertemplate,
                customdata=customdata
            )
        )
    else:
        # If no metric is provided, show only the boundaries
        fig.add_trace(
            go.Choropleth(
                geojson=df.__geo_interface__,
                z=[0] * len(df),
                locations=df.index,
                colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
                marker_line_width=0.5,
                marker_line_color='darkgray',
                hoverinfo='none',
                showscale=False
            )
        )

    if restaurants and selected_stars:
        # Map the English region names to the French ones used in df
        all_france['region'] = all_france['region'].replace(region_mapping)
        filtered_restaurants = all_france[all_france['stars'].isin(selected_stars)]

        if granularity == 'department':
            filtered_restaurants = filtered_restaurants[filtered_restaurants['region'].isin(df['region'].unique())]

        for star in selected_stars:
            star_data = filtered_restaurants[filtered_restaurants['stars'] == star]

            # Plot each restaurant as a scatter point on the map
            fig.add_trace(
                go.Scattergeo(
                    lon=star_data['longitude'],
                    lat=star_data['latitude'],
                    mode='markers',
                    marker=dict(size=8, color=star_colors.get(star)),
                    hovertemplate=(
                        f'<b>Restaurant Name:</b> %{{customdata[0]}}<br>'
                        f'<b>Location:</b> %{{customdata[1]}}<br>'
                    ),
                    customdata=star_data[['name', 'location']].values,  # Pass restaurant names and locations
                    showlegend=False,  # Ensure no legend is created for restaurants
                    name=f"{'★' * int(star)}"
                )
            )

    # Optionally show labels (region or department)
    if show_labels:
        label_column = 'region' if granularity == 'region' else 'code'
        centroids = df.geometry.centroid
        for x, y, label in zip(centroids.x, centroids.y, df[label_column]):
            fig.add_trace(
                go.Scattergeo(
                    lon=[x],
                    lat=[y],
                    text=label,
                    mode='text',
                    textposition='top center',
                    showlegend=False
                )
            )

    # Update the layout for the map
    fig.update_layout(
        geo=dict(
            scope='europe',
            resolution=50,
            showcoastlines=False,
            showland=True,
            landcolor="lightgray",
            center=dict(lat=46.603354, lon=1.888334),
            projection_scale=6,
        ),
        height=700,
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode='closest',  # Focus on the closest point for hover
        hoverdistance=5,      # Set the minimum distance for hover (tweak as needed)
    )

    return fig


def calculate_weighted_mean(df, metric, weight_column='municipal_population'):
    """
    Calculate the weighted mean for a given metric in the dataframe, based on the population or other weight column.

    Args:
        df (pd.DataFrame): The dataframe containing the data.
        metric (str): The column name of the metric for which the weighted mean is calculated.
        weight_column (str): The column used as the weight for the weighted mean (e.g., population).

    Returns:
        float: The weighted mean of the metric.
    """
    # Calculate the weighted mean
    weighted_mean = (df[metric] * df[weight_column]).sum() / df[weight_column].sum()

    return weighted_mean


def plot_demographics_barchart(df, metric, granularity, weighted_mean):
    """
    Create a horizontal bar chart with an optional vertical line indicating the weighted mean.

    Args:
        df (pd.DataFrame): The dataframe containing the data.
        metric (str): The metric to plot on the bar chart.
        granularity (str): Either 'region' or 'department' to determine the grouping.
        weighted_mean (float or None): The calculated weighted mean to display as a dashed line, or None if excluded.

    Returns:
        fig (go.Figure): The Plotly figure object with the bar chart and the weighted mean line (if applicable).
    """
    # Dictionary to map data science metric names to display-friendly titles
    metric_titles = {
        'GDP_millions(€)': 'GDP (Millions €)',
        'GDP_per_capita(€)': 'GDP per Capita (€)',
        'poverty_rate(%)': 'Poverty Rate (%)',
        'average_annual_unemployment_rate(%)': 'Unemployment Rate (%)',
        'average_net_hourly_wage(€)': 'Hourly Net Wage (€)',
        'municipal_population': 'Municipal Population',
        'population_density(inhabitants/sq_km)': 'Population Density (inhabitants/km²)'
    }

    # Dictionary for adding the appropriate symbol to the weighted mean
    metric_units = {
        'GDP_millions(€)': '€',
        'GDP_per_capita(€)': '€',
        'poverty_rate(%)': '%',
        'average_annual_unemployment_rate(%)': '%',
        'average_net_hourly_wage(€)': '€',
        'municipal_population': '',
        'population_density(inhabitants/sq_km)': ''
    }

    metric_title = metric_titles.get(metric, metric)  # Fallback to raw metric if not found in the dictionary
    metric_unit = metric_units.get(metric, '')

    # Create a horizontal bar chart
    fig = go.Figure()

    # Add the bar chart for the given metric by granularity (region/department)
    fig.add_trace(go.Bar(
        y=df[granularity],
        x=df[metric],
        orientation='h',
        marker=dict(color='#1f77b4'),
        hovertemplate=(
            f'<b>{granularity.capitalize()}:</b> %{{y}}<br>'
            f'<b>{metric_title}:</b> %{{x:.2f}}{metric_unit}<extra></extra>'
        )
    ))

    # Calculate dynamic x-axis range, adding some padding (10%) around the min/max values
    min_value = df[metric].min()
    max_value = df[metric].max()
    padding = (max_value - min_value) * 0.1  # 10% padding

    x_axis_range = [min_value - padding, max_value + padding]  # Dynamic range

    # Add the weighted mean as a red dashed vertical line if it's provided and within range
    if weighted_mean is not None and metric not in ['municipal_population', 'population_density(inhabitants/sq_km)']:
        # Adjust the x-axis range if the weighted mean is outside the range
        if weighted_mean < x_axis_range[0]:
            x_axis_range[0] = weighted_mean - padding  # Extend to include the mean
        elif weighted_mean > x_axis_range[1]:
            x_axis_range[1] = weighted_mean + padding  # Extend to include the mean

        if x_axis_range[0] <= weighted_mean <= x_axis_range[1]:
            # Add the vertical line for the weighted mean
            fig.add_shape(
                type="line",
                x0=weighted_mean,
                x1=weighted_mean,
                y0=-0.5,
                y1=len(df[granularity]) - 0.5,
                line=dict(color="red", width=2),
                name='Weighted Mean'
            )

            # Add an annotation for the weighted mean
            fig.add_annotation(
                x=weighted_mean,
                y=1,  # Position at the top of the chart
                xref="x",
                yref="paper",
                text=f"French Mean: {weighted_mean:.2f} {metric_unit}",  # Add unit to the mean
                showarrow=True,
                arrowhead=2,
                ax=-30,  # Horizontal offset for the annotation
                ay=-30,  # Vertical offset for the annotation
                font=dict(color="red", size=12),
                arrowcolor="red"
            )
        else:
            # If the weighted mean is out of range, show an annotation on the edge of the chart
            fig.add_annotation(
                x=x_axis_range[1],  # Position the annotation at the right edge
                y=1,  # Top of the chart
                xref="x",
                yref="paper",
                text=f"French Mean: {weighted_mean:.2f} {metric_unit} (off-scale)",  # Indicate that it's off-scale
                showarrow=False,  # No arrow needed
                font=dict(color="red", size=12)
            )

    # Customize layout
    fig.update_layout(
        title=f"{metric_title} by {granularity.capitalize()}",
        xaxis_title=metric_title,
        xaxis=dict(range=x_axis_range),
        yaxis=dict(autorange='reversed'),
        showlegend=False,
        plot_bgcolor='white',
        height=550,
    )

    return fig


def plot_wine_choropleth_plotly(
    df, wine_df, all_france, outline_type=None, show_restaurants=False, selected_stars=(1, 2, 3), zoom_data=None
):
    """
    Plot wine regions over a tile map using Plotly and go.Scattermap, with optional region/department outlines and restaurants.

    Args:
        df (GeoDataFrame): The base geographic data (either regions or departments).
        wine_df (GeoDataFrame): GeoDataFrame containing wine region shapes and colors.
        all_france (pd.DataFrame): DataFrame containing restaurant data.
        outline_type (str): Either 'region', 'department', or None. Used to show outlines.
        show_restaurants (bool): Whether to plot restaurant locations. Default is False.
        selected_stars (list): List of selected star ratings to plot. Default is (1, 2, 3).

    Returns:
        fig (go.Figure): The Plotly figure object.
        wine_region_curve_numbers (list): List of curve numbers corresponding to the wine region traces.
    """
    fig = go.Figure()
    wine_region_curve_numbers = []  # List to store curveNumbers for wine regions

    # Ensure zoom_data is a dictionary
    if zoom_data is None:
        zoom_data = {}

    # 1. Optionally show outlines for regions or departments based on `outline_type`
    if outline_type in ['region', 'department']:
        for _, row in df.iterrows():
            geometry = row['geometry']
            name = row[outline_type]

            # Handle different geometry types
            if geometry.geom_type == 'Polygon':
                geometries = [geometry]
            elif geometry.geom_type == 'MultiPolygon':
                geometries = geometry.geoms
            else:
                continue  # Skip unsupported geometries

            # Plot each polygon in the geometry
            for polygon in geometries:
                # Extract exterior coordinates
                lon, lat = polygon.exterior.coords.xy
                lon = list(lon)
                lat = list(lat)
                fig.add_trace(
                    go.Scattermap(
                        lon=lon,
                        lat=lat,
                        mode='lines',
                        line=dict(width=0.3, color='black'),
                        hoverinfo='text',
                        text=f"{name}",
                        showlegend=False,
                    )
                )

                # Plot interiors (holes) if any
                for interior in polygon.interiors:
                    lon_int, lat_int = interior.coords.xy
                    lon_int = list(lon_int)
                    lat_int = list(lat_int)
                    fig.add_trace(
                        go.Scattermap(
                            lon=lon_int,
                            lat=lat_int,
                            mode='lines',
                            line=dict(width=0.3, color='black'),
                            hoverinfo='skip',
                            showlegend=False,
                        )
                    )

    # 2. Plot wine regions
    for i, region_row in wine_df.iterrows():
        geometry = region_row['geometry']
        region_name = region_row['region']
        region_color = region_row['colour']

        # Handle different geometry types
        if geometry.geom_type == 'Polygon':
            polygons = [geometry]
        elif geometry.geom_type == 'MultiPolygon':
            polygons = geometry.geoms
        else:
            print(f"Skipping geometry of type: {geometry.geom_type}\nIn region: {region_name}")
            continue  # Skip unsupported geometries

        for polygon in polygons:
            # Extract exterior coordinates
            lon, lat = polygon.exterior.coords.xy
            lon = list(lon)
            lat = list(lat)

            fig.add_trace(
                go.Scattermap(
                    lon=lon,
                    lat=lat,
                    mode='lines',
                    fill='toself',
                    fillcolor=region_color,
                    line=dict(width=0.5, color='darkgray'),
                    hoverinfo='text',
                    hovertemplate=f'{region_name}<br>',
                    name='Wine Region',
                    showlegend=False
                )
            )
            # Store the curveNumber for this trace (wine region)
            wine_region_curve_numbers.append(len(fig.data) - 1)

            # Plot interiors (holes) if any
            for interior in polygon.interiors:
                lon_int, lat_int = interior.coords.xy
                lon_int = list(lon_int)
                lat_int = list(lat_int)
                fig.add_trace(
                    go.Scattermap(
                        lon=lon_int,
                        lat=lat_int,
                        mode='lines',
                        fill='toself',
                        fillcolor=region_color,
                        line=dict(width=0.5, color='darkgray'),
                        hoverinfo='text',
                        hovertemplate=f'{region_name}<br>',
                        name='Wine Region',
                        showlegend=False,
                    )
                )

    # 3. Optionally plot restaurants based on selected star ratings
    if show_restaurants and selected_stars:
        star_colors = {1: "#FFB84D", 2: "#FE6F64", 3: "#C2282D"}
        filtered_restaurants = all_france[all_france['stars'].isin(selected_stars)]

        for star in selected_stars:
            star_data = filtered_restaurants[filtered_restaurants['stars'] == star]

            if not star_data.empty:
                fig.add_trace(
                    go.Scattermap(
                        lon=star_data['longitude'].tolist(),
                        lat=star_data['latitude'].tolist(),
                        mode='markers',
                        marker=go.scattermap.Marker(size=8, color=star_colors.get(star)),
                        hovertemplate=(
                            '<b>Restaurant Name:</b> %{customdata[0]}<br>'
                            '<b>Location:</b> %{customdata[1]}<br>'
                        ),
                        customdata=star_data[['name', 'location']].values,
                        showlegend=False,
                        name=f"{'★' * int(star)}",
                    )
                )

    # 4. Adjust the layout
    # Extract zoom and center from zoom_data, using default values if keys are missing
    zoom = zoom_data.get('zoom', 5)
    center_lat = zoom_data.get('center', {}).get('lat', 46.603354)
    center_lon = zoom_data.get('center', {}).get('lon', 1.888334)

    fig.update_layout(
        map_style="carto-positron",
        map_zoom=zoom,
        map_center_lat=center_lat,
        map_center_lon=center_lon,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        hovermode='closest',
    )

    return fig, wine_region_curve_numbers





# def plot_wine_choropleth_plotly(
#     df, wine_df, all_france, outline_type=None, show_restaurants=False, selected_stars=(1, 2, 3), zoom_data=None
# ):
#     """
#     Plot wine regions over a tile map using Plotly and go.Scattermap, with optional region/department outlines and restaurants.
#
#     Args:
#         df (GeoDataFrame): The base geographic data (either regions or departments).
#         wine_df (GeoDataFrame): GeoDataFrame containing wine region shapes and colors.
#         all_france (pd.DataFrame): DataFrame containing restaurant data.
#         outline_type (str): Either 'region', 'department', or None. Used to show outlines.
#         show_restaurants (bool): Whether to plot restaurant locations. Default is False.
#         selected_stars (list): List of selected star ratings to plot. Default is (1, 2, 3).
#
#     Returns:
#         fig (go.Figure): The Plotly figure object.
#         wine_region_curve_numbers (list): List of curve numbers corresponding to the wine region traces.
#     """
#     fig = go.Figure()
#     wine_region_curve_numbers = []  # List to store curveNumbers for wine regions
#
#     # Ensure zoom_data is a dictionary
#     if zoom_data is None:
#         zoom_data = {}
#
#     # 1. Optionally show outlines for regions or departments based on `outline_type`
#     if outline_type in ['region', 'department']:
#         for _, row in df.iterrows():
#             geometry = row['geometry']
#             name = row[outline_type]
#
#             # Handle different geometry types
#             if geometry.geom_type == 'Polygon':
#                 geometries = [geometry]
#             elif geometry.geom_type == 'MultiPolygon':
#                 geometries = geometry.geoms
#             else:
#                 continue  # Skip unsupported geometries
#
#             # Plot each polygon in the geometry
#             for polygon in geometries:
#                 # Extract exterior coordinates
#                 lon, lat = polygon.exterior.coords.xy
#                 lon = list(lon)
#                 lat = list(lat)
#                 fig.add_trace(
#                     go.Scattermap(
#                         lon=lon,
#                         lat=lat,
#                         mode='lines',
#                         line=dict(width=0.3, color='black'),
#                         hoverinfo='text',
#                         text=f"{name}",
#                         showlegend=False,
#                     )
#                 )
#
#                 # Plot interiors (holes) if any
#                 for interior in polygon.interiors:
#                     lon_int, lat_int = interior.coords.xy
#                     lon_int = list(lon_int)
#                     lat_int = list(lat_int)
#                     fig.add_trace(
#                         go.Scattermap(
#                             lon=lon_int,
#                             lat=lat_int,
#                             mode='lines',
#                             line=dict(width=0.3, color='black'),
#                             hoverinfo='skip',
#                             showlegend=False,
#                         )
#                     )
#
#     # 2. Plot wine regions
#     for i, region_row in wine_df.iterrows():
#         geometry = region_row['geometry']
#         region_name = region_row['region']
#         region_color = region_row['colour']
#
#         # Handle different geometry types
#         if geometry.geom_type == 'Polygon':
#             polygons = [geometry]
#         elif geometry.geom_type == 'MultiPolygon':
#             polygons = geometry.geoms
#         else:
#             print(f"Skipping geometry of type: {geometry.geom_type}\nIn region: {region_name}")
#             continue  # Skip unsupported geometries
#
#         for polygon in polygons:
#             # Extract exterior coordinates
#             lon, lat = polygon.exterior.coords.xy
#             lon = list(lon)
#             lat = list(lat)
#
#             fig.add_trace(
#                 go.Scattermap(
#                     lon=lon,
#                     lat=lat,
#                     mode='lines',
#                     fill='toself',
#                     fillcolor=region_color,
#                     line=dict(width=0.5, color='darkgray'),
#                     hoverinfo='text',
#                     hovertemplate=f'{region_name}<br>',
#                     name='Wine Region',
#                     showlegend=False
#                 )
#             )
#             # Store the curveNumber for this trace (wine region)
#             wine_region_curve_numbers.append(len(fig.data) - 1)
#
#             # Plot interiors (holes) if any
#             for interior in polygon.interiors:
#                 lon_int, lat_int = interior.coords.xy
#                 lon_int = list(lon_int)
#                 lat_int = list(lat_int)
#                 fig.add_trace(
#                     go.Scattermap(
#                         lon=lon_int,
#                         lat=lat_int,
#                         mode='lines',
#                         fill='toself',
#                         fillcolor=region_color,
#                         line=dict(width=0.5, color='darkgray'),
#                         hoverinfo='text',
#                         hovertemplate=f'{region_name}<br>',
#                         name='Wine Region',
#                         showlegend=False,
#                     )
#                 )
#
#     # 3. Optionally plot restaurants based on selected star ratings
#     if show_restaurants and selected_stars:
#         star_colors = {1: "#FFB84D", 2: "#FE6F64", 3: "#C2282D"}
#         filtered_restaurants = all_france[all_france['stars'].isin(selected_stars)]
#
#         for star in selected_stars:
#             star_data = filtered_restaurants[filtered_restaurants['stars'] == star]
#
#             if not star_data.empty:
#                 fig.add_trace(
#                     go.Scattermap(
#                         lon=star_data['longitude'].tolist(),
#                         lat=star_data['latitude'].tolist(),
#                         mode='markers',
#                         marker=go.scattermap.Marker(size=8, color=star_colors.get(star)),
#                         hovertemplate=(
#                             '<b>Restaurant Name:</b> %{customdata[0]}<br>'
#                             '<b>Location:</b> %{customdata[1]}<br>'
#                         ),
#                         customdata=star_data[['name', 'location']].values,
#                         showlegend=False,
#                         name=f"{'★' * int(star)}",
#                     )
#                 )
#
#     # 4. Adjust the layout
#     # Extract zoom and center from zoom_data, using default values if keys are missing
#     zoom = zoom_data.get('zoom', 5)
#     center_lat = zoom_data.get('center', {}).get('lat', 46.603354)
#     center_lon = zoom_data.get('center', {}).get('lon', 1.888334)
#
#     fig.update_layout(
#         map_style="carto-voyager",
#         map_zoom=zoom,
#         map_center_lat=center_lat,
#         map_center_lon=center_lon,
#         margin={"r": 0, "t": 0, "l": 0, "b": 0},
#         hovermode='closest',
#     )
#
#     return fig, wine_region_curve_numbers


def generate_optimized_prompt(wine_region):
    """
    Generates an optimized prompt for providing a concise overview of a specified wine region, tailored to its relationship
    with Michelin-starred dining or local cuisine.

    The function bins wine regions into two categories:
    1. Regions known for their strong connection to Michelin-starred dining (e.g., Bordeaux, Bourgogne).
    2. Regions where wines are more commonly associated with local, traditional dining (e.g., Provence, Dordogne).

    Based on the category, the function creates a prompt that:
    - For Michelin regions: Emphasizes the region's connection to high-end dining and gourmet wine pairings.
    - For local cuisine regions: Focuses on how the wines complement the region's traditional cuisine, avoiding a forced Michelin connection.
    - For other regions: Provides an accurate description without assuming a specific connection to Michelin or local cuisine.

    Args:
        wine_region (str): The name of the wine region for which the prompt is being generated.

    Returns:
        str: A prompt for generating a description of the wine region, tailored to either Michelin-starred dining or local cuisine contexts.

    Example:
        prompt = generate_optimized_prompt("Bordeaux")
        print(prompt)
        # Will generate a prompt emphasizing Bordeaux's connection to Michelin-starred dining.
    """
    michelin_regions = ['Bordeaux', 'Bourgogne', 'Loire', 'Champagne', 'Rhône', 'Alsace']
    local_cuisine_regions = ['Provence', 'Dordogne', 'Languedoc-Roussillon']

    if wine_region in michelin_regions:
        prompt = f"""
        Provide a concise overview of the {wine_region} wine region, focusing on its main grape varieties and top appellations or Grand Crus. 
        Ensure the focus remains only on appellations within {wine_region}. 
        Emphasize how the wines from {wine_region} are integral to Michelin-starred dining, highlighting their pairing with gourmet dishes and their role in high-end culinary experiences.
        Keep the response organized in sub-paragraphs for clarity.
        """
    elif wine_region in local_cuisine_regions:
        prompt = f"""
        Provide a concise overview of the {wine_region} wine region, focusing on its main grape varieties and top appellations. 
        Ensure the focus remains only on appellations within {wine_region}. 
        Focus on how the wines from {wine_region} complement the local cuisine, avoiding any mention of Michelin-starred dining unless it is highly relevant.
        Keep the response organized in sub-paragraphs for clarity.
        """
    else:
        prompt = f"""
        Provide a concise overview of the {wine_region} wine region, focusing on its main grape varieties and top appellations or Grand Crus. 
        Ensure the focus remains only on appellations within {wine_region}. 
        Provide an accurate description of the wines and how they complement local cuisine or fine dining as applicable.
        Keep the response organized in sub-paragraphs for clarity.
        """
    return prompt
