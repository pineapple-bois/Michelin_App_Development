import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib-cache"))

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from fuzzywuzzy import process
import pyproj
import seaborn as sns
import pandas as pd
import geopandas as gpd
import ast

try:
    from IPython.core.display import display, HTML
except ImportError:
    def display(value):
        print(value)

    class HTML(str):
        pass


def dataframe_info(data):
    # Check if DataFrame or GeoDataFrame
    if isinstance(data, gpd.GeoDataFrame):
        print("GeoDataFrame.")
    else:
        pass
    # For each column of interest, check if it exists before printing its stats
    columns_of_interest = ["region", "department", "arrondissement", "location"]
    for col in columns_of_interest:
        if col in data.columns:
            print(f"Unique {col.capitalize()}s: {data[col].nunique()}")
        else:
            pass
    print(f"\nShape: {data.shape}")
    display(data.head(3))


def _get_best_match(search_str, df, column):
    """
    Returns the best matching string from unique values of a specified column in a dataframe.

    Args:
    - search_str (str): The string to search for.
    - df (pandas.DataFrame): DataFrame containing the data.
    - column (str): The column name in which to search for the string.

    Returns:
    - str or None: The best matching string if a good match is found, otherwise None.

    Example:
    --------
    best_region = get_best_match("Provence", all_france, "region")
    """
    unique_choices = df[column].unique()
    best_match, score = process.extractOne(search_str, unique_choices)

    if score > 80:  # adjust this threshold
        return best_match
    else:
        return None


def filter_dataframe(data, regions=None, departments=None, arrondissements=None,
                     exclude_regions=None, exclude_departments=None, exclude_arrondissements=None):
    """
    Filters the dataframe based on given conditions.

    Args:
    - data (pandas.DataFrame): The main dataframe.
    - regions (list[str]/str, optional): Region(s) to focus on.
    - departments (list[str]/str, optional): Department(s) to focus on.
    - arrondissements (list[str]/str, optional): Arrondissement(s) to focus on.
    - exclude_regions (list[str]/str, optional): Region(s) to exclude.
    - exclude_departments (list[str]/str, optional): Department(s) to exclude.
    - exclude_arrondissements (list[str]/str, optional): Arrondissement(s) to exclude.

    Returns:
    - pandas.DataFrame: Filtered dataframe.
    """

    # Convert single strings to lists for uniform handling
    regions = [regions] if isinstance(regions, str) else regions
    departments = [departments] if isinstance(departments, str) else departments
    arrondissements = [arrondissements] if isinstance(arrondissements, str) else arrondissements
    exclude_regions = [exclude_regions] if isinstance(exclude_regions, str) else exclude_regions
    exclude_departments = [exclude_departments] if isinstance(exclude_departments, str) else exclude_departments
    exclude_arrondissements = [exclude_arrondissements] if isinstance(exclude_arrondissements, str) else exclude_arrondissements

    if regions:
        matched_regions = [_get_best_match(region, data, 'region') for region in regions]
        data = data[data['region'].isin(matched_regions)]

    if departments:
        matched_departments = [_get_best_match(department, data, 'department') for department in departments]
        data = data[data['department'].isin(matched_departments)]

    if arrondissements:
        matched_arrondissements = [_get_best_match(arrondissement, data, 'arrondissement') for arrondissement in arrondissements]
        data = data[data['arrondissement'].isin(matched_arrondissements)]

    if exclude_regions:
        matched_exclude_regions = [_get_best_match(region, data, 'region') for region in exclude_regions]
        data = data[~data['region'].isin(matched_exclude_regions)]

    if exclude_departments:
        matched_exclude_departments = [_get_best_match(department, data, 'department') for department in exclude_departments]
        data = data[~data['department'].isin(matched_exclude_departments)]

    if exclude_arrondissements:
        matched_exclude_arrondissements = [_get_best_match(arrondissement, data, 'arrondissement') for arrondissement in exclude_arrondissements]
        data = data[~data['arrondissement'].isin(matched_exclude_arrondissements)]

    return data


def top_restaurants(data, granularity, star_rating, top_n, display_restaurants=True):
    """
    Display top_n restaurants with the highest count of 'star_rating' restaurants
    based on different levels of granularity: region, department, or arrondissement.

    Also prints the names and cities of those restaurants if display_restaurants is True.
    Additionally, displays the cuisine and URL of each restaurant if display_info is True.

    Args:
        data (pandas.DataFrame): The dataset containing restaurant info.
        granularity (str): One of 'region', 'department', 'arrondissement'.
        star_rating (int): The Michelin star rating (1, 2, or 3).
        top_n (int): The number of top (granularity) to consider.
        display_restaurants (bool): Whether to display individual restaurants. Default is True.
    """
    # Filter out 'bib_gourmands' before the analysis
    data = data[data['stars'].isin([1.0, 2.0, 3.0])]

    # Convert star_rating to its corresponding unicode representation
    star_unicode = int(star_rating) * u'\u2B50'

    # Filter only rows matching the given star rating
    filtered_data = data[data['stars'] == star_rating]

    # Determine the unique values in the granularity column
    unique_values = filtered_data[granularity].unique()

    # Handle cases where unique values are less than top_n
    if len(unique_values) < top_n:
        print(f"Only {len(unique_values)} unique {granularity}s found.\n")
        top_n = len(unique_values)

    # Sort filtered_data by granularity
    sorted_filtered_data = filtered_data.sort_values(by=[granularity])

    # Group by granularity and get top_n
    top_areas = sorted_filtered_data[granularity].value_counts().nlargest(top_n)

    # If there's only one unique value, you're dealing with a specific region, department, or arrondissement.
    if len(unique_values) == 1:
        print(f"{star_unicode} restaurants in {unique_values[0]}\n\n")
    else:
        print(f"Top {top_n} {granularity}s with most {star_unicode} restaurants:\n\n")

    # Displaying the top restaurants or areas
    for area, restaurant_count in top_areas.items():
        restaurants_in_area = sorted_filtered_data[sorted_filtered_data[granularity] == area][
            ['name', 'address', 'location', granularity, 'cuisine', 'url', 'price']]

        restaurant_word = "Restaurant" if restaurant_count == 1 else "Restaurants"
        print(f"{granularity.capitalize()}: {area}\n{restaurant_count} {star_unicode} {restaurant_word}\n\n")

        if display_restaurants:
            for _, row in restaurants_in_area.iterrows():
                # Check if link is NaN or None
                if pd.isna(row['url']):
                    restaurant_name = row['name']  # Just the plain text name if the link is NaN
                else:
                    restaurant_name = f"<a href='{row['url']}' target='_blank'>{row['name']}</a>"

                html_content = (f"<br>Restaurant: {restaurant_name}<br>Address: {row['address']}<br>Location:"
                                f" {row['location']}<br>Style of Cuisine: {row['cuisine']}<br>Price:"
                                f" {row['price']}<br><br>")
                display(HTML(html_content))
                print()  # This will add a newline after each restaurant block for better readability on GitHub


def top_geo_restaurants(data, granularity, top_n):
    """
    Display top_n regions/departments with the highest count of Michelin-starred restaurants
    based on the granularity level: region, department.

    Args:
        data (gpd.GeoDataFrame): The dataset containing restaurant info.
        granularity (str): One of 'region', 'department'.
        top_n (int): The number of top (granularity) to consider.
    """
    # Check if granularity is valid
    if granularity not in data.columns:
        print(f"Invalid granularity: {granularity}")
        return

    # Group by granularity and get top_n based on total stars
    top_areas = data.groupby(granularity)['michelin_stars'].sum().nlargest(top_n)

    # Output
    print(f"Top {top_n} {granularity}s with most Michelin-starred restaurants:\n\n")

    # Displaying the top areas
    for position, (area, _) in enumerate(top_areas.iteritems(), start=1):
        restaurants_in_area = data[data[granularity] == area]

        total_1_star = restaurants_in_area['1_star'].sum()
        total_2_star = restaurants_in_area['2_star'].sum()
        total_3_star = restaurants_in_area['3_star'].sum()
        total_starred_restaurants = restaurants_in_area['starred_restaurants'].sum()
        total_stars = restaurants_in_area['michelin_stars'].sum()

        print(f"{position}: {granularity.capitalize()}: {area}")
        print(f"Total Stars: {total_stars}")
        print(f"Total Restaurants: {total_starred_restaurants}")
        if total_3_star:
            print(f"{total_3_star} ⭐⭐⭐ {'Restaurant' if total_3_star == 1 else 'Restaurants'}")
        if total_2_star:
            print(f"{total_2_star} ⭐⭐ {'Restaurant' if total_2_star == 1 else 'Restaurants'}")
        if total_1_star:
            print(f"{total_1_star} ⭐ {'Restaurant' if total_1_star == 1 else 'Restaurants'}")
        print("\n")


def plot_choropleth(df, column, title, granularity='department', restaurants=False,
                    star_rating=None, show_legend=True, cmap='Blues', figsize=(10, 10)):
    """
    Function to plot a choropleth map and optionally restaurant locations.

    Args:
        df (GeoDataFrame): The DataFrame containing the data.
        column (str): The name of the column to plot.
        title (str): The title of the plot.
        granularity (str): Level of granularity - 'arrondissement', 'department', or 'region'. Default is 'department'.
        restaurants (bool): If True, plot restaurant locations. Default is False.
        star_rating (int): Default is None = 'all'
        show_legend (bool): If True, display the legend. Default is True.
        cmap (str): The colormap to use. Default is 'Blues'.
        figsize (tuple): The size of the figure. Default is (10, 10).

    Returns:
        None
    """
    # Check if the column exists and contains numerical data
    if column not in df.columns:
        raise ValueError(
            f"The column '{column}' does not exist in the DataFrame. "
            f"Available numerical columns are:\n\n{df.select_dtypes(include=['number']).columns.tolist()}")

    if not np.issubdtype(df[column].dtype, np.number):
        raise ValueError(
            f"The column '{column}' does not contain numerical data. "
            f"Available numerical columns are:\n\n{df.select_dtypes(include=['number']).columns.tolist()}")

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    df = df.to_crs("EPSG:2154")  # RGF93 / Lambert-93

    # Plot the choropleth and get the returned artists and collection
    cax = df.plot(column=column, cmap=cmap, linewidth=0.8, edgecolor='0.8', legend=False, ax=ax)

    # Create the colorbar at the bottom
    cbar = fig.colorbar(cax.collections[0], ax=ax, orientation='horizontal', fraction=0.05, pad=0.05)
    cbar.set_label(column)

    all_handles = []
    all_labels = []

    # Handle the label_column based on granularity
    if granularity == 'region':
        label_column = 'region'
    elif granularity in ['department', 'arrondissement']:
        label_column = 'code'
    else:
        raise ValueError(f"Invalid granularity: {granularity}. Choose from ['region', 'department', 'arrondissement'].")

    # Check for unique departments if the 'department' column exists
    unique_departments = df['department'].unique() if 'department' in df.columns else []
    unique_regions = df['region'].unique()

    if len(unique_departments) == 1:
        title += f"\n{unique_departments[0]}"
    elif len(unique_regions) == 1:
        title += f"\n{unique_regions[0]}"

    for x, y, label in zip(df.geometry.centroid.x, df.geometry.centroid.y, df[label_column]):
        ax.text(x, y, label, fontsize=8, backgroundcolor='white')

    if show_legend:
        label_handles = [Line2D([0], [0], marker='o', color='w',
                                label=f"{code}: {df.loc[df[label_column] == code, granularity].values[0]}", markersize=0,
                                alpha=0) for code in df[label_column].unique()]
        all_handles.extend(label_handles)
        all_labels.extend([h.get_label() for h in label_handles])

    if restaurants:
        star_colors = {'1': 'green', '2': 'orange', '3': 'red'}
        added_labels = set()
        transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)

        # Check if a star rating has been specified
        if star_rating is not None:
            star_colors = {str(star_rating): star_colors[str(star_rating)]}

        for star, color in star_colors.items():
            for idx, row in df.iterrows():
                locations = row['locations']
                # If locations is a string, convert it and force keys to be strings
                if not isinstance(locations, dict):
                    try:
                        locations = ast.literal_eval(locations)
                        locations = {str(k): v for k, v in locations.items()}
                    except Exception as e:
                        print(f"Row {idx}: Error converting locations: {e}")
                        continue

                if star in locations and locations[star] is not None:
                    for coord in locations[star]:
                        # Make sure coord is a pair of numbers
                        if isinstance(coord, (list, tuple)) and len(coord) == 2:
                            lat, lon = coord
                            x, y = transformer.transform(lon, lat)
                            ax.scatter(x, y, c=color, s=50, marker='d')
                        else:
                            print(f"Row {idx}: Unexpected coordinate format: {coord}")

            if star not in added_labels:
                all_handles.append(
                    Line2D([0], [0], marker='d', color=color, label=f"{star} star restaurant",
                           markersize=8, linestyle='None'))
                added_labels.add(star)

        all_labels.extend([h.get_label() for h in all_handles[len(all_handles) - len(star_colors):]])

    # Move the legend to the left and outside the plot
    if show_legend and (granularity in ['region', 'department', 'arrondissement'] or restaurants):
        ax.legend(handles=all_handles, labels=all_labels, loc='upper left',
                  bbox_to_anchor=(1.05, 1), title="Legend", borderaxespad=0.)

    plt.suptitle(title)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')

    plt.tight_layout()
    plt.show()


def plot_multi_choropleth(df, columns, titles, granularity='department', show_labels=True, cmap='Blues',
                          figsize=(10, 10), restaurants=False):
    """
    Function to plot a choropleth map.

    Args:
        df (GeoDataFrame): The DataFrame containing the data.
        columns (list): The names of the columns to plot.
        titles (list): The titles of the plots.
        granularity (str): Level of granularity - 'arrondissement', 'department', or 'region'. Default is 'department'.
        show_labels (bool): Whether to show the labels. Default is True.
        cmap (str): The colormap to use. Default is 'Blues'.
        figsize (tuple): The size of the figure. Default is (10, 10).
        restaurants (bool): Whether to plot restaurants. Default is False.

    Returns:
        None
    """
    # Before plotting, ensure data is available for the chosen granularity.
    if granularity == 'arrondissement':
        missing_columns = [col for col in columns if col in ['GDP_millions(€)', 'per_capita_GDP', 'unemployment_rate']]
        if missing_columns:
            raise ValueError(
                f"Data for\n{missing_columns}\nis not available at the 'arrondissement' granularity.")

    # Convert to a projected CRS for accurate centroid calculation and plotting.
    df = df.to_crs("EPSG:2154")  # Lambert-93

    # Ensure that `columns` and `titles` are lists
    if not isinstance(columns, list):
        columns = [columns]
    if not isinstance(titles, list):
        titles = [titles]

    cols = len(columns)
    fig, axes = plt.subplots(1, cols, figsize=figsize)
    if cols == 1:
        axes = [axes]

    for ax, column, title in zip(axes, columns, titles):
        df.plot(column=column,
                cmap=cmap,
                linewidth=0.8,
                ax=ax,
                edgecolor='0.8',
                legend=True,
                legend_kwds={'orientation': "horizontal"})
        ax.set_title(title)

        # If show_labels is True, display labels based on granularity
        if show_labels:
            if granularity == 'region':
                label_column = 'region'
            elif granularity == 'department':
                label_column = 'code'
            elif granularity == 'arrondissement':
                label_column = 'arrondissement'
            else:
                raise ValueError(
                    f"Invalid granularity: {granularity}. Choose from ['region', 'department', 'arrondissement'].")

            for x, y, label in zip(df.geometry.centroid.x, df.geometry.centroid.y, df[label_column]):
                ax.text(x, y, label, fontsize=8, backgroundcolor='white')

        # Plot restaurants if restaurants argument is True
        if restaurants:
            star_colors = {'1': 'green', '2': 'orange', '3': 'red'}
            for star, color in star_colors.items():
                for _, row in df.iterrows():
                    locations = row['locations']
                    if star in locations and locations[
                        star] is not None:  # Check if locations for this star rating exist
                        for lat, lon in locations[star]:  # Get lat, long for each restaurant
                            x, y = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform(lon,
                                                                                                                   lat)
                            ax.scatter(x, y, c=color, s=50, marker='d')

        ax.set_yticklabels([])
        ax.set_xticklabels([])
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axis('off')

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


def plot_area_info(geo_df, data_df, code_or_name,
                   display_restaurants=True, display_info=False, figsize=(10, 10)):
    """
    Plots Michelin Starred Restaurants on a map for a specified department or arrondissement and optionally
    displays restaurant-specific info.

    Parameters:
    -----------
    geo_df : GeoDataFrame containing boundaries and relevant demographic data

    data_df : DataFrame containing restaurant information

    code_or_name : str or int
        The name of the department/arrondissement or the code. For department, code is usually a 2-digit number.

    display_restaurants : bool, optional
        If True, plots the location of Michelin Starred Restaurants on the map.
        Default is True.

    display_info : bool, optional
        If True, prints additional info for each restaurant.
        Default is False.

    figsize : tuple, optional
        Size of the plotted map. Default is (10, 10).

    Returns:
    --------
    None
        Displays a map and prints relevant demographic and restaurant-specific info.

    Example:
    --------
    >>> plot_area_info(geo_df=arrondissements, data_df=all_france, code_or_name='Nice',
                       display_restaurants=True, display_info=True)

    Notes:
    ------
    The function automatically determines the granularity (department vs. arrondissement)
    based on the columns present in `geo_df`.
    """
    # Determine the granularity based on geo_df
    if 'arrondissement' in geo_df.columns:
        granularity = 'arrondissement'
    else:
        granularity = 'department'

    # Handle input based on granularity
    if granularity == 'arrondissement':
        arrondissement_name = _get_best_match(code_or_name, geo_df, 'arrondissement')
        filtered_geo = geo_df[geo_df['arrondissement'] == arrondissement_name]
        filtered_data = data_df[data_df['arrondissement'] == arrondissement_name]
    else:
        filtered_geo = geo_df[geo_df['code'] == code_or_name]
        filtered_data = data_df[data_df['department_num'] == code_or_name]

    fig, ax = plt.subplots(figsize=figsize)
    filtered_geo.plot(ax=ax, color='lightgrey', edgecolor='k')

    if display_restaurants:
        star_colors = {'1': 'green', '2': 'orange', '3': 'red'}

        added_stars = set()
        for star, color in star_colors.items():
            star_data = filtered_data[filtered_data['stars'] == float(star)]
            for _, row in star_data.iterrows():
                ax.scatter(row['longitude'], row['latitude'], c=color, s=50, marker='d',
                           label=f"{star} star" if star not in added_stars else "")
                added_stars.add(star)

    handles, labels = ax.get_legend_handles_labels()
    unique_labels = dict(zip(labels, handles))
    ax.legend(unique_labels.values(), unique_labels.keys())

    area_info = filtered_geo.iloc[0]
    title_value = area_info[granularity] if granularity == 'arrondissement' else area_info['department']
    ax.set_title(f"Michelin Starred Restaurants\n{title_value}")
    ax.set_axis_off()
    plt.show()

    # Dynamic demographics
    common_cols = ['region', 'capital', 'municipal_population', 'population_density(inhabitants/sq_km)']

    if granularity == 'department':
        specific_cols = ['area(sq_km)', 'average_net_hourly_wage(€)', 'poverty_rate(%)',
                         'average_annual_unemployment_rate(%)', 'GDP_per_capita(€)']  # department-specific
    else:
        specific_cols = ['average_net_hourly_wage(€)', 'poverty_rate(%)']  # arrondissement-specific

    demographic_cols = common_cols + specific_cols

    # Print the demographic data dynamically
    print(f"Demographics of {area_info[granularity]}:\n")
    for col in demographic_cols:
        # Split the column name by underscores
        words = col.split('_')
        # Capitalize each word
        capitalized_words = [word.capitalize() for word in words if not word.startswith('(')]
        # Special case for 'GDP'
        capitalized_words = ['GDP' if word == 'Gdp' else word for word in capitalized_words]
        # Form the name and print it
        name = ' '.join(capitalized_words)
        print(f"{name}: {area_info[col]} ")  # Note that we use col here, not the formatted_name
    print("\n\n\n")

    # 3. List of Starred Restaurants:
    star_columns = ['3_star', '2_star', '1_star']

    for star_col in star_columns:
        # Extract the star count and determine the appropriate Unicode star symbol
        star_count = filtered_geo[star_col].values[0]
        if star_count > 0:  # Only proceed if there are restaurants with that star rating
            star_rating = int(star_col.split('_')[0])
            star_unicode = star_rating * u'\u2B50'

            restaurant_word = "Restaurant" if star_count == 1 else "Restaurants"
            print(f"{star_count} {star_unicode} {restaurant_word}:\n")

            # Get the restaurants from the data dataframe with the matching star rating
            restaurants_in_area = filtered_data[filtered_data['stars'] == star_rating]

            for _, restaurant in restaurants_in_area.iterrows():
                if display_info:
                    # Check if link is NaN or None
                    if pd.isna(restaurant['url']):
                        restaurant_name = restaurant['name']  # Just the plain text name if the link is NaN
                    else:
                        restaurant_name = f"<a href='{restaurant['url']}' target='_blank'>{restaurant['name']}</a>"

                    html_content = (f"<br>Restaurant: {restaurant_name}<br>Address: {restaurant['address']}<br>Location:"
                                    f" {restaurant['location']}<br>Style of Cuisine: {restaurant['cuisine']}<br>Price:"
                                    f" {restaurant['price']}<br><br>")
                    display(HTML(html_content))
                    print()  # This will add a newline after each restaurant block for better readability on GitHub
            print("")
