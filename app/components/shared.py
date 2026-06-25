from dash import dcc, html


MICHELIN_RATING_COLORS = {
    0.25: "#808080",
    0.5: "#640A64",
    1: "#FFB84D",
    2: "#FE6F64",
    3: "#C2282D",
}

color_map = MICHELIN_RATING_COLORS

NAV_LINKS = (
    {
        "label": "Guide",
        "href": "/",
        "id": "home-button",
        "active_paths": ("/", "/home"),
    },
    {
        "label": "Analysis",
        "href": "/analysis",
        "id": "analysis-button",
        "active_paths": ("/analysis",),
    },
    {
        "label": "Economics",
        "href": "/economics",
        "id": "economics-button",
        "active_paths": ("/economics",),
    },
    {
        "label": "Wine",
        "href": "/wine",
        "id": "wine-button",
        "active_paths": ("/wine",),
    },
)


def nav_link_class(pathname, link_id):
    for link in NAV_LINKS:
        if link["id"] == link_id and pathname in link["active_paths"]:
            return "nav-link active"
    return "nav-link"


def michelin_stars(count):
    stars = []
    for i in range(int(count)):
        style = {
            "height": "20px",
            "width": "auto",
            "vertical-align": "middle",
        }
        if i < count - 1:
            style["marginRight"] = "3px"
        stars.append(html.Img(
            src="assets/images/michelin_star.png",
            className="michelin-star",
            style=style,
        ))
    return stars


def bib_gourmand():
    return html.Img(
        src="assets/images/michelin_bib.png",
        className="bib-image",
        style={"height": "20px", "width": "auto", "vertical-align": "middle"},
    )


def green_star(with_margin=False):
    style = {"height": "20px", "width": "auto", "vertical-align": "middle"}
    if with_margin:
        style["marginLeft"] = "3px"

    return html.Img(
        src="assets/images/michelin_green_star.png",
        className="green-star",
        style=style,
    )


def inverted_michelin_stars(count):
    return [
        html.Img(
            src="assets/images/michelin_star.png",
            className="michelin-star-invert",
            style={
                "width": "16px",
                "vertical-align": "middle",
                "margin-right": "2px",
                "filter": "brightness(0) invert(1)",
            },
        )
        for _ in range(int(count))
    ]


def inverted_bib_gourmand():
    return html.Img(
        src="assets/images/michelin_bib.png",
        className="bib-image-invert",
        style={
            "width": "18px",
            "vertical-align": "middle",
            "filter": "brightness(0) invert(1)",
        },
    )


def get_header_with_buttons():
    return html.Div(
        children=[
            html.Div(
                [
                    html.H1(
                        ["Michelin Guide to France. ", html.Span("2026", className="year-text")],
                        className="title-section",
                    ),
                ],
                className="header-title",
            ),
            html.Div(
                id="hamburger-icon",
                n_clicks=0,
                className="hamburger-menu",
                children=[
                    html.Div(className="bar"),
                    html.Div(className="bar"),
                    html.Div(className="bar"),
                ],
            ),
            html.Div(
                id="navigation-menu",
                className="nav-dropdown",
                children=[
                    html.A(
                        link["label"],
                        href=link["href"],
                        id=link["id"],
                        className="nav-link",
                    )
                    for link in NAV_LINKS
                ],
            ),
        ],
        className="header-container",
    )


def get_footer():
    return html.Div(
        children=[
            html.Div(
                children=[
                    html.Img(src="assets/images/github-mark.png", className="info-image"),
                    html.Div(
                        children=[
                            html.Div(
                                children=[
                                    html.Span(
                                        "The Michelin Guide to France was built from this ",
                                        className="info-text",
                                    ),
                                    dcc.Link(
                                        "GitHub Repository",
                                        href="https://github.com/pineapple-bois/Michelin_Rated_Restaurants",
                                        target="_blank",
                                        className="info-link",
                                    ),
                                ],
                                className="info-line",
                            ),
                            html.Div(
                                children=[
                                    html.Span("© pineapple-bois 2024", className="info-footer"),
                                    html.Span(
                                        " | This website is an independent project and is not affiliated with or endorsed by ",
                                        className="disclaimer-text",
                                    ),
                                    dcc.Link(
                                        "the official Michelin Guide",
                                        href="https://guide.michelin.com/en/fr/restaurants",
                                        target="_blank",
                                        className="disclaimer-link",
                                    ),
                                ],
                                className="footer-inline",
                            ),
                        ],
                        className="text-container",
                    ),
                ],
                className="info-container",
            )
        ],
        className="footer-main",
    )
