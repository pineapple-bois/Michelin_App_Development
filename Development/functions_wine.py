import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib-cache"))

import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np
import pyproj
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

try:
    from sklearn.cluster import DBSCAN
except ImportError:  # Optional notebook-only simplification path.
    DBSCAN = None

try:
    import alphashape
except ImportError:  # Optional; alpha simplification falls back to convex hull.
    alphashape = None


def _require_optional_dependency(dependency, package_name, purpose):
    if dependency is None:
        raise RuntimeError(
            f"{package_name} is required for {purpose}. "
            "Install the wine-development dependencies before running this notebook path."
        )


def plot_choropleth_wine(
    df,
    wine_gdf,
    title,
    restaurants=False,
    star_rating=None,
    figsize=(10, 10),
    colour_col="colour",
):
    """
    Function to plot a base map and optionally wine regions and restaurant locations.

    Args:
        df (GeoDataFrame): The DataFrame containing the base data.
        wine_gdf (GeoDataFrame): GeoDataFrame with wine regions.
        title (str): The title of the plot.
        restaurants (bool): If True, plot restaurant locations. Default is False.
        star_rating (int): Default is None = 'all'.
        figsize (tuple): The size of the figure. Default is (10, 10).

    Returns:
        None
    """

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    df = df.to_crs("EPSG:2154")  # RGF93 / Lambert-93
    df.boundary.plot(linewidth=0.8, edgecolor='0.8', ax=ax)

    # Process the wine GeoDataFrame
    wine_gdf = wine_gdf.to_crs("EPSG:2154")
    union_geometry = df.unary_union
    wine_gdf = wine_gdf[wine_gdf.geometry.intersects(union_geometry)]
    if colour_col not in wine_gdf.columns and "colours" in wine_gdf.columns:
        colour_col = "colours"
    wine_gdf.plot(ax=ax, color=wine_gdf[colour_col])

    all_handles = []
    added_labels = set()

    # Plot restaurants if needed
    if restaurants:
        star_colors = {'1': 'green', '2': 'orange', '3': 'red'}
        transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)

        if star_rating is not None:
            star_colors = {str(star_rating): star_colors[str(star_rating)]}

        for star, color in star_colors.items():
            for _, row in df.iterrows():
                locations = row['locations']
                if star in locations and locations[star] is not None:
                    for lat, lon in locations[star]:
                        x, y = transformer.transform(lon, lat)
                        ax.scatter(x, y, c=color, s=50, marker='d')

            if star not in added_labels:
                all_handles.append(
                    Line2D([0], [0], marker='d', color=color, label=f"{star} star restaurant", markersize=8,
                           linestyle='None'))
                added_labels.add(star)

    # Add legend for wine regions
    wine_colors = wine_gdf[colour_col].unique()
    wine_regions = [wine_gdf[wine_gdf[colour_col] == color]['region'].iloc[0] for color in wine_colors]
    wine_legend_handles = [Patch(facecolor=color, edgecolor=color, label=region) for region, color in
                           zip(wine_regions, wine_colors)]
    all_handles.extend(wine_legend_handles)

    ax.legend(handles=all_handles, loc='upper left', bbox_to_anchor=(1.05, 1), title="Legend", borderaxespad=0.)

    plt.suptitle(title)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')

    plt.tight_layout()
    plt.show()


def plot_coloured_aoc_map(aoc_df, colour_col="colour", figsize=(10, 10)):
    """
    Plot AOC wine regions coloured by region, with a legend.

    Args:
        aoc_df (GeoDataFrame): AOC polygons with 'region' and colour info.
        colour_col (str): Name of the column containing colour values.
        figsize (tuple): Figure size.
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    aoc_df = aoc_df.to_crs("EPSG:2154")

    # Plot filled AOCs
    aoc_df.plot(ax=ax, color=aoc_df[colour_col], linewidth=0.05, edgecolor="0.8")

    # Create legend from region-colour mapping
    region_color_pairs = aoc_df.drop_duplicates(subset=["region", colour_col])[["region", colour_col]]
    handles = [
        Patch(facecolor=row[colour_col], edgecolor="black", label=row["region"])
        for _, row in region_color_pairs.iterrows()
    ]

    ax.legend(handles=handles, title="Region", loc='upper left', bbox_to_anchor=(1.05, 1), borderaxespad=0.)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.axis("off")

    plt.tight_layout()
    plt.show()


def cluster_merge_and_simplify(gdf, region, distance_threshold=5000, tolerance=300):
    _require_optional_dependency(DBSCAN, "scikit-learn", "DBSCAN-based cluster merging")

    print(f"🔁 Clustering fallback for region: {region}")
    region_df = gdf[gdf["region"] == region].copy()
    region_df["geometry"] = region_df["geometry"].apply(lambda geom: geom if geom.is_valid else geom.buffer(0))
    region_df = region_df.explode(index_parts=False)

    coords = np.array([[geom.centroid.x, geom.centroid.y] for geom in region_df.geometry])
    clustering = DBSCAN(eps=distance_threshold, min_samples=1).fit(coords)
    region_df["cluster"] = clustering.labels_

    clusters = region_df.dissolve(by="cluster")
    clusters["geometry"] = clusters["geometry"].simplify(tolerance=tolerance, preserve_topology=True)
    final_geom = unary_union(clusters.geometry)

    return gpd.GeoDataFrame({"region": [region], "geometry": [final_geom]}, crs=gdf.crs)


def robust_union_and_simplify(df, region, tolerance=300, distance_threshold=5000):
    print(f"🛠 Fallback union: {region}")
    region_df = df[df["region"] == region].copy()
    region_df["geometry"] = region_df["geometry"].apply(lambda g: g if g.is_valid else g.buffer(0))
    region_df = region_df[~region_df.geometry.is_empty]

    try:
        merged_geom = unary_union(region_df.geometry)
        simplified = gpd.GeoDataFrame(
            {"region": [region], "geometry": [merged_geom.simplify(tolerance, preserve_topology=True)]},
            crs=df.crs
        )
        return simplified
    except Exception as e:
        print(f"❌ Union failed on {region}: {e}")
        # Try clustering instead
        return cluster_merge_and_simplify(df, region, distance_threshold, tolerance)


def robust_dissolve_and_simplify(df, region, tolerance=300, distance_threshold=5000):
    """
    Attempts to dissolve and simplify a region. Falls back to union, then cluster-merge if needed.
    """
    try:
        print(f"Processing: {region}")
        part = df[df["region"] == region].dissolve(by="region", as_index=False)
        part["geometry"] = part["geometry"].buffer(0)
        part["geometry"] = part["geometry"].simplify(tolerance=tolerance, preserve_topology=True)
        return part
    except Exception as e:
        print(f"⚠️ Standard dissolve failed for {region}: {e}")
        return robust_union_and_simplify(df, region, tolerance, distance_threshold)

def drop_small_parts(geom, min_area=10_000_000):  # 10 km²
    if isinstance(geom, MultiPolygon):
        parts = [p for p in geom.geoms if p.area >= min_area]
        return MultiPolygon(parts)
    return geom if geom.area >= min_area else None


"""

```python
all_regions = gpd.GeoDataFrame(
    pd.concat(
        [robust_dissolve_and_simplify(aoc_final, r, tolerance=100000, distance_threshold=100000)
         for r in aoc_final["region"].unique()],
        ignore_index=True
    ),
    crs=aoc_final.crs
)
```

"""


def super_simplify_aoc_extremities(
    row, original_crs, crs_target="EPSG:2154",
    simplify_tol=5000, smooth_buffer=None, preserve_topology=True
):
    """
    Aggressively simplifies an AOC geometry by creating a polygon from the extremities.
    This version computes the convex hull of the union of all parts.

    Steps:
    1. Reproject to a target metric CRS.
    2. Explode multipolygons and fix invalid geometries.
    3. Unify the parts with a unary_union and compute the convex hull.
    4. Optionally smooth the hull with a buffering trick.
    5. Simplify the hull and force it to a single Polygon.

    Parameters:
        row (GeoSeries): A row from a GeoDataFrame, containing 'geometry', 'region', 'app', and 'colour'.
        original_crs (str or CRS): The original CRS of the input geometry.
        crs_target (str): Target projected CRS for operations.
        simplify_tol (float): Tolerance for geometry simplification.
        smooth_buffer (float or None): Optional smoothing buffer radius.
        preserve_topology (bool): Whether to preserve topology during simplify.

    Returns:
        GeoDataFrame: A single-row GeoDataFrame with the simplified convex-hull Polygon.
    """
    region_name = row["region"]
    app_name = row["app"]
    colour = row["colour"]
    geom = row["geometry"]

    # Reproject geometry to the target CRS
    gdf = gpd.GeoDataFrame({"geometry": [geom]}, crs=original_crs).to_crs(crs_target)

    # Explode multipolygons and fix any invalid geometries
    exploded = gdf.explode(index_parts=False)
    exploded["geometry"] = exploded["geometry"].apply(lambda g: g if g.is_valid else g.buffer(0))
    exploded = exploded[~exploded.geometry.is_empty]

    # Merge all parts and compute the convex hull from the extremities
    merged_geom = unary_union(exploded.geometry)
    hull = merged_geom.convex_hull

    # Optional smoothing with morphological buffering
    if smooth_buffer is not None:
        try:
            hull = hull.buffer(smooth_buffer).buffer(-smooth_buffer)
        except Exception as e:
            print(f"⚠️ Buffering failed for {app_name}: {e}")

    # Simplify the hull
    try:
        simplified = hull.simplify(simplify_tol, preserve_topology=preserve_topology)
        if simplified.is_empty:
            print(f"⚠️ Simplify emptied {app_name}, fallback to hull")
            simplified = hull
    except Exception as e:
        print(f"❌ Simplify failed for {app_name}: {e}")
        simplified = hull

    print(f"✅ AOC {app_name} → polygon with area {simplified.area:.2f}")

    return gpd.GeoDataFrame(
        {"region": [region_name], "aoc": [app_name], "geometry": [simplified], "colour": [colour]},
        crs=crs_target
    )

"""

```python
aoc_simplified = gpd.GeoDataFrame(
    pd.concat(
        [super_simplify_aoc_extremities(
            row, aoc_final.crs,
            simplify_tol=1000, smooth_buffer=None,
            preserve_topology=True
        ) for _, row in aoc_final.iterrows()],
        ignore_index=True
    ),
    crs="EPSG:2154"
)
```

"""


def super_simplify_aoc_alpha(
    row, original_crs, crs_target="EPSG:2154",
    alpha_param=1.0, simplify_tol=500, smooth_buffer=None,
    preserve_topology=True, area_threshold=1e-4
):
    """
    Simplifies an AOC geometry using an alpha shape to create a polygon with
    irregular, more natural boundaries. If the alpha shape produces a degenerate
    result (empty or near zero area), falls back to a convex hull.

    Parameters:
        row (GeoSeries): A row containing 'geometry', 'region', 'app', and 'colour'.
        original_crs (str or CRS): The original CRS of the input geometry.
        crs_target (str): Target projected CRS for operations.
        alpha_param (float): Parameter for the alpha shape (controls concavity).
        simplify_tol (float): Tolerance for geometry simplification (in CRS units).
        smooth_buffer (float or None): Optional smoothing buffer radius.
        preserve_topology (bool): Whether to preserve topology during simplification.
        area_threshold (int):

    Returns:
        GeoDataFrame: A single-row GeoDataFrame with the resulting polygon.
    """
    region_name = row["region"]
    app_name = row["app"]
    colour = row["colour"]
    geom = row["geometry"]


    try:
        # Reproject to metric CRS
        gdf = gpd.GeoDataFrame({"geometry": [geom]}, crs=original_crs).to_crs(crs_target)

        # Explode and fix geometries
        exploded = gdf.explode(index_parts=False)
        exploded["geometry"] = exploded["geometry"].apply(lambda g: g if g.is_valid else g.buffer(0))
        exploded = exploded[~exploded.geometry.is_empty]

        if exploded.empty:
            print(f"⚠️ {app_name} has no valid geometry after explode")
            return None

        merged_geom = unary_union(exploded.geometry)

        # Extract points: include exteriors + interiors
        points = []
        if merged_geom.geom_type == "Polygon":
            points.extend(merged_geom.exterior.coords)
            for ring in merged_geom.interiors:
                points.extend(ring.coords)
        elif merged_geom.geom_type == "MultiPolygon":
            for poly in merged_geom.geoms:
                points.extend(poly.exterior.coords)
                for ring in poly.interiors:
                    points.extend(ring.coords)
        else:
            points.extend(merged_geom.coords)

        # Alpha shape (fallback: convex hull)
        try:
            if alphashape is None:
                raise RuntimeError("alphashape is not installed")
            alpha_geom = alphashape.alphashape(points, alpha_param)
            if not alpha_geom or alpha_geom.area < area_threshold:
                print(f"⚠️ Degenerate alpha for {app_name}, fallback to convex hull")
                alpha_geom = merged_geom.convex_hull
        except Exception as e:
            print(f"❌ Alpha shape failed for {app_name}: {e}")
            alpha_geom = merged_geom.convex_hull

        # Optional smoothing
        if smooth_buffer:
            try:
                alpha_geom = alpha_geom.buffer(smooth_buffer).buffer(-smooth_buffer)
            except Exception as e:
                print(f"⚠️ Buffering failed for {app_name}: {e}")

        # Simplify
        try:
            simplified = alpha_geom.simplify(simplify_tol, preserve_topology=preserve_topology)
            if simplified.is_empty or simplified.area < area_threshold:
                print(f"⚠️ Simplify emptied {app_name}, fallback to alpha_geom")
                simplified = alpha_geom
        except Exception as e:
            print(f"❌ Simplify failed for {app_name}: {e}")
            simplified = alpha_geom

        # Reduce to largest polygon if MultiPolygon
        if simplified.geom_type == "MultiPolygon":
            parts = list(simplified.geoms)
            simplified = max(parts, key=lambda p: p.area)

        # Clean again if needed
        if not simplified.is_valid:
            simplified = simplified.buffer(0)

        # Final CRS check
        if isinstance(simplified, (Polygon, MultiPolygon)):
            simplified = gpd.GeoSeries([simplified], crs=crs_target).iloc[0]
        else:
            print(f"⚠️ Unexpected geometry type for {app_name}: {simplified.geom_type}")
            return None

        area_ha = gpd.GeoSeries([simplified], crs=crs_target).area.iloc[0] / 10_000  # m² → ha
        print(f"✅ AOC {app_name} → polygon with area {area_ha:.2f} ha")

        return gpd.GeoDataFrame(
            {"region": [region_name], "aoc": [app_name], "geometry": [simplified], "colour": [colour]},
            crs=crs_target
        )

    except Exception as e:
        print(f"❌ Full failure for {app_name}: {e}")
        return None

"""

```python

aoc_simplified_alpha = gpd.GeoDataFrame(
    pd.concat(
        [super_simplify_aoc_alpha(
            row, aoc_final.crs,
            alpha_param=1.0, simplify_tol=1000,
            smooth_buffer=None, preserve_topology=True
        ) for _, row in aoc_final.iterrows()],
        ignore_index=True
    ),
    crs="EPSG:2154"
)

```


"""
