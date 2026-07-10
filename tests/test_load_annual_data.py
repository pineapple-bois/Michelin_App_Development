import datetime as dt
import json
from pathlib import Path

import pytest

from scripts import load_annual_data


def _csv_row(columns):
    values = {
        "name": "Test Table",
        "address": "1 Test Street",
        "location": "Testville",
        "arrondissement": "Test Arrondissement",
        "department_num": "01",
        "department": "Ain",
        "capital": "Bourg-en-Bresse",
        "region": "Auvergne-Rhone-Alpes",
        "price": "EUR",
        "cuisine": "Modern Cuisine",
        "url": "https://example.test",
        "award": "Selected Restaurants",
        "stars": "0.25",
        "greenstar": "0",
        "longitude": "5.0",
        "latitude": "46.0",
    }
    return [values[column] for column in columns]


def _write_csv(path, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ",".join(columns) + "\n" + ",".join(_csv_row(columns)) + "\n",
        encoding="utf-8",
    )


def _property_value(name):
    if name in {"code", "department_num"}:
        return "01"
    if name == "region":
        return "Auvergne-Rhone-Alpes"
    if name == "arrondissement":
        return "Belley"
    if name == "department":
        return "Ain"
    if name == "capital":
        return "Bourg-en-Bresse"
    if name == "locations":
        return "{}"
    return 1


def _write_geojson(path, product):
    path.parent.mkdir(parents=True, exist_ok=True)
    properties = {
        name: _property_value(name)
        for name in product.required_properties
    }
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": properties,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                },
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _create_et_products(tmp_path, year=2027):
    et_root = tmp_path / "Michelin_Rated_Restaurants"
    product_root = (
        et_root / load_annual_data.FRANCE_PRODUCT_ROOT / str(year)
    )
    for product in load_annual_data.ANNUAL_PRODUCT_MANIFEST:
        path = product_root / product.source
        if product.kind == "csv":
            _write_csv(path, product.required_columns)
        else:
            _write_geojson(path, product)
    return et_root


def _create_app_repo(tmp_path, version="2026.4"):
    repo_root = tmp_path / "Michelin_App_Development"
    previous_year = load_annual_data.guide_year_from_version(version)
    previous_dir = repo_root / "assets" / "data" / str(previous_year)
    previous_dir.mkdir(parents=True, exist_ok=True)
    (previous_dir / "previous.txt").write_text("previous", encoding="utf-8")
    (repo_root / "assets" / "data" / "wine_regions_aoc_area.geojson").write_text(
        "wine-data",
        encoding="utf-8",
    )
    (repo_root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "michelin-guide-france"',
                f'version = "{version}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return repo_root


class FakeInstalledPackage:
    def __init__(self, version):
        self.version = version
        self.install_count = 0

    def read(self):
        return self.version

    def refresh(self, repo_root):
        self.install_count += 1
        self.version = load_annual_data.read_pyproject_version(
            repo_root / "pyproject.toml"
        )


def _app_import_checker(repo_root, expected_version, expected_year):
    assert load_annual_data.runtime_data_dir_for_version(
        repo_root,
        expected_version,
    ) == repo_root / "assets" / "data" / str(expected_year)
    assert (repo_root / "assets" / "data" / str(expected_year)).is_dir()


def _passing_tests(_repo_root):
    return None


def _run_release(tmp_path, *, version="2026.4", today=dt.date(2027, 4, 1), **kwargs):
    et_root = kwargs.pop("et_root", None) or _create_et_products(tmp_path, today.year)
    repo_root = kwargs.pop("repo_root", None) or _create_app_repo(tmp_path, version)
    installed = FakeInstalledPackage(version)
    summary = load_annual_data.prepare_annual_release(
        et_root=et_root,
        today=today,
        repo_root=repo_root,
        installed_version_reader=installed.read,
        refresh_install=installed.refresh,
        app_import_checker=kwargs.pop("app_import_checker", _app_import_checker),
        test_runner=kwargs.pop("test_runner", _passing_tests),
        tree_remover=kwargs.pop("tree_remover", None) or load_annual_data.shutil.rmtree,
    )
    return summary, repo_root, et_root, installed


def test_march_31_update_is_blocked():
    with pytest.raises(load_annual_data.AnnualReleaseError, match="before 2027-04-01"):
        load_annual_data.release_year_for_date(dt.date(2027, 3, 31))


@pytest.mark.parametrize("today", [dt.date(2027, 4, 1), dt.date(2027, 9, 15)])
def test_april_1_and_later_dates_are_eligible(today):
    assert load_annual_data.release_year_for_date(today) == 2027


def test_invalid_et_repository_root_fails(tmp_path):
    repo_root = _create_app_repo(tmp_path)
    invalid_et_root = tmp_path / "wrong"
    invalid_et_root.mkdir()

    installed = FakeInstalledPackage("2026.4")
    with pytest.raises(load_annual_data.AnnualReleaseError, match="not the expected"):
        load_annual_data.prepare_annual_release(
            et_root=invalid_et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=_app_import_checker,
            test_runner=_passing_tests,
        )


def test_missing_current_year_product_directory_fails(tmp_path):
    et_root = tmp_path / "Michelin_Rated_Restaurants"
    (et_root / load_annual_data.FRANCE_PRODUCT_ROOT).mkdir(parents=True)
    repo_root = _create_app_repo(tmp_path)
    installed = FakeInstalledPackage("2026.4")

    with pytest.raises(load_annual_data.AnnualReleaseError, match="Missing current-year"):
        load_annual_data.prepare_annual_release(
            et_root=et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=_app_import_checker,
            test_runner=_passing_tests,
        )


def test_incomplete_source_manifest_fails(tmp_path):
    et_root = _create_et_products(tmp_path, 2027)
    missing_product = load_annual_data.ANNUAL_PRODUCT_MANIFEST[0]
    (et_root / load_annual_data.FRANCE_PRODUCT_ROOT / "2027" / missing_product.source).unlink()
    repo_root = _create_app_repo(tmp_path)
    installed = FakeInstalledPackage("2026.4")

    with pytest.raises(load_annual_data.AnnualReleaseError, match="Missing required ET product"):
        load_annual_data.prepare_annual_release(
            et_root=et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=_app_import_checker,
            test_runner=_passing_tests,
        )


def test_malformed_csv_input_fails(tmp_path):
    et_root = _create_et_products(tmp_path, 2027)
    product = load_annual_data.ANNUAL_PRODUCT_MANIFEST[0]
    _write_csv(
        et_root / load_annual_data.FRANCE_PRODUCT_ROOT / "2027" / product.source,
        ("name", "department_num"),
    )
    repo_root = _create_app_repo(tmp_path)
    installed = FakeInstalledPackage("2026.4")

    with pytest.raises(load_annual_data.AnnualReleaseError, match="missing required CSV"):
        load_annual_data.prepare_annual_release(
            et_root=et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=_app_import_checker,
            test_runner=_passing_tests,
        )


def test_malformed_geojson_input_fails(tmp_path):
    et_root = _create_et_products(tmp_path, 2027)
    product = next(
        product
        for product in load_annual_data.ANNUAL_PRODUCT_MANIFEST
        if product.kind == "geojson"
    )
    path = et_root / load_annual_data.FRANCE_PRODUCT_ROOT / "2027" / product.source
    path.write_text('{"type": "FeatureCollection", "features": []}', encoding="utf-8")
    repo_root = _create_app_repo(tmp_path)
    installed = FakeInstalledPackage("2026.4")

    with pytest.raises(load_annual_data.AnnualReleaseError, match="at least one"):
        load_annual_data.prepare_annual_release(
            et_root=et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=_app_import_checker,
            test_runner=_passing_tests,
        )


def test_application_already_using_current_calendar_year_reports_no_update(tmp_path):
    summary, repo_root, _et_root, installed = _run_release(
        tmp_path,
        version="2027.2",
        today=dt.date(2027, 4, 1),
        test_runner=lambda _repo_root: pytest.fail("tests should not run"),
    )

    assert summary.changed is False
    assert summary.validation_result == "no annual update required"
    assert installed.version == "2027.2"
    assert (repo_root / "assets" / "data" / "2027").is_dir()


def test_installed_guide_year_must_be_expected_previous_year(tmp_path):
    et_root = _create_et_products(tmp_path, 2027)
    repo_root = _create_app_repo(tmp_path, version="2025.0")
    installed = FakeInstalledPackage("2025.0")

    with pytest.raises(load_annual_data.AnnualReleaseError, match="Unexpected active"):
        load_annual_data.prepare_annual_release(
            et_root=et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=_app_import_checker,
            test_runner=_passing_tests,
        )


def test_successful_annual_transition_resets_version_and_switches_runtime_dir(tmp_path):
    summary, repo_root, _et_root, installed = _run_release(
        tmp_path,
        version="2026.8",
        today=dt.date(2027, 4, 1),
    )

    assert summary.changed is True
    assert summary.previous_version == "2026.8"
    assert summary.new_version == "2027.0"
    assert load_annual_data.read_pyproject_version(repo_root / "pyproject.toml") == "2027.0"
    assert installed.version == "2027.0"
    assert load_annual_data.runtime_data_dir_for_version(repo_root, "2027.0") == (
        repo_root / "assets" / "data" / "2027"
    )
    assert (repo_root / "assets" / "data" / "2027").is_dir()
    assert not (repo_root / "assets" / "data" / "2026").exists()
    assert not load_annual_data.annual_backup_path(
        repo_root / "assets" / "data" / "2026"
    ).exists()
    assert summary.previous_directory_removed is True
    assert summary.wine_unchanged is True


def test_stale_annual_backup_path_blocks_transition(tmp_path):
    et_root = _create_et_products(tmp_path, 2027)
    repo_root = _create_app_repo(tmp_path, version="2026.0")
    previous_dir = repo_root / "assets" / "data" / "2026"
    load_annual_data.annual_backup_path(previous_dir).mkdir()
    installed = FakeInstalledPackage("2026.0")

    with pytest.raises(load_annual_data.AnnualReleaseError, match="Stale annual backup"):
        load_annual_data.prepare_annual_release(
            et_root=et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=_app_import_checker,
            test_runner=_passing_tests,
        )

    assert previous_dir.is_dir()
    assert not (repo_root / "assets" / "data" / "2027").exists()


def test_failure_after_previous_directory_moves_to_backup_rolls_back(tmp_path):
    et_root = _create_et_products(tmp_path, 2027)
    repo_root = _create_app_repo(tmp_path, version="2026.5")
    installed = FakeInstalledPackage("2026.5")
    previous_dir = repo_root / "assets" / "data" / "2026"
    backup_dir = load_annual_data.annual_backup_path(previous_dir)

    def failing_final_cleanup(path):
        if path == backup_dir:
            assert backup_dir.is_dir()
            assert not previous_dir.exists()
            raise OSError("final cleanup failed")
        load_annual_data.shutil.rmtree(path)

    with pytest.raises(load_annual_data.AnnualReleaseError, match="final cleanup failed"):
        load_annual_data.prepare_annual_release(
            et_root=et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=_app_import_checker,
            test_runner=_passing_tests,
            tree_remover=failing_final_cleanup,
        )

    assert load_annual_data.read_pyproject_version(repo_root / "pyproject.toml") == "2026.5"
    assert installed.version == "2026.5"
    assert previous_dir.is_dir()
    assert (previous_dir / "previous.txt").read_text(encoding="utf-8") == "previous"
    assert not backup_dir.exists()
    assert not (repo_root / "assets" / "data" / "2027").exists()


def test_failing_final_cleanup_reports_rollback_failure_too(tmp_path):
    et_root = _create_et_products(tmp_path, 2027)
    repo_root = _create_app_repo(tmp_path, version="2026.6")
    installed = FakeInstalledPackage("2026.6")
    previous_dir = repo_root / "assets" / "data" / "2026"
    backup_dir = load_annual_data.annual_backup_path(previous_dir)
    new_dir = repo_root / "assets" / "data" / "2027"

    def failing_cleanup_and_rollback(path):
        if path == backup_dir:
            raise OSError("final cleanup failed")
        if path == new_dir:
            raise OSError("rollback remove failed")
        load_annual_data.shutil.rmtree(path)

    with pytest.raises(
        load_annual_data.AnnualReleaseError,
        match="(?s)final cleanup failed.*Rollback also failed.*rollback remove failed",
    ):
        load_annual_data.prepare_annual_release(
            et_root=et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=_app_import_checker,
            test_runner=_passing_tests,
            tree_remover=failing_cleanup_and_rollback,
        )

    assert backup_dir.is_dir()
    assert new_dir.is_dir()


def test_keyboard_interrupt_during_post_switch_operation_rolls_back(tmp_path):
    et_root = _create_et_products(tmp_path, 2027)
    repo_root = _create_app_repo(tmp_path, version="2026.7")
    installed = FakeInstalledPackage("2026.7")
    previous_dir = repo_root / "assets" / "data" / "2026"

    def interrupted_tests(_repo_root):
        raise KeyboardInterrupt

    with pytest.raises(load_annual_data.AnnualReleaseError, match="KeyboardInterrupt"):
        load_annual_data.prepare_annual_release(
            et_root=et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=_app_import_checker,
            test_runner=interrupted_tests,
        )

    assert load_annual_data.read_pyproject_version(repo_root / "pyproject.toml") == "2026.7"
    assert installed.version == "2026.7"
    assert previous_dir.is_dir()
    assert not load_annual_data.annual_backup_path(previous_dir).exists()
    assert not (repo_root / "assets" / "data" / "2027").exists()


def test_post_install_validation_failure_restores_previous_state(tmp_path):
    et_root = _create_et_products(tmp_path, 2027)
    repo_root = _create_app_repo(tmp_path, version="2026.3")
    installed = FakeInstalledPackage("2026.3")
    wine_before = load_annual_data.file_sha256(
        repo_root / "assets" / "data" / "wine_regions_aoc_area.geojson"
    )

    def failing_import_check(_repo_root, _expected_version, _expected_year):
        raise load_annual_data.AnnualReleaseError("import check failed")

    with pytest.raises(load_annual_data.AnnualReleaseError, match="Rolled back"):
        load_annual_data.prepare_annual_release(
            et_root=et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=failing_import_check,
            test_runner=_passing_tests,
        )

    assert load_annual_data.read_pyproject_version(repo_root / "pyproject.toml") == "2026.3"
    assert installed.version == "2026.3"
    assert (repo_root / "assets" / "data" / "2026").is_dir()
    assert not (repo_root / "assets" / "data" / "2027").exists()
    assert load_annual_data.file_sha256(
        repo_root / "assets" / "data" / "wine_regions_aoc_area.geojson"
    ) == wine_before


def test_test_failure_restores_previous_state_and_preserves_previous_directory(tmp_path):
    et_root = _create_et_products(tmp_path, 2027)
    repo_root = _create_app_repo(tmp_path, version="2026.1")
    installed = FakeInstalledPackage("2026.1")

    def failing_tests(_repo_root):
        raise load_annual_data.AnnualReleaseError("pytest failed")

    with pytest.raises(load_annual_data.AnnualReleaseError, match="pytest failed"):
        load_annual_data.prepare_annual_release(
            et_root=et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=_app_import_checker,
            test_runner=failing_tests,
        )

    assert load_annual_data.read_pyproject_version(repo_root / "pyproject.toml") == "2026.1"
    assert installed.version == "2026.1"
    assert (repo_root / "assets" / "data" / "2026").is_dir()
    assert not (repo_root / "assets" / "data" / "2027").exists()


def test_superseded_annual_data_is_removed_only_after_success(tmp_path):
    et_root = _create_et_products(tmp_path, 2027)
    repo_root = _create_app_repo(tmp_path, version="2026.0")
    installed = FakeInstalledPackage("2026.0")

    with pytest.raises(load_annual_data.AnnualReleaseError):
        load_annual_data.prepare_annual_release(
            et_root=et_root,
            today=dt.date(2027, 4, 1),
            repo_root=repo_root,
            installed_version_reader=installed.read,
            refresh_install=installed.refresh,
            app_import_checker=lambda *_args: (_ for _ in ()).throw(
                load_annual_data.AnnualReleaseError("validation failed")
            ),
            test_runner=_passing_tests,
        )
    assert (repo_root / "assets" / "data" / "2026").is_dir()

    installed = FakeInstalledPackage("2026.0")
    summary = load_annual_data.prepare_annual_release(
        et_root=et_root,
        today=dt.date(2027, 4, 1),
        repo_root=repo_root,
        installed_version_reader=installed.read,
        refresh_install=installed.refresh,
        app_import_checker=_app_import_checker,
        test_runner=_passing_tests,
    )

    assert summary.previous_directory_removed is True
    assert not (repo_root / "assets" / "data" / "2026").exists()
