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
    for area, restaurant_count in top_areas.items():
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
    Create a horizontal bar chart with a vertical line indicating the weighted mean.

    Args:
        df (pd.DataFrame): The dataframe containing the data.
        metric (str): The metric to plot on the bar chart.
        granularity (str): Either 'region' or 'department' to determine the grouping.
        weighted_mean (float): The calculated weighted mean to display as a dashed line.

    Returns:
        fig (go.Figure): The Plotly figure object with the bar chart and the weighted mean line.
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

    # Only add the weighted mean if it's not excluded
    if metric not in ['municipal_population', 'population_density(inhabitants/sq_km)']:
        # Add the weighted mean as a red dashed vertical line
        fig.add_shape(
            type="line",
            x0=weighted_mean,
            x1=weighted_mean,
            y0=-0.5,
            y1=len(df[granularity]) - 0.5,
            line=dict(color="red", width=2, dash="dash"),
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
            ax=40,  # Horizontal offset for the annotation
            ay=-40,  # Vertical offset for the annotation
            font=dict(color="red", size=12),
            arrowcolor="red"
        )

    # Customize layout
    fig.update_layout(
        title=f"{metric_title} by {granularity.capitalize()}",
        xaxis_title=metric_title,
        showlegend=False,
        plot_bgcolor='white',
        height=550,
    )

    return fig


def plot_wine_choropleth_plotly(df, wine_df, all_france, outline_type=None, show_restaurants=False, selected_stars=(1, 2, 3)):
    """
    Plot a choropleth map for wine regions, with optional overlays for region/department outlines and restaurants.

    Args:
        df (GeoDataFrame): The base geographic data (either regions or departments).
        wine_df (GeoDataFrame): GeoDataFrame containing wine region shapes and colors.
        all_france (pd.DataFrame): DataFrame containing restaurant data.
        outline_type (str): Either 'region', 'department', or None (default). Used to show outlines.
        show_restaurants (bool): Whether to plot restaurant locations. Default is False.
        selected_stars (list): List of selected star ratings to plot. Default is (1, 2, 3).

    Returns:
        fig (go.Figure): The Plotly figure object.
    """

    # Initialize Plotly figure
    fig = go.Figure()

    # 1. Optionally show outlines for regions or departments based on `outline_type`
    if outline_type in ['region', 'department']:
        fig.add_trace(
            go.Choropleth(
                geojson=df.__geo_interface__,
                z=[0] * len(df),  # Placeholder Z values
                locations=df.index,
                showscale=False,
                marker_line_width=0.3,
                marker_line_color='darkgray',
                colorscale=[[0, 'rgba(0, 0, 0, 0)'], [1, 'rgba(0, 0, 0, 0)']],  # Transparent fill
                hoverinfo='skip',  # No hover needed for outlines
                name=f"{outline_type.capitalize()} Outlines"
            )
        )

    # 2. Plot wine regions
    for i, region_row in wine_df.iterrows():
        # Extracting the exterior coordinates from each Polygon geometry
        geometry = region_row['geometry']

        # Check if geometry is a MultiPolygon or Polygon
        if geometry.geom_type == 'Polygon':
            polygons = [geometry]
        elif geometry.geom_type == 'MultiPolygon':
            polygons = geometry.geoms
        else:
            continue

        for polygon in polygons:
            # Convert the polygon coordinates to Python lists
            lon, lat = polygon.exterior.coords.xy
            lon = list(lon)
            lat = list(lat)

            fig.add_trace(
                go.Scattergeo(
                    lon=lon,  # Longitude of the polygon points
                    lat=lat,  # Latitude of the polygon points
                    mode='lines',
                    fill='toself',
                    fillcolor=region_row['colour'],  # Use the 'colours' column for the fill color
                    line=dict(width=0.5, color='darkgray'),
                    hoverinfo='text',
                    hovertemplate=f'{region_row["region"]}<br>',
                    name='Wine Region',
                    showlegend=False  # No legend for individual wine regions
                )
            )

    # 3. Optionally plot restaurants based on selected star ratings
    if show_restaurants and selected_stars:
        star_colors = {1: "#FFB84D", 2: "#FE6F64", 3: "#C2282D"}
        filtered_restaurants = all_france[all_france['stars'].isin(selected_stars)]

        for star in selected_stars:
            star_data = filtered_restaurants[filtered_restaurants['stars'] == star]

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
                    showlegend=False,  # No legend for restaurants
                    name=f"{'★' * int(star)}"
                )
            )

    # Update layout
    fig.update_layout(
        clickmode='event+select',  # Enable click events for the map
        geo=dict(
            scope='europe',
            resolution=50,
            showcoastlines=False,
            showland=True,
            landcolor="lightgray",
            center=dict(lat=46.603354, lon=1.888334),
            projection_scale=6,  # Zoom level for France
        ),
        height=700,
        margin=dict(l=10, r=10, t=30, b=10),
    )

    return fig
