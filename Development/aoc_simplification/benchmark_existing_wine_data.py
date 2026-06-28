"""Benchmark the existing deployed Wine GeoJSON.

Development-only helper. It reads assets/data/wine_regions_cleaned.geojson and
writes small JSON/CSV summaries under Development/WineData/generated/.
It does not modify production data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = PROJECT_ROOT / "assets" / "data" / "wine_regions_cleaned.geojson"
DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT
    / "Development"
    / "WineData"
    / "generated"
    / "aoc_simplification_benchmark"
)
REGION_COLUMN_CANDIDATES = ("region", "Region", "REGION", "name", "Name", "nom", "Nom")


def count_coordinates(geom) -> int:
    if geom is None or geom.is_empty:
        return 0
    geom_type = geom.geom_type
    if geom_type == "Point":
        return 1
    if geom_type == "MultiPoint":
        return sum(count_coordinates(part) for part in geom.geoms)
    if geom_type in {"LineString", "LinearRing"}:
        return len(geom.coords)
    if geom_type == "MultiLineString":
        return sum(count_coordinates(part) for part in geom.geoms)
    if geom_type == "Polygon":
        exterior = len(geom.exterior.coords) if geom.exterior else 0
        interiors = sum(len(ring.coords) for ring in geom.interiors)
        return exterior + interiors
    if geom_type == "MultiPolygon":
        return sum(count_coordinates(part) for part in geom.geoms)
    if geom_type == "GeometryCollection":
        return sum(count_coordinates(part) for part in geom.geoms)
    return 0


def count_polygon_parts(geom) -> int:
    if geom is None or geom.is_empty:
        return 0
    geom_type = geom.geom_type
    if geom_type == "Polygon":
        return 1
    if geom_type == "MultiPolygon":
        return len(geom.geoms)
    if geom_type == "GeometryCollection":
        return sum(count_polygon_parts(part) for part in geom.geoms)
    return 0


def detect_region_column(columns: list[str]) -> str | None:
    for candidate in REGION_COLUMN_CANDIDATES:
        if candidate in columns:
            return candidate
    return None


def series_to_jsonable(value):
    return value.item() if hasattr(value, "item") else value


def benchmark(source: Path, output_dir: Path) -> tuple[Path, Path, dict[str, object]]:
    import geopandas as gpd

    if not source.exists():
        raise FileNotFoundError(source)

    gdf = gpd.read_file(source, engine="pyogrio")
    columns = list(gdf.columns)
    region_column = detect_region_column(columns)
    metric_gdf = gdf.to_crs("EPSG:2154") if gdf.crs is not None else gdf

    invalid_mask = ~gdf.geometry.is_valid
    empty_mask = gdf.geometry.is_empty
    geometry_type_counts = {
        str(key): int(value)
        for key, value in gdf.geometry.geom_type.value_counts().sort_index().items()
    }

    region_names: list[str] = []
    region_rows = []
    if region_column:
        region_names = sorted(gdf[region_column].dropna().astype(str).unique())
        for region, group in gdf.groupby(region_column, sort=True):
            metric_group = metric_gdf.loc[group.index]
            bounds = group.total_bounds
            region_rows.append(
                {
                    "region_column": region_column,
                    "region": str(region),
                    "feature_count": int(len(group)),
                    "coordinate_count": int(group.geometry.apply(count_coordinates).sum()),
                    "geometry_part_count": int(group.geometry.apply(count_polygon_parts).sum()),
                    "invalid_geometry_count": int((~group.geometry.is_valid).sum()),
                    "empty_geometry_count": int(group.geometry.is_empty.sum()),
                    "minx": float(bounds[0]),
                    "miny": float(bounds[1]),
                    "maxx": float(bounds[2]),
                    "maxy": float(bounds[3]),
                    "area_m2": float(metric_group.geometry.area.sum()),
                }
            )

    summary = {
        "source_path": str(source),
        "source_file_size_bytes": int(source.stat().st_size),
        "source_file_size_mb": round(source.stat().st_size / (1024 * 1024), 3),
        "crs": str(gdf.crs) if gdf.crs is not None else None,
        "feature_count": int(len(gdf)),
        "region_column_detected": region_column,
        "region_names_present": region_names,
        "region_count": len(region_names) if region_column else None,
        "property_columns": [column for column in columns if column != "geometry"],
        "all_columns": columns,
        "geometry_type_counts": geometry_type_counts,
        "invalid_geometry_count": int(invalid_mask.sum()),
        "empty_geometry_count": int(empty_mask.sum()),
        "total_coordinate_count": int(gdf.geometry.apply(count_coordinates).sum()),
        "total_geometry_part_count": int(gdf.geometry.apply(count_polygon_parts).sum()),
        "total_bounds": [float(value) for value in gdf.total_bounds],
        "total_area_m2_epsg_2154": float(metric_gdf.geometry.area.sum()),
        "region_column_note": (
            f"Detected region column {region_column!r}."
            if region_column
            else f"No region column detected from candidates: {REGION_COLUMN_CANDIDATES}."
        ),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "old_wine_regions_benchmark.json"
    csv_path = output_dir / "old_wine_regions_by_region.csv"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    if region_rows:
        import pandas as pd

        frame = pd.DataFrame(region_rows)
        frame.to_csv(csv_path, index=False)
    else:
        csv_path.write_text(
            "region_column,region,feature_count,coordinate_count,geometry_part_count,"
            "invalid_geometry_count,empty_geometry_count,minx,miny,maxx,maxy,area_m2\n",
            encoding="utf-8",
        )

    return json_path, csv_path, summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark the existing deployed wine_regions_cleaned.geojson.",
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        json_path, csv_path, summary = benchmark(args.source.resolve(), args.output_dir.resolve())
    except Exception as exc:
        parser.exit(1, f"error: {exc}\n")

    print(f"benchmark_json: {json_path}")
    print(f"by_region_csv: {csv_path}")
    print(f"file_size_mb: {summary['source_file_size_mb']}")
    print(f"feature_count: {summary['feature_count']}")
    print(f"region_column_detected: {summary['region_column_detected']}")
    print(f"region_count: {summary['region_count']}")
    print(f"total_coordinate_count: {summary['total_coordinate_count']}")
    print(f"total_geometry_part_count: {summary['total_geometry_part_count']}")
    print(f"invalid_geometry_count: {summary['invalid_geometry_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
