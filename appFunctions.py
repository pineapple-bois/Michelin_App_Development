import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from dash import html, dcc
from pandas.io.formats.printing import justify

from layouts.layout_main import michelin_stars, bib_gourmand, color_map


# Hover-tip text
text_color_map = {
    0.5: "#FFB84D",
    1: "#640A64",
    2: "#640A64",
    3: "#FFB84D"
}


def plot_regional_outlines(region_df, region):
    fig = go.Figure(go.Scattermapbox())  # Initialize empty figure with mapbox

    # Filter the GeoDataFrame for the selected region
    filtered_region = region_df[region_df['region'] == region]

    # Loop through the filtered GeoDataFrame
    for _, row in filtered_region.iterrows():
        geometry = row['geometry']
        if geometry.geom_type == 'Polygon':
            x, y = geometry.exterior.xy
            fig.add_trace(go.Scattermapbox(
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
                fig.add_trace(go.Scattermapbox(
                    lat=list(y),
                    lon=list(x),
                    mode='lines',
                    line=dict(width=1, color='black'),
                    hoverinfo='none',
                    showlegend=False
                ))

    # Update map layout settings
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=5,  # Zoom level to show all of France
        mapbox_center_lat=46.603354,  # Approximate latitude for France center
        mapbox_center_lon=1.888334,  # Approximate longitude for France center
        margin={"r": 0, "t": 0, "l": 0, "b": 0},  # Remove margins
        showlegend=False
    )
    return fig


def plot_department_outlines(geo_df, department_code):
    fig = go.Figure(go.Scattermapbox())  # Initialize empty figure with mapbox

    # Filter the GeoDataFrame for the selected department
    specific_geometry = geo_df[geo_df['code'] == str(department_code)]['geometry'].iloc[0]

    # Plot the geometry's boundaries
    if specific_geometry.geom_type == 'Polygon':
        x, y = specific_geometry.exterior.xy
        fig.add_trace(go.Scattermapbox(
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
                fig.add_trace(go.Scattermapbox(
                    lat=list(y),
                    lon=list(x),
                    mode='lines',
                    line=dict(width=0.5, color='black'),
                    hoverinfo='none',
                    showlegend=False
                ))


    # Update map layout settings
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=5,  # Zoom level to show all of France
        mapbox_center_lat=46.603354,  # Approximate latitude for France center
        mapbox_center_lon=1.888334,  # Approximate longitude for France center
        margin={"r": 0, "t": 0, "l": 0, "b": 0},  # Remove margins
        showlegend=False
    )
    return fig


def get_restaurant_details(row):
    name = row['name']
    stars = row['stars']
    cuisine = row['cuisine']
    price = row['price']
    address = row['address']
    location = row['location']
    arrondissement = row['arrondissement']
    website_url = row['url']

    # Color for the border based on the number of stars
    border_color = color_map.get(stars, '#ccc')  # Default to grey if no stars count matches

    # Create the address information with a conditional for Paris arrondissements
    if row['department_num'] == '75':
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
    hover_text = (
        f"<span style=\"font-family: 'Libre Franklin', sans-serif; font-size: 12px; color: {text_color_map[row['stars']]};\">"
        f"<span style='font-size: 14px;'>{row['name']}</span><br>"
        f"{row['location']}<br>"
    )
    return hover_text


def plot_interactive_department(data_df, geo_df, department_code, selected_stars):
    # Before plotting, determine the correct zoom level
    zoom = 11 if department_code == '75' else 8  # Extra zoom for Paris

    # Initialize a blank figure
    fig = go.Figure()
    fig.update_layout(autosize=True)

    # Get the specific geometry
    specific_geometry = geo_df[geo_df['code'] == str(department_code)]['geometry'].iloc[0]

    # Plot the geometry's boundaries
    if specific_geometry.geom_type == 'Polygon':
        x, y = specific_geometry.exterior.xy
        fig.add_trace(go.Scattermapbox(
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
                fig.add_trace(go.Scattermapbox(
                    lat=list(y),
                    lon=list(x),
                    mode='lines',
                    line=dict(width=0.5, color='black'),
                    hoverinfo='none',
                    showlegend=False
                ))

    dept_data = data_df[(data_df['department_num'] == str(department_code)) & (data_df['stars'].isin(selected_stars))].copy()
    dept_data['color'] = dept_data['stars'].map(color_map)
    dept_data['hover_text'] = dept_data.apply(generate_hover_text, axis=1)

    # Overlay restaurant points without adding them to the legend
    for star, color in color_map.items():
        subset = dept_data[dept_data['stars'] == star]

        # Adjust hover text for Bib Gourmand
        if star == 0.5:
            label_name = '🍽️'
        else:
            label_name = f"{'★' * int(star)}"

        fig.add_trace(go.Scattermapbox(
            lat=subset['latitude'],
            lon=subset['longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(size=11, color=color),
            text=subset['hover_text'],
            customdata=subset.index,
            hovertemplate='%{text}',
            name=label_name,
            showlegend=False  # This ensures that the trace isn't added to the legend
        ))

    # Adjusting layouts
    fig.update_layout(
        font=dict(
            family="Courier New, monospace",
            size=18,
            color="white"
        ),
        width=800,
        height=600,
        hovermode='closest',  # This changes the cursor on hover
        hoverdistance=20,
        mapbox_style="carto-positron",
        mapbox_zoom=zoom,
        mapbox_center_lat=dept_data['latitude'].mean(),
        mapbox_center_lon=dept_data['longitude'].mean(),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},  # Remove margins
    )

    return fig


def plot_single_choropleth_plotly(df, selected_stars, granularity='region', show_labels=True, cmap='Reds'):
    """
    Plot a single choropleth map using Plotly.

    Args:
        df (GeoDataFrame): The DataFrame containing the data.
        selected_stars (list): List of selected star levels (e.g., [0.5, 1, 2, 3]).
        granularity (str): Level of granularity - 'arrondissement', 'department', or 'region'. Default is 'region'.
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
            '<b>Total Restaurants:</b> %{z}<extra></extra>'
        )
        customdata = df[['arrondissement']].values
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

    # Update the layout for the figure, centering on France and adjusting size
    fig.update_layout(
        geo=dict(
            scope='europe',  # Set the scope to Europe
            resolution=50,
            showcoastlines=False,
            showland=True,
            landcolor="lightgray",
            center=dict(lat=46.603354, lon=1.888334),  # Center on France (approximate lat, lon)
            projection_scale=6,  # Increase the scale for zoom (larger map)
        ),
        margin=dict(l=10, r=10, t=30, b=10),  # Reduce margins to reduce white space
    )

    return fig


def top_restaurants(data, granularity, star_rating, top_n, display_restaurants=True):
    """
    Returns a list of Dash components for top_n regions or departments with the highest count of 'star_rating' restaurants.
    If display_restaurants is True, detailed restaurant info will be returned; otherwise, just the ranking.

    Args:
        data (pandas.DataFrame): The dataset containing restaurant info.
        granularity (str): Either 'region' or 'department'.
        star_rating (int): The Michelin star rating (2 or 3).
        top_n (int): The number of top (granularity) to consider.
        display_restaurants (bool): Whether to display individual restaurants. Default is True.
    Returns:
        list: Dash components containing the ranking or restaurant details.
    """
    # Ensure access to department name, code, and region
    if 'department' not in data.columns or 'department_num' not in data.columns or 'region' not in data.columns:
        raise ValueError("Data must contain 'department', 'department_num', and 'region' columns.")

    # Filter out non-starred restaurants
    filtered_data = data[data['stars'] == star_rating]

    # Handling Paris (department 75) or the Île-de-France region
    if top_n == 'paris':
        if granularity == 'department':
            # Focus on Paris as department (75)
            filtered_data = filtered_data[filtered_data['department_num'] == '75']
        elif granularity == 'region':
            # Focus on Île-de-France region for Paris case
            filtered_data = filtered_data[filtered_data['region'] == 'Île-de-France']

    # Group by granularity and count the number of restaurants for each
    top_areas = filtered_data[granularity].value_counts().nlargest(top_n)

    components = []  # Initialize a list for storing Dash components

    # Loop over the top areas to create the ranking or restaurant details
    for area, restaurant_count in top_areas.iteritems():
        restaurant_word = "Restaurant" if restaurant_count == 1 else "Restaurants"

        # Get department code and region (for departments only)
        if granularity == 'department':
            department_info = filtered_data[filtered_data['department'] == area].iloc[0]
            department_code = department_info['department_num']
            region_name = department_info['region']
            display_area = f"{area} ({department_code}): {region_name}"
        else:
            display_area = area

        # Add area on one line, count and stars on the next line
        area_component = html.Div([
            # Line 1: Area name
            html.Div(display_area, style={
                "font-weight": "bold",
                "font-size": "20px"
            }),

            # Line 2: Restaurant count and Michelin stars
            html.Div([
                f"{restaurant_count}  ",  # Display the count
                html.Span(michelin_stars(star_rating), style={"vertical-align": "middle"}),  # Michelin star images
                f" {restaurant_word}"  # Text to follow the stars
            ], style={"margin-left": "10px", "display": "inline-block"})  # Margin-left for indentation
        ], style={
            "margin-bottom": "40px",
            "text-align": "center"
        })  # Add spacing between entries

        components.append(area_component)  # Add the area component to the list

        # If display_restaurants is True, show detailed restaurant info
        if display_restaurants:
            # Get restaurants in this area
            restaurants_in_area = filtered_data[filtered_data[granularity] == area]

            # Create restaurant cards for each restaurant in the area
            restaurant_cards = [get_restaurant_details(row) for _, row in restaurants_in_area.iterrows()]

            # Wrap the restaurant cards in a flexbox container for side-by-side display
            components.append(html.Div(
                children=restaurant_cards,
                className='restaurant-cards-container',
                style={
                    'display': 'flex',
                    'flex-wrap': 'wrap',
                    'gap': '20px',
                    'margin-bottom': '40px',
                    'justify-content': 'center'
                }
            ))

    return components
