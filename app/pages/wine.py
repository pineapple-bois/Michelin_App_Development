import dash

from app.app_config import CONFIG
from app.layouts.wine import get_wine_layout


dash.register_page(
    __name__,
    path="/wine",
    name="Wine",
    title=CONFIG.browser_title("Wine"),
    order=4,
)


def layout(**_kwargs):
    return get_wine_layout()
