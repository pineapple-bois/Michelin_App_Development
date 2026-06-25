import pytest


@pytest.mark.parametrize("path", ["/", "/home", "/analysis", "/economics", "/wine", "/missing"])
def test_routes_return_dash_html_shell(app_module, path):
    response = app_module.server.test_client().get(path)

    assert response.status_code == 200
    assert "text/html" in response.headers.get("Content-Type", "")

    body = response.get_data(as_text=True)
    assert "<html" in body.lower()
    assert "_dash-config" in body
    assert "_dash-renderer" in body
