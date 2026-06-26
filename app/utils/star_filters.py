from app.components.shared import color_map

def update_button_active_state_helper(n_clicks_list, ids, filter_type):
    """
    Generalized function to update the button states for different filter types (e.g., analysis, department, etc.).

    Args:
        n_clicks_list (list): List of n_clicks from the buttons.
        ids (list): List of button ids.
        filter_type (str): The type of filter (analysis, department, demographics, wine).

    Returns:
        list: Class names for each button.
        list: Styles for each button.
    """
    # Initialize empty lists to store class names and styles
    class_names = []
    styles = []

    for n_clicks, button_id in zip(n_clicks_list, ids):
        index = button_id['index']

        # Determine if the button is currently active
        is_active = n_clicks % 2 == 0  # Even clicks mean 'active'
        if is_active:
            background_color = color_map[index]  # Full color for active state
        else:
            background_color = (f"rgba({int(color_map[index][1:3], 16)},"
                                f"{int(color_map[index][3:5], 16)},"
                                f"{int(color_map[index][5:7], 16)},"
                                f"0.6)")  # Lighter color for inactive

        # Update class name and style based on the active/inactive state
        class_name = f"me-1 star-button-{filter_type} editorial-rating-button" + (" active" if is_active else "")
        color_style = {
            "display": 'inline-block',
            "width": '100%',
            'backgroundColor': background_color,
        }

        class_names.append(class_name)
        styles.append(color_style)

    return class_names, styles
