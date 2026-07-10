import dash

from app.app_config import CONFIG
from app.layouts.layout_main import get_main_layout


dash.register_page(
    __name__,
    path="/",
    name="Guide",
    title=CONFIG.browser_title(),
    order=0,
)


def layout(**_kwargs):
    return get_main_layout()
