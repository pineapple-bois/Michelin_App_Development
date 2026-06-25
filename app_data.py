from dataclasses import dataclass

import geopandas as gpd
import pandas as pd
from pandas.api.types import is_numeric_dtype

from app_config import CONFIG, RuntimeConfig


RESTAURANT_COLUMNS = (
    "name",
    "address",
    "location",
    "arrondissement",
    "department_num",
    "department",
    "capital",
    "region",
    "price",
    "cuisine",
    "url",
    "award",
    "stars",
    "greenstar",
    "longitude",
    "latitude",
)

AGGREGATE_COUNT_COLUMNS = (
    "selected",
    "bib_gourmand",
    "1_star",
    "2_star",
    "3_star",
    "total_stars",
    "starred_restaurants",
    "green_stars",
)

DEMOGRAPHIC_COLUMNS = (
    "GDP_millions(€)",
    "GDP_per_capita(€)",
    "poverty_rate(%)",
    "average_annual_unemployment_rate(%)",
    "average_net_hourly_wage(€)",
    "municipal_population",
    "population_density(inhabitants/sq_km)",
    "area(sq_km)",
)

REGION_COLUMNS = ("region", *AGGREGATE_COUNT_COLUMNS, *DEMOGRAPHIC_COLUMNS, "locations", "geometry")
DEPARTMENT_COLUMNS = (
    "code",
    "department",
    "capital",
    "region",
    *AGGREGATE_COUNT_COLUMNS,
    *DEMOGRAPHIC_COLUMNS,
    "locations",
    "geometry",
)
ARRONDISSEMENT_COLUMNS = (
    "code",
    "arrondissement",
    "department_num",
    "department",
    "capital",
    "region",
    *AGGREGATE_COUNT_COLUMNS,
    "municipal_population",
    "population_density(inhabitants/sq_km)",
    "poverty_rate(%)",
    "average_net_hourly_wage(€)",
    "locations",
    "geometry",
)
PARIS_COLUMNS = (
    "code",
    "arrondissement",
    "department_num",
    "department",
    "capital",
    "region",
    "green_stars",
    "selected",
    "bib_gourmand",
    "1_star",
    "2_star",
    "3_star",
    "total_stars",
    "starred_restaurants",
    "locations",
    "geometry",
)
WINE_COLUMNS = ("region", "colour", "geometry")


@dataclass(frozen=True)
class MichelinData:
    all_france: pd.DataFrame
    all_monaco: pd.DataFrame
    region_df: gpd.GeoDataFrame
    department_df: gpd.GeoDataFrame
    arron_df: gpd.GeoDataFrame
    paris_df: gpd.GeoDataFrame
    monaco_df: gpd.GeoDataFrame
    wine_df: gpd.GeoDataFrame
    geo_df: gpd.GeoDataFrame
    unique_regions: list[str]
    initial_options: list[dict[str, str]]
    dept_to_code: dict[str, str]
    region_to_name: dict[str, str]

    def get_combined_restaurant_data(self, include_monaco=False):
        if include_monaco:
            return pd.concat([self.all_france, self.all_monaco], ignore_index=True)
        return self.all_france

    def get_geo_df(self, include_monaco=False):
        combined = self.get_combined_restaurant_data(include_monaco=include_monaco)
        dept_codes = combined["department_num"].unique()

        if not include_monaco:
            return self.department_df[self.department_df["code"].isin(dept_codes)]

        merged_df = pd.concat([self.department_df, self.monaco_df], ignore_index=True)
        return gpd.GeoDataFrame(merged_df, geometry="geometry", crs=self.department_df.crs)


def _require_columns(frame, name, required_columns):
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        raise RuntimeError(f"{name} is missing required columns: {', '.join(missing)}")


def _require_non_numeric(frame, name, columns):
    numeric_columns = [column for column in columns if is_numeric_dtype(frame[column])]
    if numeric_columns:
        raise RuntimeError(f"{name} columns must preserve string-like identifiers: {', '.join(numeric_columns)}")


def _read_restaurants(config: RuntimeConfig, filename, name):
    frame = pd.read_csv(config.data_path(filename), dtype={"department_num": str})
    _require_columns(frame, name, RESTAURANT_COLUMNS)
    _require_non_numeric(frame, name, ("department_num",))
    return frame


def _read_geojson(config: RuntimeConfig, filename, name, required_columns):
    frame = gpd.read_file(config.data_path(filename), engine="pyogrio")
    _require_columns(frame, name, required_columns)
    return frame


def load_michelin_data(config: RuntimeConfig = CONFIG):
    all_france = _read_restaurants(config, "all_restaurants(arrondissements).csv", "all_france")
    all_monaco = _read_restaurants(config, "monaco_restaurants.csv", "all_monaco")

    region_df = _read_geojson(config, "region_restaurants.geojson", "region_df", REGION_COLUMNS)
    department_df = _read_geojson(config, "department_restaurants.geojson", "department_df", DEPARTMENT_COLUMNS)
    arron_df = _read_geojson(config, "arrondissement_restaurants.geojson", "arron_df", ARRONDISSEMENT_COLUMNS)
    paris_df = _read_geojson(config, "paris_restaurants.geojson", "paris_df", PARIS_COLUMNS)
    monaco_df = _read_geojson(config, "monaco_restaurants.geojson", "monaco_df", DEPARTMENT_COLUMNS)
    wine_df = _read_geojson(config, "wine_regions_cleaned.geojson", "wine_df", WINE_COLUMNS)

    _require_non_numeric(department_df, "department_df", ("code",))
    _require_non_numeric(arron_df, "arron_df", ("code", "department_num"))
    _require_non_numeric(paris_df, "paris_df", ("code", "department_num"))
    _require_non_numeric(monaco_df, "monaco_df", ("code",))

    departments_with_restaurants = all_france["department_num"].unique()
    geo_df = department_df[department_df["code"].isin(departments_with_restaurants)]

    unique_regions = sorted(geo_df["region"].unique())
    initial_departments = (
        geo_df[geo_df["region"] == unique_regions[0]][["department", "code"]]
        .drop_duplicates()
        .to_dict("records")
    )
    initial_options = [
        {
            "label": f"{dept['department']} ({dept['code']})",
            "value": dept["department"],
        }
        for dept in initial_departments
    ]
    dept_to_code = geo_df.drop_duplicates(subset="department").set_index("department")["code"].to_dict()
    region_to_name = {region: region for region in geo_df["region"].unique()}

    return MichelinData(
        all_france=all_france,
        all_monaco=all_monaco,
        region_df=region_df,
        department_df=department_df,
        arron_df=arron_df,
        paris_df=paris_df,
        monaco_df=monaco_df,
        wine_df=wine_df,
        geo_df=geo_df,
        unique_regions=unique_regions,
        initial_options=initial_options,
        dept_to_code=dept_to_code,
        region_to_name=region_to_name,
    )


DATA = load_michelin_data()
