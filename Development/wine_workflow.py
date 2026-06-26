"""Source checks for the Wine region development workflow.

This module is intentionally lightweight: it uses the dependencies already
required by the app and avoids notebook-only inspection packages. It does not
write deployable GeoJSON; use it to check the cleaned AOC source before
experimenting in ``Wine_Regions.ipynb``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd


HERE = Path(__file__).resolve().parent
WINE_DATA = HERE / "WineData"
DEFAULT_SOURCE = WINE_DATA / "aoc_regions.gpkg"
REQUIRED_AOC_COLUMNS = {"region", "app", "colour", "geometry"}


def display_path(path):
    path = Path(path)
    try:
        return str(path.resolve().relative_to(HERE))
    except ValueError:
        return str(path)


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
    return parser.parse_args()


def main():
    args = parse_args()
    validate_clean_aoc_source(args.source)


if __name__ == "__main__":
    main()
