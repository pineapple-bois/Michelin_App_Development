import plotly.graph_objects as go


ECONOMICS_METRIC_COLORSCALE = [
    [0.0, "#EDF2F5"],
    [0.35, "#C7D6DE"],
    [0.68, "#8EACBB"],
    [1.0, "#23485A"],
]
ECONOMICS_BAR_COLOR = "#4F7486"
ECONOMICS_REFERENCE_RED = "#C2282D"
ECONOMICS_REFERENCE_RED_DARK = "#A01F25"


def plot_demographic_choropleth_plotly(df, all_france, metric=None, granularity='region', show_labels=True, cmap='Blues',
                                    restaurants=False, selected_stars=[1, 2, 3], zoom_data=None):
    """
    Plot a choropleth map for demographic metrics using Plotly's map object. Optionally, plot restaurant locations from 'all_france'.

    Args:
        df (GeoDataFrame): The DataFrame containing the geographic data.
        all_france (pd.DataFrame): DataFrame containing restaurant data with latitude and longitude.
        metric (str): The demographic metric to visualize. Default is None.
        granularity (str): The level of granularity - 'department' or 'region'. Default is 'region'.
        show_labels (bool): Whether to show labels. Default is True.
        cmap (str): The colormap to use. Default is 'Blues'.
        restaurants (bool): Whether to plot restaurant locations. Default is False.
        selected_stars (list): List of selected star ratings (e.g., [1, 2, 3]).
        zoom_data (dict): Dictionary containing 'zoom' and 'center' information.

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

    metric_colorscale = ECONOMICS_METRIC_COLORSCALE if cmap == 'Blues' else cmap

    # Initialize Plotly figure for a map
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
            go.Choroplethmap(
                geojson=df.__geo_interface__,
                z=df[metric],
                locations=df.index,
                colorscale=metric_colorscale,
                colorbar=dict(
                    title="",
                    tickfont=dict(color="#40545F", size=11),
                    outlinewidth=0,
                ),
                marker_line_width=0.5,
                marker_line_color='darkgray',
                hovertemplate=hovertemplate,
                customdata=customdata
            )
        )
    else:
        # If no metric is provided, show only the boundaries
        fig.add_trace(
            go.Choroplethmap(
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

    # **Handle empty restaurant case**
    if restaurants and selected_stars:
        filtered_restaurants = all_france[all_france['stars'].isin(selected_stars)]

        # Filter by the regions present in the dataframe (df)
        if granularity == 'department':
            filtered_restaurants = filtered_restaurants[filtered_restaurants['region'].isin(df['region'].unique())]

        # **If no restaurants match, skip plotting**
        if filtered_restaurants.empty:
            restaurants = False  # Set to False to skip plotting

        for star in selected_stars:
            star_data = filtered_restaurants[filtered_restaurants['stars'] == star]

            # Plot each restaurant as a scatter point on the map
            if not star_data.empty:
                fig.add_trace(
                    go.Scattermap(
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
                go.Scattermap(
                    lon=[x],
                    lat=[y],
                    text=label,
                    mode='text',
                    textposition='top center',
                    showlegend=False
                )
            )

    # **Calculate zoom and center based on region geometry if zoom_data is not provided**
    if not zoom_data and granularity == 'department':
        # Use the first geometry in the DataFrame
        try:
            specific_geometry = df['geometry'].iloc[0]
            centroid = specific_geometry.centroid
            zoom = 5.5  # Adjust as needed for the zoom level
            center = {'lat': centroid.y, 'lon': centroid.x}
        except Exception as e:
            print(f"Error calculating centroid: {str(e)}")
            zoom = 4.5  # Fallback zoom level
            center = {'lat': 46.603354, 'lon': 1.888334}  # Default center on France
    else:
        zoom = zoom_data.get('zoom', 4.5)
        center = zoom_data.get('center', {'lat': 46.603354, 'lon': 1.888334})

    fig.update_layout(
        map=dict(
            style="../assets/basicTileMap.json",
            #style="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
            center=center,
            zoom=zoom
        ),
        margin=dict(l=10, r=10, t=30, b=10),
        height=700
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
        marker=dict(color=ECONOMICS_BAR_COLOR),
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
                line=dict(color=ECONOMICS_REFERENCE_RED, width=1.5),
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
                font=dict(color=ECONOMICS_REFERENCE_RED_DARK, size=11),
                arrowcolor=ECONOMICS_REFERENCE_RED
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
                font=dict(color=ECONOMICS_REFERENCE_RED_DARK, size=11)
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
