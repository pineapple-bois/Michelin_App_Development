from dash import html

from components.shared import bib_gourmand, color_map, green_star, michelin_stars

def get_restaurant_details(row):
    """
    Generate an HTML Div containing detailed information about a restaurant.

    Parameters:
        row (pd.Series or dict): A pandas Series or dictionary containing restaurant information.

    Returns:
        details_layout (dash_html_components.Div): A Dash HTML Div containing the restaurant's details.
    """
    try:
        name = row['name']
        stars = row['stars']
        greenstar = row['greenstar']
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
    components = []

    if stars == 0.5:
        components.append(bib_gourmand())
    elif stars in [1, 2, 3]:
        components.extend(michelin_stars(stars))
    # Append green star if applicable
    if greenstar == 1:
        components.append(green_star(with_margin=bool(components)))

    star_component = html.Span(components, className='restaurant-stars')

    # Create HTML content to display this information, organized in divs
    details_layout = html.Div([
        html.Div([
            html.Div([
                html.Span(name, className='restaurant-name'),
                star_component
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
            html.A("Visit Website", href=website_url, target='_blank',
                   className='restaurant-website', style={'display': 'block', 'marginTop': '10px'})
        ], className='details-website')
    ], className='restaurant-details', style={'borderColor': border_color})

    return details_layout
