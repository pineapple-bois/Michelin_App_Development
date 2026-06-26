"""Generate development-only Wine-region GeoJSON candidates.

This is a local generation tool. It writes only under
``Development/WineData/generated/candidates`` and never promotes data into the
live app.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import make_valid
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon


os.environ.setdefault("OGR_GEOJSON_MAX_OBJ_SIZE", "0")

HERE = Path(__file__).resolve().parent
WINE_DATA = HERE / "WineData"
DEFAULT_SOURCE = WINE_DATA / "aoc_regions.gpkg"
DEFAULT_OUTPUT_DIR = WINE_DATA / "generated" / "candidates"
METRIC_CRS = "EPSG:2154"
EXPORT_CRS = "EPSG:4326"
EXPECTED_REGIONS = [
    "Alsace",
    "Bordeaux",
    "Bourgogne",
    "Corse",
    "Dordogne",
    "Jura",
    "Languedoc-Roussillon",
    "Loire",
    "Provence",
    "Rhône",
    "Savoie",
    "Sud-Ouest",
]
DEFAULT_SIMPLIFICATION_TOLERANCES_M = [500, 1000, 2500, 5000]
REQUIRED_COLUMNS = {"region", "app", "colour", "geometry"}
STRATEGIES = {
    "dissolved-region-raw": "Repair, project to EPSG:2154, dissolve by region, export EPSG:4326.",
    "dissolved-region-simplified": (
        "Repair, project to EPSG:2154, dissolve by region, simplify with "
        "preserve_topology=True, export EPSG:4326."
    ),
}
INDEX_COLUMNS = [
    "candidate_name",
    "strategy",
    "tolerance_m",
    "output_path",
    "file_size_bytes",
    "file_size_mb",
    "feature_count",
    "region_count",
    "geometry_type_counts",
    "invalid_geometry_count",
    "empty_geometry_count",
    "coordinate_count",
    "geometry_part_count",
    "total_area_m2",
    "area_retained_pct_vs_dissolved_raw",
    "minx",
    "miny",
    "maxx",
    "maxy",
    "regions_present",
    "missing_regions",
    "generated_at",
]


def display_path(path):
    path = Path(path)
    try:
        return str(path.resolve().relative_to(HERE))
    except ValueError:
        return str(path)


def deterministic_generated_at(source_path):
    """Use source mtime so reruns are deterministic for unchanged source data."""
    source_mtime = Path(source_path).stat().st_mtime
    return (
        datetime.fromtimestamp(source_mtime, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def polygonal_parts(geometry):
    if geometry is None or geometry.is_empty:
        return []
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    if isinstance(geometry, GeometryCollection):
        parts = []
        for part in geometry.geoms:
            parts.extend(polygonal_parts(part))
        return parts
    return []


def polygonal_geometry(geometry):
    if isinstance(geometry, (Polygon, MultiPolygon)):
        return geometry

    parts = polygonal_parts(geometry)
    if not parts:
        return geometry
    if len(parts) == 1:
        return parts[0]
    return MultiPolygon(parts)


def repair_geometry(geometry):
    if geometry is None or geometry.is_empty:
        return geometry

    repaired = geometry if geometry.is_valid else make_valid(geometry)
    repaired = polygonal_geometry(repaired)

    if repaired is not None and not repaired.is_empty and not repaired.is_valid:
        repaired = repaired.buffer(0)
        repaired = polygonal_geometry(repaired)

    if repaired is not None and not repaired.is_empty and not repaired.is_valid:
        repaired = make_valid(repaired)
        repaired = polygonal_geometry(repaired)

    return repaired


def repair_invalid_geometries(frame):
    repaired = frame.copy()
    invalid_mask = ~repaired.geometry.is_valid
    invalid_count = int(invalid_mask.sum())
    print(f"Repairing {invalid_count} invalid geometries.", flush=True)
    if invalid_count:
        repaired.loc[invalid_mask, "geometry"] = repaired.loc[invalid_mask, "geometry"].apply(
            repair_geometry
        )
    return repaired[repaired.geometry.notna() & ~repaired.geometry.is_empty].copy()


def geometry_coordinate_count(geometry):
    if geometry is None or geometry.is_empty:
        return 0
    geom_type = geometry.geom_type
    if geom_type == "Polygon":
        return len(geometry.exterior.coords) + sum(len(ring.coords) for ring in geometry.interiors)
    if geom_type == "MultiPolygon":
        return sum(geometry_coordinate_count(polygon) for polygon in geometry.geoms)
    if geom_type in {"LineString", "LinearRing"}:
        return len(geometry.coords)
    if geom_type == "MultiLineString":
        return sum(len(part.coords) for part in geometry.geoms)
    if geom_type == "Point":
        return 1
    if geom_type == "MultiPoint":
        return len(geometry.geoms)
    if geom_type == "GeometryCollection":
        return sum(geometry_coordinate_count(part) for part in geometry.geoms)
    return 0


def geometry_part_count(geometry):
    if geometry is None or geometry.is_empty:
        return 0
    geom_type = geometry.geom_type
    if geom_type == "Polygon":
        return 1
    if geom_type == "MultiPolygon":
        return len(geometry.geoms)
    if geom_type == "GeometryCollection":
        return sum(geometry_part_count(part) for part in geometry.geoms)
    return 0


def sorted_region_frame(frame):
    order = {region: index for index, region in enumerate(EXPECTED_REGIONS)}
    sorted_frame = frame.copy()
    sorted_frame["_region_order"] = sorted_frame["region"].map(order).fillna(len(order)).astype(int)
    sorted_frame = sorted_frame.sort_values(["_region_order", "region"], kind="mergesort")
    return sorted_frame.drop(columns=["_region_order"]).reset_index(drop=True)


def load_source(source_path):
    source_path = Path(source_path)
    if not source_path.exists():
        raise SystemExit(f"Source data not found: {display_path(source_path)}")

    print(f"Reading source: {display_path(source_path)}", flush=True)
    frame = gpd.read_file(source_path, engine="pyogrio")
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise SystemExit("Source is missing required columns: " + ", ".join(missing))
    if frame.crs is None:
        raise SystemExit(f"Source CRS is missing; expected {EXPORT_CRS}")
    if frame.crs.to_epsg() != 4326:
        raise SystemExit(f"Source CRS is {frame.crs}; expected EPSG:4326")

    frame = frame[["region", "app", "colour", "geometry"]].copy()
    return frame.sort_values(["region", "app"], kind="mergesort").reset_index(drop=True)


def build_dissolved_regions(source_frame):
    repaired = repair_invalid_geometries(source_frame)

    print(f"Projecting source to {METRIC_CRS}.", flush=True)
    working = repaired.to_crs(METRIC_CRS)
    working["app_label"] = working["region"]
    working = working.sort_values(["region", "app"], kind="mergesort").reset_index(drop=True)

    print("Dissolving repaired AOC geometries by region/app/colour.", flush=True)
    dissolved = working.dissolve(
        by=["region", "app_label", "colour"],
        as_index=False,
        aggfunc={"app": "count"},
    ).rename(columns={"app": "aoc_count", "app_label": "app"})

    dissolved = sorted_region_frame(dissolved)
    print("Repairing dissolved region geometries.", flush=True)
    dissolved["geometry"] = dissolved.geometry.apply(repair_geometry)
    dissolved = dissolved[["region", "app", "colour", "aoc_count", "geometry"]]
    dissolved = dissolved[dissolved.geometry.notna() & ~dissolved.geometry.is_empty].copy()
    return sorted_region_frame(dissolved)


def candidate_from_dissolved(dissolved, tolerance_m=None):
    candidate = dissolved.copy()
    if tolerance_m is not None:
        print(f"Simplifying dissolved regions at {tolerance_m} m.", flush=True)
        candidate["geometry"] = candidate.geometry.simplify(
            tolerance_m,
            preserve_topology=True,
        )
        print("Repairing simplified region geometries.", flush=True)
        candidate["geometry"] = candidate.geometry.apply(repair_geometry)

    candidate = candidate[candidate.geometry.notna() & ~candidate.geometry.is_empty].copy()
    return sorted_region_frame(candidate)


def write_geojson(frame_metric, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    print(f"Writing {display_path(output_path)}.", flush=True)
    export_frame = frame_metric.to_crs(EXPORT_CRS)
    invalid_count = int((~export_frame.geometry.is_valid).sum())
    if invalid_count:
        print(f"Repairing {invalid_count} geometries after reprojection.", flush=True)
        export_frame = repair_invalid_geometries(export_frame)

    export_frame = sorted_region_frame(export_frame)
    export_frame.to_file(output_path, driver="GeoJSON")
    return output_path


def percent_retained(current, baseline):
    if not baseline:
        return None
    return round((float(current) / float(baseline)) * 100, 3)


def calculate_metrics(output_path, candidate_name, strategy, tolerance_m, raw_area_m2, generated_at):
    output_path = Path(output_path)
    frame = gpd.read_file(output_path, engine="pyogrio")
    metric_frame = frame.to_crs(METRIC_CRS)
    minx, miny, maxx, maxy = [float(value) for value in frame.total_bounds]
    regions_present = [region for region in EXPECTED_REGIONS if region in set(frame["region"])]
    unexpected_regions = sorted(set(frame["region"]).difference(EXPECTED_REGIONS))
    regions_present.extend(unexpected_regions)

    geometry_type_counts = {
        str(key): int(value)
        for key, value in frame.geometry.geom_type.value_counts().sort_index().items()
    }
    total_area_m2 = float(metric_frame.geometry.area.sum())

    return {
        "candidate_name": candidate_name,
        "strategy": strategy,
        "tolerance_m": tolerance_m,
        "output_path": display_path(output_path),
        "file_size_bytes": int(output_path.stat().st_size),
        "file_size_mb": round(output_path.stat().st_size / 1024**2, 3),
        "feature_count": int(len(frame)),
        "region_count": int(frame["region"].nunique()),
        "geometry_type_counts": geometry_type_counts,
        "invalid_geometry_count": int((~frame.geometry.is_valid).sum()),
        "empty_geometry_count": int(frame.geometry.is_empty.sum()),
        "coordinate_count": int(frame.geometry.apply(geometry_coordinate_count).sum()),
        "geometry_part_count": int(frame.geometry.apply(geometry_part_count).sum()),
        "total_area_m2": total_area_m2,
        "area_retained_pct_vs_dissolved_raw": percent_retained(total_area_m2, raw_area_m2),
        "minx": minx,
        "miny": miny,
        "maxx": maxx,
        "maxy": maxy,
        "regions_present": regions_present,
        "missing_regions": [region for region in EXPECTED_REGIONS if region not in set(frame["region"])],
        "generated_at": generated_at,
    }


def csv_ready(record):
    csv_record = record.copy()
    for key in ["geometry_type_counts", "regions_present", "missing_regions"]:
        csv_record[key] = json.dumps(csv_record[key], ensure_ascii=False, sort_keys=True)
    return csv_record


def read_existing_index(index_json):
    if not Path(index_json).exists():
        return []
    with Path(index_json).open(encoding="utf-8") as handle:
        records = json.load(handle)
    if not isinstance(records, list):
        raise SystemExit(f"Existing index is not a list: {display_path(index_json)}")
    return records


def write_candidate_index(records, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index_csv = output_dir / "index.csv"
    index_json = output_dir / "index.json"

    ordered_records = sorted(records, key=candidate_index_sort_key)
    csv_records = [csv_ready(record) for record in ordered_records]
    pd.DataFrame(csv_records, columns=INDEX_COLUMNS).to_csv(index_csv, index=False)
    index_json.write_text(
        json.dumps(ordered_records, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return index_csv, index_json


def candidate_index_sort_key(record):
    if record["candidate_name"] == "dissolved_region_raw":
        return (0, 0, record["candidate_name"])
    if record["strategy"] == "dissolved-region-simplified":
        return (1, int(record["tolerance_m"]), record["candidate_name"])
    return (2, int(record["tolerance_m"]), record["candidate_name"])


def update_candidate_index(new_records, output_dir):
    output_dir = Path(output_dir)
    index_json = output_dir / "index.json"
    existing = read_existing_index(index_json)
    replacement_names = {record["candidate_name"] for record in new_records}
    merged = [record for record in existing if record.get("candidate_name") not in replacement_names]
    merged.extend(new_records)
    return write_candidate_index(merged, output_dir)


def validate_record(record):
    errors = []
    warnings = []
    if record["feature_count"] != len(EXPECTED_REGIONS):
        errors.append(f"{record['candidate_name']} has {record['feature_count']} features")
    if record["region_count"] != len(EXPECTED_REGIONS):
        errors.append(f"{record['candidate_name']} has {record['region_count']} regions")
    if record["missing_regions"]:
        errors.append(f"{record['candidate_name']} missing regions: {record['missing_regions']}")
    if record["empty_geometry_count"]:
        errors.append(f"{record['candidate_name']} has empty geometries")
    if record["invalid_geometry_count"]:
        warnings.append(
            f"{record['candidate_name']} has {record['invalid_geometry_count']} invalid geometries"
        )
    return errors, warnings


def output_name_for(strategy, tolerance_m=None):
    if strategy == "dissolved-region-raw":
        return "dissolved_region_raw.geojson"
    if strategy == "dissolved-region-simplified":
        return f"dissolved_region_simplified_{tolerance_m}m.geojson"
    raise ValueError(f"Unknown strategy: {strategy}")


def candidate_name_for(strategy, tolerance_m=None):
    return output_name_for(strategy, tolerance_m).removesuffix(".geojson")


def run_generation(source_path, output_dir, requested_candidates):
    source_frame = load_source(source_path)
    generated_at = deterministic_generated_at(source_path)
    dissolved = build_dissolved_regions(source_frame)
    raw_area_m2 = float(dissolved.geometry.area.sum())

    records = []
    validation_errors = []
    validation_warnings = []
    for strategy, tolerance_m in requested_candidates:
        candidate_name = candidate_name_for(strategy, tolerance_m)
        output_path = Path(output_dir) / output_name_for(strategy, tolerance_m)
        print(f"Generating {candidate_name}.", flush=True)
        candidate = candidate_from_dissolved(
            dissolved,
            tolerance_m=tolerance_m if strategy == "dissolved-region-simplified" else None,
        )
        write_geojson(candidate, output_path)
        record = calculate_metrics(
            output_path=output_path,
            candidate_name=candidate_name,
            strategy=strategy,
            tolerance_m=0 if tolerance_m is None else tolerance_m,
            raw_area_m2=raw_area_m2,
            generated_at=generated_at,
        )
        records.append(record)
        record_errors, record_warnings = validate_record(record)
        validation_errors.extend(record_errors)
        validation_warnings.extend(record_warnings)

    if validation_errors:
        raise SystemExit("Candidate validation failed:\n- " + "\n- ".join(validation_errors))
    if validation_warnings:
        print("Candidate validation completed with warnings:")
        print("- " + "\n- ".join(validation_warnings))

    index_csv, index_json = update_candidate_index(records, output_dir)
    print("Updated candidate index.", flush=True)
    print(f"- {display_path(index_csv)}", flush=True)
    print(f"- {display_path(index_json)}", flush=True)
    return records


def list_strategies():
    print("Available Wine-region candidate strategies:")
    for strategy, description in STRATEGIES.items():
        print(f"- {strategy}: {description}")
    print()
    print("--all will run:")
    print("- dissolved-region-raw")
    for tolerance_m in DEFAULT_SIMPLIFICATION_TOLERANCES_M:
        print(f"- dissolved-region-simplified --tolerance {tolerance_m}")


def requested_candidates_from_args(args, parser):
    if args.all:
        return [("dissolved-region-raw", None)] + [
            ("dissolved-region-simplified", tolerance_m)
            for tolerance_m in DEFAULT_SIMPLIFICATION_TOLERANCES_M
        ]

    if args.strategy == "dissolved-region-raw":
        if args.tolerance is not None:
            parser.error("--tolerance is only valid for dissolved-region-simplified")
        return [("dissolved-region-raw", None)]

    if args.strategy == "dissolved-region-simplified":
        if args.tolerance is None:
            parser.error("--strategy dissolved-region-simplified requires --tolerance")
        if args.tolerance <= 0:
            parser.error("--tolerance must be a positive integer number of metres")
        return [("dissolved-region-simplified", args.tolerance)]

    return []


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--list-strategies", action="store_true")
    parser.add_argument("--strategy", choices=sorted(STRATEGIES))
    parser.add_argument("--tolerance", type=int, help="Simplification tolerance in metres.")
    parser.add_argument("--all", action="store_true", help="Generate all Mission 2 candidates.")
    args = parser.parse_args()

    if args.all and args.strategy:
        parser.error("Use either --all or --strategy, not both")
    if args.list_strategies and (args.all or args.strategy or args.tolerance is not None):
        parser.error("--list-strategies cannot be combined with generation options")
    return args, parser


def main():
    args, parser = parse_args()
    if args.list_strategies:
        list_strategies()
        return

    if not args.all and not args.strategy:
        print("No candidate generation requested. Use --strategy, --all, or --list-strategies.")
        print()
        parser.print_help()
        return

    requested_candidates = requested_candidates_from_args(args, parser)
    run_generation(args.source, args.output_dir, requested_candidates)


if __name__ == "__main__":
    main()
