#!/usr/bin/env python3
"""Merge saved AOC simplification metrics into the tracked region policy CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parent

IDENTITY_COLUMNS = [
    "region",
    "region_slug",
    "status",
    "preferred_run_id",
    "overlap_strategy",
    "overlap_clip_enabled",
    "buffer_dist_m",
    "simplify_m",
]
SIZE_COLUMNS = [
    "old_size_mb",
    "raw_size_mb",
    "closed_size_mb",
    "candidate_size_mb",
    "candidate_size_to_old",
    "candidate_size_to_raw",
]
AREA_COLUMNS = [
    "old_area_m2",
    "raw_area_m2",
    "closed_area_m2",
    "candidate_area_m2",
    "candidate_area_to_old",
    "candidate_area_to_raw",
    "closed_area_to_raw",
    "candidate_area_change_pct_from_raw",
    "candidate_area_to_pre_partition_union",
]
OVERLAP_COLUMNS = [
    "fully_covered_app_count",
    "partially_reduced_app_count",
    "maximum_removed_percent",
    "overlap_area_before_m2",
    "overlap_area_after_m2",
    "residual_overlap_ratio",
    "residual_overlap_within_tolerance",
]
FRAGMENTATION_COLUMNS = [
    "old_part_count",
    "raw_part_count",
    "closed_part_count",
    "candidate_part_count",
    "candidate_parts_to_old",
    "candidate_parts_to_raw",
]
COORDINATE_COLUMNS = [
    "old_coordinate_count",
    "raw_coordinate_count",
    "closed_coordinate_count",
    "candidate_coordinate_count",
    "candidate_coordinates_to_old",
    "candidate_coordinates_to_raw",
]
FEATURE_COLUMNS = [
    "old_feature_count",
    "raw_feature_count",
    "candidate_feature_count",
    "source_app_count",
    "retained_app_count",
    "dropped_app_count",
]
VALIDITY_COLUMNS = [
    "raw_invalid_geometry_count",
    "candidate_invalid_geometry_count",
    "candidate_empty_geometry_count",
]
HUMAN_COLUMNS = [
    "size_assessment",
    "area_assessment",
    "fragmentation_assessment",
    "visual_notes",
    "decision_notes",
    "next_experiment",
]
FIELDNAMES = (
    IDENTITY_COLUMNS
    + SIZE_COLUMNS
    + AREA_COLUMNS
    + OVERLAP_COLUMNS
    + FRAGMENTATION_COLUMNS
    + COORDINATE_COLUMNS
    + FEATURE_COLUMNS
    + VALIDITY_COLUMNS
    + HUMAN_COLUMNS
)

REQUIRED_STAGES = {
    "old_app_geometry",
    "raw_selected_aoc_geometry",
    "morphologically_closed",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="close500")
    parser.add_argument(
        "--policy",
        type=Path,
        default=EXPERIMENT_ROOT / "region_policy.csv",
    )
    return parser.parse_args()


def nested(mapping: dict[str, Any], *keys: str) -> Any:
    value: Any = mapping
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def as_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def formatted(value: Any, places: int) -> str:
    number = as_number(value)
    return "" if number is None else f"{number:.{places}f}"


def whole_number(value: Any) -> str:
    number = as_number(value)
    return "" if number is None else str(round(number))


def ratio(numerator: Any, denominator: Any, places: int = 4) -> str:
    numerator_number = as_number(numerator)
    denominator_number = as_number(denominator)
    if numerator_number is None or denominator_number in (None, 0):
        return ""
    return f"{numerator_number / denominator_number:.{places}f}"


def region_name(metrics: dict[str, Any], slug: str) -> str:
    possible_names = (
        metrics.get("region"),
        nested(metrics, "metadata", "region"),
        nested(metrics, "parameters", "region"),
        nested(metrics, "config", "region"),
    )
    for name in possible_names:
        if isinstance(name, str) and name.strip():
            return name.strip()
    return slug.replace("_", " ").title()


def boolean_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower()
    return ""


def fully_covered_app_count(operation_report: dict[str, Any]) -> str:
    count = operation_report.get("fully_covered_app_count")
    if count is not None:
        return whole_number(count)
    names = operation_report.get("fully_covered_app_names")
    return str(len(names)) if isinstance(names, list) else ""


def count_dropped_apps(operation_report: dict[str, Any]) -> str:
    fully_covered_count = fully_covered_app_count(operation_report)
    if fully_covered_count:
        return fully_covered_count
    dropped_names = operation_report.get("dropped_app_names")
    if isinstance(dropped_names, list):
        return str(len(dropped_names))
    source = as_number(operation_report.get("source_app_count"))
    retained = as_number(operation_report.get("retained_app_count"))
    if source is None or retained is None:
        return ""
    return str(round(source - retained))


def extract_metrics(metrics: dict[str, Any]) -> dict[str, str]:
    stages = metrics["stages"]
    old = stages["old_app_geometry"]
    raw = stages["raw_selected_aoc_geometry"]
    closed = stages["morphologically_closed"]
    candidate = stages.get("final_candidate")
    if not isinstance(candidate, dict):
        candidate = stages["simplified_final_candidate"]
    operation_report = metrics.get("partition") or metrics.get("clipping") or {}

    old_size = old.get("approx_geojson_size_mb")
    raw_size = raw.get("approx_geojson_size_mb")
    closed_size = closed.get("approx_geojson_size_mb")
    candidate_size = metrics.get("candidate_file_size_mb")
    if candidate_size is None:
        candidate_size = candidate.get("approx_geojson_size_mb")

    old_area = old.get("area_m2_epsg_2154")
    raw_area = raw.get("area_m2_epsg_2154")
    closed_area = closed.get("area_m2_epsg_2154")
    candidate_area = candidate.get("area_m2_epsg_2154")
    overlap_area_before = operation_report.get("overlap_area_before_m2")
    if overlap_area_before is None:
        overlap_area_before = nested(
            metrics, "overlap", "before_partition", "overlap_area_m2"
        )
    overlap_area_after = operation_report.get("overlap_area_after_m2")
    if overlap_area_after is None:
        overlap_area_after = nested(
            metrics, "overlap", "after_partition", "overlap_area_m2"
        )
    pre_partition_union_area = nested(
        metrics, "overlap", "before_partition", "union_area_m2"
    )
    residual_within_tolerance = nested(
        metrics, "overlap", "residual_overlap_within_tolerance"
    )
    if residual_within_tolerance is None:
        residual_within_tolerance = nested(
            metrics, "final_validation", "residual_overlap_within_tolerance"
        )

    old_parts = old.get("polygon_part_count")
    raw_parts = raw.get("polygon_part_count")
    closed_parts = closed.get("polygon_part_count")
    candidate_parts = candidate.get("polygon_part_count")

    old_coordinates = old.get("coordinate_count")
    raw_coordinates = raw.get("coordinate_count")
    closed_coordinates = closed.get("coordinate_count")
    candidate_coordinates = candidate.get("coordinate_count")

    raw_area_number = as_number(raw_area)
    candidate_area_number = as_number(candidate_area)
    area_change = None
    if raw_area_number not in (None, 0) and candidate_area_number is not None:
        area_change = ((candidate_area_number / raw_area_number) - 1) * 100

    return {
        "old_size_mb": formatted(old_size, 4),
        "raw_size_mb": formatted(raw_size, 4),
        "closed_size_mb": formatted(closed_size, 4),
        "candidate_size_mb": formatted(candidate_size, 4),
        "candidate_size_to_old": ratio(candidate_size, old_size),
        "candidate_size_to_raw": ratio(candidate_size, raw_size),
        "old_area_m2": whole_number(old_area),
        "raw_area_m2": whole_number(raw_area),
        "closed_area_m2": whole_number(closed_area),
        "candidate_area_m2": whole_number(candidate_area),
        "candidate_area_to_old": ratio(candidate_area, old_area),
        "candidate_area_to_raw": ratio(candidate_area, raw_area),
        "closed_area_to_raw": ratio(closed_area, raw_area),
        "candidate_area_change_pct_from_raw": formatted(area_change, 2),
        "candidate_area_to_pre_partition_union": ratio(
            candidate_area, pre_partition_union_area
        ),
        "overlap_strategy": str(
            metrics.get("overlap_strategy") or operation_report.get("strategy") or ""
        ),
        "fully_covered_app_count": fully_covered_app_count(operation_report),
        "partially_reduced_app_count": whole_number(
            operation_report.get("partially_reduced_app_count")
        ),
        "maximum_removed_percent": formatted(
            operation_report.get("maximum_removed_percent"), 2
        ),
        "overlap_area_before_m2": whole_number(overlap_area_before),
        "overlap_area_after_m2": formatted(overlap_area_after, 4),
        "residual_overlap_ratio": ratio(
            overlap_area_after, overlap_area_before, places=12
        ),
        "residual_overlap_within_tolerance": boolean_text(
            residual_within_tolerance
        ),
        "old_part_count": whole_number(old_parts),
        "raw_part_count": whole_number(raw_parts),
        "closed_part_count": whole_number(closed_parts),
        "candidate_part_count": whole_number(candidate_parts),
        "candidate_parts_to_old": ratio(candidate_parts, old_parts),
        "candidate_parts_to_raw": ratio(candidate_parts, raw_parts),
        "old_coordinate_count": whole_number(old_coordinates),
        "raw_coordinate_count": whole_number(raw_coordinates),
        "closed_coordinate_count": whole_number(closed_coordinates),
        "candidate_coordinate_count": whole_number(candidate_coordinates),
        "candidate_coordinates_to_old": ratio(candidate_coordinates, old_coordinates),
        "candidate_coordinates_to_raw": ratio(candidate_coordinates, raw_coordinates),
        "old_feature_count": whole_number(old.get("feature_count")),
        "raw_feature_count": whole_number(raw.get("feature_count")),
        "candidate_feature_count": whole_number(candidate.get("feature_count")),
        "source_app_count": whole_number(operation_report.get("source_app_count")),
        "retained_app_count": whole_number(
            operation_report.get("retained_app_count")
        ),
        "dropped_app_count": count_dropped_apps(operation_report),
        "raw_invalid_geometry_count": whole_number(raw.get("invalid_geometry_count")),
        "candidate_invalid_geometry_count": whole_number(
            candidate.get("invalid_geometry_count")
        ),
        "candidate_empty_geometry_count": whole_number(
            candidate.get("empty_geometry_count")
        ),
    }


def read_policy(policy_path: Path) -> dict[str, dict[str, str]]:
    with policy_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    policies: dict[str, dict[str, str]] = {}
    for row in rows:
        slug = row.get("region_slug", "").strip()
        if not slug:
            raise ValueError("Every policy row must have a region_slug")
        if slug in policies:
            raise ValueError(f"Duplicate region_slug in policy: {slug}")
        policies[slug] = {field: row.get(field, "") for field in FIELDNAMES}
    return policies


def read_metrics(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, f"{path}: {error}"
    if not isinstance(data, dict):
        return None, f"{path}: top-level JSON value is not an object"
    stages = data.get("stages")
    if not isinstance(stages, dict):
        return None, f"{path}: missing stages object"
    missing_stages = sorted(REQUIRED_STAGES - stages.keys())
    if missing_stages:
        return None, f"{path}: missing stages: {', '.join(missing_stages)}"
    if any(not isinstance(stages[name], dict) for name in REQUIRED_STAGES):
        return None, f"{path}: one or more required stages are not objects"
    candidate = stages.get("final_candidate") or stages.get(
        "simplified_final_candidate"
    )
    if not isinstance(candidate, dict):
        return None, f"{path}: missing final candidate stage"
    return data, None


def main() -> int:
    args = parse_args()
    policy_path = args.policy.resolve()
    output_root = EXPERIMENT_ROOT / "outputs"
    metric_paths = sorted(output_root.glob(f"*/{args.run_id}/metrics.json"))
    policies = read_policy(policy_path)
    updated_slugs: set[str] = set()
    problems: list[str] = []

    for metric_path in metric_paths:
        metrics, problem = read_metrics(metric_path)
        if problem is not None:
            problems.append(problem)
            continue
        assert metrics is not None
        slug = metric_path.parent.parent.name
        row = policies.setdefault(
            slug,
            {field: "" for field in FIELDNAMES},
        )
        row["region"] = row["region"] or region_name(metrics, slug)
        row["region_slug"] = slug
        row["status"] = row["status"] or "benchmarking"
        row["preferred_run_id"] = row["preferred_run_id"] or args.run_id
        row.update(extract_metrics(metrics))
        if args.run_id == "close500_smallest_wins":
            row["preferred_run_id"] = "close500_smallest_wins"
            row["overlap_strategy"] = "smallest-wins"
            row["buffer_dist_m"] = "500"
            row["simplify_m"] = "250"
        elif args.run_id == "close500":
            row["overlap_strategy"] = "none"
            row["overlap_clip_enabled"] = row["overlap_clip_enabled"] or "false"
            row["buffer_dist_m"] = "500"
            row["simplify_m"] = "250"
        updated_slugs.add(slug)

    policy_path.parent.mkdir(parents=True, exist_ok=True)
    with policy_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for slug in sorted(policies):
            writer.writerow(policies[slug])

    missing_slugs = sorted(set(policies) - updated_slugs)
    print(f"Metrics files found: {len(metric_paths)}")
    print(f"Rows updated: {len(updated_slugs)}")
    print(
        "Rows without usable metrics: "
        + (", ".join(missing_slugs) if missing_slugs else "none")
    )
    print(f"Malformed/incomplete metrics files: {len(problems)}")
    for problem in problems:
        print(f"  - {problem}")
    print(f"Policy written: {policy_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
