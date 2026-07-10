import dash

from app.app_config import CONFIG
from app.layouts.layout_404 import get_404_layout


dash.register_page(
    __name__,
    path="/404",
    name="404",
    title=CONFIG.browser_title("404"),
    order=99,
)


def layout(**_kwargs):
    return get_404_layout()
