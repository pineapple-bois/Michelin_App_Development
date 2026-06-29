import pytest

from app.callbacks.wine import resolve_wine_feature


@pytest.fixture
def feature_lookup():
    return {
        "aoc-known": {
            "region": "Bourgogne",
            "app": "Known appellation",
            "colour": "#123456",
        }
    }


def test_resolve_wine_feature_uses_location(feature_lookup):
    click_data = {
        "points": [
            {
                "curveNumber": 99,
                "pointNumber": 123,
                "location": "aoc-known",
            }
        ]
    }

    assert resolve_wine_feature(click_data, feature_lookup) == feature_lookup["aoc-known"]


@pytest.mark.parametrize(
    "click_data",
    [
        None,
        {},
        {"points": []},
        {"points": [{}]},
        {"points": [{"customdata": ["Restaurant"]}]},
        {"points": [{"location": None}]},
    ],
)
def test_resolve_wine_feature_fails_closed_without_feature_id(click_data, feature_lookup):
    assert resolve_wine_feature(click_data, feature_lookup) is None


def test_resolve_wine_feature_fails_closed_for_unknown_feature_id(feature_lookup):
    click_data = {"points": [{"location": "aoc-unknown"}]}

    assert resolve_wine_feature(click_data, feature_lookup) is None
