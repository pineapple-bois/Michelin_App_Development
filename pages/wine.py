import dash

from layouts.layout_analysis import get_wine_layout


dash.register_page(
    __name__,
    path="/wine",
    name="Wine",
    title="Wine - Gastronomic Guide to France",
    order=4,
)


def layout(**_kwargs):
    return get_wine_layout()
