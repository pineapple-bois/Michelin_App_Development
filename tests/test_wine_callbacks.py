import pytest
from dash import dcc, html, no_update

from app.callbacks.wine import (
    build_wine_info_response,
    restaurant_filter_style,
    restaurant_overlay_visible,
    restaurant_visibility_patch,
    regional_outline_visibility_patch,
    regional_outlines_visible,
    resolve_wine_feature,
)


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


@pytest.mark.parametrize(
    ("selected_granularity", "expected"),
    [
        ("region", True),
        (None, False),
        ("department", False),
    ],
)
def test_regional_outlines_visible_only_for_region_selection(selected_granularity, expected):
    assert regional_outlines_visible(selected_granularity) is expected


@pytest.mark.parametrize(
    ("selected_granularity", "expected"),
    [
        ("region", True),
        (None, False),
    ],
)
def test_regional_outline_visibility_patch_updates_only_outline_layer(selected_granularity, expected):
    patch = regional_outline_visibility_patch(selected_granularity).to_plotly_json()

    assert patch["operations"] == [
        {
            "operation": "Assign",
            "location": ["layout", "map", "layers", 0, "visible"],
            "params": {"value": expected},
        }
    ]


@pytest.mark.parametrize(
    ("n_clicks_rest", "expected"),
    [
        (None, False),
        (0, False),
        (1, True),
        (2, False),
    ],
)
def test_restaurant_overlay_visible_only_for_odd_toggle_clicks(n_clicks_rest, expected):
    assert restaurant_overlay_visible(n_clicks_rest) is expected


def test_restaurant_filter_style_tracks_overlay_visibility():
    assert restaurant_filter_style(True) == {'width': '30%', 'display': 'block'}
    assert restaurant_filter_style(False) == {'width': '30%', 'display': 'none'}


@pytest.mark.parametrize(
    ("n_clicks_rest", "n_clicks_stars", "expected_visibility"),
    [
        (0, [0, 0, 0], [False, False, False]),
        (1, [0, 0, 0], [True, True, True]),
        (1, [0, 1, 0], [True, False, True]),
        (2, [0, 0, 0], [False, False, False]),
    ],
)
def test_restaurant_visibility_patch_updates_only_restaurant_traces(
    n_clicks_rest,
    n_clicks_stars,
    expected_visibility,
):
    ids = [
        {"type": "filter-button-wine", "index": 1},
        {"type": "filter-button-wine", "index": 2},
        {"type": "filter-button-wine", "index": 3},
    ]
    patch = restaurant_visibility_patch(
        n_clicks_rest,
        n_clicks_stars,
        ids,
    ).to_plotly_json()

    assert patch["operations"] == [
        {
            "operation": "Assign",
            "location": ["data", 1, "visible"],
            "params": {"value": expected_visibility[0]},
        },
        {
            "operation": "Assign",
            "location": ["data", 2, "visible"],
            "params": {"value": expected_visibility[1]},
        },
        {
            "operation": "Assign",
            "location": ["data", 3, "visible"],
            "params": {"value": expected_visibility[2]},
        },
    ]


class FakeCache:
    def __init__(self):
        self.values = {}
        self.get_calls = []
        self.set_calls = []

    def get(self, key):
        self.get_calls.append(key)
        return self.values.get(key)

    def set(self, key, value):
        self.set_calls.append((key, value))
        self.values[key] = value


class FakeRequestLimit:
    def __init__(self, exceeded=False):
        self.exceeded = exceeded
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.exceeded


class FakeOpenAIClient:
    def __init__(self):
        self.requests = []
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.requests.append(kwargs)
        region = kwargs["messages"][0]["content"].removeprefix("prompt:")
        content = f"Generated regional content for {region}"
        message = type("Message", (), {"content": content})()
        choice = type("Choice", (), {"message": message})()
        return type("Response", (), {"choices": [choice]})()


def _click(feature_id):
    return {"points": [{"location": feature_id}]}


def _feature_lookup_for_regions(data_boundary):
    grouped = data_boundary.wine_df.groupby("region")
    same_region = grouped.get_group("Bourgogne")
    other_region = next(
        group
        for region, group in grouped
        if region != same_region.iloc[0]["region"]
    )

    rows = [same_region.iloc[0], same_region.iloc[1], other_region.iloc[0]]
    lookup = {
        row["feature_id"]: {
            "region": row["region"],
            "app": row["app"],
            "colour": row["colour"],
        }
        for row in rows
    }
    return rows, lookup


def _prompt_builder(region):
    return f"prompt:{region}"


def test_wine_info_reuses_explicit_region_cache_for_different_aocs(data_boundary):
    rows, lookup = _feature_lookup_for_regions(data_boundary)
    first_bourgogne, second_bourgogne, other_region = rows
    assert first_bourgogne["region"] == second_bourgogne["region"]
    assert first_bourgogne["feature_id"] != second_bourgogne["feature_id"]
    assert first_bourgogne["region"] != other_region["region"]

    cache = FakeCache()
    request_limit = FakeRequestLimit()
    openai_client = FakeOpenAIClient()

    first_response = build_wine_info_response(
        _click(first_bourgogne["feature_id"]),
        lookup,
        cache,
        openai_client,
        request_limit,
        prompt_builder=_prompt_builder,
    )
    second_response = build_wine_info_response(
        _click(second_bourgogne["feature_id"]),
        lookup,
        cache,
        openai_client,
        request_limit,
        prompt_builder=_prompt_builder,
    )
    other_response = build_wine_info_response(
        _click(other_region["feature_id"]),
        lookup,
        cache,
        openai_client,
        request_limit,
        prompt_builder=_prompt_builder,
    )

    first_region = first_bourgogne["region"]
    other_parent_region = other_region["region"]

    assert cache.get_calls == [
        f"wine_info_{first_region}",
        f"wine_info_{first_region}",
        f"wine_info_{other_parent_region}",
    ]
    assert [key for key, _ in cache.set_calls] == [
        f"wine_info_{first_region}",
        f"wine_info_{other_parent_region}",
    ]
    assert len(openai_client.requests) == 2
    assert request_limit.calls == 2

    assert isinstance(first_response[0], dcc.Markdown)
    assert isinstance(second_response[0], dcc.Markdown)
    assert isinstance(other_response[0], dcc.Markdown)
    assert first_response[2].children == first_region
    assert second_response[2].children == first_region
    assert other_response[2].children == other_parent_region
    assert first_response[0].children == second_response[0].children
    assert other_response[0].children != first_response[0].children


def test_wine_info_uses_cached_response_without_openai_or_request_limit(feature_lookup):
    cache = FakeCache()
    cache.values["wine_info_Bourgogne"] = {
        "content": "Cached regional Bourgogne content",
        "color": "#abcdef",
    }
    request_limit = FakeRequestLimit()
    openai_client = FakeOpenAIClient()

    response = build_wine_info_response(
        _click("aoc-known"),
        feature_lookup,
        cache,
        openai_client,
        request_limit,
        prompt_builder=_prompt_builder,
    )

    assert isinstance(response[0], dcc.Markdown)
    assert response[0].children == "Cached regional Bourgogne content"
    assert response[2].children == "Bourgogne"
    assert response[2].style == {"color": "#abcdef"}
    assert openai_client.requests == []
    assert request_limit.calls == 0


@pytest.mark.parametrize(
    "click_data",
    [
        None,
        {},
        {"points": []},
        {"points": [{}]},
        {"points": [{"customdata": ["Restaurant"]}]},
        {"points": [{"location": None}]},
        {"points": [{"location": "aoc-unknown"}]},
    ],
)
def test_wine_info_failed_payloads_do_not_invoke_openai_or_request_limit(click_data, feature_lookup):
    cache = FakeCache()
    request_limit = FakeRequestLimit()
    openai_client = FakeOpenAIClient()

    response = build_wine_info_response(
        click_data,
        feature_lookup,
        cache,
        openai_client,
        request_limit,
        prompt_builder=_prompt_builder,
    )

    assert openai_client.requests == []
    assert request_limit.calls == 0
    assert response[2] is no_update


def test_wine_info_restaurant_click_payload_fails_closed_without_replacing_content(feature_lookup):
    cache = FakeCache()
    request_limit = FakeRequestLimit()
    openai_client = FakeOpenAIClient()
    click_data = {
        "points": [
            {
                "curveNumber": 1,
                "pointNumber": 0,
                "customdata": ["Restaurant", "Paris"],
                "lon": 2.35,
                "lat": 48.85,
            }
        ]
    }

    response = build_wine_info_response(
        click_data,
        feature_lookup,
        cache,
        openai_client,
        request_limit,
        prompt_builder=_prompt_builder,
    )

    assert response == (no_update, no_update, no_update, no_update)
    assert cache.get_calls == []
    assert openai_client.requests == []
    assert request_limit.calls == 0


def test_wine_info_request_limit_checked_only_after_uncached_valid_aoc(feature_lookup):
    cache = FakeCache()
    request_limit = FakeRequestLimit(exceeded=True)
    openai_client = FakeOpenAIClient()

    response = build_wine_info_response(
        _click("aoc-known"),
        feature_lookup,
        cache,
        openai_client,
        request_limit,
        prompt_builder=_prompt_builder,
    )

    assert isinstance(response[0], html.Div)
    assert response[0].children == "You have reached the maximum number of requests."
    assert response[2] is no_update
    assert openai_client.requests == []
    assert request_limit.calls == 1
    assert cache.set_calls == []
