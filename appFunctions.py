import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from dash import html, dcc
from layouts.layout_main import michelin_star, bib_gourmand


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


def plot_interactive_department(data_df, geo_df, department_code, selected_stars):
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

    # Tooltip section
    color_map = {
        0.5: "#640A64",
        1: "#FFB84D",
        2: "#FE6F64",
        3: "#C2282D"  # (r, g, b, opacity)
    }

    text_color_map = {
        0.5: "#FFB84D",
        1: "#640A64",
        2: "#640A64",
        3: "#FFB84D"
    }

    dept_data = data_df[(data_df['department_num'] == str(department_code)) & (data_df['stars'].isin(selected_stars))].copy()
    dept_data['color'] = dept_data['stars'].map(color_map)

    # Modify the hover text function
    dept_data['hover_text'] = dept_data.apply(
        lambda row: f"<span style=\"font-family: 'Libre Franklin', sans-serif; font-size: 13px; color: {text_color_map[row['stars']]};\">"
                    f"<span style='font-size: 16px;'>{row['name']}</span><br>"
                    f"<span style='font-size: 13px;'>{row['cuisine']}</span><br>"
                    f"<span style='font-size: 13px;'>{row['price']}</span><br>"
                    f"<br>"
                    f"{row['address']}, {row['location']}<br>"
                    f"<br>"
                    f"<a href='{row['url']}' target='_blank' style='font-family: Libre Franklin, sans-serif; font-size: 15px; color: {text_color_map[row['stars']]};'>Visit website</a><br>",
        axis=1
    )

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
            marker=go.scattermapbox.Marker(size=9, color=color),
            text=subset['hover_text'],
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
        mapbox_style="carto-positron",
        mapbox_zoom=8,
        mapbox_center_lat=dept_data['latitude'].mean(),
        mapbox_center_lon=dept_data['longitude'].mean(),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},  # Remove margins
    )

    return fig