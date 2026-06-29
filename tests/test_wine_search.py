import pandas as pd
from shapely.geometry import MultiPolygon, Polygon

from app.utils.wine_search import (
    MAX_WINE_APPELLATION_ZOOM,
    MIN_WINE_APPELLATION_ZOOM,
    build_wine_search_index,
    map_view_for_feature,
    map_view_for_region,
    map_view_from_bounds,
    normalize_wine_search_text,
    wine_records_for_region,
    wine_region_options,
    wine_search_lookup,
    wine_search_options,
)


def _polygon(min_lon, min_lat, max_lon, max_lat):
    return Polygon(
        [
            (min_lon, min_lat),
            (max_lon, min_lat),
            (max_lon, max_lat),
            (min_lon, max_lat),
        ]
    )


def test_wine_search_normalisation_is_accent_insensitive():
    assert normalize_wine_search_text(" Saint-Émilion ") == "saint emilion"
    assert normalize_wine_search_text("Châteauneuf-du-Pape") == "chateauneuf du pape"


def test_wine_search_normalisation_handles_apostrophes_punctuation_and_hyphens():
    value = "L’Ancienne-Côte, du Pape!"

    assert normalize_wine_search_text(value) == "l ancienne cote du pape"


def test_wine_search_records_retain_stable_feature_ids():
    frame = pd.DataFrame(
        [
            {
                "feature_id": "aoc-stable",
                "app": "Pauillac",
                "region": "Bordeaux",
                "geometry": _polygon(-0.8, 45.1, -0.6, 45.3),
            }
        ]
    )

    records = build_wine_search_index(frame)

    assert records[0].feature_id == "aoc-stable"
    assert wine_search_options(records)[0]["value"] == "aoc-stable"


def test_wine_search_duplicate_display_labels_are_disambiguated():
    frame = pd.DataFrame(
        [
            {
                "feature_id": "aoc-one",
                "app": "Village",
                "region": "Bordeaux",
                "geometry": _polygon(0, 0, 1, 1),
            },
            {
                "feature_id": "aoc-two",
                "app": "Village",
                "region": "Rhône",
                "geometry": _polygon(2, 2, 3, 3),
            },
        ]
    )

    labels = {record.label for record in build_wine_search_index(frame)}

    assert labels == {"Village — Bordeaux", "Village — Rhône"}


def test_wine_search_exact_and_fuzzy_suggestions_resolve_to_feature_ids(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    lookup = wine_search_lookup(records)

    exact_options = wine_search_options(records, search_value="saint emilion")
    fuzzy_options = wine_search_options(records, search_value="chateaunef du pape")
    altenberg_options = wine_search_options(records, search_value="altenberg bergheim")

    exact_record = lookup[exact_options[0]["value"]]
    fuzzy_labels = {option["label"] for option in fuzzy_options}
    altenberg_labels = {option["label"] for option in altenberg_options}

    assert exact_record.app == "Saint-Emilion"
    assert "Châteauneuf-du-Pape" in fuzzy_labels
    assert any(
        option["label"] == "Châteauneuf-du-Pape"
        and "chateaunef du pape" in option["search"]
        for option in fuzzy_options
    )
    assert "Altenberg de Bergheim" in altenberg_labels


def test_wine_region_options_are_built_from_search_records(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    options = wine_region_options(records)

    assert {"label": "Bordeaux", "value": "Bordeaux"} in options
    assert {"label": "Rhône", "value": "Rhône"} in options
    assert options == sorted(options, key=lambda option: option["label"])


def test_wine_region_filter_scopes_appellation_records(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    bordeaux_records = wine_records_for_region(records, "Bordeaux")

    assert bordeaux_records
    assert {record.region for record in bordeaux_records} == {"Bordeaux"}
    assert wine_records_for_region(records, None) == records


def test_wine_polygon_bounds_produce_valid_center_and_zoom():
    view = map_view_from_bounds(_polygon(2.0, 43.0, 2.2, 43.2).bounds)

    assert view["center"] == {"lat": 43.1, "lon": 2.1}
    assert MIN_WINE_APPELLATION_ZOOM <= view["zoom"] <= MAX_WINE_APPELLATION_ZOOM


def test_wine_multipolygon_bounds_use_complete_geometry():
    geometry = MultiPolygon(
        [
            _polygon(0.0, 43.0, 0.2, 43.2),
            _polygon(2.0, 44.0, 2.2, 44.2),
        ]
    )

    view = map_view_from_bounds(geometry.bounds)

    assert view["center"] == {"lat": 43.6, "lon": 1.1}
    assert view["zoom"] < MAX_WINE_APPELLATION_ZOOM


def test_wine_very_small_bounds_respect_maximum_zoom():
    view = map_view_from_bounds((2.0, 43.0, 2.00001, 43.00001))

    assert view["zoom"] == MAX_WINE_APPELLATION_ZOOM


def test_wine_very_large_bounds_respect_minimum_zoom():
    view = map_view_from_bounds((-6.0, 41.0, 10.0, 51.0))

    assert view["zoom"] == MIN_WINE_APPELLATION_ZOOM


def test_wine_unknown_or_malformed_feature_ids_fail_safely(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    lookup = wine_search_lookup(records)

    assert map_view_for_feature("aoc-missing", lookup) is None
    assert map_view_for_feature(None, lookup) is None
    assert map_view_for_region("missing", records) is None
    assert map_view_for_region(None, records) is None
    assert map_view_from_bounds(("bad", 1, 2, 3)) is None


def test_wine_region_bounds_produce_wider_view_than_compact_appellation(data_boundary):
    records = build_wine_search_index(data_boundary.wine_df)
    region_view = map_view_for_region("Bordeaux", records)
    appellation = next(record for record in records if record.app == "Pauillac")
    appellation_view = map_view_for_feature(
        appellation.feature_id,
        wine_search_lookup(records),
    )

    assert region_view["zoom"] < appellation_view["zoom"]
    assert MIN_WINE_APPELLATION_ZOOM <= region_view["zoom"] <= MAX_WINE_APPELLATION_ZOOM
