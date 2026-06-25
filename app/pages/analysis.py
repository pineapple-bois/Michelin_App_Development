import dash

from app.layouts.analysis import get_analysis_layout


dash.register_page(
    __name__,
    path="/analysis",
    name="Analysis",
    title="Analysis - Gastronomic Guide to France",
    order=2,
)


def layout(**_kwargs):
    return get_analysis_layout()
