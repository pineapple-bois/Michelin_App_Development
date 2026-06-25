import dash

from app.layouts.layout_404 import get_404_layout


dash.register_page(
    __name__,
    path="/404",
    name="404",
    title="404 - Gastronomic Guide to France",
    order=99,
)


def layout(**_kwargs):
    return get_404_layout()
