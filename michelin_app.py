import dash
import dash_bootstrap_components as dbc
import uuid
from openai import OpenAI
from dash import dcc, html
from flask import Flask, abort, redirect, request, session
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix

from app.app_data import DATA
from app.app_config import CONFIG
from app.callbacks.analysis import register_analysis_callbacks
from app.callbacks.economics import register_economics_callbacks
from app.callbacks.guide import register_guide_callbacks
from app.callbacks.navigation import register_navigation_callbacks
from app.callbacks.responsive import (
    RESPONSIVE_INPUT_MODE_STORE_ID,
    initial_responsive_input_mode,
    register_responsive_input_callbacks,
)
from app.callbacks.wine import register_wine_callbacks


PRODUCTION_HOSTS = frozenset({
    "restaurant-guide-france.net",
    "www.restaurant-guide-france.net",
})
PUBLIC_PAGE_PATHS = frozenset({
    "/",
    "/home",
    "/analysis",
    "/economics",
    "/wine",
})
DASH_CATCH_ALL_ENDPOINT = "/<path:path>"
SESSION_INITIALIZATION_ENDPOINTS = frozenset({
    "/",
    DASH_CATCH_ALL_ENDPOINT,
    "/_dash-update-component",
})
IMPOSSIBLE_PATH_MARKERS = (
    "/wp-",
    "/wp/",
    "/wordpress/",
    "/wp-includes/",
)
SENSITIVE_PATH_PREFIXES = (
    "/.env",
    "/.git",
    "/.hg",
    "/.svn",
)


def is_allowed_production_host(host):
    hostname = host.partition(":")[0].rstrip(".").lower()
    return hostname in PRODUCTION_HOSTS


def is_impossible_request(path, query_args):
    normalized_path = path.lower()
    if ".php" in normalized_path:
        return True
    if normalized_path.startswith(SENSITIVE_PATH_PREFIXES):
        return True
    if any(marker in normalized_path for marker in IMPOSSIBLE_PATH_MARKERS):
        return True

    return any(
        key.lower() == "rest_route" and value.lower().startswith("/wp/")
        for key, value in query_args.items(multi=True)
    )


# Initialize openai with API key
client = OpenAI(
    api_key=CONFIG.openai_api_key
)


server = Flask(__name__)
server.wsgi_app = ProxyFix(server.wsgi_app, x_proto=1)
server.secret_key = CONFIG.flask_secret_key
server.config.update(
    SESSION_COOKIE_SECURE=CONFIG.is_production,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP,
                          "https://fonts.googleapis.com/css2?family=Kaisei+Decol&family=Libre+Franklin:"
                          "ital,wght@0,100..900;1,100..900&display=swap"],
    external_scripts=['https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.js'],
    pages_folder=str(CONFIG.pages_dir),
    server=server)


@server.get("/robots.txt")
def robots_txt():
    response = server.response_class(
        "User-agent: *\nDisallow: /\n",
        mimetype="text/plain",
    )
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response


@server.before_request
def reject_invalid_request():
    if CONFIG.is_production and not is_allowed_production_host(request.host):
        abort(404)

    if is_impossible_request(request.path, request.args):
        abort(404)

    if (
        request.endpoint == DASH_CATCH_ALL_ENDPOINT
        and request.path not in PUBLIC_PAGE_PATHS
    ):
        abort(404)


@server.before_request
def enforce_https_redirect():
    if CONFIG.force_https and not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)


@server.before_request
def ensure_session():
    if request.endpoint not in SESSION_INITIALIZATION_ENDPOINTS:
        return

    # Ensure every session has a user_id,
    if 'user_id' not in session:
        # Regular users get a dynamically generated session ID
        session['user_id'] = str(uuid.uuid4())
        session['request_count'] = 0  # Initialize request count for new session


@server.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), geolocation=(), microphone=()",
    )
    return response


app.title = CONFIG.browser_title()
app.index_string = CONFIG.asset_path("custom_header.html").read_text(encoding="utf-8")
app.layout = html.Div([
    dcc.Store(id='selected-stars', data=[]),
    dcc.Store(id='available-stars', data=[]),
    dcc.Store(id='department-centroid-store', data={}),
    dcc.Store(id='paris-arrondissement-centroid', data={}),
    dcc.Store(id='region-demographics-centroid', data={}),
    dcc.Store(
        id=RESPONSIVE_INPUT_MODE_STORE_ID,
        data=initial_responsive_input_mode(),
    ),
    dcc.Location(id='url', refresh=False),
    dash.page_container
])

# Initialize the cache (Maybe Redis or filesystem-based caching for production...?)
cache = Cache(app.server, config=CONFIG.cache_config)

register_navigation_callbacks(app)
register_responsive_input_callbacks(app)
register_guide_callbacks(app, DATA)
register_analysis_callbacks(app, DATA)
register_economics_callbacks(app, DATA)
register_wine_callbacks(app, DATA, CONFIG, cache, client)


if __name__ == '__main__':
    app.run_server(debug=CONFIG.debug)
