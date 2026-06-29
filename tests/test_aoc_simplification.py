from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import MultiPolygon, Polygon, box

from Development.aoc_simplification.run_experiment import (
    normalise_run_id,
    prepare_output_directory,
)
from Development.aoc_simplification.simplification import (
    calculate_overlap_metrics,
    count_coordinates,
    count_polygon_parts,
    partition_appellations_smallest_first,
    repair_geometry,
    slugify_region,
)


def _partition_frame(rows, *, region="Test Region"):
    return gpd.GeoDataFrame(
        [
            {"region": region, "app": app, "colour": colour, "geometry": geometry}
            for app, geometry, colour in rows
        ],
        geometry="geometry",
        crs="EPSG:2154",
    )


def _geometry_by_app(frame):
    return {str(row["app"]): row.geometry for _, row in frame.iterrows()}


def _diagnostic_by_app(report):
    return {item.app: item for item in report.per_app}


@pytest.mark.parametrize(
    ("display_name", "expected"),
    [
        ("Bordeaux", "bordeaux"),
        ("Rhône", "rhone"),
        ("Sud-Ouest", "sud_ouest"),
        ("Languedoc-Roussillon", "languedoc_roussillon"),
    ],
)
def test_slugify_region(display_name, expected):
    assert slugify_region(display_name) == expected


def test_coordinate_and_polygon_part_counting():
    first = Polygon([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)])
    second = Polygon([(3, 0), (4, 0), (4, 1), (3, 1), (3, 0)])
    geometry = MultiPolygon([first, second])

    assert count_coordinates(geometry) == 10
    assert count_polygon_parts(geometry) == 2


def test_run_id_is_normalised_and_must_not_be_empty():
    assert normalise_run_id("Overlap Close 500!") == "overlap_close_500"
    with pytest.raises(ValueError, match="Run ID"):
        normalise_run_id("---")


def test_output_directory_requires_explicit_overwrite(tmp_path: Path):
    run_dir = tmp_path / "bordeaux" / "close500"
    run_dir.mkdir(parents=True)
    marker = run_dir / "marker.txt"
    marker.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        prepare_output_directory(run_dir, overwrite=False)
    assert marker.exists()

    prepare_output_directory(run_dir, overwrite=True)
    assert run_dir.is_dir()
    assert not marker.exists()


def test_repair_geometry_returns_valid_polygonal_output():
    bow_tie = Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])
    assert not bow_tie.is_valid

    repaired = repair_geometry(bow_tie)

    assert repaired is not None
    assert repaired.is_valid
    assert repaired.geom_type in {"Polygon", "MultiPolygon"}


def test_smallest_wins_for_contained_polygon():
    small = box(1, 1, 3, 3)
    large = box(0, 0, 4, 4)
    source = _partition_frame(
        [("Small", small, "#111111"), ("Large", large, "#222222")]
    )

    partitioned, report = partition_appellations_smallest_first(source)
    result = _geometry_by_app(partitioned)

    assert result["Small"].equals(small)
    assert result["Large"].area == pytest.approx(large.area - small.area)
    assert result["Small"].intersection(result["Large"]).area == pytest.approx(0)
    assert report.overlap_area_before_m2 == pytest.approx(small.area)
    assert report.overlap_area_after_m2 <= report.overlap_tolerance_m2


def test_smallest_wins_for_partial_overlap():
    small = box(0, 0, 2, 2)
    large = box(1, 0, 5, 2)
    source = _partition_frame(
        [("Small", small, "#111111"), ("Large", large, "#222222")]
    )

    partitioned, report = partition_appellations_smallest_first(source)
    result = _geometry_by_app(partitioned)
    diagnostics = _diagnostic_by_app(report)

    assert result["Small"].equals(small)
    assert result["Large"].area == pytest.approx(6)
    assert diagnostics["Large"].removed_overlap_area_m2 == pytest.approx(2)
    assert calculate_overlap_metrics(partitioned).overlap_area_m2 == pytest.approx(0)


def test_three_nested_appellations_follow_complete_area_priority():
    smallest = box(4, 4, 6, 6)
    middle = box(2, 2, 8, 8)
    largest = box(0, 0, 10, 10)
    source = _partition_frame(
        [
            ("Smallest", smallest, "#111111"),
            ("Middle", middle, "#222222"),
            ("Largest", largest, "#333333"),
        ]
    )

    partitioned, report = partition_appellations_smallest_first(source)
    result = _geometry_by_app(partitioned)
    diagnostics = _diagnostic_by_app(report)

    assert result["Smallest"].area == pytest.approx(4)
    assert result["Middle"].area == pytest.approx(32)
    assert result["Largest"].area == pytest.approx(64)
    assert diagnostics["Smallest"].priority_rank == 1
    assert diagnostics["Middle"].priority_rank == 2
    assert diagnostics["Largest"].priority_rank == 3
    assert calculate_overlap_metrics(partitioned).overlap_area_m2 == pytest.approx(0)


def test_disjoint_appellations_remain_unchanged():
    first = box(0, 0, 2, 2)
    second = box(4, 0, 7, 2)
    source = _partition_frame(
        [("First", first, "#111111"), ("Second", second, "#222222")]
    )

    partitioned, report = partition_appellations_smallest_first(source)
    result = _geometry_by_app(partitioned)

    assert result["First"].equals(first)
    assert result["Second"].equals(second)
    assert report.partially_reduced_app_count == 0
    assert report.fully_covered_app_count == 0


def test_equal_area_tie_uses_app_label_order():
    shared = box(0, 0, 2, 2)
    source = _partition_frame(
        [("Zulu", shared, "#111111"), ("Alpha", shared, "#222222")]
    )

    partitioned, report = partition_appellations_smallest_first(source)
    diagnostics = _diagnostic_by_app(report)

    assert list(partitioned["app"]) == ["Alpha"]
    assert diagnostics["Alpha"].priority_rank == 1
    assert diagnostics["Zulu"].priority_rank == 2
    assert diagnostics["Zulu"].became_empty


def test_multipolygon_priority_uses_total_complete_appellation_area():
    complete_multipolygon = MultiPolygon(
        [box(0, 0, 2, 2), box(10, 0, 12, 2)]
    )
    single_polygon = box(1, 0, 4, 2)
    source = _partition_frame(
        [
            ("Composite", complete_multipolygon, "#111111"),
            ("Specific", single_polygon, "#222222"),
        ]
    )

    partitioned, report = partition_appellations_smallest_first(source)
    diagnostics = _diagnostic_by_app(report)
    result = _geometry_by_app(partitioned)

    assert diagnostics["Specific"].priority_area_m2 == pytest.approx(6)
    assert diagnostics["Composite"].priority_area_m2 == pytest.approx(8)
    assert diagnostics["Specific"].priority_rank == 1
    assert result["Specific"].equals(single_polygon)
    assert result["Composite"].area == pytest.approx(6)


def test_fully_covered_broad_appellation_is_reported():
    left = box(0, 0, 2, 4)
    right = box(2, 0, 4, 4)
    broad = box(0, 0, 4, 4)
    source = _partition_frame(
        [
            ("Left", left, "#111111"),
            ("Right", right, "#222222"),
            ("Broad", broad, "#333333"),
        ]
    )

    partitioned, report = partition_appellations_smallest_first(source)
    diagnostics = _diagnostic_by_app(report)

    assert set(partitioned["app"]) == {"Left", "Right"}
    assert report.fully_covered_app_count == 1
    assert report.fully_covered_app_names == ["Broad"]
    assert diagnostics["Broad"].became_empty
    assert diagnostics["Broad"].removed_overlap_percent == pytest.approx(100)


def test_partition_output_is_valid_and_polygonal():
    source = _partition_frame(
        [
            ("Small", box(1, 1, 3, 3), "#111111"),
            ("Large", box(0, 0, 4, 4), "#222222"),
        ]
    )

    partitioned, _ = partition_appellations_smallest_first(source)

    assert partitioned.geometry.is_valid.all()
    assert set(partitioned.geom_type).issubset({"Polygon", "MultiPolygon"})


def test_partition_rejects_wrong_input_contract():
    valid = _partition_frame(
        [("First", box(0, 0, 2, 2), "#111111")]
    )

    multiple_regions = gpd.GeoDataFrame(
        [
            {"region": "One", "app": "A", "colour": "#111111", "geometry": box(0, 0, 1, 1)},
            {"region": "Two", "app": "B", "colour": "#222222", "geometry": box(2, 0, 3, 1)},
        ],
        geometry="geometry",
        crs="EPSG:2154",
    )
    with pytest.raises(ValueError, match="exactly one"):
        partition_appellations_smallest_first(multiple_regions)

    duplicate_app = gpd.GeoDataFrame(
        [valid.iloc[0].to_dict(), valid.iloc[0].to_dict()],
        geometry="geometry",
        crs=valid.crs,
    )
    with pytest.raises(ValueError, match="one complete row per app"):
        partition_appellations_smallest_first(duplicate_app)

    with pytest.raises(ValueError, match="missing required columns"):
        partition_appellations_smallest_first(valid.drop(columns="colour"))


def test_residual_overlap_is_within_reported_tolerance():
    source = _partition_frame(
        [
            ("Small", box(0, 0, 2, 2), "#111111"),
            ("Medium", box(1, 0, 4, 3), "#222222"),
            ("Large", box(-1, -1, 5, 4), "#333333"),
        ]
    )

    partitioned, report = partition_appellations_smallest_first(source)
    overlap = calculate_overlap_metrics(partitioned)

    assert overlap.overlap_area_m2 <= report.overlap_tolerance_m2
    assert report.overlap_area_after_m2 == pytest.approx(overlap.overlap_area_m2)
