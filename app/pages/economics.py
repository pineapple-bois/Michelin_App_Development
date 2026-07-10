import dash

from app.app_config import CONFIG
from app.layouts.economics import get_economics_layout


dash.register_page(
    __name__,
    path="/economics",
    name="Economics",
    title=CONFIG.browser_title("Economics"),
    order=3,
)


def layout(**_kwargs):
    return get_economics_layout()
