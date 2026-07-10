import dash

from app.app_config import CONFIG
from app.layouts.layout_main import get_main_layout


dash.register_page(
    __name__,
    path="/home",
    name="Home",
    title=CONFIG.browser_title(),
    order=1,
)


def layout(**_kwargs):
    return get_main_layout()
