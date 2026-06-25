import plotly.graph_objects as go

from components.shared import color_map

# Hover-tip text
text_color_map = {
    0.1:  "#689c44",   # Green star green
    0.25: '#FFFFFF',   # Selected
    0.5: "#FFB84D",
    1: "#640A64",
    2: "#640A64",
    3: "#FFB84D"
}

def plot_geometry_outline(fig, geometry, line_width=0.5):
    """
    Draw the geographic boundary of a department, region, or arrondissement on a Plotly map.

    Parameters:
        fig (go.Figure): The Plotly figure to which the outline will be added.
        geometry (shapely.geometry.Polygon or MultiPolygon):
            A geometry object representing the area to be outlined.
            Typically obtained via `geometry = geo_df['geometry'].iloc[0]`
        line_width (float): Width of the outline line in pixels.

    Notes:
        This function handles both single Polygon and MultiPolygon geometries, and plots their exterior boundaries
        using black lines on the map.
    """
    if geometry.geom_type == 'Polygon':
        x, y = geometry.exterior.xy
        fig.add_trace(go.Scattermap(
            lat=list(y),
            lon=list(x),
            mode='lines',
            line=dict(width=line_width, color='black'),
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
                line=dict(width=line_width, color='black'),
                hoverinfo='none',
                showlegend=False
            ))

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
        specific_geometry = row['geometry']
        plot_geometry_outline(fig, specific_geometry, line_width=1)

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

    Parameters:
        geo_df (GeoDataFrame): A GeoDataFrame containing geometries of departments with a 'code' column.
        department_code (str or int): The code of the department to plot.
        zoom_data (dict, optional): Contains zoom and centre information.

    Returns:
        fig (plotly.graph_objs.Figure): A Plotly Figure object with the department outline plotted.
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
    plot_geometry_outline(fig, specific_geometry, line_width=0.5)

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

def plot_arrondissement_outlines(paris_df, arrondissement, zoom_data=None):
    """
    Plot the outlines of a selected Paris arrondissement on a map.

    Parameters:
        paris_df (GeoDataFrame): A GeoDataFrame containing geometries of Paris arrondissements with 'arrondissement' and 'geometry'.
        arrondissement (str): The name of the arrondissement to plot.
        zoom_data (dict, optional): Contains zoom and centre information.

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
    plot_geometry_outline(fig, specific_geometry, line_width=1)

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

def generate_hover_text(row):
    """
    Generate HTML-formatted hover text for a restaurant.

    Parameters:
        row (pd.Series or dict): A pandas Series or dictionary containing restaurant information.

    Returns:
        hover_text (str): An HTML-formatted string for hover text.
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

def label_properties(star):
    """
    Return:
        display label
        marker size
        opacity
        colour
    for a given star rating.
    """
    if star == 0.25:
        return "Selected", 9, 0.9, color_map[0.25]
    elif star == 0.5:
        return "Bib", 11, 1, color_map[0.5]
    else:
        return "★" * int(star), 11, 1, color_map[star]

def add_star_trace(fig, subset, label_name,
                   marker_size, marker_opacity, marker_color):
    """
    Add a scatter marker layer to a Plotly map for a specific group of restaurants.

    Each trace corresponds to a single star rating (e.g. 1★, Bib Gourmand, Selected)
    and is styled with a consistent marker size, opacity, and colour. Hover text and
    clickData are included for interactivity.

    Parameters:
        fig (go.Figure): The Plotly figure to which the trace will be added.
        subset (pd.DataFrame): Subset of restaurants sharing a specific star rating.
        label_name (str): Label used in the legend and for identifying the trace.
        marker_size (int): Marker size for the restaurant points.
        marker_opacity (float): Opacity level for the markers.
        marker_color (str): Colour to apply to the markers (hex or CSS format).
    """
    if subset.empty:
        return

    fig.add_trace(go.Scattermap(
        lat=subset['latitude'],
        lon=subset['longitude'],
        mode='markers',
        marker=dict(
            size=marker_size,
            color=marker_color,
            opacity=marker_opacity
        ),
        text=subset['hover_text'],
        customdata=subset.index,
        hovertemplate='%{text}',
        name=label_name,
        showlegend=False,
        meta=subset.index   # <- NEW: include explicitly for clickData
    ))

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
    plot_geometry_outline(fig, specific_geometry, line_width=0.5)

    # Before filtering, inspect all restaurants in the department
    all_in_dept = data_df[data_df['department_num'] == str(department_code)]

    # Now do star filtering
    dept_data = all_in_dept[all_in_dept['stars'].isin(selected_stars)].copy()

    # If dept_data is not empty, add restaurant points
    if not dept_data.empty:
        dept_data['color'] = dept_data['stars'].map(color_map).fillna('#808080')  # Default to grey for 0.25
        dept_data['hover_text'] = dept_data.apply(generate_hover_text, axis=1)

        # Plot background outlines for green star restaurants
        green_outline_data = dept_data[dept_data['greenstar'] == 1]
        if not green_outline_data.empty:
            fig.add_trace(go.Scattermap(
                lat=green_outline_data['latitude'],
                lon=green_outline_data['longitude'],
                mode='markers',
                marker=dict(
                    size=11 if (green_outline_data['stars'] == 0.25).any() else 15,
                    color='#689c44',
                    opacity=0.8
                ),
                hoverinfo='skip',
                showlegend=False
            ))

        # Plot each group of star-rated restaurants (including 0.25 if present)
        for star in sorted(dept_data['stars'].unique(), reverse=False):
            subset = dept_data[dept_data['stars'] == star]
            if subset.empty:
                continue

            base_label, marker_size, marker_opacity, marker_color = label_properties(star)

            # Split and add traces
            add_star_trace(
                fig,
                subset[subset['greenstar'] != 1],
                base_label,
                marker_size,
                marker_opacity,
                marker_color
            )

            add_star_trace(
                fig,
                subset[subset['greenstar'] == 1],
                base_label + (" 🌿" if star in [0.25, 0.5] else "🌿"),
                marker_size,
                marker_opacity,
                marker_color
            )

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
    plot_geometry_outline(fig, specific_geometry, line_width=1)

    # Before filtering, inspect all restaurants in the department
    all_in_arron = data_df[data_df['arrondissement'] == arrondissement]
    # Now do star filtering
    arr_data = all_in_arron[all_in_arron['stars'].isin(selected_stars)].copy()

    # Proceed to plot starred restaurants
    # If dept_data is not empty, add restaurant points
    if not arr_data.empty:
        arr_data['color'] = arr_data['stars'].map(color_map).fillna('#808080')  # Default to grey for 0.25
        arr_data['hover_text'] = arr_data.apply(generate_hover_text, axis=1)

        # Plot background outlines for green star restaurants
        green_outline_data = arr_data[arr_data['greenstar'] == 1]
        if not green_outline_data.empty:
            fig.add_trace(go.Scattermap(
                lat=green_outline_data['latitude'],
                lon=green_outline_data['longitude'],
                mode='markers',
                marker=dict(
                    size=11 if (green_outline_data['stars'] == 0.25).any() else 15,
                    color='#689c44',
                    opacity=0.8
                ),
                hoverinfo='skip',
                showlegend=False
            ))

        # Plot each group of star-rated restaurants (including 0.25 if present)
        for star in sorted(arr_data['stars'].unique(), reverse=False):
            subset = arr_data[arr_data['stars'] == star]
            if subset.empty:
                continue

            base_label, marker_size, marker_opacity, marker_color = label_properties(star)

            # Split and add traces
            add_star_trace(
                fig,
                subset[subset['greenstar'] != 1],
                base_label,
                marker_size,
                marker_opacity,
                marker_color
            )

            add_star_trace(
                fig,
                subset[subset['greenstar'] == 1],
                base_label + (" 🌿" if star in [0.25, 0.5] else "🌿"),
                marker_size,
                marker_opacity,
                marker_color
            )

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
