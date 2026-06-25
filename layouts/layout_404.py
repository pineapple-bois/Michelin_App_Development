from dash import html, dcc

from components.shared import get_footer, get_header_with_buttons


# 404 error page
def get_error_section():
    return html.Div(
        className='not-found-content-container',
        children=[
            html.H1("404: Page Not Found 🍍", className='custom-text'),
            html.P("Sorry, the page you are looking for does not exist.", className='custom-text'),
            dcc.Link("Return to Home Page", href="/", className="header-button")
        ]
    )


def get_404_layout():
    # Header with buttons
    header = html.Div(
        children=[
            get_header_with_buttons()
        ],
        className='header'
    )

    body = get_error_section()
    footer = get_footer()

    # Combine all sections into the main layout
    return html.Div([
        header,
        body,
        footer
    ], className='main-layout')
