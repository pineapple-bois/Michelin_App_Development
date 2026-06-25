import geopandas as gpd
import pandas as pd


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
