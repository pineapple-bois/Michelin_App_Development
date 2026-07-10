from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import shlex
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path


APP_DISTRIBUTION_NAME = "michelin-guide-france"
UPSTREAM_REPOSITORY_URL = "https://github.com/pineapple-bois/Michelin_Rated_Restaurants"
FRANCE_PRODUCT_ROOT = Path("data/products/france")
RELEASE_GATE_MONTH = 4
RELEASE_GATE_DAY = 1

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
ASSETS_DATA_DIR = REPO_ROOT / "assets" / "data"
WINE_DATA_PATH = ASSETS_DATA_DIR / "wine_regions_aoc_area.geojson"

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
FLAT_RESTAURANT_COLUMNS = tuple(
    column for column in RESTAURANT_COLUMNS if column != "arrondissement"
)
AGGREGATE_COUNT_PROPERTIES = (
    "selected",
    "bib_gourmand",
    "1_star",
    "2_star",
    "3_star",
    "total_stars",
    "starred_restaurants",
    "green_stars",
)
DEMOGRAPHIC_PROPERTIES = (
    "gdp_current_prices_million_eur",
    "gdp_per_capita_eur",
    "poverty_rate_percent",
    "census_unemployment_rate_15_64_percent",
    "average_net_monthly_wage_fte_eur",
    "median_living_standard_eur",
    "municipal_population",
    "population_density_per_sq_km",
    "area_sq_km",
)


class AnnualReleaseError(RuntimeError):
    """Raised when the manual annual data release cannot proceed safely."""


@dataclass(frozen=True)
class AnnualProduct:
    source: Path
    destination: Path
    kind: str
    required_columns: tuple[str, ...] = ()
    required_properties: tuple[str, ...] = ()
    string_properties: tuple[str, ...] = ()


ANNUAL_PRODUCT_MANIFEST = (
    AnnualProduct(
        Path("all_restaurants(arrondissements).csv"),
        Path("all_restaurants(arrondissements).csv"),
        "csv",
        required_columns=RESTAURANT_COLUMNS,
    ),
    AnnualProduct(
        Path("all_restaurants.csv"),
        Path("all_restaurants.csv"),
        "csv",
        required_columns=FLAT_RESTAURANT_COLUMNS,
    ),
    AnnualProduct(
        Path("monaco_restaurants.csv"),
        Path("monaco_restaurants.csv"),
        "csv",
        required_columns=RESTAURANT_COLUMNS,
    ),
    AnnualProduct(
        Path("geodata/arrondissement_restaurants.geojson"),
        Path("geodata/arrondissement_restaurants.geojson"),
        "geojson",
        required_properties=(
            "code",
            "arrondissement",
            "department_num",
            "department",
            "capital",
            "region",
            *AGGREGATE_COUNT_PROPERTIES,
            "locations",
        ),
        string_properties=("code", "department_num"),
    ),
    AnnualProduct(
        Path("geodata/department_restaurants.geojson"),
        Path("geodata/department_restaurants.geojson"),
        "geojson",
        required_properties=(
            "code",
            "department",
            "capital",
            "region",
            *AGGREGATE_COUNT_PROPERTIES,
            *DEMOGRAPHIC_PROPERTIES,
            "locations",
        ),
        string_properties=("code",),
    ),
    AnnualProduct(
        Path("geodata/monaco_restaurants.geojson"),
        Path("geodata/monaco_restaurants.geojson"),
        "geojson",
        required_properties=(
            "code",
            "department",
            "capital",
            "region",
            *AGGREGATE_COUNT_PROPERTIES,
            "locations",
        ),
        string_properties=("code",),
    ),
    AnnualProduct(
        Path("geodata/paris_restaurants.geojson"),
        Path("geodata/paris_restaurants.geojson"),
        "geojson",
        required_properties=(
            "code",
            "arrondissement",
            "department_num",
            "department",
            "capital",
            "region",
            *AGGREGATE_COUNT_PROPERTIES,
            "locations",
        ),
        string_properties=("code", "department_num"),
    ),
    AnnualProduct(
        Path("geodata/region_restaurants.geojson"),
        Path("geodata/region_restaurants.geojson"),
        "geojson",
        required_properties=(
            "region",
            *AGGREGATE_COUNT_PROPERTIES,
            *DEMOGRAPHIC_PROPERTIES,
            "locations",
        ),
    ),
)


@dataclass(frozen=True)
class AnnualReleaseSummary:
    et_root: Path
    source_year: int
    previous_version: str
    new_version: str
    previous_data_dir: Path
    new_data_dir: Path
    installed_files: tuple[tuple[Path, Path], ...]
    validation_result: str
    test_result: str
    previous_directory_removed: bool
    wine_unchanged: bool
    changed: bool


def release_year_for_date(today: dt.date) -> int:
    gate = dt.date(today.year, RELEASE_GATE_MONTH, RELEASE_GATE_DAY)
    if today < gate:
        raise AnnualReleaseError(
            "Annual Michelin data updates are disabled before "
            f"{gate.isoformat()}; today is {today.isoformat()}."
        )
    return today.year


def guide_year_from_version(version: str) -> int:
    major = version.split(".", maxsplit=1)[0]
    if not (major.isdigit() and len(major) == 4):
        raise AnnualReleaseError(
            f"Application version {version!r} must start with a four-digit Guide year."
        )
    return int(major)


def runtime_data_dir_for_version(repo_root: Path, version: str) -> Path:
    return repo_root / "assets" / "data" / str(guide_year_from_version(version))


def annual_backup_path(previous_data_dir: Path) -> Path:
    return previous_data_dir.with_name(f".{previous_data_dir.name}.annual-backup")


def validate_et_root(et_root: Path) -> Path:
    resolved = et_root.expanduser().resolve()
    expected = resolved / FRANCE_PRODUCT_ROOT
    if not expected.is_dir():
        raise AnnualReleaseError(
            f"{resolved} is not the expected Michelin ET repository root. "
            f"Expected to find {FRANCE_PRODUCT_ROOT}/ beneath it."
        )
    return resolved


def product_root_for_year(et_root: Path, year: int) -> Path:
    product_root = et_root / FRANCE_PRODUCT_ROOT / str(year)
    if not product_root.is_dir():
        raise AnnualReleaseError(
            f"Missing current-year ET product directory: {product_root}"
        )
    return product_root


def read_installed_application_version() -> str:
    try:
        return metadata.version(APP_DISTRIBUTION_NAME)
    except metadata.PackageNotFoundError as exc:
        raise AnnualReleaseError(
            f"{APP_DISTRIBUTION_NAME!r} is not installed. Run "
            "`python -m pip install -r requirements.txt` from the application "
            "repository before preparing an annual release."
        ) from exc


def read_pyproject_version(pyproject_path: Path = PYPROJECT_PATH) -> str:
    with pyproject_path.open("rb") as handle:
        data = tomllib.load(handle)
    try:
        version = data["project"]["version"]
    except KeyError as exc:
        raise AnnualReleaseError(
            f"{pyproject_path} is missing project.version."
        ) from exc
    if not isinstance(version, str) or not version.strip():
        raise AnnualReleaseError(f"{pyproject_path} project.version is invalid.")
    return version


def write_pyproject_version(pyproject_path: Path, version: str) -> None:
    lines = pyproject_path.read_text(encoding="utf-8").splitlines(keepends=True)
    in_project = False
    replacements = 0
    version_pattern = re.compile(r'^(\s*version\s*=\s*")[^"]+(".*)$')
    updated_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"

        if in_project:
            match = version_pattern.match(line)
            if match:
                line = f'{match.group(1)}{version}{match.group(2)}\n'
                replacements += 1
        updated_lines.append(line)

    if replacements != 1:
        raise AnnualReleaseError(
            f"Expected exactly one [project] version entry in {pyproject_path}; "
            f"found {replacements}."
        )

    pyproject_path.write_text("".join(updated_lines), encoding="utf-8")
    if read_pyproject_version(pyproject_path) != version:
        raise AnnualReleaseError(f"Failed to update {pyproject_path} to {version}.")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_manifest_paths(product_root: Path) -> None:
    seen_sources: set[Path] = set()
    seen_destinations: set[Path] = set()
    for product in ANNUAL_PRODUCT_MANIFEST:
        if product.source in seen_sources:
            raise AnnualReleaseError(
                f"Ambiguous annual source in manifest: {product.source}"
            )
        seen_sources.add(product.source)

        if product.destination in seen_destinations:
            raise AnnualReleaseError(
                f"Ambiguous annual destination in manifest: {product.destination}"
            )
        seen_destinations.add(product.destination)

        source_path = product_root / product.source
        if not source_path.exists():
            raise AnnualReleaseError(f"Missing required ET product: {source_path}")
        if not source_path.is_file():
            raise AnnualReleaseError(
                f"Expected ET product to be a regular file: {source_path}"
            )


def _require_csv(path: Path, required_columns: tuple[str, ...]) -> None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or ()
            missing = [column for column in required_columns if column not in fieldnames]
            if missing:
                raise AnnualReleaseError(
                    f"{path} is missing required CSV columns: {', '.join(missing)}"
                )
            first_row = next(reader, None)
    except UnicodeDecodeError as exc:
        raise AnnualReleaseError(f"{path} is not valid UTF-8 CSV.") from exc
    except csv.Error as exc:
        raise AnnualReleaseError(f"{path} is malformed CSV: {exc}") from exc

    if first_row is None:
        raise AnnualReleaseError(f"{path} does not contain any restaurant rows.")
    if "department_num" in required_columns and not str(first_row.get("department_num", "")).strip():
        raise AnnualReleaseError(f"{path} contains an empty department_num value.")


def _require_geojson(path: Path, product: AnnualProduct) -> None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AnnualReleaseError(f"{path} is malformed GeoJSON: {exc}") from exc

    if payload.get("type") != "FeatureCollection":
        raise AnnualReleaseError(f"{path} must be a GeoJSON FeatureCollection.")
    features = payload.get("features")
    if not isinstance(features, list) or not features:
        raise AnnualReleaseError(f"{path} must contain at least one GeoJSON feature.")

    for index, feature in enumerate(features):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise AnnualReleaseError(f"{path} feature {index} is not a GeoJSON Feature.")
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            raise AnnualReleaseError(f"{path} feature {index} has no properties object.")
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict) or not geometry.get("type"):
            raise AnnualReleaseError(f"{path} feature {index} has no geometry object.")

        missing = [
            prop for prop in product.required_properties
            if prop not in properties
        ]
        if missing:
            raise AnnualReleaseError(
                f"{path} feature {index} is missing required properties: "
                f"{', '.join(missing)}"
            )
        empty_identifiers = [
            prop for prop in product.string_properties
            if not isinstance(properties.get(prop), str) or not properties[prop].strip()
        ]
        if empty_identifiers:
            raise AnnualReleaseError(
                f"{path} feature {index} must preserve string identifiers: "
                f"{', '.join(empty_identifiers)}"
            )


def validate_manifest_products(base_dir: Path, *, source: bool) -> None:
    if source:
        _require_manifest_paths(base_dir)

    for product in ANNUAL_PRODUCT_MANIFEST:
        relative_path = product.source if source else product.destination
        path = base_dir / relative_path
        if not path.is_file():
            raise AnnualReleaseError(f"Missing required annual product: {path}")
        if product.kind == "csv":
            _require_csv(path, product.required_columns)
        elif product.kind == "geojson":
            _require_geojson(path, product)
        else:
            raise AnnualReleaseError(f"Unsupported annual product kind: {product.kind}")

    if not source:
        expected_files = {product.destination for product in ANNUAL_PRODUCT_MANIFEST}
        actual_files = {
            path.relative_to(base_dir)
            for path in base_dir.rglob("*")
            if path.is_file()
        }
        if actual_files != expected_files:
            missing = sorted(expected_files - actual_files)
            extra = sorted(actual_files - expected_files)
            details = []
            if missing:
                details.append(
                    "missing: " + ", ".join(str(path) for path in missing)
                )
            if extra:
                details.append("extra: " + ", ".join(str(path) for path in extra))
            raise AnnualReleaseError(
                "Staged annual directory does not match the manifest exactly "
                f"({'; '.join(details)})."
            )


def stage_annual_products(source_root: Path, staging_dir: Path) -> tuple[tuple[Path, Path], ...]:
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)

    installed_files = []
    for product in ANNUAL_PRODUCT_MANIFEST:
        source_path = source_root / product.source
        destination_path = staging_dir / product.destination
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        installed_files.append((product.source, product.destination))

    validate_manifest_products(staging_dir, source=False)
    return tuple(installed_files)


def _failure_message(exc: BaseException) -> str:
    message = str(exc)
    if message:
        return message
    return exc.__class__.__name__


def _format_command(args: list[str]) -> str:
    return " ".join(shlex.quote(str(arg)) for arg in args)


def run_checked_command(args: list[str], *, cwd: Path, description: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        output = "\n".join(
            part for part in (result.stdout.strip(), result.stderr.strip()) if part
        )
        raise AnnualReleaseError(
            f"{description} failed with exit code {result.returncode}: "
            f"{_format_command(args)}"
            + (f"\n{output}" if output else "")
        )
    return result


def refresh_editable_install(repo_root: Path = REPO_ROOT) -> None:
    run_checked_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-e",
            ".",
            "--no-deps",
            "--no-build-isolation",
        ],
        cwd=repo_root,
        description="Editable package metadata refresh",
    )


def run_application_import_check(
    repo_root: Path,
    expected_version: str,
    expected_year: int,
) -> None:
    expected_data_dir = repo_root / "assets" / "data" / str(expected_year)
    code = (
        "from pathlib import Path\n"
        "from app.app_config import CONFIG\n"
        "import michelin_app\n"
        f"expected_version = {expected_version!r}\n"
        f"expected_year = {expected_year!r}\n"
        f"expected_data_dir = Path({str(expected_data_dir)!r}).resolve()\n"
        "assert CONFIG.application_version == expected_version\n"
        "assert CONFIG.guide_year == expected_year\n"
        "assert CONFIG.annual_data_path().resolve() == expected_data_dir\n"
        "assert michelin_app.app.server is michelin_app.server\n"
    )
    run_checked_command(
        [sys.executable, "-c", code],
        cwd=repo_root,
        description="Application import and runtime data-year validation",
    )


def run_full_test_suite(repo_root: Path = REPO_ROOT) -> None:
    run_checked_command(
        [sys.executable, "-m", "pytest"],
        cwd=repo_root,
        description="Full pytest suite",
    )


def _restore_previous_state(
    *,
    repo_root: Path,
    pyproject_path: Path,
    previous_version: str,
    previous_data_dir: Path,
    previous_backup_dir: Path,
    new_dir: Path,
    staging_dir: Path,
    refresh_install,
    tree_remover,
) -> None:
    for path in (new_dir, staging_dir):
        if path.exists():
            tree_remover(path)

    if previous_backup_dir.exists():
        if previous_data_dir.exists():
            raise AnnualReleaseError(
                "Cannot restore annual backup because the previous-year "
                f"directory already exists: {previous_data_dir}"
            )
        previous_backup_dir.rename(previous_data_dir)
    elif not previous_data_dir.exists():
        raise AnnualReleaseError(
            "Cannot restore previous annual data directory because the backup "
            f"path is missing: {previous_backup_dir}"
        )

    write_pyproject_version(pyproject_path, previous_version)
    refresh_install(repo_root)


def prepare_annual_release(
    *,
    et_root: Path,
    today: dt.date | None = None,
    repo_root: Path = REPO_ROOT,
    installed_version_reader=read_installed_application_version,
    refresh_install=refresh_editable_install,
    app_import_checker=run_application_import_check,
    test_runner=run_full_test_suite,
    tree_remover=shutil.rmtree,
) -> AnnualReleaseSummary:
    today = today or dt.date.today()
    source_year = release_year_for_date(today)
    repo_root = repo_root.resolve()
    pyproject_path = repo_root / "pyproject.toml"
    assets_data_dir = repo_root / "assets" / "data"
    wine_data_path = assets_data_dir / "wine_regions_aoc_area.geojson"

    resolved_et_root = validate_et_root(et_root)
    source_root = product_root_for_year(resolved_et_root, source_year)
    validate_manifest_products(source_root, source=True)

    previous_version = installed_version_reader()
    pyproject_version = read_pyproject_version(pyproject_path)
    if pyproject_version != previous_version:
        raise AnnualReleaseError(
            "Installed package metadata does not match pyproject.toml "
            f"({previous_version!r} != {pyproject_version!r}). Refresh the local "
            "editable install before preparing an annual release."
        )

    active_year = guide_year_from_version(previous_version)
    previous_data_dir = assets_data_dir / str(active_year)
    previous_backup_dir = annual_backup_path(previous_data_dir)
    new_version = f"{source_year}.0"
    new_data_dir = assets_data_dir / str(source_year)
    installed_files = tuple(
        (product.source, product.destination)
        for product in ANNUAL_PRODUCT_MANIFEST
    )

    if not wine_data_path.is_file():
        raise AnnualReleaseError(f"Wine data file is missing: {wine_data_path}")

    if active_year == source_year:
        if not previous_data_dir.is_dir():
            raise AnnualReleaseError(
                f"Active annual application directory is missing: {previous_data_dir}"
            )
        wine_hash = file_sha256(wine_data_path)
        return AnnualReleaseSummary(
            et_root=resolved_et_root,
            source_year=source_year,
            previous_version=previous_version,
            new_version=previous_version,
            previous_data_dir=previous_data_dir,
            new_data_dir=new_data_dir,
            installed_files=installed_files,
            validation_result="no annual update required",
            test_result="not run",
            previous_directory_removed=False,
            wine_unchanged=file_sha256(wine_data_path) == wine_hash,
            changed=False,
        )

    if active_year != source_year - 1:
        raise AnnualReleaseError(
            "Unexpected active Guide year for annual transition: "
            f"application version {previous_version!r} selects {active_year}, "
            f"but {source_year - 1} was expected for a {source_year}.0 release."
        )

    if not previous_data_dir.is_dir():
        raise AnnualReleaseError(
            f"Previous annual application directory is missing: {previous_data_dir}"
        )
    if new_data_dir.exists():
        raise AnnualReleaseError(
            f"Target annual application directory already exists: {new_data_dir}"
        )
    if previous_backup_dir.exists():
        raise AnnualReleaseError(
            f"Stale annual backup path already exists: {previous_backup_dir}. "
            "Inspect and remove or restore it before preparing another annual release."
        )
    wine_hash_before = file_sha256(wine_data_path)
    staging_dir = assets_data_dir / f".{source_year}.staging"

    try:
        installed_files = stage_annual_products(source_root, staging_dir)
        staging_dir.rename(new_data_dir)

        write_pyproject_version(pyproject_path, new_version)
        refresh_install(repo_root)

        refreshed_version = installed_version_reader()
        if refreshed_version != new_version:
            raise AnnualReleaseError(
                "Editable install did not expose the new application version "
                f"({refreshed_version!r} != {new_version!r})."
            )

        expected_runtime_dir = runtime_data_dir_for_version(repo_root, new_version)
        if expected_runtime_dir != new_data_dir:
            raise AnnualReleaseError(
                f"New version {new_version} resolves to {expected_runtime_dir}, "
                f"not {new_data_dir}."
            )

        app_import_checker(repo_root, new_version, source_year)
        test_runner(repo_root)

        if file_sha256(wine_data_path) != wine_hash_before:
            raise AnnualReleaseError("Wine data changed during annual release preparation.")

        previous_data_dir.rename(previous_backup_dir)
        tree_remover(previous_backup_dir)

    except BaseException as exc:
        try:
            _restore_previous_state(
                repo_root=repo_root,
                pyproject_path=pyproject_path,
                previous_version=previous_version,
                previous_data_dir=previous_data_dir,
                previous_backup_dir=previous_backup_dir,
                new_dir=new_data_dir,
                staging_dir=staging_dir,
                refresh_install=refresh_install,
                tree_remover=tree_remover,
            )
        except BaseException as rollback_exc:
            raise AnnualReleaseError(
                f"{_failure_message(exc)}\n"
                f"Rollback also failed: {_failure_message(rollback_exc)}"
            ) from exc
        raise AnnualReleaseError(
            f"{_failure_message(exc)}\n"
            f"Rolled back to {previous_version}; previous annual data "
            f"directory preserved at {previous_data_dir}."
        ) from exc

    return AnnualReleaseSummary(
        et_root=resolved_et_root,
        source_year=source_year,
        previous_version=previous_version,
        new_version=new_version,
        previous_data_dir=previous_data_dir,
        new_data_dir=new_data_dir,
        installed_files=installed_files,
        validation_result="staged products and application import passed",
        test_result="full pytest suite passed",
        previous_directory_removed=not previous_data_dir.exists(),
        wine_unchanged=file_sha256(wine_data_path) == wine_hash_before,
        changed=True,
    )


def print_summary(summary: AnnualReleaseSummary) -> None:
    if not summary.changed:
        print("No annual Michelin data update is required.")
    else:
        print("Annual Michelin data release prepared.")

    print(f"ET repository root: {summary.et_root}")
    print(f"Upstream repository: {UPSTREAM_REPOSITORY_URL}")
    print(f"Source product year: {summary.source_year}")
    print(f"Previous application version: {summary.previous_version}")
    print(f"New application version: {summary.new_version}")
    print(f"Previous annual data directory: {summary.previous_data_dir}")
    print(f"New annual data directory: {summary.new_data_dir}")
    print("Files installed:" if summary.changed else "Annual manifest files:")
    for source, destination in summary.installed_files:
        print(f"  {FRANCE_PRODUCT_ROOT / str(summary.source_year) / source} -> assets/data/{summary.source_year}/{destination}")
    print(f"Validation result: {summary.validation_result}")
    print(f"Test result: {summary.test_result}")
    print(
        "Previous annual directory removed: "
        f"{'yes' if summary.previous_directory_removed else 'no'}"
    )
    print(
        "Wine data unchanged: "
        f"{'yes' if summary.wine_unchanged else 'no'} "
        "(assets/data/wine_regions_aoc_area.geojson)"
    )
    if summary.changed:
        print()
        print("Next manual steps:")
        print("  1. Run the application.")
        print("  2. Sense-check the new Michelin Guide.")
        print("  3. Review restaurant totals and maps.")
        print("  4. Inspect git diff.")
        print("  5. Commit manually.")
        print("  6. Deploy manually.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare the local application repository for the annual Michelin "
            "France data release from a local ET checkout."
        )
    )
    parser.add_argument(
        "--et-root",
        required=True,
        type=Path,
        help="Path to the local Michelin_Rated_Restaurants repository root.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = prepare_annual_release(et_root=args.et_root)
    except AnnualReleaseError as exc:
        print(f"Annual data release failed: {exc}", file=sys.stderr)
        return 1

    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
