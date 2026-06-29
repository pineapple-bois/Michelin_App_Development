#!/usr/bin/env python3
"""Diagnose invalid regional candidate features without modifying candidates."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import GeometryCollection, MultiPolygon, Point, box
from shapely.validation import explain_validity

try:
    from shapely import make_valid
except ImportError:  # pragma: no cover - compatibility with older Shapely
    from shapely.validation import make_valid

try:
    from .simplification import (
        WORKING_CRS,
        count_coordinates,
        count_polygon_parts,
        slugify_region,
    )
except ImportError:  # Direct script execution.
    from simplification import (
        WORKING_CRS,
        count_coordinates,
        count_polygon_parts,
        slugify_region,
    )


REQUIRED_COLUMNS = {"region", "app", "geometry"}
DIAGNOSTIC_PADDING_M = 250.0
NEARBY_CONTEXT_M = 1000.0


def find_project_root(start: Path) -> Path:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / "michelin_app.py").is_file() and (
            candidate / "Development" / "aoc_simplification"
        ).is_dir():
            return candidate
    raise FileNotFoundError(f"Could not locate the Michelin project root from {start}.")


def normalise_slug(value: str, *, label: str) -> str:
    slug = slugify_region(value)
    if not slug:
        raise argparse.ArgumentTypeError(
            f"{label} must contain at least one ASCII letter or number"
        )
    return slug


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", required=True, help="Exact region display name.")
    parser.add_argument(
        "--run-id",
        default="close500_smallest_wins",
        help="Candidate run directory to inspect.",
    )
    parser.add_argument(
        "--repair-in-place",
        action="store_true",
        help=(
            "Repair only invalid features in candidate.geojson, create a timestamped "
            "backup, validate a round-trip reload, and then atomically replace the file."
        ),
    )
    parser.add_argument(
        "--max-area-change-m2",
        type=float,
        default=500.0,
        help="Maximum permitted absolute area change for any repaired feature.",
    )
    return parser.parse_args()


def polygon_components(geometry) -> list:
    if geometry is None or geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type in {"MultiPolygon", "GeometryCollection"}:
        components = []
        for child in geometry.geoms:
            components.extend(polygon_components(child))
        return components
    return []


def combine_polygons(polygons: list):
    retained = [polygon for polygon in polygons if polygon is not None and not polygon.is_empty]
    if not retained:
        return None
    return retained[0] if len(retained) == 1 else MultiPolygon(retained)


def project_geometry(geometry, source_crs):
    series = gpd.GeoSeries([geometry], crs=source_crs)
    return series.to_crs(WORKING_CRS).iloc[0]


def geometry_measurements(geometry) -> dict[str, Any]:
    if geometry is None or geometry.is_empty:
        return {
            "valid": False,
            "validity_reason": "Empty geometry",
            "geometry_type": None,
            "area_m2": 0.0,
            "coordinate_count": 0,
            "polygon_part_count": 0,
            "empty": True,
        }
    return {
        "valid": bool(geometry.is_valid),
        "validity_reason": explain_validity(geometry),
        "geometry_type": geometry.geom_type,
        "area_m2": float(geometry.area),
        "coordinate_count": int(count_coordinates(geometry)),
        "polygon_part_count": int(count_polygon_parts(geometry)),
        "empty": False,
    }


def repair_outcome(
    geometry,
    *,
    original_area_m2: float,
    original_part_count: int,
    error: str | None = None,
) -> dict[str, Any]:
    measurements = geometry_measurements(geometry)
    area_change = measurements["area_m2"] - original_area_m2
    area_change_percent = (
        area_change / original_area_m2 * 100 if original_area_m2 else None
    )
    return {
        **measurements,
        "area_change_m2": area_change,
        "area_change_percent": area_change_percent,
        "part_count_change": measurements["polygon_part_count"]
        - original_part_count,
        "app_becomes_empty": measurements["empty"],
        "error": error,
    }


def try_make_valid(geometry):
    try:
        return make_valid(geometry), None
    except Exception as error:  # Diagnostic capture; do not hide the failure.
        return None, f"{type(error).__name__}: {error}"


def validity_error_point(geometry):
    """Return the coordinate reported by explain_validity, when present."""
    reason = explain_validity(geometry)
    if "[" not in reason or not reason.endswith("]"):
        return None
    coordinate_text = reason.rsplit("[", 1)[1][:-1]
    parts = coordinate_text.split()
    if len(parts) != 2:
        return None
    try:
        return Point(float(parts[0]), float(parts[1]))
    except ValueError:
        return None


def safe_difference(left, right):
    if left is None or left.is_empty:
        return None
    if right is None or right.is_empty:
        return left
    try:
        return left.difference(right)
    except Exception:
        return None


def safe_intersection(left, right):
    if left is None or left.is_empty or right is None or right.is_empty:
        return None
    try:
        return left.intersection(right)
    except Exception:
        return None


# --- Additional diagnostic-safe geometry helpers ---
def valid_polygonal_geometry(geometry):
    """Return valid polygonal geometry for diagnostic context only."""
    if geometry is None or geometry.is_empty:
        return None
    if geometry.is_valid:
        return combine_polygons(polygon_components(geometry))
    repaired, _ = try_make_valid(geometry)
    return combine_polygons(polygon_components(repaired))


def repair_invalid_feature_geometry(geometry):
    """Repair one invalid feature and return polygonal geometry only."""
    repaired, error = try_make_valid(geometry)
    if error is not None:
        raise ValueError(error)
    polygonal = combine_polygons(polygon_components(repaired))
    if polygonal is None or polygonal.is_empty:
        raise ValueError("Repair produced no polygonal geometry")
    if not polygonal.is_valid:
        raise ValueError(
            f"Repair remains invalid: {explain_validity(polygonal)}"
        )
    return polygonal


def overlap_area_with_geometries(geometry, others) -> float:
    """Measure overlap without unioning a collection that may contain invalid input."""
    if geometry is None or geometry.is_empty:
        return 0.0
    total = 0.0
    for other in others:
        polygonal_other = valid_polygonal_geometry(other)
        intersection = safe_intersection(geometry, polygonal_other)
        if intersection is not None and not intersection.is_empty:
            total += float(intersection.area)
    return total


def is_retained_component(component) -> bool:
    return bool(
        component is not None
        and not component.is_empty
        and component.geom_type == "Polygon"
        and component.is_valid
        and component.area > 0
        and count_coordinates(component) >= 4
    )


def analyse_feature(
    row,
    *,
    source_crs,
    candidate_working: gpd.GeoDataFrame,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_geometry = row.geometry
    working_geometry = project_geometry(source_geometry, source_crs)
    source_components = polygon_components(source_geometry)
    working_components = polygon_components(working_geometry)
    if len(source_components) != len(working_components):
        raise ValueError(
            f"Component count changed during reprojection for {row.get('app', '')!r}: "
            f"{len(source_components)} -> {len(working_components)}"
        )

    source_measurements = geometry_measurements(source_geometry)
    working_measurements = geometry_measurements(working_geometry)
    full_area = working_measurements["area_m2"]
    full_parts = working_measurements["polygon_part_count"]

    component_reports = []
    invalid_component_indices = []
    for component_index, (source_component, working_component) in enumerate(
        zip(source_components, working_components)
    ):
        source_component_measurements = geometry_measurements(source_component)
        working_component_measurements = geometry_measurements(working_component)
        is_invalid = not source_component.is_valid
        is_degenerate = not is_retained_component(working_component)
        if is_invalid or is_degenerate:
            invalid_component_indices.append(component_index)
            component_reports.append(
                {
                    "component_index": component_index,
                    "source_epsg4326": source_component_measurements,
                    "projected_working_crs": working_component_measurements,
                    "area_percent_of_feature": (
                        working_component_measurements["area_m2"] / full_area * 100
                        if full_area
                        else None
                    ),
                    "degenerate": is_degenerate,
                }
            )

    made_valid, make_valid_error = try_make_valid(working_geometry)
    extracted_polygonal = combine_polygons(polygon_components(made_valid))
    retained_components = [
        working_component
        for source_component, working_component in zip(
            source_components, working_components
        )
        if source_component.is_valid and is_retained_component(working_component)
    ]
    dropped_invalid_components = combine_polygons(retained_components)

    other_geometries = list(
        candidate_working.loc[candidate_working.index != row.name, "geometry"]
    )
    nearby_parts = [
        polygonal
        for geometry in other_geometries
        if (polygonal := valid_polygonal_geometry(geometry)) is not None
        and not polygonal.is_empty
    ]
    nearby_context = GeometryCollection(nearby_parts)

    repair_geometries = {
        "make_valid_polygonal_extraction": extracted_polygonal,
        "drop_invalid_or_degenerate_components": dropped_invalid_components,
    }
    repairs = {
        "make_valid": repair_outcome(
            made_valid,
            original_area_m2=full_area,
            original_part_count=full_parts,
            error=make_valid_error,
        ),
        "make_valid_polygonal_extraction": repair_outcome(
            extracted_polygonal,
            original_area_m2=full_area,
            original_part_count=full_parts,
        ),
        "drop_invalid_or_degenerate_components": repair_outcome(
            dropped_invalid_components,
            original_area_m2=full_area,
            original_part_count=full_parts,
        ),
    }
    for repair_name, repair_geometry in repair_geometries.items():
        added = safe_difference(repair_geometry, working_geometry)
        removed = safe_difference(working_geometry, repair_geometry)
        overlap_area = overlap_area_with_geometries(
            repair_geometry,
            other_geometries,
        )
        repairs[repair_name].update(
            {
                "added_area_m2": 0.0 if added is None else float(added.area),
                "removed_area_m2": 0.0 if removed is None else float(removed.area),
                "overlap_with_other_apps_m2": overlap_area,
            }
        )

    source_error_point = validity_error_point(source_geometry)
    working_error_point = (
        None
        if source_error_point is None
        else project_geometry(source_error_point, source_crs)
    )
    report = {
        "source_index": str(row.name),
        "region": str(row.get("region", "")),
        "app": str(row.get("app", "")),
        "source_epsg4326": source_measurements,
        "projected_working_crs": working_measurements,
        "validity_error_coordinate_epsg4326": (
            None
            if source_error_point is None
            else [float(source_error_point.x), float(source_error_point.y)]
        ),
        "suspect_component_count": len(component_reports),
        "suspect_components": component_reports,
        "repair_options": repairs,
    }
    plot_geometries = {
        "complete": working_geometry,
        "error_point": working_error_point,
        "nearby": nearby_context,
        "locally_repaired": extracted_polygonal,
        "drop_invalid_components": dropped_invalid_components,
        "repair_added": safe_difference(extracted_polygonal, working_geometry),
        "repair_removed": safe_difference(working_geometry, extracted_polygonal),
        "repair_overlap": GeometryCollection(
            [
                intersection
                for other in other_geometries
                if (
                    intersection := safe_intersection(
                        extracted_polygonal,
                        valid_polygonal_geometry(other),
                    )
                )
                is not None
                and not intersection.is_empty
            ]
        ),
    }
    return report, plot_geometries


def plot_geometry(axis, geometry, *, facecolor: str, edgecolor: str = "#303030") -> None:
    if geometry is None or geometry.is_empty:
        axis.text(
            0.5,
            0.5,
            "Empty geometry",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )
        return
    gpd.GeoSeries([geometry], crs=WORKING_CRS).plot(
        ax=axis,
        color=facecolor,
        edgecolor=edgecolor,
        linewidth=0.5,
    )


def write_diagnostic_plot(
    output_path: Path,
    *,
    region: str,
    app: str,
    geometries: dict[str, Any],
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    complete = geometries["complete"]
    error_point = geometries["error_point"]
    if error_point is None:
        minx, miny, maxx, maxy = complete.bounds
        centre_x = (minx + maxx) / 2
        centre_y = (miny + maxy) / 2
        half_width = max((maxx - minx) * 0.1, DIAGNOSTIC_PADDING_M)
        half_height = max((maxy - miny) * 0.1, DIAGNOSTIC_PADDING_M)
    else:
        centre_x, centre_y = error_point.x, error_point.y
        half_width = DIAGNOSTIC_PADDING_M
        half_height = DIAGNOSTIC_PADDING_M

    zoom_bounds = (
        centre_x - half_width,
        centre_y - half_height,
        centre_x + half_width,
        centre_y + half_height,
    )
    zoom_box = box(*zoom_bounds)
    context_box = zoom_box.buffer(NEARBY_CONTEXT_M)

    nearby = safe_intersection(geometries["nearby"], context_box)
    panels = (
        ("complete", "Original geometry"),
        ("locally_repaired", "make_valid result"),
        ("repair_removed", "Removed by repair"),
        ("repair_added", "Added by repair"),
        ("repair_overlap", "Overlap after repair"),
    )
    figure, axes = plt.subplots(1, 5, figsize=(30, 7), facecolor="white")

    for axis, (key, title) in zip(axes, panels):
        axis.set_facecolor("white")
        if nearby is not None and not nearby.is_empty:
            gpd.GeoSeries([nearby], crs=WORKING_CRS).boundary.plot(
                ax=axis,
                linewidth=0.6,
                alpha=0.5,
            )
        geometry = safe_intersection(geometries[key], zoom_box)
        plot_geometry(axis, geometry, facecolor="#d9d9d9")
        if error_point is not None:
            axis.scatter([error_point.x], [error_point.y], marker="x", s=60)
        axis.set_xlim(zoom_bounds[0], zoom_bounds[2])
        axis.set_ylim(zoom_bounds[1], zoom_bounds[3])
        axis.set_aspect("equal")
        axis.set_axis_off()
        axis.set_title(title)

    figure.suptitle(f"{region} — {app}", fontsize=16)
    figure.tight_layout()
    figure.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def repair_candidate_in_place(
    candidate_path: Path,
    *,
    max_area_change_m2: float,
) -> dict[str, Any]:
    """Repair invalid candidate features, validate round-trip output, and replace atomically."""
    if max_area_change_m2 < 0:
        raise ValueError("--max-area-change-m2 must be non-negative")

    candidate = gpd.read_file(candidate_path, engine="pyogrio")
    if candidate.crs is None:
        raise ValueError("Candidate has no CRS.")

    invalid_mask = ~candidate.geometry.is_valid
    invalid_indices = list(candidate.index[invalid_mask])
    if not invalid_indices:
        return {
            "candidate_path": str(candidate_path),
            "repaired_feature_count": 0,
            "backup_path": None,
            "features": [],
        }

    repaired_candidate = candidate.copy()
    feature_reports = []
    for index in invalid_indices:
        original = candidate.at[index, "geometry"]
        repaired = repair_invalid_feature_geometry(original)

        original_working = project_geometry(original, candidate.crs)
        repaired_working = project_geometry(repaired, candidate.crs)
        area_change_m2 = float(repaired_working.area - original_working.area)
        if abs(area_change_m2) > max_area_change_m2:
            raise ValueError(
                f"Repair for {candidate.at[index, 'app']!r} changes area by "
                f"{area_change_m2:.6f} m², exceeding {max_area_change_m2:.6f} m²"
            )

        repaired_candidate.at[index, "geometry"] = repaired
        feature_reports.append(
            {
                "source_index": str(index),
                "region": str(candidate.at[index, "region"]),
                "app": str(candidate.at[index, "app"]),
                "original_validity_reason": explain_validity(original),
                "repaired_geometry_type": repaired.geom_type,
                "area_change_m2": area_change_m2,
                "original_part_count": int(count_polygon_parts(original)),
                "repaired_part_count": int(count_polygon_parts(repaired)),
            }
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = candidate_path.with_name(
        f"{candidate_path.stem}.backup-{timestamp}{candidate_path.suffix}"
    )
    temporary_path = candidate_path.with_name(
        f".{candidate_path.stem}.repair-{timestamp}{candidate_path.suffix}"
    )

    try:
        repaired_candidate.to_file(
            temporary_path,
            driver="GeoJSON",
            engine="pyogrio",
        )
        reloaded = gpd.read_file(temporary_path, engine="pyogrio")

        if len(reloaded) != len(candidate):
            raise ValueError(
                f"Round-trip feature count changed: {len(candidate)} -> {len(reloaded)}"
            )
        if reloaded.geometry.is_empty.any():
            empty_count = int(reloaded.geometry.is_empty.sum())
            raise ValueError(
                f"Round-trip candidate contains {empty_count} empty geometries"
            )
        invalid_reloaded = ~reloaded.geometry.is_valid
        if invalid_reloaded.any():
            reasons = [
                f"{reloaded.at[index, 'app']}: "
                f"{explain_validity(reloaded.at[index, 'geometry'])}"
                for index in reloaded.index[invalid_reloaded]
            ]
            raise ValueError(
                "Round-trip candidate still contains invalid geometries: "
                + "; ".join(reasons)
            )

        shutil.copy2(candidate_path, backup_path)
        os.replace(temporary_path, candidate_path)
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise

    return {
        "candidate_path": str(candidate_path),
        "repaired_feature_count": len(feature_reports),
        "backup_path": str(backup_path),
        "features": feature_reports,
    }


def diagnose_region(region: str, run_id: str) -> Path:
    project_root = find_project_root(Path(__file__).parent)
    experiment_root = project_root / "Development" / "aoc_simplification"
    region_slug = normalise_slug(region, label="region")
    run_slug = normalise_slug(run_id, label="run ID")
    candidate_path = (
        experiment_root / "outputs" / region_slug / run_slug / "candidate.geojson"
    )
    if not candidate_path.is_file():
        raise FileNotFoundError(f"Candidate does not exist: {candidate_path}")

    candidate = gpd.read_file(candidate_path, engine="pyogrio")
    missing = sorted(REQUIRED_COLUMNS - set(candidate.columns))
    if missing:
        raise ValueError(f"Candidate is missing required columns: {', '.join(missing)}")
    if candidate.crs is None:
        raise ValueError("Candidate has no CRS.")

    candidate_working = candidate.to_crs(WORKING_CRS)

    invalid = candidate.loc[~candidate.geometry.is_valid].copy()
    output_directory = (
        experiment_root
        / "outputs"
        / "_invalid_diagnostics"
        / region_slug
        / run_slug
    )
    output_directory.mkdir(parents=True, exist_ok=True)

    feature_reports = []
    for _, row in invalid.iterrows():
        feature_report, plot_geometries = analyse_feature(
            row,
            source_crs=candidate.crs,
            candidate_working=candidate_working,
        )
        feature_reports.append(feature_report)
        plot_name = f"{slugify_region(feature_report['app']) or 'unnamed_app'}.png"
        write_diagnostic_plot(
            output_directory / plot_name,
            region=feature_report["region"],
            app=feature_report["app"],
            geometries=plot_geometries,
        )

    report = {
        "region": region,
        "region_slug": region_slug,
        "run_id": run_slug,
        "candidate_path": candidate_path.relative_to(project_root).as_posix(),
        "candidate_crs": candidate.crs.to_string(),
        "measurement_crs": WORKING_CRS,
        "candidate_feature_count": int(len(candidate)),
        "invalid_feature_count": int(len(invalid)),
        "invalid_features": feature_reports,
    }
    report_path = output_directory / "diagnostics.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def main() -> int:
    args = parse_args()
    project_root = find_project_root(Path(__file__).parent)
    experiment_root = project_root / "Development" / "aoc_simplification"
    region_slug = normalise_slug(args.region, label="region")
    run_slug = normalise_slug(args.run_id, label="run ID")
    candidate_path = (
        experiment_root
        / "outputs"
        / region_slug
        / run_slug
        / "candidate.geojson"
    )

    if args.repair_in_place:
        result = repair_candidate_in_place(
            candidate_path,
            max_area_change_m2=args.max_area_change_m2,
        )
        print(
            f"Repaired {result['repaired_feature_count']} invalid feature(s) in "
            f"{result['candidate_path']}"
        )
        if result["backup_path"] is not None:
            print(f"Backup: {result['backup_path']}")
        for feature in result["features"]:
            print(
                f"- {feature['region']} / {feature['app']}: "
                f"area change {feature['area_change_m2']:.9f} m², "
                f"parts {feature['original_part_count']} -> "
                f"{feature['repaired_part_count']}"
            )
        return 0

    report_path = diagnose_region(args.region, args.run_id)
    print(f"Wrote invalid-candidate diagnostics: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
