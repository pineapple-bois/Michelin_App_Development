import math

import plotly.graph_objects as go
from dash import html
from pyproj import Transformer

from app.components.shared import green_star, michelin_stars
from app.utils.map_constraints import apply_france_split_bounds
from app.utils.restaurant_cards import get_restaurant_details

ANALYSIS_RATING_COLORS = {
    0.5: "#7a2466",
    1: "#d7a23c",
    2: "#df6f61",
    3: "#bd2a34",
}

ANALYSIS_BAR_LINE_COLOR = "rgba(70, 55, 50, 0.18)"

ANALYSIS_CHOROPLETH_COLORSCALE = [
    [0.0, "#fff8f5"],
    [0.18, "#f6d9cf"],
    [0.42, "#ec9f91"],
    [0.68, "#d95c54"],
    [1.0, "#a91f29"],
]
ANALYSIS_FRANCE_MAP_ZOOM = 4.0

WEB_MERCATOR_TO_WGS84 = Transformer.from_crs(
    'EPSG:3857',
    'EPSG:4326',
    always_xy=True,
)


def _map_zoom_from_projection_scale(projection_scale):
    """Translate the former geo projection scale to comparable MapLibre zoom."""
    return math.log2(projection_scale) + 2

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
            marker=dict(
                color=ANALYSIS_RATING_COLORS[0.5],
                line=dict(color=ANALYSIS_BAR_LINE_COLOR, width=0.4),
            ),
            orientation='h',
            hovertemplate='<b>Restaurants:</b> %{x}<extra></extra>',
        ))
    if 1 in select_stars:
        traces.append(go.Bar(
            y=filtered_df[granularity],
            x=filtered_df['1_star'],
            name="1 Star",
            marker=dict(
                color=ANALYSIS_RATING_COLORS[1],
                line=dict(color=ANALYSIS_BAR_LINE_COLOR, width=0.4),
            ),
            orientation='h',
            hovertemplate='<b>Restaurants:</b> %{x}<extra></extra>',
        ))
    if 2 in select_stars:
        traces.append(go.Bar(
            y=filtered_df[granularity],
            x=filtered_df['2_star'],
            name="2 Stars",
            marker=dict(
                color=ANALYSIS_RATING_COLORS[2],
                line=dict(color=ANALYSIS_BAR_LINE_COLOR, width=0.4),
            ),
            orientation='h',
            hovertemplate='<b>Restaurants:</b> %{x}<extra></extra>',
        ))
    if 3 in select_stars:
        traces.append(go.Bar(
            y=filtered_df[granularity],
            x=filtered_df['3_star'],
            name="3 Stars",
            marker=dict(
                color=ANALYSIS_RATING_COLORS[3],
                line=dict(color=ANALYSIS_BAR_LINE_COLOR, width=0.4),
            ),
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
        font=dict(color="#333333"),
        showlegend=False,
        xaxis=dict(
            title_standoff=15,
            gridcolor="rgba(0, 0, 0, 0.08)",
            zerolinecolor="rgba(0, 0, 0, 0.12)",
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            ticklabelposition="outside",
            automargin=True,
            autorange='reversed',
            tickfont=dict(size=11),
        )
    )

    return fig_bar

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

    colorscale = ANALYSIS_CHOROPLETH_COLORSCALE if cmap == 'Reds' else cmap

    # Add the choropleth map with hover info based on granularity
    fig.add_trace(
        go.Choroplethmap(
            subplot='map',
            geojson=df.__geo_interface__,  # GeoJSON representation of the dataframe
            z=df['total_restaurants'],  # Use total restaurants for coloring
            locations=df.index,  # Match the locations via index
            colorscale=colorscale,
            colorbar=dict(
                tickfont=dict(size=11, color="#555555"),
                thickness=10,
                len=0.72,
                outlinewidth=0,
            ),
            marker_line_width=0.35,
            marker_line_color='rgba(80, 80, 80, 0.45)',
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
                go.Scattermap(
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
        avg_lon, avg_lat = WEB_MERCATOR_TO_WGS84.transform(
            float(avg_x),
            float(avg_y),
        )

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
        avg_lon, avg_lat = WEB_MERCATOR_TO_WGS84.transform(
            float(avg_x),
            float(avg_y),
        )

    else:
        # Default centering on France
        avg_lat, avg_lon = 46.603354, 1.888334
        map_zoom = ANALYSIS_FRANCE_MAP_ZOOM

    # MapLibre is required here because layout.geo has no native maximum-bounds
    # contract. Preserve the former relative framing by translating its
    # projection scale to the corresponding tile-map zoom.
    fig.update_layout(
        map=dict(
            style='carto-positron',
            center=dict(lat=avg_lat, lon=avg_lon),
            zoom=(
                map_zoom
                if granularity == 'region'
                else _map_zoom_from_projection_scale(zoom_level)
            ),
        ),
        margin=dict(l=10, r=10, t=30, b=10),  # Reduce margins to reduce white space
    )

    return apply_france_split_bounds(fig)

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

    # Filter the data based on star type
    if star_rating == 'green':
        filtered_data = data[data['greenstar'] == 1]
        star_icon = html.Span(green_star(with_margin=False), style={"vertical-align": "middle"})
    else:
        filtered_data = data[data['stars'] == star_rating]
        star_icon = html.Span(michelin_stars(star_rating), style={"vertical-align": "middle"})

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
                star_icon,
                f" {restaurant_word}"
            ], style={"margin-left": "10px", "display": "inline-block"})
        ], style={"margin-bottom": "40px", "text-align": "center"})

        components.append(area_component)

        # Display restaurant details for this area if required
        if display_restaurants:
            restaurants_in_area = filtered_data[filtered_data[granularity] == area]
            restaurant_cards = [
                get_restaurant_details(row, extra_class_name='editorial-guide-entry')
                for _, row in restaurants_in_area.iterrows()
            ]

            components.append(html.Div(
                children=restaurant_cards,
                className='restaurant-cards-container editorial-card-grid',
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
                        star_icon,
                        f" {restaurant_word}"
                    ], style={"margin-left": "10px", "display": "inline-block"})
                ], style={"margin-bottom": "40px", "text-align": "center"})

                tied_components.append(tied_area_component)

                # Show detailed restaurant info for the tied areas if required
                if display_restaurants:
                    restaurants_in_area = filtered_data[filtered_data[granularity] == area]
                    restaurant_cards = [
                        get_restaurant_details(row, extra_class_name='editorial-guide-entry')
                        for _, row in restaurants_in_area.iterrows()
                    ]

                    tied_components.append(html.Div(
                        children=restaurant_cards,
                        className='restaurant-cards-container editorial-card-grid',
                        style={'display': 'flex', 'flex-wrap': 'wrap', 'gap': '20px', 'margin-bottom': '40px',
                               'justify-content': 'center'}
                    ))

        # Add a header for the tied areas
        components.append(html.Div("Tied Areas:", style={"font-weight": "bold", "font-size": "22px"}))
        components.extend(tied_components)  # Add the tied areas to the main components

    return components
