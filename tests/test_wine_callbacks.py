import json

import pytest
from dash import html, no_update

from app.callbacks.wine import (
    WINE_VIEW_GEOGRAPHY_KEY,
    build_wine_region_heading,
    build_wine_info_response,
    format_hectares,
    map_view_from_relayout,
    restaurant_filter_style,
    restaurant_overlay_visible,
    reset_restaurant_star_clicks,
    restaurant_visibility_patch,
    render_wine_info,
    regional_outline_visibility_patch,
    regional_outlines_visible,
    resolve_wine_feature,
    selected_wine_map_view,
    updated_wine_view_store,
    wine_geography_key,
    wine_view_revision,
    wine_hover_highlight_patch,
    wine_hover_overlay_response,
    wine_navigation_command,
    wine_navigation_patch,
)
from app.utils.wine_figures import RESTAURANT_TRACE_BELOW
from app.utils.wine_search import build_wine_search_index, wine_search_lookup
from app.utils.wine_search import map_view_for_feature, map_view_for_region


@pytest.fixture
def feature_lookup():
    return {
        "aoc-known": {
            "region": "Bourgogne",
            "app": "Known appellation protected designation",
            "display_name": "Known appellation",
            "categorie": "Vin tranquille",
            "prompt_signals": ["late_harvest"],
            "colour": "#123456",
            "source_area_m2": 18_000_000,
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
    ("source_area_m2", "expected"),
    [
        (18_000, "1.8"),
        (1_800_000, "180"),
        (18_000_000, "1800"),
    ],
)
def test_format_hectares_uses_two_significant_figures(source_area_m2, expected):
    assert format_hectares(source_area_m2) == expected


def test_wine_region_heading_separates_region_appellation_and_area(feature_lookup):
    heading = build_wine_region_heading(feature_lookup["aoc-known"], "#abcdef")

    assert isinstance(heading, html.Div)
    assert heading.className == "wine-region-heading"
    assert heading.children[0].children == "Bourgogne"
    assert heading.children[0].style == {"color": "#abcdef"}
    assert heading.children[1].children == "Known appellation · 1800 hectares"
    assert heading.children[1].className == "wine-appellation-area"


def _hover_point(curve_number=0, customdata=None, location="aoc-known"):
    return {
        "points": [
            {
                "curveNumber": curve_number,
                "customdata": customdata
                or ["Bourgogne", "Known appellation", "aoc-known"],
                "location": location,
            }
        ]
    }


def test_wine_hover_overlay_hides_without_hover_data(feature_lookup):
    assert wine_hover_overlay_response(None, feature_lookup) == ("", "", True)


def test_wine_hover_overlay_shows_semantic_aoc_content(feature_lookup):
    assert wine_hover_overlay_response(_hover_point(), feature_lookup) == (
        "Known appellation",
        "Bourgogne",
        False,
    )


def test_wine_hover_overlay_hides_for_restaurant_hover(feature_lookup):
    restaurant_hover = _hover_point(
        curve_number=1,
        customdata=["Restaurant", "Paris"],
        location=None,
    )

    assert wine_hover_overlay_response(restaurant_hover, feature_lookup) == (
        "",
        "",
        True,
    )


@pytest.mark.parametrize(
    "hover_data",
    [
        {},
        {"points": []},
        {"points": [{}]},
        _hover_point(customdata=["Bourgogne"]),
        _hover_point(customdata=["Bourgogne", "Known appellation", None]),
        _hover_point(customdata=["Bourgogne", "Known appellation", "aoc-other"]),
    ],
)
def test_wine_hover_overlay_hides_for_malformed_payloads(hover_data, feature_lookup):
    assert wine_hover_overlay_response(hover_data, feature_lookup) == ("", "", True)


def test_wine_hover_overlay_hides_for_unknown_aoc(feature_lookup):
    unknown_hover = _hover_point(
        customdata=["Bourgogne", "Unknown appellation", "aoc-unknown"],
        location="aoc-unknown",
    )

    assert wine_hover_overlay_response(unknown_hover, feature_lookup) == ("", "", True)


def test_wine_hover_overlay_hides_for_unknown_trace(feature_lookup):
    assert wine_hover_overlay_response(
        _hover_point(curve_number=99),
        feature_lookup,
    ) == ("", "", True)


def test_wine_hover_highlight_selects_valid_aoc(feature_lookup):
    patch = wine_hover_highlight_patch(
        _hover_point(),
        feature_lookup,
        {"aoc-known": 7},
    ).to_plotly_json()

    assert patch["operations"] == [
        {
            "operation": "Assign",
            "location": ["data", 0, "selectedpoints"],
            "params": {"value": [7]},
        }
    ]


@pytest.mark.parametrize(
    "hover_data",
    [
        None,
        _hover_point(curve_number=1, customdata=["Restaurant", "Paris"]),
        _hover_point(location="aoc-unknown"),
    ],
)
def test_wine_hover_highlight_clears_for_non_aoc_hover(hover_data, feature_lookup):
    patch = wine_hover_highlight_patch(
        hover_data,
        feature_lookup,
        {"aoc-known": 7},
    ).to_plotly_json()

    assert patch["operations"] == [
        {
            "operation": "Assign",
            "location": ["data", 0, "selectedpoints"],
            "params": {"value": []},
        }
    ]


@pytest.mark.parametrize(
    ("n_clicks", "expected"),
    [
        (None, False),
        (0, False),
        (1, True),
        (2, False),
    ],
)
def test_regional_outlines_visible_tracks_toggle_clicks(n_clicks, expected):
    assert regional_outlines_visible(n_clicks) is expected


@pytest.mark.parametrize(
    ("n_clicks", "expected"),
    [
        (None, False),
        (0, False),
        (1, True),
        (2, False),
    ],
)
def test_regional_outline_visibility_patch_updates_only_outline_layer(n_clicks, expected):
    patch = regional_outline_visibility_patch(n_clicks).to_plotly_json()

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


def test_restaurant_star_clicks_reset_only_when_overlay_closes():
    ids = [
        {"type": "filter-button-wine", "index": 1},
        {"type": "filter-button-wine", "index": 2},
        {"type": "filter-button-wine", "index": 3},
    ]

    assert reset_restaurant_star_clicks(1, ids) is None
    assert reset_restaurant_star_clicks(2, ids) == [0, 0, 0]
    assert reset_restaurant_star_clicks(2, []) is None


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
            "location": ["data", 1, "below"],
            "params": {"value": RESTAURANT_TRACE_BELOW},
        },
        {
            "operation": "Assign",
            "location": ["data", 2, "visible"],
            "params": {"value": expected_visibility[1]},
        },
        {
            "operation": "Assign",
            "location": ["data", 2, "below"],
            "params": {"value": RESTAURANT_TRACE_BELOW},
        },
        {
            "operation": "Assign",
            "location": ["data", 3, "visible"],
            "params": {"value": expected_visibility[2]},
        },
        {
            "operation": "Assign",
            "location": ["data", 3, "below"],
            "params": {"value": RESTAURANT_TRACE_BELOW},
        },
    ]


def test_selected_wine_map_view_uses_appellation_on_first_selection(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    search_lookup = wine_search_lookup(records)
    selected_record = records[0]

    selected_view = selected_wine_map_view(
        selected_record.region,
        selected_record.feature_id,
        records,
        search_lookup,
    )
    expected_view = map_view_for_feature(selected_record.feature_id, search_lookup)

    assert selected_view == expected_view


def test_first_region_selection_builds_canonical_wine_patch(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    search_lookup = wine_search_lookup(records)
    expected_view = map_view_for_region("Bordeaux", records)

    patch = wine_navigation_patch(
        "Bordeaux",
        None,
        records,
        search_lookup,
    ).to_plotly_json()

    assert patch["operations"] == [
        {
            "operation": "Assign",
            "location": ["layout", "map", "uirevision"],
            "params": {"value": "wine-aoc-map-v1:Bordeaux:all"},
        },
        {
            "operation": "Assign",
            "location": ["layout", "map", "zoom"],
            "params": {"value": expected_view["zoom"]},
        },
        {
            "operation": "Assign",
            "location": ["layout", "map", "center"],
            "params": {"value": expected_view["center"]},
        },
    ]

    assert wine_navigation_command(
        "Bordeaux",
        None,
        records,
        search_lookup,
    ) == {
        "uirevision": "wine-aoc-map-v1:Bordeaux:all",
        "zoom": expected_view["zoom"],
        "center": expected_view["center"],
    }


def test_first_alsace_appellation_selection_builds_brand_patch(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    search_lookup = wine_search_lookup(records)
    brand = next(record for record in records if record.display_name == "Brand")
    expected_view = map_view_for_feature(brand.feature_id, search_lookup)

    patch = wine_navigation_patch(
        "Alsace",
        brand.feature_id,
        records,
        search_lookup,
    ).to_plotly_json()

    assert patch["operations"][0]["params"]["value"] == (
        f"wine-aoc-map-v1:Alsace:{brand.feature_id}"
    )
    assert patch["operations"][1]["params"]["value"] == expected_view["zoom"]
    assert patch["operations"][2]["params"]["value"] == expected_view["center"]


def test_delayed_appellation_navigation_cannot_override_current_region(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    search_lookup = wine_search_lookup(records)
    selected_region = records[0].region
    stale_record = next(
        record for record in records if record.region != selected_region
    )

    selected_view = selected_wine_map_view(
        selected_region,
        stale_record.feature_id,
        records,
        search_lookup,
    )

    assert selected_view == map_view_for_region(selected_region, records)


def test_selected_wine_map_view_uses_region_without_appellation(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    search_lookup = wine_search_lookup(records)

    selected_view = selected_wine_map_view(
        "Bordeaux",
        None,
        records,
        search_lookup,
    )

    assert selected_view == map_view_for_region("Bordeaux", records)


def test_wine_view_revision_changes_for_geographic_navigation():
    geography = {"region": "Bordeaux", "feature_id": None}

    assert wine_view_revision(geography) == "wine-aoc-map-v1:Bordeaux:all"


def test_manual_map_pan_and_zoom_persistence_stays_unchanged():
    existing_view = {"center": {"lat": 44.0, "lon": 1.0}, "zoom": 6}
    updated_view = map_view_from_relayout(
        {"map.center": {"lat": 45.5, "lon": 2.5}, "map.zoom": 8.5},
        existing_view,
    )

    assert updated_view == {"center": {"lat": 45.5, "lon": 2.5}, "zoom": 8.5}
    assert map_view_from_relayout({"autosize": True}, existing_view) is None
    assert map_view_from_relayout({}, existing_view) is None


def test_region_navigation_reset_overrides_stale_wine_view(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    search_lookup = wine_search_lookup(records)
    selected_region = records[0].region
    stale_record = next(
        record for record in records if record.region != selected_region
    )
    stale_geography = wine_geography_key(
        stale_record.region,
        stale_record.feature_id,
        search_lookup,
    )
    stale_view = {
        "center": {"lat": 43.0, "lon": 1.0},
        "zoom": 9,
        WINE_VIEW_GEOGRAPHY_KEY: stale_geography,
    }

    updated_view = updated_wine_view_store(
        {"wine-region-selector", "wine-map-graph"},
        {"map.center": stale_view["center"], "map.zoom": stale_view["zoom"]},
        selected_region,
        stale_record.feature_id,
        records,
        search_lookup,
        stale_view,
    )
    expected_view = map_view_for_region(selected_region, records)

    assert updated_view["center"] == expected_view["center"]
    assert updated_view["zoom"] == expected_view["zoom"]
    assert updated_view[WINE_VIEW_GEOGRAPHY_KEY] == {
        "region": selected_region,
        "feature_id": None,
    }


def test_stale_relayout_is_rejected_after_wine_geography_change(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    search_lookup = wine_search_lookup(records)
    selected_region = records[0].region
    previous_region = next(
        record.region for record in records if record.region != selected_region
    )
    stale_view = {
        "center": {"lat": 43.0, "lon": 1.0},
        "zoom": 9,
        WINE_VIEW_GEOGRAPHY_KEY: {
            "region": previous_region,
            "feature_id": None,
        },
    }

    updated_view = updated_wine_view_store(
        {"wine-map-graph"},
        {"map.center": stale_view["center"], "map.zoom": stale_view["zoom"]},
        selected_region,
        None,
        records,
        search_lookup,
        stale_view,
    )

    assert updated_view is None


def test_manual_relayout_is_preserved_for_current_wine_geography(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    search_lookup = wine_search_lookup(records)
    selected_region = records[0].region
    geography = {
        "region": selected_region,
        "feature_id": None,
    }
    existing_view = {
        "center": {"lat": 44.0, "lon": 2.0},
        "zoom": 7,
        WINE_VIEW_GEOGRAPHY_KEY: geography,
    }
    manual_view = {
        "map.center": {"lat": 44.5, "lon": 2.5},
        "map.zoom": 8,
    }

    updated_view = updated_wine_view_store(
        {"wine-map-graph"},
        manual_view,
        selected_region,
        None,
        records,
        search_lookup,
        existing_view,
    )

    assert updated_view == {
        "center": manual_view["map.center"],
        "zoom": manual_view["map.zoom"],
        WINE_VIEW_GEOGRAPHY_KEY: geography,
    }


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
    def __init__(self, content=None):
        self.requests = []
        self.chat = self
        self.completions = self
        self.content = content

    def create(self, **kwargs):
        self.requests.append(kwargs)
        region = kwargs["messages"][0]["content"].removeprefix("prompt:")
        content = self.content or json.dumps(
            {
                "summary": f"Generated regional content for {region}",
                "principal_grapes": ["Pinot Noir"],
                "supporting_grapes": [],
                "wine_styles": ["Red"],
                "key_facts": [],
                "renowned_estates": [],
                "editorial_note": f"Editorial note for {region}",
            }
        )
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
            "display_name": row["display_name"],
            "categorie": row["categorie"],
            "prompt_signals": row["prompt_signals"],
            "colour": row["colour"],
            "source_area_m2": row["source_area_m2"],
        }
        for row in rows
    }
    return rows, lookup


def _prompt_builder(region, appellation, prompt_signals):
    signals = ",".join(prompt_signals)
    return f"prompt:{region}:{appellation}:{signals}"


def test_wine_info_uses_appellation_specific_cache_for_different_aocs(data_boundary):
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
        f"wine_info_v3_{first_bourgogne['app']}_{first_region}",
        f"wine_info_v3_{second_bourgogne['app']}_{first_region}",
        f"wine_info_v3_{other_region['app']}_{other_parent_region}",
    ]
    assert [key for key, _ in cache.set_calls] == cache.get_calls
    assert all(isinstance(value["content"], dict) for _, value in cache.set_calls)
    assert len(openai_client.requests) == 3
    assert [
        request["messages"][0]["content"]
        for request in openai_client.requests
    ] == [
        (
            f"prompt:{first_region}:{first_bourgogne['app']}:"
            + ",".join(first_bourgogne["prompt_signals"])
        ),
        (
            f"prompt:{first_region}:{second_bourgogne['app']}:"
            + ",".join(second_bourgogne["prompt_signals"])
        ),
        (
            f"prompt:{other_parent_region}:{other_region['app']}:"
            + ",".join(other_region["prompt_signals"])
        ),
    ]
    assert request_limit.calls == 3

    assert isinstance(first_response[0], html.Div)
    assert isinstance(second_response[0], html.Div)
    assert isinstance(other_response[0], html.Div)
    assert first_response[2].children[0].children == first_region
    assert first_response[2].children[1].children.startswith(first_bourgogne["display_name"])
    assert second_response[2].children[0].children == first_region
    assert second_response[2].children[1].children.startswith(second_bourgogne["display_name"])
    assert other_response[2].children[0].children == other_parent_region
    assert other_response[2].children[1].children.startswith(other_region["display_name"])
    assert first_response[0].children[0].children != second_response[0].children[0].children
    assert other_response[0].children[0].children != first_response[0].children[0].children


def test_wine_info_uses_cached_response_without_openai_or_request_limit(feature_lookup):
    cache = FakeCache()
    cache.values["wine_info_v3_Known appellation protected designation_Bourgogne"] = {
        "content": {
            "summary": "Cached regional Bourgogne content",
            "editorial_note": "Cached editorial note",
        },
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

    assert isinstance(response[0], html.Div)
    assert response[0].style == {"--wine-region-accent": "#abcdef"}
    assert response[0].children[0].children == "Cached regional Bourgogne content"
    assert response[0].children[-1].children == "Cached editorial note"
    assert response[2].children[0].children == "Bourgogne"
    assert response[2].children[0].style == {"color": "#abcdef"}
    assert response[2].children[1].children == "Known appellation · 1800 hectares"
    assert openai_client.requests == []
    assert request_limit.calls == 0


def _wine_info_sections(rendered):
    return {
        child.children[0].children: child
        for child in rendered.children
        if isinstance(child, html.Section)
    }


def test_render_wine_info_styles_complete_sauternes_content():
    rendered = render_wine_info(
        {
            "summary": "Botrytised sweetness balanced by vivid acidity and long ageing potential.",
            "principal_grapes": ["Sémillon"],
            "supporting_grapes": ["Sauvignon Blanc", "Muscadelle"],
            "wine_styles": ["Sweet white"],
            "food_pairings": ["Foie gras", "Roquefort", "Tarte Tatin"],
            "key_facts": [
                {"label": "Climate", "text": "Autumn mists encourage noble rot."},
                {"label": "Harvest", "text": "Grapes are selected through successive passes."},
                {"label": "Incomplete"},
                "invalid",
            ],
            "renowned_estates": [
                "Château d’Yquem",
                "Château Rieussec",
                "Château Suduiraut",
                {"name": "Old response shape"},
            ],
            "editorial_note": "The best examples retain freshness across decades.",
        },
        "maroon",
    )

    assert isinstance(rendered, html.Div)
    assert rendered.className == "wine-info-content"
    assert rendered.style == {"--wine-region-accent": "maroon"}
    assert rendered.children[0].className == "wine-info-summary"
    sections = _wine_info_sections(rendered)
    assert list(sections) == [
        "Grape varieties / Cépages",
        "Styles",
        "Classic pairings",
        "Renowned estates",
        "Key facts",
    ]
    assert all(
        section.children[0].className == "wine-info-section-heading"
        for section in sections.values()
    )

    grape_pills = sections["Grape varieties / Cépages"].children[1].children
    assert [pill.children for pill in grape_pills] == [
        "Sémillon",
        "Sauvignon Blanc",
        "Muscadelle",
    ]
    assert grape_pills[0].className.endswith("--principal-grape")
    assert all(
        pill.className.endswith("--supporting-grape") for pill in grape_pills[1:]
    )

    style_pills = sections["Styles"].children[1].children
    assert style_pills[0].className.endswith("--style")
    pairing_pills = sections["Classic pairings"].children[1].children
    assert [pill.children for pill in pairing_pills] == [
        "Foie gras",
        "Roquefort",
        "Tarte Tatin",
    ]
    assert all(pill.className.endswith("--pairing") for pill in pairing_pills)

    fact_items = sections["Key facts"].children[1].children
    assert len(fact_items) == 2
    assert fact_items[0].className == "wine-info-key-fact"
    assert fact_items[0].children[0].children == "Climate:"
    assert fact_items[0].children[1] == " Autumn mists encourage noble rot."

    estate_list = sections["Renowned estates"].children[1]
    assert isinstance(estate_list, html.Ul)
    assert estate_list.className == "wine-info-estates"
    assert [item.children for item in estate_list.children] == [
        "Château d’Yquem",
        "Château Rieussec",
        "Château Suduiraut",
    ]
    assert rendered.children[-1].className == "wine-info-editorial-note"


def test_render_wine_info_hides_absent_chablis_sections():
    rendered = render_wine_info(
        {
            "summary": "A mineral, high-acid expression of Chardonnay.",
            "principal_grapes": ["Chardonnay"],
            "supporting_grapes": [],
            "wine_styles": ["Dry white"],
            "food_pairings": ["Oysters", "Grilled fish"],
            "key_facts": [],
            "renowned_estates": [],
            "editorial_note": "Site and vintage shape its expression.",
        },
        "#8b1e3f",
    )

    sections = _wine_info_sections(rendered)
    assert list(sections) == [
        "Grape varieties / Cépages",
        "Styles",
        "Classic pairings",
    ]
    grape_pills = sections["Grape varieties / Cépages"].children[1].children
    assert len(grape_pills) == 1
    assert grape_pills[0].className.endswith("--principal-grape")


def test_render_wine_info_omits_empty_optional_arrays():
    rendered = render_wine_info(
        {
            "summary": "Summary only.",
            "principal_grapes": [],
            "supporting_grapes": None,
            "wine_styles": [],
            "food_pairings": [],
            "key_facts": [],
            "renowned_estates": [],
            "editorial_note": "Final note.",
        },
        "maroon",
    )

    assert len(rendered.children) == 2
    assert all(isinstance(child, html.P) for child in rendered.children)


@pytest.mark.parametrize("model_content", ["not valid JSON", "[]"])
def test_wine_info_invalid_json_response_is_not_cached(feature_lookup, model_content):
    cache = FakeCache()
    request_limit = FakeRequestLimit()
    openai_client = FakeOpenAIClient(content=model_content)

    response = build_wine_info_response(
        _click("aoc-known"),
        feature_lookup,
        cache,
        openai_client,
        request_limit,
        prompt_builder=_prompt_builder,
    )

    assert response[0] == "We couldn't load the wine information. Please try again."
    assert response[2] is no_update
    assert cache.set_calls == []


def test_wine_search_callback_is_isolated_from_info_callback(app_module):
    callback_map = app_module.app.callback_map
    info_callbacks = [
        metadata
        for output, metadata in callback_map.items()
        if "llm-output-container.children" in output
    ]
    navigation_callbacks = [
        metadata
        for metadata in callback_map.values()
        if any(
            callback_input["id"] == "wine-appellation-search"
            and callback_input["property"] == "value"
            for callback_input in metadata["inputs"]
        )
        and "wine-map-graph" in str(metadata["output"])
    ]
    region_navigation_callbacks = [
        metadata
        for metadata in callback_map.values()
        if any(
            callback_input["id"] == "wine-region-selector"
            and callback_input["property"] == "value"
            for callback_input in metadata["inputs"]
        )
        and "wine-map-graph" in str(metadata["output"])
    ]

    assert len(info_callbacks) == 1
    assert info_callbacks[0]["inputs"] == [
        {"id": "wine-map-graph", "property": "clickData"}
    ]
    assert len(navigation_callbacks) == 1
    assert "llm-output-container" not in str(navigation_callbacks[0]["output"])
    assert {
        "id": "wine-map-ready",
        "property": "data",
    } in navigation_callbacks[0]["inputs"]
    assert len(region_navigation_callbacks) == 1
    assert "llm-output-container" not in str(region_navigation_callbacks[0]["output"])

    appellation_value_callbacks = [
        output
        for output in callback_map
        if "wine-appellation-search.value" in output
    ]
    assert appellation_value_callbacks == []


def test_wine_hover_callback_is_isolated_from_openai_info_callback(app_module):
    hover_callbacks = [
        metadata
        for output, metadata in app_module.app.callback_map.items()
        if "wine-map-hover-overlay.hidden" in output
    ]

    assert len(hover_callbacks) == 1
    assert hover_callbacks[0]["inputs"] == [
        {"id": "wine-map-graph", "property": "hoverData"}
    ]
    assert "llm-output-container" not in str(hover_callbacks[0]["output"])


def test_restaurant_star_reset_callback_is_driven_by_overlay_toggle(app_module):
    reset_callbacks = [
        metadata
        for output, metadata in app_module.app.callback_map.items()
        if "filter-button-wine" in output and output.endswith(".n_clicks")
    ]

    assert len(reset_callbacks) == 1
    assert reset_callbacks[0]["inputs"] == [
        {"id": "toggle-show-details-wine", "property": "n_clicks"}
    ]


def test_regional_outline_callback_uses_boolean_toggle(app_module):
    outline_callbacks = [
        metadata
        for metadata in app_module.app.callback_map.values()
        if metadata["inputs"] == [
            {"id": "toggle-regional-outlines-wine", "property": "n_clicks"}
        ]
    ]

    assert len(outline_callbacks) == 1
    assert "wine-map-graph.figure" in str(outline_callbacks[0]["output"])


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
