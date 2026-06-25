import plotly.graph_objects as go

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
