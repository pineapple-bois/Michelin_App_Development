"""Run one tracked AOC-first Wine geometry experiment."""

from __future__ import annotations

import argparse
import json
import math
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd

try:
    from .simplification import (
        OUTPUT_COLUMNS,
        OUTPUT_CRS,
        WORKING_CRS,
        metrics_for_frame,
        process_region,
        slugify_region,
    )
except ImportError:  # Direct execution from this directory.
    from simplification import (
        OUTPUT_COLUMNS,
        OUTPUT_CRS,
        WORKING_CRS,
        metrics_for_frame,
        process_region,
        slugify_region,
    )


SCRIPT_VERSION = "1"
REQUIRED_AOC_COLUMNS = set(OUTPUT_COLUMNS)
OLD_REGION_COLUMNS = ("region", "Region", "REGION", "name", "Name", "nom", "Nom")


def find_project_root(start: Path) -> Path:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / "michelin_app.py").exists() and (candidate / "Development").is_dir():
            return candidate
    raise FileNotFoundError(f"Could not locate the Michelin project root from {start}.")


def non_negative_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("value must be a finite non-negative number")
    return number


def normalise_run_id(value: str) -> str:
    run_id = slugify_region(value)
    if not run_id:
        raise ValueError("Run ID must contain at least one ASCII letter or number.")
    return run_id


def prepare_output_directory(path: Path, *, overwrite: bool) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"Run directory already exists: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _detect_old_region_column(gdf: gpd.GeoDataFrame) -> str | None:
    return next((column for column in OLD_REGION_COLUMNS if column in gdf.columns), None)


def _ratio(numerator: float | int, denominator: float | int) -> float | None:
    if not denominator:
        return None
    return float(numerator) / float(denominator)


def _git_commit(project_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _plot_frame(ax, frame: gpd.GeoDataFrame, *, absent_message: str | None = None) -> None:
    ax.set_facecolor("white")
    if frame.empty:
        ax.text(
            0.5,
            0.5,
            absent_message or "No geometry",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
    else:
        plot_frame = frame.to_crs(OUTPUT_CRS)
        plot_kwargs = {
            "ax": ax,
            "edgecolor": "#303030",
            "linewidth": 0.3,
        }
        if "colour" in plot_frame.columns:
            plot_kwargs["color"] = plot_frame["colour"].fillna("#8a6f96")
        else:
            plot_kwargs["color"] = "#8a6f96"
        plot_frame.plot(**plot_kwargs)
    ax.set_aspect("equal")
    ax.set_axis_off()


def _shared_bounds(frames: list[gpd.GeoDataFrame]) -> tuple[float, float, float, float] | None:
    bounds = []
    for frame in frames:
        if frame.empty:
            continue
        values = frame.to_crs(OUTPUT_CRS).total_bounds
        if all(math.isfinite(float(value)) for value in values):
            bounds.append(values)
    if not bounds:
        return None
    minx = min(float(item[0]) for item in bounds)
    miny = min(float(item[1]) for item in bounds)
    maxx = max(float(item[2]) for item in bounds)
    maxy = max(float(item[3]) for item in bounds)
    padding_x = max((maxx - minx) * 0.05, 0.01)
    padding_y = max((maxy - miny) * 0.05, 0.01)
    return minx - padding_x, miny - padding_y, maxx + padding_x, maxy + padding_y


def write_plots(
    candidate: gpd.GeoDataFrame,
    raw: gpd.GeoDataFrame,
    old_region: gpd.GeoDataFrame,
    *,
    region: str,
    run_id: str,
    preview_path: Path,
    comparison_path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.dpi": 180,
        }
    )

    figure, axis = plt.subplots(figsize=(14, 9))
    figure.patch.set_facecolor("white")
    _plot_frame(axis, candidate)
    axis.set_title(f"{region}: {run_id}")
    figure.tight_layout()
    figure.savefig(preview_path, bbox_inches="tight")
    plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(24, 8))
    figure.patch.set_facecolor("white")
    panels = (
        (old_region, "Old app geometry", "Not present in old data"),
        (raw, "Raw AOC source", None),
        (candidate, "Processed candidate", None),
    )
    shared_bounds = _shared_bounds([old_region, raw, candidate])
    for axis, (frame, title, absent_message) in zip(axes, panels):
        _plot_frame(axis, frame, absent_message=absent_message)
        axis.set_title(title)
        if shared_bounds is not None:
            axis.set_xlim(shared_bounds[0], shared_bounds[2])
            axis.set_ylim(shared_bounds[1], shared_bounds[3])
    figure.suptitle(f"{region}: {run_id}")
    figure.tight_layout()
    figure.savefig(comparison_path, bbox_inches="tight")
    plt.close(figure)


def _write_json(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def run_experiment(args: argparse.Namespace) -> Path:
    project_root = find_project_root(Path(__file__).parent)
    old_path = project_root / "assets" / "data" / "wine_regions_cleaned.geojson"
    source_path = project_root / "Development" / "WineData" / "aoc_regions.gpkg"
    for path in (old_path, source_path):
        if not path.exists():
            raise FileNotFoundError(f"Required input does not exist: {path}")

    region_slug = slugify_region(args.region)
    if not region_slug:
        raise ValueError("Region name must contain at least one ASCII letter or number.")
    run_id = normalise_run_id(args.run_id)
    outputs_root = project_root / "Development" / "aoc_simplification" / "outputs"
    run_dir = outputs_root / region_slug / run_id
    if run_dir.exists() and not args.overwrite:
        raise FileExistsError(
            f"Run directory already exists: {run_dir}; pass --overwrite to replace it."
        )

    print(f"Reading selected AOC source from {source_path}")
    source = gpd.read_file(source_path, engine="pyogrio")
    missing = sorted(REQUIRED_AOC_COLUMNS - set(source.columns))
    if missing:
        raise ValueError(f"AOC source is missing required columns: {', '.join(missing)}")
    available_regions = sorted(source["region"].dropna().astype(str).unique())
    if args.region not in available_regions:
        raise ValueError(
            f"Unknown region {args.region!r}. Available regions: {', '.join(available_regions)}"
        )
    selected = source.loc[source["region"].astype(str) == args.region, OUTPUT_COLUMNS].copy()
    del source

    print(f"Processing {args.region}: overlap_clip={args.overlap_clip}, "
          f"buffer={args.buffer} m, simplify={args.simplify} m")
    stages = process_region(
        selected,
        overlap_clip=args.overlap_clip,
        buffer_dist_m=args.buffer,
        simplify_m=args.simplify,
    )

    print(f"Reading old app comparison geometry from {old_path}")
    old = gpd.read_file(old_path, engine="pyogrio")
    old_region_column = _detect_old_region_column(old)
    if old_region_column is None:
        raise ValueError("Could not identify a region column in the old app geometry.")
    old_region = old.loc[old[old_region_column].astype(str) == args.region].copy()
    del old

    old_metrics = metrics_for_frame(old_region)
    raw_metrics = metrics_for_frame(stages.raw)
    candidate_metrics = metrics_for_frame(stages.final)
    stage_metrics = {
        "old_app_geometry": old_metrics,
        "raw_selected_aoc_geometry": raw_metrics,
        "dissolved_by_app": metrics_for_frame(stages.dissolved),
        "morphologically_closed": metrics_for_frame(stages.closed),
        "simplified_final_candidate": candidate_metrics,
    }
    if stages.overlap_clipped is not None:
        stage_metrics["overlap_clipped"] = metrics_for_frame(stages.overlap_clipped)

    clipping = stages.clipping_report.as_dict()
    metrics = {
        "old_region_present": not old_region.empty,
        "stages": stage_metrics,
        "ratios": {
            "candidate_size_to_old_size": _ratio(
                candidate_metrics["approx_geojson_size_mb"],
                old_metrics["approx_geojson_size_mb"],
            ),
            "candidate_coordinate_count_to_old_coordinate_count": _ratio(
                candidate_metrics["coordinate_count"], old_metrics["coordinate_count"]
            ),
            "candidate_part_count_to_old_part_count": _ratio(
                candidate_metrics["polygon_part_count"], old_metrics["polygon_part_count"]
            ),
            "candidate_area_to_raw_area": _ratio(
                candidate_metrics["area_m2_epsg_2154"], raw_metrics["area_m2_epsg_2154"]
            ),
        },
        "source_app_names": sorted(stages.raw["app"].dropna().astype(str).unique()),
        "retained_app_names": sorted(stages.final["app"].dropna().astype(str).unique()),
        "dropped_app_names": clipping["dropped_app_names"],
        "empty_after_clipping_app_names": clipping["empty_after_clipping_app_names"],
        "clipping": clipping,
    }

    generated_at = datetime.now(timezone.utc).isoformat()
    params = {
        "region": args.region,
        "region_slug": region_slug,
        "run_id": run_id,
        "overlap_clip_enabled": args.overlap_clip,
        "buffer_dist_m": args.buffer,
        "simplify_m": args.simplify,
        "aoc_source_path": str(source_path),
        "old_app_source_path": str(old_path),
        "output_crs": OUTPUT_CRS,
        "working_crs": WORKING_CRS,
        "generated_at": generated_at,
        "script_version": SCRIPT_VERSION,
        "git_commit": _git_commit(project_root),
        "command": shlex.join(sys.argv),
    }

    prepare_output_directory(run_dir, overwrite=args.overwrite)
    candidate_path = run_dir / "candidate.geojson"
    preview_path = run_dir / "preview.png"
    comparison_path = run_dir / "comparison.png"
    metrics_path = run_dir / "metrics.json"
    params_path = run_dir / "params.json"

    print(f"Writing run outputs to {run_dir}")
    stages.final[OUTPUT_COLUMNS].to_file(
        candidate_path,
        driver="GeoJSON",
        engine="pyogrio",
    )
    metrics["candidate_file_size_mb"] = round(candidate_path.stat().st_size / (1024 * 1024), 6)
    write_plots(
        stages.final,
        stages.raw,
        old_region,
        region=args.region,
        run_id=run_id,
        preview_path=preview_path,
        comparison_path=comparison_path,
    )
    _write_json(metrics_path, metrics)
    _write_json(params_path, params)
    return run_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate one development-only AOC simplification experiment.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--region", required=True, help="Exact source region display name.")
    parser.add_argument("--run-id", required=True, help="Readable run identifier.")
    parser.add_argument(
        "--buffer",
        type=non_negative_float,
        default=500.0,
        help="Closing distance in metres.",
    )
    parser.add_argument(
        "--simplify",
        type=non_negative_float,
        default=250.0,
        help="Simplification tolerance in metres.",
    )
    overlap = parser.add_mutually_exclusive_group()
    overlap.add_argument(
        "--overlap-clip",
        dest="overlap_clip",
        action="store_true",
        help="Clip smaller overlapping AOCs.",
    )
    overlap.add_argument(
        "--no-overlap-clip",
        dest="overlap_clip",
        action="store_false",
        help="Keep source AOC overlaps.",
    )
    parser.set_defaults(overlap_clip=False)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing run directory.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        run_dir = run_experiment(args)
    except Exception as exc:
        parser.exit(1, f"error: {exc}\n")
    print(f"Completed experiment: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
