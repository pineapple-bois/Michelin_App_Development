import dash
import dash_bootstrap_components as dbc
import uuid
from openai import OpenAI
from dash import dcc, html
from flask import Flask, session, request, redirect
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix

from app_data import DATA
from app_config import CONFIG
from callbacks.analysis import register_analysis_callbacks
from callbacks.economics import register_economics_callbacks
from callbacks.guide import register_guide_callbacks
from callbacks.navigation import register_navigation_callbacks
from callbacks.wine import register_wine_callbacks


# Initialize openai with API key
client = OpenAI(
    api_key=CONFIG.openai_api_key
)


server = Flask(__name__)
server.wsgi_app = ProxyFix(server.wsgi_app, x_proto=1, x_host=1)
server.secret_key = CONFIG.flask_secret_key
app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP,
                          "https://fonts.googleapis.com/css2?family=Kaisei+Decol&family=Libre+Franklin:"
                          "ital,wght@0,100..900;1,100..900&display=swap"],
    external_scripts=['https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.js'],
    server=server)


@server.before_request
def enforce_https_redirect():
    if CONFIG.force_https and not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)


@server.before_request
def ensure_session():
    # Ensure every session has a user_id,
    if 'user_id' not in session:
        # Regular users get a dynamically generated session ID
        session['user_id'] = str(uuid.uuid4())
        session['request_count'] = 0  # Initialize request count for new session


app.title = 'Gastronomic Guide to France - pineapple-bois'
app.index_string = CONFIG.asset_path("custom_header.html").read_text(encoding="utf-8")
app.layout = html.Div([
    dcc.Store(id='selected-stars', data=[]),
    dcc.Store(id='available-stars', data=[]),
    dcc.Store(id='department-centroid-store', data={}),
    dcc.Store(id='paris-arrondissement-centroid', data={}),
    dcc.Store(id='region-demographics-centroid', data={}),
    dcc.Location(id='url', refresh=False),
    dash.page_container
])

# Initialize the cache (Maybe Redis or filesystem-based caching for production...?)
cache = Cache(app.server, config=CONFIG.cache_config)

register_navigation_callbacks(app)
register_guide_callbacks(app, DATA)
register_analysis_callbacks(app, DATA)
register_economics_callbacks(app, DATA)
register_wine_callbacks(app, DATA, CONFIG, cache, client)


if __name__ == '__main__':
    app.run_server(debug=CONFIG.debug)
