from dash import html
import dash_bootstrap_components as dbc

from components.shared import (
    color_map,
    get_footer,
    get_header_with_buttons,
    inverted_bib_gourmand,
    inverted_michelin_stars,
)


star_placeholder = [0.5, 1, 2, 3]

unique_regions = [
    'Auvergne-Rhône-Alpes',
    'Bourgogne-Franche-Comté',
    'Bretagne',
    'Centre-Val de Loire',
    'Corse',
    'Grand Est',
    'Hauts-de-France',
    'Normandie',
    'Nouvelle-Aquitaine',
    'Occitanie',
    'Pays de la Loire',
    "Provence-Alpes-Côte d'Azur",
    'Île-de-France'
]


def create_star_button(value, label, filter_type):
    # Generate color with reduced opacity for active state
    normal_bg_color = color_map[value]
    return dbc.Button(
        label,
        id={
            'type': f'filter-button-{filter_type}',  # Dynamic ID based on filter type
            'index': value,
        },
        className=f"me-1 star-button-{filter_type} active",  # Dynamic class name
        outline=True,
        style={
            'display': 'inline-block',
            'backgroundColor': normal_bg_color,
            'width': '100%',
            'opacity': 1
        },
        n_clicks=0,
    )


def star_filter_row(available_stars, filter_type, exclude_stars=None):
    """
    Create a button for each available star rating, optionally excluding specific stars.

    Args:
        available_stars (list): List of available stars to create buttons for.
        filter_type (str): Type of filter (used for dynamic class names).
        exclude_stars (list): Optional list of stars to exclude from the filter.

    Returns:
        html.Div: Div containing buttons for the stars.
    """
    # Exclude specified stars if exclude_stars is provided
    if exclude_stars:
        available_stars = [star for star in available_stars if star not in exclude_stars]
    # Create a button for each available star rating
    buttons = [create_star_button(star, inverted_michelin_stars(star) if star != 0.5 else inverted_bib_gourmand(), filter_type) for star in available_stars]
    return html.Div(buttons, className=f'star-filter-buttons-{filter_type}')  # Dynamic class


def star_filter_section(available_stars=star_placeholder, filter_type="analysis", exclude_stars=None):
    """
    Create a star filter section, optionally excluding specific star ratings.

    Args:
        available_stars (list): List of available stars to create buttons for.
        filter_type (str): Type of filter (used for dynamic class names).
        exclude_stars (list): Optional list of stars to exclude from the filter.

    Returns:
        html.Div: Div containing the star filter section.
    """
    star_buttons = star_filter_row(available_stars, filter_type, exclude_stars=exclude_stars)
    return html.Div([
        html.H6(f"Filter by Michelin Rating", className=f'star-select-title-{filter_type}'),  # Dynamic title
        star_buttons
    ], className=f'star-filter-section-{filter_type}', id=f'star-filter-{filter_type}')  # Dynamic ID and class


def get_analysis_page_layout(content):
    # Header with buttons
    header = html.Div(
        children=[
            get_header_with_buttons()
        ],
        className='header'
    )

    body = html.Div(
        children=[
            content,
        ],
        className='content-container'
    )

    footer = get_footer()

    # Combine all sections into the main layout
    return html.Div([
        header,
        body,
        footer
    ], className='main-layout')
