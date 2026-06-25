import dash

from layouts.economics import get_economics_layout


dash.register_page(
    __name__,
    path="/economics",
    name="Economics",
    title="Economics - Gastronomic Guide to France",
    order=3,
)


def layout(**_kwargs):
    return get_economics_layout()
