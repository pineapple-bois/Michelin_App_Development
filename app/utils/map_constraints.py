"""Shared declarative viewport constraints for interactive application maps."""


# Guide-only envelope padded for geometry-centred regional cameras, including
# Corsica and edge regions on the widest stacked layout. MapLibre uses this as
# maxBounds: users can still zoom in and pan, but cannot escape the useful
# France-and-neighbours area or zoom out to world scale.
METROPOLITAN_FRANCE_MAP_BOUNDS = {
    "west": -17.0,
    "east": 20.0,
    "south": 37.0,
    "north": 55.0,
}

# Plotly exposes no separate MapLibre minZoom layout property: the effective
# minimum is derived from maxBounds and the rendered canvas. This Wine-only
# envelope yields a measured minimum of 4.7 on the 811 x 760 desktop map while
# leaving the Guide and the other editorial maps unchanged.
WINE_MAP_BOUNDS = {
    "west": -8.719389,
    "east": 13.219389,
    "south": 39.024491,
    "north": 53.166278,
}

# Wide padding for a full-width editorial map. Its landscape canvas needs a
# broad east-west envelope before MapLibre will honour the intended zoom.
FRANCE_OVERVIEW_MAP_BOUNDS = {
    "west": -35.0,
    "east": 40.0,
    "south": 32.0,
    "north": 60.0,
}

# Tighter padding for maps displayed beside a chart. Their narrower canvas can
# fit mainland France and Corsica without opening the wider overview envelope.
FRANCE_SPLIT_MAP_BOUNDS = {
    "west": -12.0,
    "east": 17.0,
    "south": 36.0,
    "north": 56.0,
}


def apply_metropolitan_france_bounds(fig):
    """Apply the shared native MapLibre France viewport constraint."""
    fig.update_layout(map_bounds=METROPOLITAN_FRANCE_MAP_BOUNDS)
    return fig


def apply_wine_bounds(fig):
    """Apply the Wine-only native viewport constraint."""
    fig.update_layout(map_bounds=WINE_MAP_BOUNDS)
    return fig


def apply_france_overview_bounds(fig):
    """Apply the padded native constraint used by editorial overview maps."""
    fig.update_layout(map_bounds=FRANCE_OVERVIEW_MAP_BOUNDS)
    return fig


def apply_france_split_bounds(fig):
    """Apply the native constraint used by map-and-chart split layouts."""
    fig.update_layout(map_bounds=FRANCE_SPLIT_MAP_BOUNDS)
    return fig
