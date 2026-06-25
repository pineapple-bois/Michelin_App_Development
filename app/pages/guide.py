import dash

from app.layouts.layout_main import get_main_layout


dash.register_page(
    __name__,
    path="/",
    name="Guide",
    title="Gastronomic Guide to France - pineapple-bois",
    order=0,
)


def layout(**_kwargs):
    return get_main_layout()
