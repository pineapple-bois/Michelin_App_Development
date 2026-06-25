import pytest


@pytest.fixture(scope="session")
def app_module():
    import michelin_app

    return michelin_app


@pytest.fixture(scope="session")
def data_boundary():
    from app.app_data import DATA

    return DATA
