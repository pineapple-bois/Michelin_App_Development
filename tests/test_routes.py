from dataclasses import replace

import pytest


@pytest.mark.parametrize("path", ["/", "/home", "/analysis", "/economics", "/wine"])
def test_public_routes_return_dash_html_shell(app_module, path):
    response = app_module.server.test_client().get(path)

    assert response.status_code == 200
    assert "text/html" in response.headers.get("Content-Type", "")

    body = response.get_data(as_text=True)
    assert "<html" in body.lower()
    assert "_dash-config" in body
    assert "_dash-renderer" in body


@pytest.mark.parametrize(
    "path",
    [
        "/missing",
        "/404",
        "/shell.php",
        "/.env",
        "/.git/config",
        "/wp-login.php",
        "/wordpress/wp-includes/wlwmanifest.xml",
        "/assets/shell.php",
        "/?rest_route=/wp/v2/users",
    ],
)
def test_unknown_and_impossible_routes_return_404_without_session(app_module, path):
    response = app_module.server.test_client().get(path)

    assert response.status_code == 404
    assert "Set-Cookie" not in response.headers


def test_robots_txt_is_plain_text_cacheable_and_session_free(app_module):
    response = app_module.server.test_client().get("/robots.txt")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "User-agent: *\nDisallow: /\n"
    assert response.content_type == "text/plain; charset=utf-8"
    assert response.headers["Cache-Control"] == "public, max-age=86400"
    assert "Set-Cookie" not in response.headers


@pytest.mark.parametrize(
    "path",
    [
        "/_dash-layout",
        "/_dash-dependencies",
        "/_favicon.ico",
        "/assets/styles.css",
    ],
)
def test_dash_framework_and_asset_routes_remain_available(app_module, path):
    response = app_module.server.test_client().get(path)

    assert response.status_code == 200


def test_dash_callback_route_remains_available(app_module):
    response = app_module.server.test_client().options("/_dash-update-component")

    assert response.status_code == 200


def test_direct_asset_request_does_not_create_session(app_module):
    response = app_module.server.test_client().get("/assets/styles.css")

    assert "Set-Cookie" not in response.headers


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("restaurant-guide-france.net", True),
        ("www.restaurant-guide-france.net", True),
        ("restaurant-guide-france.net:443", True),
        ("RESTAURANT-GUIDE-FRANCE.NET.", True),
        ("michelin-guide-france.herokuapp.com", False),
        ("example.com", False),
    ],
)
def test_production_host_allowlist(app_module, host, expected):
    assert app_module.is_allowed_production_host(host) is expected


def test_production_host_validation_ignores_forwarded_host(
    app_module,
    monkeypatch,
):
    monkeypatch.setattr(
        app_module,
        "CONFIG",
        replace(app_module.CONFIG, is_production=True, force_https=False),
    )
    client = app_module.server.test_client()

    allowed_response = client.get(
        "/",
        headers={
            "Host": "restaurant-guide-france.net",
            "X-Forwarded-Host": "example.com",
        },
    )
    rejected_response = client.get(
        "/",
        headers={
            "Host": "example.com",
            "X-Forwarded-Host": "restaurant-guide-france.net",
        },
    )

    assert allowed_response.status_code == 200
    assert rejected_response.status_code == 404
    assert "Set-Cookie" not in rejected_response.headers


@pytest.mark.parametrize("path", ["/", "/missing"])
def test_baseline_security_headers_are_added(app_module, path):
    response = app_module.server.test_client().get(path)

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Permissions-Policy"] == (
        "camera=(), geolocation=(), microphone=()"
    )
    assert "Strict-Transport-Security" not in response.headers


def test_production_session_cookie_settings(app_module, monkeypatch):
    assert app_module.server.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app_module.server.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert (
        app_module.server.config["SESSION_COOKIE_SECURE"]
        is app_module.CONFIG.is_production
    )

    monkeypatch.setitem(app_module.server.config, "SESSION_COOKIE_SECURE", True)
    response = app_module.server.test_client().get("/")
    cookie = response.headers["Set-Cookie"]

    assert "Secure" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
