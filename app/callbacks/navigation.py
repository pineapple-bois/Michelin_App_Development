from dash.dependencies import Input, Output, State

from app.components.shared import NAV_LINKS, nav_link_class


def register_navigation_callbacks(app):
    # Toggle nav menu open/closed
    @app.callback(
        Output('navigation-menu', 'className'),
        Input('hamburger-icon', 'n_clicks'),
        State('navigation-menu', 'className'),
        prevent_initial_call=True
    )
    def toggle_menu_class(n_clicks, current_class):
        if current_class == 'nav-dropdown':
            return 'nav-dropdown visible'
        else:
            return 'nav-dropdown'

    @app.callback(
        [Output(link['id'], 'className') for link in NAV_LINKS],
        Input('url', 'pathname')
    )
    def update_nav_classes(pathname):
        return [nav_link_class(pathname, link['id']) for link in NAV_LINKS]
