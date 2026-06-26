"""Source checks for the Wine region development workflow.

This module is intentionally lightweight: it uses the dependencies already
required by the app and avoids notebook-only inspection packages. It does not
write deployable GeoJSON; use it to check the cleaned AOC source before
experimenting in ``Wine_Regions.ipynb``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd


HERE = Path(__file__).resolve().parent
WINE_DATA = HERE / "WineData"
DEFAULT_SOURCE = WINE_DATA / "aoc_regions.gpkg"
DEFAULT_AUDIT_DIR = WINE_DATA / "generated" / "audit"
REQUIRED_AOC_COLUMNS = {"region", "app", "colour", "geometry"}


def display_path(path):
    path = Path(path)
    try:
        return str(path.resolve().relative_to(HERE))
    except ValueError:
        return str(path)


def _geometry_coordinate_count(geometry):
    if geometry is None or geometry.is_empty:
        return 0

    geom_type = geometry.geom_type
    if geom_type == "Polygon":
        return len(geometry.exterior.coords) + sum(len(ring.coords) for ring in geometry.interiors)
    if geom_type == "MultiPolygon":
        return sum(_geometry_coordinate_count(polygon) for polygon in geometry.geoms)
    if geom_type in {"LineString", "LinearRing"}:
        return len(geometry.coords)
    if geom_type == "MultiLineString":
        return sum(len(part.coords) for part in geometry.geoms)
    if geom_type == "Point":
        return 1
    if geom_type == "MultiPoint":
        return len(geometry.geoms)
    if geom_type == "GeometryCollection":
        return sum(_geometry_coordinate_count(part) for part in geometry.geoms)
    return 0


def _geometry_polygon_part_count(geometry):
    if geometry is None or geometry.is_empty:
        return 0

    geom_type = geometry.geom_type
    if geom_type == "Polygon":
        return 1
    if geom_type == "MultiPolygon":
        return len(geometry.geoms)
    if geom_type == "GeometryCollection":
        return sum(_geometry_polygon_part_count(part) for part in geometry.geoms)
    return 0


def _bounds_dict(total_bounds):
    minx, miny, maxx, maxy = [float(value) for value in total_bounds]
    return {"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy}


def describe_clean_aoc_source(path):
    path = Path(path)
    frame = gpd.read_file(path, engine="pyogrio")
    attribute_columns = [column for column in ["region", "app", "colour"] if column in frame.columns]
    missing_columns = sorted(REQUIRED_AOC_COLUMNS.difference(frame.columns))
    null_attribute_values = (
        int(frame[attribute_columns].isna().sum().sum()) if attribute_columns else None
    )
    blank_attribute_values = (
        int(frame[attribute_columns].astype(str).apply(lambda col: col.str.strip().eq("")).sum().sum())
        if attribute_columns
        else None
    )

    return frame, {
        "path": display_path(path),
        "size_mb": round(path.stat().st_size / 1024**2, 1),
        "rows": len(frame),
        "crs": str(frame.crs),
        "columns": ", ".join(frame.columns),
        "geometry_types": ", ".join(sorted(frame.geometry.geom_type.unique())),
        "regions": frame["region"].nunique() if "region" in frame.columns else None,
        "apps": frame["app"].nunique() if "app" in frame.columns else None,
        "missing_required_columns": ", ".join(missing_columns) if missing_columns else "",
        "null_attribute_values": null_attribute_values,
        "blank_attribute_values": blank_attribute_values,
        "duplicate_app_rows": (
            int(frame.duplicated(subset=["app"]).sum()) if "app" in frame.columns else None
        ),
        "missing_geometries": int(frame.geometry.isna().sum()),
        "empty_geometries": int(frame.geometry.is_empty.sum()),
        "invalid_geometries": int((~frame.geometry.is_valid).sum()),
    }


def source_contract_report(frame, path):
    path = Path(path)
    geometry_type_counts = {
        str(key): int(value)
        for key, value in frame.geometry.geom_type.value_counts().sort_index().items()
    }
    attribute_columns = [column for column in ["region", "app", "colour"] if column in frame.columns]
    total_bounds = _bounds_dict(frame.total_bounds)

    return {
        "source_path": display_path(path),
        "source_file_size_bytes": int(path.stat().st_size),
        "source_file_size_mb": round(path.stat().st_size / 1024**2, 3),
        "row_count": int(len(frame)),
        "crs": str(frame.crs),
        "columns": list(frame.columns),
        "missing_required_columns": sorted(REQUIRED_AOC_COLUMNS.difference(frame.columns)),
        "region_count": int(frame["region"].nunique()) if "region" in frame.columns else None,
        "aoc_count": int(frame["app"].nunique()) if "app" in frame.columns else None,
        "geometry_type_counts": geometry_type_counts,
        "total_bounds": total_bounds,
        "null_attribute_values": (
            int(frame[attribute_columns].isna().sum().sum()) if attribute_columns else None
        ),
        "blank_attribute_values": (
            int(frame[attribute_columns].astype(str).apply(lambda col: col.str.strip().eq("")).sum().sum())
            if attribute_columns
            else None
        ),
        "duplicate_app_rows": (
            int(frame.duplicated(subset=["app"]).sum()) if "app" in frame.columns else None
        ),
        "missing_geometries": int(frame.geometry.isna().sum()),
        "empty_geometries": int(frame.geometry.is_empty.sum()),
        "invalid_geometry_count": int((~frame.geometry.is_valid).sum()),
    }


def _frame_with_geometry_metrics(frame):
    audited = frame.copy()
    audited["is_invalid_geometry"] = ~audited.geometry.is_valid
    audited["geometry_type"] = audited.geometry.geom_type
    audited["coordinate_count"] = audited.geometry.apply(_geometry_coordinate_count).astype("int64")
    audited["polygon_part_count"] = audited.geometry.apply(_geometry_polygon_part_count).astype("int64")
    audited["is_polygon_row"] = audited["geometry_type"].eq("Polygon")
    audited["is_multipolygon_row"] = audited["geometry_type"].eq("MultiPolygon")
    return audited


def region_summary(frame):
    return (
        frame.assign(is_invalid=~frame.geometry.is_valid)
        .groupby("region", dropna=False)
        .agg(
            aoc_count=("app", "count"),
            invalid_geometries=("is_invalid", "sum"),
            colours=("colour", "nunique"),
        )
        .reset_index()
        .sort_values("region")
    )


def audit_region_summary(audited):
    return (
        audited.groupby("region", dropna=False)
        .agg(
            aoc_count=("app", "count"),
            invalid_geometry_count=("is_invalid_geometry", "sum"),
            geometry_type_count=("geometry_type", "nunique"),
            colour_count=("colour", "nunique"),
            source_coordinate_count=("coordinate_count", "sum"),
            polygon_part_count=("polygon_part_count", "sum"),
        )
        .reset_index()
        .sort_values("region", kind="mergesort")
    )


def geometry_complexity_by_region(audited):
    return (
        audited.groupby("region", dropna=False)
        .agg(
            aoc_count=("app", "count"),
            invalid_geometry_count=("is_invalid_geometry", "sum"),
            polygon_rows=("is_polygon_row", "sum"),
            multipolygon_rows=("is_multipolygon_row", "sum"),
            polygon_part_count=("polygon_part_count", "sum"),
            approximate_coordinate_count=("coordinate_count", "sum"),
            min_aoc_coordinate_count=("coordinate_count", "min"),
            median_aoc_coordinate_count=("coordinate_count", "median"),
            max_aoc_coordinate_count=("coordinate_count", "max"),
        )
        .reset_index()
        .sort_values("region", kind="mergesort")
    )


def top_complex_aocs(audited, top_n):
    columns = [
        "region",
        "app",
        "geometry_type",
        "is_invalid_geometry",
        "polygon_part_count",
        "coordinate_count",
    ]
    return (
        audited[columns]
        .sort_values(
            ["coordinate_count", "polygon_part_count", "region", "app"],
            ascending=[False, False, True, True],
            kind="mergesort",
        )
        .head(top_n)
        .reset_index(drop=True)
    )


def strategy_table():
    rows = [
        {
            "strategy": "Raw AOC polygons",
            "keeps_aoc_detail": "yes",
            "likely_payload": "too high",
            "notes": "Useful for inspection, not a deployed default.",
        },
        {
            "strategy": "Dissolve by region",
            "keeps_aoc_detail": "no",
            "likely_payload": "medium",
            "notes": "Best first baseline for an expanded region map.",
        },
        {
            "strategy": "Dissolve then simplify",
            "keeps_aoc_detail": "no",
            "likely_payload": "low",
            "notes": "Preferred app candidate if visual QA is acceptable.",
        },
        {
            "strategy": "Simplify AOCs then dissolve",
            "keeps_aoc_detail": "partial",
            "likely_payload": "low-medium",
            "notes": "May preserve local shapes, but can introduce gaps or slivers.",
        },
        {
            "strategy": "Hull per region",
            "keeps_aoc_detail": "no",
            "likely_payload": "very low",
            "notes": "Good stress test for payload, risky for recognisable wine geography.",
        },
        {
            "strategy": "Region map plus AOC detail-on-demand",
            "keeps_aoc_detail": "yes",
            "likely_payload": "split",
            "notes": "Future option if app needs clickable AOC detail without loading all AOCs upfront.",
        },
    ]
    return pd.DataFrame(rows)


def write_audit_outputs(audit_dir, contract, summary, complexity, top_aocs):
    audit_dir = Path(audit_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "source_contract": audit_dir / "source_contract.json",
        "region_summary": audit_dir / "region_summary.csv",
        "geometry_complexity_by_region": audit_dir / "geometry_complexity_by_region.csv",
        "top_complex_aocs": audit_dir / "top_complex_aocs.csv",
    }

    paths["source_contract"].write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary.to_csv(paths["region_summary"], index=False)
    complexity.to_csv(paths["geometry_complexity_by_region"], index=False)
    top_aocs.to_csv(paths["top_complex_aocs"], index=False)
    return paths


def run_audit(source_path, audit_dir, write_outputs=True, top_n=25):
    source_path = Path(source_path)
    frame = gpd.read_file(source_path, engine="pyogrio")
    audited = _frame_with_geometry_metrics(frame)

    contract = source_contract_report(frame, source_path)
    summary = audit_region_summary(audited)
    complexity = geometry_complexity_by_region(audited)
    top_aocs = top_complex_aocs(audited, top_n=top_n)

    print("Wine source audit")
    print(pd.Series(contract).to_string())
    print()
    print("Region summary")
    print(summary.to_string(index=False))
    print()
    print("Geometry complexity by region")
    print(complexity.to_string(index=False))
    print()
    print(f"Top {len(top_aocs)} complex AOCs")
    print(top_aocs.to_string(index=False))

    if write_outputs:
        print()
        paths = write_audit_outputs(audit_dir, contract, summary, complexity, top_aocs)
        print("Wrote audit outputs")
        for path in paths.values():
            print(f"- {display_path(path)}")


def validate_clean_aoc_source(path):
    frame, report = describe_clean_aoc_source(path)
    errors = []
    warnings = []

    missing_columns = sorted(REQUIRED_AOC_COLUMNS.difference(frame.columns))
    if missing_columns:
        errors.append(f"missing required columns: {', '.join(missing_columns)}")

    if frame.empty:
        errors.append("source AOC dataset is empty")

    if str(frame.crs) != "EPSG:4326":
        errors.append(f"source CRS is {frame.crs}, expected EPSG:4326")

    if not missing_columns:
        for column in ["region", "app", "colour"]:
            null_count = int(frame[column].isna().sum())
            blank_count = int(frame[column].astype(str).str.strip().eq("").sum())
            if null_count:
                errors.append(f"{column} has {null_count} null values")
            if blank_count:
                errors.append(f"{column} has {blank_count} blank values")

        duplicate_apps = int(frame.duplicated(subset=["app"]).sum())
        if duplicate_apps:
            errors.append(f"app has {duplicate_apps} duplicate rows")

    if frame.geometry.isna().any() or frame.geometry.is_empty.any():
        errors.append("source has missing or empty geometries")

    if not frame.geometry.is_valid.all():
        warnings.append(
            "source has invalid geometries; repair during dissolve/export before writing app data"
        )

    print("Clean AOC source contract")
    print(pd.Series(report).to_string())
    print()

    if errors:
        raise SystemExit("Clean source validation failed:\n- " + "\n- ".join(errors))

    if warnings:
        print("Clean source validation passed with topology warnings:")
        print("- " + "\n- ".join(warnings))
    else:
        print(f"Clean source validation passed: {display_path(path)}")

    print()
    print("AOC source region counts")
    print(region_summary(frame).to_string(index=False))
    print()
    print("Payload reduction strategies")
    print(strategy_table().to_string(index=False))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Run a read-only source audit and write deterministic CSV/JSON summaries.",
    )
    parser.add_argument(
        "--audit-dir",
        type=Path,
        default=DEFAULT_AUDIT_DIR,
        help="Directory for audit CSV/JSON outputs.",
    )
    parser.add_argument(
        "--no-write-audit",
        action="store_true",
        help="Print audit summaries without writing CSV/JSON files.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=25,
        help="Number of highest-complexity AOCs to include in top_complex_aocs.csv.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.audit:
        run_audit(
            args.source,
            audit_dir=args.audit_dir,
            write_outputs=not args.no_write_audit,
            top_n=args.top_n,
        )
        return

    validate_clean_aoc_source(args.source)


if __name__ == "__main__":
    main()
