import dash

from app.app_config import CONFIG
from app.layouts.analysis import get_analysis_layout


dash.register_page(
    __name__,
    path="/analysis",
    name="Analysis",
    title=CONFIG.browser_title("Analysis"),
    order=2,
)


def layout(**_kwargs):
    return get_analysis_layout()
