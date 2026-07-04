"""Shared declarative viewport constraints for interactive application maps."""


# Padded metropolitan-France extent including Corsica and Monaco. MapLibre uses
# this as maxBounds: users can still zoom in and pan, but cannot escape the
# useful France-wide map area or zoom out beyond it.
METROPOLITAN_FRANCE_MAP_BOUNDS = {
    "west": -6.0,
    "east": 10.5,
    "south": 40.5,
    "north": 52.0,
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


def apply_france_overview_bounds(fig):
    """Apply the padded native constraint used by editorial overview maps."""
    fig.update_layout(map_bounds=FRANCE_OVERVIEW_MAP_BOUNDS)
    return fig


def apply_france_split_bounds(fig):
    """Apply the native constraint used by map-and-chart split layouts."""
    fig.update_layout(map_bounds=FRANCE_SPLIT_MAP_BOUNDS)
    return fig
