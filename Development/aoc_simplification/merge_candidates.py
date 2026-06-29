#!/usr/bin/env python3
"""Validate and concatenate completed regional AOC candidate GeoJSON files."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

try:
    from .simplification import count_coordinates, count_polygon_parts, slugify_region
except ImportError:  # Direct script execution.
    from simplification import count_coordinates, count_polygon_parts, slugify_region


OUTPUT_CRS = "EPSG:4326"
AREA_CRS = "EPSG:2154"
REQUIRED_COLUMNS = ["region", "app", "colour", "geometry"]
POLYGON_TYPES = {"Polygon", "MultiPolygon"}


class MergeValidationError(ValueError):
    """Raised when candidate files cannot be merged safely."""


@dataclass
class CandidateInventory:
    slug: str
    display_name: str
    source_path: Path
    source_path_relative: str
    source_size_bytes: int
    source_crs: str
    frame: gpd.GeoDataFrame
    geometry_type_counts: dict[str, int]
    coordinate_count: int
    polygon_part_count: int
    invalid_geometry_count: int
    empty_geometry_count: int
    duplicate_feature_count: int
    area_m2_epsg_2154: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "region_slug": self.slug,
            "region": self.display_name,
            "source_file": self.source_path_relative,
            "source_file_size_mb": round(self.source_size_bytes / (1024 * 1024), 6),
            "feature_count": int(len(self.frame)),
            "app_count": int(self.frame["app"].nunique()),
            "property_names": [column for column in REQUIRED_COLUMNS if column != "geometry"],
            "source_crs": self.source_crs,
            "output_crs": str(self.frame.crs),
            "geometry_type_counts": self.geometry_type_counts,
            "coordinate_count": self.coordinate_count,
            "polygon_part_count": self.polygon_part_count,
            "invalid_geometry_count": self.invalid_geometry_count,
            "empty_geometry_count": self.empty_geometry_count,
            "duplicate_feature_count": self.duplicate_feature_count,
            "approx_geojson_size_mb": round(
                self.source_size_bytes / (1024 * 1024), 6
            ),
            "area_m2_epsg_2154": round(self.area_m2_epsg_2154, 3),
        }


def find_project_root(start: Path) -> Path:
    """Find the repository root without relying on the current working directory."""
    resolved = start.resolve()
    for candidate in [resolved, *resolved.parents]:
        if (candidate / "michelin_app.py").is_file() and (
            candidate / "Development" / "aoc_simplification"
        ).is_dir():
            return candidate
    raise FileNotFoundError(f"Could not locate the Michelin project root from {start}.")


def normalise_run_id(value: str) -> str:
    run_id = slugify_region(value)
    if not run_id:
        raise argparse.ArgumentTypeError(
            "run ID must contain at least one ASCII letter or number"
        )
    return run_id


def parse_args(project_root: Path) -> argparse.Namespace:
    default_output = (
        project_root
        / "Development"
        / "aoc_simplification"
        / "datasets"
        / "aoc_regions_close500.geojson"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", type=normalise_run_id, default="close500")
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help="Output GeoJSON path; relative paths are resolved from the project root.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing merged GeoJSON and metrics file.",
    )
    return parser.parse_args()


def resolve_output_path(path: Path, project_root: Path) -> Path:
    resolved = path if path.is_absolute() else project_root / path
    resolved = resolved.resolve()
    if resolved.suffix.lower() != ".geojson":
        raise ValueError("Merged output must use a .geojson filename.")
    return resolved


def metrics_path_for(output_path: Path) -> Path:
    return output_path.with_name(f"{output_path.stem}_metrics.json")


def geometry_type_counts(frame: gpd.GeoDataFrame) -> dict[str, int]:
    counts = Counter(str(value) for value in frame.geom_type.dropna())
    return dict(sorted(counts.items()))


def geometry_counts(frame: gpd.GeoDataFrame) -> tuple[int, int, int, int]:
    non_null = frame.geometry.dropna()
    coordinate_count = int(non_null.map(count_coordinates).sum())
    polygon_part_count = int(non_null.map(count_polygon_parts).sum())
    invalid_count = int((~non_null.is_valid).sum())
    empty_count = int(frame.geometry.isna().sum() + non_null.is_empty.sum())
    return coordinate_count, polygon_part_count, invalid_count, empty_count


def duplicate_feature_count(frame: gpd.GeoDataFrame) -> int:
    fingerprints = frame.apply(
        lambda row: (
            str(row["region"]),
            str(row["app"]),
            str(row["colour"]),
            row.geometry.normalize().wkb_hex if row.geometry is not None else None,
        ),
        axis=1,
    )
    return int(fingerprints.duplicated().sum())


def _missing_or_blank_count(frame: gpd.GeoDataFrame, column: str) -> int:
    values = frame[column].fillna("").astype(str).str.strip()
    return int(values.eq("").sum())


def inspect_candidate(
    path: Path,
    *,
    project_root: Path,
    warnings: list[str],
) -> tuple[CandidateInventory | None, list[str]]:
    slug = path.parent.parent.name
    errors: list[str] = []
    try:
        frame = gpd.read_file(path, engine="pyogrio")
    except Exception as error:
        return None, [f"{path}: could not be read: {error}"]

    if frame.empty:
        return None, [f"{path}: candidate contains no features"]

    actual_columns = list(frame.columns)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in actual_columns]
    extra_columns = [column for column in actual_columns if column not in REQUIRED_COLUMNS]
    if missing_columns:
        errors.append(f"missing required columns: {', '.join(missing_columns)}")
    if extra_columns:
        errors.append(f"unexpected columns: {', '.join(extra_columns)}")
    if errors:
        return None, [f"{path}: {error}" for error in errors]

    for column in ("region", "app", "colour"):
        missing_count = _missing_or_blank_count(frame, column)
        if missing_count:
            errors.append(f"{column} has {missing_count} missing or blank values")

    region_names = sorted(frame["region"].dropna().astype(str).str.strip().unique())
    if len(region_names) != 1:
        errors.append(
            "expected exactly one region display name, found "
            + (", ".join(region_names) if region_names else "none")
        )
    display_name = region_names[0] if len(region_names) == 1 else ""
    if display_name and slugify_region(display_name) != slug:
        errors.append(
            f"folder slug {slug!r} does not match canonical display-name slug "
            f"{slugify_region(display_name)!r}"
        )

    if frame.crs is None:
        errors.append("CRS is missing")
        source_crs = ""
    else:
        source_crs = frame.crs.to_string()

    coordinates, parts, invalid, empty = geometry_counts(frame)
    types = geometry_type_counts(frame)
    unexpected_types = sorted(set(types) - POLYGON_TYPES)
    if unexpected_types:
        errors.append(f"non-polygon geometry types: {', '.join(unexpected_types)}")
    if invalid:
        errors.append(f"contains {invalid} invalid geometries")
    if empty:
        errors.append(f"contains {empty} empty or missing geometries")

    duplicates = duplicate_feature_count(frame)
    if duplicates:
        errors.append(f"contains {duplicates} duplicate features")

    if errors:
        return None, [f"{path}: {error}" for error in errors]

    if frame.crs != OUTPUT_CRS:
        warnings.append(f"{slug}: reprojected {source_crs} to {OUTPUT_CRS}")
        frame = frame.to_crs(OUTPUT_CRS)
        coordinates, parts, invalid, empty = geometry_counts(frame)
        if invalid or empty:
            return None, [
                f"{path}: CRS normalization produced {invalid} invalid and "
                f"{empty} empty geometries"
            ]

    frame = frame[REQUIRED_COLUMNS].copy()
    frame.insert(1, "region_slug", slug)
    area = float(frame.to_crs(AREA_CRS).geometry.area.sum())
    relative_path = path.resolve().relative_to(project_root).as_posix()
    inventory = CandidateInventory(
        slug=slug,
        display_name=display_name,
        source_path=path,
        source_path_relative=relative_path,
        source_size_bytes=path.stat().st_size,
        source_crs=source_crs,
        frame=frame,
        geometry_type_counts=geometry_type_counts(frame),
        coordinate_count=coordinates,
        polygon_part_count=parts,
        invalid_geometry_count=invalid,
        empty_geometry_count=empty,
        duplicate_feature_count=duplicates,
        area_m2_epsg_2154=area,
    )
    return inventory, []


def collect_inventory(
    project_root: Path,
    run_id: str,
) -> tuple[list[CandidateInventory], list[str]]:
    output_root = project_root / "Development" / "aoc_simplification" / "outputs"
    region_directories = sorted(path for path in output_root.glob("*") if path.is_dir())
    candidate_paths = sorted(
        output_root.glob(f"*/{run_id}/candidate.geojson"),
        key=lambda path: path.parent.parent.name,
    )
    errors: list[str] = []
    warnings: list[str] = []

    missing_directories = [
        path.name
        for path in region_directories
        if not (path / run_id / "candidate.geojson").is_file()
    ]
    if missing_directories:
        errors.append(
            f"region directories missing {run_id}/candidate.geojson: "
            + ", ".join(missing_directories)
        )
    if not candidate_paths:
        errors.append(f"no candidates matched outputs/*/{run_id}/candidate.geojson")

    inventories: list[CandidateInventory] = []
    for path in candidate_paths:
        inventory, candidate_errors = inspect_candidate(
            path,
            project_root=project_root,
            warnings=warnings,
        )
        errors.extend(candidate_errors)
        if inventory is not None:
            inventories.append(inventory)

    display_names = Counter(item.display_name for item in inventories)
    duplicate_names = sorted(name for name, count in display_names.items() if count > 1)
    if duplicate_names:
        errors.append("duplicate region display names: " + ", ".join(duplicate_names))

    schemas = {
        tuple(column for column in item.frame.columns if column != "geometry")
        for item in inventories
    }
    if len(schemas) > 1:
        errors.append(f"inconsistent candidate schemas after validation: {sorted(schemas)!r}")

    if errors:
        raise MergeValidationError("\n".join(f"- {error}" for error in errors))
    return inventories, warnings


def concatenate_candidates(inventories: list[CandidateInventory]) -> gpd.GeoDataFrame:
    merged = gpd.GeoDataFrame(
        pd.concat([item.frame for item in inventories], ignore_index=True),
        geometry="geometry",
        crs=OUTPUT_CRS,
    )
    coordinates, parts, invalid, empty = geometry_counts(merged)
    if invalid or empty:
        raise MergeValidationError(
            f"Merged data contains {invalid} invalid and {empty} empty geometries."
        )
    duplicates = duplicate_feature_count(merged)
    if duplicates:
        raise MergeValidationError(f"Merged data contains {duplicates} duplicate features.")
    if coordinates <= 0 or parts <= 0:
        raise MergeValidationError("Merged data contains no polygon coordinates or parts.")
    return merged


def build_metadata(
    merged: gpd.GeoDataFrame,
    inventories: list[CandidateInventory],
    *,
    run_id: str,
    warnings: list[str],
    merged_file_size_bytes: int,
) -> dict[str, Any]:
    coordinates, parts, invalid, empty = geometry_counts(merged)
    bounds = [round(float(value), 8) for value in merged.total_bounds]
    return {
        "run_id": run_id,
        "input_file_count": len(inventories),
        "input_region_slugs": [item.slug for item in inventories],
        "input_region_display_names": [item.display_name for item in inventories],
        "source_file_paths": [item.source_path_relative for item in inventories],
        "merged_file_size_mb": round(merged_file_size_bytes / (1024 * 1024), 6),
        "merged_feature_count": int(len(merged)),
        "distinct_region_count": int(merged["region"].nunique()),
        "distinct_app_count": int(merged["app"].nunique()),
        "geometry_type_counts": geometry_type_counts(merged),
        "coordinate_count": coordinates,
        "polygon_part_count": parts,
        "invalid_geometry_count": invalid,
        "empty_geometry_count": empty,
        "crs": merged.crs.to_string(),
        "bounds": bounds,
        "inventory_warnings": warnings,
        "regions": [item.as_dict() for item in inventories],
    }


def write_outputs(
    merged: gpd.GeoDataFrame,
    inventories: list[CandidateInventory],
    *,
    run_id: str,
    warnings: list[str],
    output_path: Path,
    overwrite: bool,
) -> Path:
    metadata_path = metrics_path_for(output_path)
    existing = [path for path in (output_path, metadata_path) if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "Refusing to overwrite existing output(s): "
            + ", ".join(str(path) for path in existing)
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output_path.with_name(f".{output_path.name}.tmp")
    temporary_metadata = metadata_path.with_name(f".{metadata_path.name}.tmp")
    try:
        merged.to_file(
            temporary_output,
            driver="GeoJSON",
            engine="pyogrio",
            index=False,
        )
        metadata = build_metadata(
            merged,
            inventories,
            run_id=run_id,
            warnings=warnings,
            merged_file_size_bytes=temporary_output.stat().st_size,
        )
        temporary_metadata.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary_output.replace(output_path)
        temporary_metadata.replace(metadata_path)
    finally:
        temporary_output.unlink(missing_ok=True)
        temporary_metadata.unlink(missing_ok=True)
    return metadata_path


def main() -> int:
    try:
        project_root = find_project_root(Path(__file__))
        args = parse_args(project_root)
        output_path = resolve_output_path(args.output, project_root)
        inventories, warnings = collect_inventory(project_root, args.run_id)
        merged = concatenate_candidates(inventories)
        metadata_path = write_outputs(
            merged,
            inventories,
            run_id=args.run_id,
            warnings=warnings,
            output_path=output_path,
            overwrite=args.overwrite,
        )
    except (FileExistsError, FileNotFoundError, MergeValidationError, ValueError) as error:
        print(f"Merge failed:\n{error}", file=sys.stderr)
        return 1

    print(f"Regional candidates: {len(inventories)}")
    print("Region slugs: " + ", ".join(item.slug for item in inventories))
    print(f"Merged features: {len(merged)}")
    print(f"Merged GeoJSON: {output_path}")
    print(f"Merged metrics: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
