from dataclasses import dataclass
import math
import re

from fuzzywuzzy import fuzz
from unidecode import unidecode


MIN_WINE_APPELLATION_ZOOM = 5.0
MAX_WINE_APPELLATION_ZOOM = 11.5
DEFAULT_SEARCH_OPTION_LIMIT = 30
REGION_SELECTION_ZOOM_BOOST = 0.75


@dataclass(frozen=True)
class WineSearchRecord:
    feature_id: str
    app: str
    region: str
    label: str
    search_text: str
    bounds: tuple[float, float, float, float]


def normalize_wine_search_text(value) -> str:
    text = unidecode(str(value or "")).casefold()
    text = re.sub(r"['`´’‘‛ʼ]", " ", text)
    text = re.sub(r"[-‐‑‒–—―/.,;:!?()\[\]{}&+]", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build_wine_search_index(wine_df) -> list[WineSearchRecord]:
    app_counts = wine_df["app"].astype(str).value_counts().to_dict()
    records = []

    for row in wine_df[["feature_id", "app", "region", "geometry"]].itertuples(index=False):
        app = str(row.app)
        region = str(row.region)
        feature_id = str(row.feature_id)
        label = f"{app} — {region}" if app_counts.get(app, 0) > 1 else app
        search_text = normalize_wine_search_text(f"{app} {region}")
        records.append(
            WineSearchRecord(
                feature_id=feature_id,
                app=app,
                region=region,
                label=label,
                search_text=search_text,
                bounds=tuple(float(value) for value in row.geometry.bounds),
            )
        )

    return sorted(records, key=lambda record: normalize_wine_search_text(record.label))


def wine_search_lookup(records: list[WineSearchRecord]) -> dict[str, WineSearchRecord]:
    return {record.feature_id: record for record in records}


def wine_region_options(records: list[WineSearchRecord]) -> list[dict[str, str]]:
    return [
        {"label": region, "value": region}
        for region in sorted({record.region for record in records})
    ]


def wine_records_for_region(records: list[WineSearchRecord], region) -> list[WineSearchRecord]:
    if not isinstance(region, str) or not region:
        return records
    return [record for record in records if record.region == region]


def wine_search_option(record: WineSearchRecord, search_alias: str | None = None) -> dict[str, str]:
    search_text = record.search_text
    if search_alias:
        search_text = f"{search_text} {search_alias}"

    return {
        "label": record.label,
        "value": record.feature_id,
        "search": search_text,
    }


def wine_search_options(
    records: list[WineSearchRecord],
    search_value=None,
    selected_feature_id=None,
    limit: int = DEFAULT_SEARCH_OPTION_LIMIT,
) -> list[dict[str, str]]:
    selected_feature_id = selected_feature_id if isinstance(selected_feature_id, str) else None
    normalized_query = normalize_wine_search_text(search_value)

    if not normalized_query:
        return [wine_search_option(record) for record in records]

    tokens = normalized_query.split()
    exact_records = [
        record
        for record in records
        if normalized_query in record.search_text
        or all(token in record.search_text for token in tokens)
    ]
    exact_records = sorted(
        exact_records,
        key=lambda record: (
            _exact_match_rank(record, normalized_query, tokens),
            normalize_wine_search_text(record.label),
        ),
    )

    ranked_records = list(exact_records)
    ranked_ids = {record.feature_id for record in ranked_records}
    records_by_id = {record.feature_id: record for record in records}

    if len(ranked_records) < limit:
        fuzzy_matches = sorted(
            (
                (_fuzzy_record_score(normalized_query, record), record)
                for record in records
                if record.feature_id not in ranked_ids
            ),
            key=lambda match: (
                -match[0],
                normalize_wine_search_text(match[1].label),
            ),
        )
        for score, record in fuzzy_matches:
            if score < _fuzzy_score_threshold(normalized_query):
                continue
            ranked_records.append(record)
            ranked_ids.add(record.feature_id)
            if len(ranked_records) >= limit:
                break

    selected_record = None
    if selected_feature_id and selected_feature_id not in ranked_ids:
        selected_record = records_by_id.get(selected_feature_id)
        if selected_record is not None:
            ranked_records.append(selected_record)

    if selected_record is not None and len(ranked_records) > limit:
        return [
            wine_search_option(record, normalized_query)
            for record in [*ranked_records[:limit - 1], selected_record]
        ]

    return [
        wine_search_option(record, normalized_query)
        for record in ranked_records[:limit]
    ]


def _fuzzy_score_threshold(normalized_query: str) -> int:
    if len(normalized_query) <= 5:
        return 82
    if len(normalized_query) <= 10:
        return 76
    return 70


def _fuzzy_record_score(normalized_query: str, record: WineSearchRecord) -> int:
    app_text = normalize_wine_search_text(record.app)
    score = max(
        fuzz.ratio(normalized_query, app_text),
        fuzz.token_sort_ratio(normalized_query, app_text),
        fuzz.token_set_ratio(normalized_query, app_text),
    )

    length_gap = abs(len(normalized_query) - len(app_text))
    partial_score = fuzz.partial_ratio(normalized_query, app_text)
    if partial_score >= 84 and length_gap <= max(4, len(normalized_query) // 2):
        score = max(score, partial_score)

    return score


def _exact_match_rank(
    record: WineSearchRecord,
    normalized_query: str,
    tokens: list[str],
) -> int:
    app_text = normalize_wine_search_text(record.app)
    if app_text == normalized_query:
        return 0
    if app_text.startswith(normalized_query):
        return 1
    if normalized_query in app_text:
        return 2
    if all(token in app_text for token in tokens):
        return 3
    return 4


def map_view_from_bounds(
    bounds,
    min_zoom: float = MIN_WINE_APPELLATION_ZOOM,
    max_zoom: float = MAX_WINE_APPELLATION_ZOOM,
) -> dict | None:
    try:
        min_lon, min_lat, max_lon, max_lat = [float(value) for value in bounds]
    except (TypeError, ValueError):
        return None

    values = (min_lon, min_lat, max_lon, max_lat)
    if not all(math.isfinite(value) for value in values):
        return None
    if max_lon < min_lon or max_lat < min_lat:
        return None

    center = {
        "lat": (min_lat + max_lat) / 2,
        "lon": (min_lon + max_lon) / 2,
    }

    lon_span = max(max_lon - min_lon, 0.0001)
    lat_span = max(max_lat - min_lat, 0.0001)
    padded_span = max(lon_span, lat_span * 1.45) * 1.35
    padded_span = max(padded_span, 0.008)
    zoom = math.log2(360 / padded_span) - 1.1
    zoom = min(max(zoom, min_zoom), max_zoom)

    return {
        "center": {
            "lat": round(center["lat"], 6),
            "lon": round(center["lon"], 6),
        },
        "zoom": round(zoom, 2),
    }


def map_view_for_feature(feature_id, search_lookup) -> dict | None:
    if not isinstance(feature_id, str):
        return None

    record = search_lookup.get(feature_id)
    if record is None:
        return None

    return map_view_from_bounds(record.bounds)


def map_view_for_region(region, records: list[WineSearchRecord]) -> dict | None:
    region_records = wine_records_for_region(records, region)
    if not isinstance(region, str) or not region_records:
        return None

    min_lons, min_lats, max_lons, max_lats = zip(
        *(record.bounds for record in region_records)
    )
    view = map_view_from_bounds(
        (
            min(min_lons),
            min(min_lats),
            max(max_lons),
            max(max_lats),
        )
    )
    if view is None:
        return None

    view["zoom"] = min(view["zoom"] + REGION_SELECTION_ZOOM_BOOST, MAX_WINE_APPELLATION_ZOOM)
    return view
