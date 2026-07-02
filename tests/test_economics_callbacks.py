import pytest

from app.callbacks.economics import restaurant_overlay_active


@pytest.mark.parametrize(
    ("n_clicks", "expected"),
    [
        (None, False),
        (0, False),
        (1, True),
        (2, False),
    ],
)
def test_restaurant_overlay_active_tracks_toggle_clicks(n_clicks, expected):
    assert restaurant_overlay_active(n_clicks) is expected
