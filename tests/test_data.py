import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, Polygon

from app.app_data import _validate_wine_data, wine_feature_id


def _assert_string_like_values(frame, column):
    values = frame[column].dropna()

    assert not values.empty
    assert values.map(lambda value: isinstance(value, str)).all()


def test_core_data_frames_load(data_boundary):
    assert isinstance(data_boundary.all_france, pd.DataFrame)
    assert isinstance(data_boundary.all_monaco, pd.DataFrame)
    assert isinstance(data_boundary.region_df, gpd.GeoDataFrame)
    assert isinstance(data_boundary.department_df, gpd.GeoDataFrame)
    assert isinstance(data_boundary.arron_df, gpd.GeoDataFrame)
    assert isinstance(data_boundary.paris_df, gpd.GeoDataFrame)
    assert isinstance(data_boundary.monaco_df, gpd.GeoDataFrame)
    assert isinstance(data_boundary.wine_df, gpd.GeoDataFrame)

    assert not data_boundary.all_france.empty
    assert not data_boundary.all_monaco.empty
    assert not data_boundary.region_df.empty
    assert not data_boundary.department_df.empty
    assert not data_boundary.arron_df.empty
    assert not data_boundary.paris_df.empty
    assert not data_boundary.monaco_df.empty
    assert not data_boundary.wine_df.empty


def test_identifier_columns_keep_string_semantics(data_boundary):
    _assert_string_like_values(data_boundary.all_france, "department_num")
    _assert_string_like_values(data_boundary.all_monaco, "department_num")
    _assert_string_like_values(data_boundary.department_df, "code")
    _assert_string_like_values(data_boundary.arron_df, "code")
    _assert_string_like_values(data_boundary.arron_df, "department_num")
    _assert_string_like_values(data_boundary.paris_df, "code")
    _assert_string_like_values(data_boundary.paris_df, "department_num")
    _assert_string_like_values(data_boundary.monaco_df, "code")


def test_derived_data_collections_are_available(data_boundary):
    assert data_boundary.unique_regions
    assert data_boundary.initial_options
    assert data_boundary.dept_to_code
    assert data_boundary.region_to_name
    assert not data_boundary.geo_df.empty

    combined = data_boundary.get_combined_restaurant_data(include_monaco=True)
    assert len(combined) >= len(data_boundary.all_france)

    geo_with_monaco = data_boundary.get_geo_df(include_monaco=True)
    assert not geo_with_monaco.empty
    assert len(geo_with_monaco) >= len(data_boundary.geo_df)


def _wine_frame(rows, geometries):
    return gpd.GeoDataFrame(rows, geometry=geometries, crs="EPSG:4326")


def test_wine_feature_ids_are_deterministic_and_unique(data_boundary):
    wine_df = data_boundary.wine_df
    expected = [
        wine_feature_id(region, app)
        for region, app in wine_df[["region", "app"]].itertuples(index=False, name=None)
    ]

    assert wine_df["feature_id"].tolist() == expected
    assert wine_df["feature_id"].is_unique

    reversed_frame = _validate_wine_data(
        wine_df.drop(columns="feature_id").iloc[::-1].reset_index(drop=True)
    )
    assert reversed_frame.set_index(["region", "app"])["feature_id"].to_dict() == (
        wine_df.set_index(["region", "app"])["feature_id"].to_dict()
    )


def test_wine_region_app_pairs_must_be_unique():
    frame = _wine_frame(
        [
            {"region": "Test", "app": "Repeated", "colour": "#123456"},
            {"region": "Test", "app": "Repeated", "colour": "#123456"},
        ],
        [
            Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]),
            Polygon([(2, 2), (3, 2), (3, 3), (2, 2)]),
        ],
    )

    with pytest.raises(RuntimeError, match=r"duplicate \(region, app\) pairs"):
        _validate_wine_data(frame)


def test_wine_geometry_types_are_limited_to_polygon_and_multipolygon(data_boundary):
    assert set(data_boundary.wine_df.geometry.geom_type) == {"Polygon", "MultiPolygon"}

    frame = _wine_frame(
        [{"region": "Test", "app": "Point AOC", "colour": "#123456"}],
        [Point(0, 0)],
    )
    with pytest.raises(RuntimeError, match="unsupported geometry types: Point"):
        _validate_wine_data(frame)


def test_wine_parent_region_must_have_one_colour():
    frame = _wine_frame(
        [
            {"region": "Test", "app": "First", "colour": "#123456"},
            {"region": "Test", "app": "Second", "colour": "#654321"},
        ],
        [
            Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]),
            Polygon([(2, 2), (3, 2), (3, 3), (2, 2)]),
        ],
    )

    with pytest.raises(RuntimeError, match="exactly one colour: Test"):
        _validate_wine_data(frame)
