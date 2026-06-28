"""Reusable geometry operations for Wine AOC simplification experiments."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any

import geopandas as gpd
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

try:
    from shapely import make_valid
except ImportError:  # pragma: no cover - compatibility with older Shapely
    from shapely.validation import make_valid


WORKING_CRS = "EPSG:2154"
OUTPUT_CRS = "EPSG:4326"
OUTPUT_COLUMNS = ["region", "app", "colour", "geometry"]


@dataclass(frozen=True)
class ClippingReport:
    source_app_count: int
    retained_app_count: int
    dropped_app_names: list[str]
    empty_after_clipping_app_names: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_app_count": self.source_app_count,
            "retained_app_count": self.retained_app_count,
            "dropped_app_names": self.dropped_app_names,
            "empty_after_clipping_app_names": self.empty_after_clipping_app_names,
        }


@dataclass
class RegionStages:
    raw: gpd.GeoDataFrame
    repaired: gpd.GeoDataFrame
    overlap_clipped: gpd.GeoDataFrame | None
    dissolved: gpd.GeoDataFrame
    closed: gpd.GeoDataFrame
    final: gpd.GeoDataFrame
    clipping_report: ClippingReport


def slugify_region(value: object) -> str:
    """Return a lowercase ASCII slug while preserving the display value elsewhere."""
    normalized = unicodedata.normalize("NFKD", str(value).strip())
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = "".join(character.lower() if character.isalnum() else "_" for character in ascii_value)
    slug = "_".join(part for part in slug.split("_") if part)
    return slug


def _polygon_parts(geom) -> list:
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    if geom.geom_type in {"MultiPolygon", "GeometryCollection"}:
        parts = []
        for child in geom.geoms:
            parts.extend(_polygon_parts(child))
        return parts
    return []


def repair_geometry(geom):
    """Repair a geometry and retain only non-empty polygonal components."""
    if geom is None or geom.is_empty:
        return None

    repaired = geom
    if not geom.is_valid:
        try:
            repaired = make_valid(geom, method="structure", keep_collapsed=False)
        except TypeError:
            repaired = make_valid(geom)
        except Exception:
            repaired = geom

    if repaired is not None and not repaired.is_empty and not repaired.is_valid:
        try:
            repaired = repaired.buffer(0)
        except Exception:
            return None

    parts = _polygon_parts(repaired)
    if not parts:
        return None
    result = parts[0] if len(parts) == 1 else MultiPolygon(parts)
    if not result.is_valid:
        try:
            result = result.buffer(0)
        except Exception:
            return None
        parts = _polygon_parts(result)
        if not parts:
            return None
        result = parts[0] if len(parts) == 1 else MultiPolygon(parts)
    return result if result.geom_type in {"Polygon", "MultiPolygon"} else None


def repair_frame(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    repaired = gdf.copy()
    repaired.geometry = repaired.geometry.apply(repair_geometry)
    repaired = repaired.loc[repaired.geometry.notna()].copy()
    repaired = repaired.loc[~repaired.geometry.is_empty].copy()
    return repaired.reset_index(drop=True)


def project_for_operations(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError("Input geometry has no CRS; EPSG:4326 source data is required.")
    return gdf.to_crs(WORKING_CRS)


def reproject_for_output(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError("Processed geometry has no CRS.")
    return gdf.to_crs(OUTPUT_CRS)


def _app_names(gdf: gpd.GeoDataFrame) -> list[str]:
    if "app" not in gdf.columns:
        return []
    return sorted(gdf["app"].dropna().astype(str).unique().tolist())


def clip_overlapping_aocs(
    gdf: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, ClippingReport]:
    """Give larger AOC rows priority and subtract already-retained coverage."""
    source_apps = _app_names(gdf)
    ordered = gdf.copy()
    ordered["_area"] = ordered.geometry.area
    ordered["_source_order"] = range(len(ordered))
    ordered = ordered.sort_values(
        ["_area", "app", "_source_order"],
        ascending=[False, True, True],
        kind="mergesort",
    )

    rows = []
    kept_geometries = []
    emptied_apps: set[str] = set()
    for _, row in ordered.iterrows():
        geom = row.geometry
        if kept_geometries:
            geom = geom.difference(unary_union(kept_geometries))
        geom = repair_geometry(geom)
        if geom is None or geom.is_empty:
            emptied_apps.add(str(row["app"]))
            continue
        values = row.drop(labels=["_area", "_source_order"]).to_dict()
        values["geometry"] = geom
        rows.append(values)
        kept_geometries.append(geom)

    clipped = gpd.GeoDataFrame(rows, geometry="geometry", crs=gdf.crs)
    if clipped.empty:
        clipped = gpd.GeoDataFrame(columns=list(gdf.columns), geometry="geometry", crs=gdf.crs)
    retained_apps = _app_names(clipped)
    report = ClippingReport(
        source_app_count=len(source_apps),
        retained_app_count=len(retained_apps),
        dropped_app_names=sorted(set(source_apps) - set(retained_apps)),
        empty_after_clipping_app_names=sorted(emptied_apps),
    )
    return clipped.reset_index(drop=True), report


def dissolve_by_app(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    dissolved = gdf[OUTPUT_COLUMNS].dissolve(
        by=["region", "app", "colour"],
        as_index=False,
        sort=True,
    )
    return repair_frame(dissolved[OUTPUT_COLUMNS])


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
    if geom_type in {"MultiPolygon", "GeometryCollection"}:
        return sum(count_coordinates(part) for part in geom.geoms)
    return 0


def count_polygon_parts(geom) -> int:
    if geom is None or geom.is_empty:
        return 0
    if geom.geom_type == "Polygon":
        return 1
    if geom.geom_type in {"MultiPolygon", "GeometryCollection"}:
        return sum(count_polygon_parts(part) for part in geom.geoms)
    return 0


def approximate_geojson_size_mb(gdf: gpd.GeoDataFrame) -> float:
    if gdf.empty:
        return 0.0
    output = reproject_for_output(gdf)
    return len(output.to_json().encode("utf-8")) / (1024 * 1024)


def metrics_for_frame(gdf: gpd.GeoDataFrame | None) -> dict[str, Any]:
    if gdf is None or gdf.empty:
        return {
            "feature_count": 0,
            "app_count": 0,
            "coordinate_count": 0,
            "polygon_part_count": 0,
            "invalid_geometry_count": 0,
            "empty_geometry_count": 0,
            "approx_geojson_size_mb": 0.0,
            "area_m2_epsg_2154": 0.0,
        }
    metric = project_for_operations(gdf)
    geometries = gdf.geometry.dropna()
    return {
        "feature_count": int(len(gdf)),
        "app_count": int(gdf["app"].nunique()) if "app" in gdf.columns else 0,
        "coordinate_count": int(geometries.apply(count_coordinates).sum()),
        "polygon_part_count": int(geometries.apply(count_polygon_parts).sum()),
        "invalid_geometry_count": int((~geometries.is_valid).sum()),
        "empty_geometry_count": int(geometries.is_empty.sum() + gdf.geometry.isna().sum()),
        "approx_geojson_size_mb": round(approximate_geojson_size_mb(gdf), 6),
        "area_m2_epsg_2154": float(metric.geometry.area.sum()),
    }


def process_region(
    source_region: gpd.GeoDataFrame,
    *,
    overlap_clip: bool = False,
    buffer_dist_m: float = 500,
    simplify_m: float = 250,
) -> RegionStages:
    if buffer_dist_m < 0 or simplify_m < 0:
        raise ValueError("Buffer and simplification distances must be non-negative.")
    if source_region.empty:
        raise ValueError("Selected region contains no source rows.")

    raw = source_region[OUTPUT_COLUMNS].copy().reset_index(drop=True)
    repaired = repair_frame(project_for_operations(raw))
    source_apps = _app_names(repaired)
    clipping_report = ClippingReport(len(source_apps), len(source_apps), [], [])

    if overlap_clip:
        overlap_clipped, clipping_report = clip_overlapping_aocs(repaired)
        dissolve_input = overlap_clipped
    else:
        overlap_clipped = None
        dissolve_input = repaired

    if dissolve_input.empty:
        raise ValueError("No polygon geometry remained before dissolve.")
    dissolved = dissolve_by_app(dissolve_input)

    closed = dissolved.copy()
    if buffer_dist_m > 0:
        closed.geometry = closed.geometry.buffer(buffer_dist_m).buffer(-buffer_dist_m)
        closed = repair_frame(closed)
    if closed.empty:
        raise ValueError("No polygon geometry remained after morphological closing.")

    simplified = closed.copy()
    if simplify_m > 0:
        simplified.geometry = simplified.geometry.simplify(
            simplify_m,
            preserve_topology=True,
        )
    final = reproject_for_output(repair_frame(simplified))[OUTPUT_COLUMNS]
    if final.empty:
        raise ValueError("No polygon geometry remained after final simplification and repair.")

    return RegionStages(
        raw=raw,
        repaired=repaired,
        overlap_clipped=overlap_clipped,
        dissolved=dissolved,
        closed=closed,
        final=final.reset_index(drop=True),
        clipping_report=clipping_report,
    )
