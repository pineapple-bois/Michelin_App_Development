"""Compatibility re-exports for legacy imports.

The large mixed helper implementation was split by purpose into focused
``utils`` modules during Phase 6. Existing callbacks may still import from
``utils.appFunctions`` until the direct-import cleanup removes this shim.
"""

from utils.analysis_figures import (
    create_michelin_bar_chart,
    plot_single_choropleth_plotly,
    top_restaurants,
)
from utils.economics_figures import (
    calculate_weighted_mean,
    plot_demographic_choropleth_plotly,
    plot_demographics_barchart,
)
from utils.guide_figures import (
    add_star_trace,
    default_map_figure,
    generate_hover_text,
    label_properties,
    plot_arrondissement_outlines,
    plot_department_outlines,
    plot_geometry_outline,
    plot_interactive_department,
    plot_paris_arrondissement,
    plot_regional_outlines,
    text_color_map,
)
from utils.restaurant_cards import get_restaurant_details
from utils.star_filters import update_button_active_state_helper
from utils.wine_figures import plot_wine_choropleth_plotly
from utils.wine_prompts import generate_optimized_prompt

__all__ = [
    "add_star_trace",
    "calculate_weighted_mean",
    "create_michelin_bar_chart",
    "default_map_figure",
    "generate_hover_text",
    "generate_optimized_prompt",
    "get_restaurant_details",
    "label_properties",
    "plot_arrondissement_outlines",
    "plot_demographic_choropleth_plotly",
    "plot_demographics_barchart",
    "plot_department_outlines",
    "plot_geometry_outline",
    "plot_interactive_department",
    "plot_paris_arrondissement",
    "plot_regional_outlines",
    "plot_single_choropleth_plotly",
    "plot_wine_choropleth_plotly",
    "text_color_map",
    "top_restaurants",
    "update_button_active_state_helper",
]
