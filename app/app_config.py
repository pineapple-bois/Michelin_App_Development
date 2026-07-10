import logging
import os
import secrets
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

from dotenv import load_dotenv


APP_DISTRIBUTION_NAME = "michelin-guide-france"
PACKAGE_DIR = Path(__file__).resolve().parent
BASE_DIR = PACKAGE_DIR.parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = ASSETS_DIR / "data"
PAGES_DIR = PACKAGE_DIR / "pages"

LOGGER = logging.getLogger(__name__)
CACHE_TYPE_ALIASES = {
    "simple": "flask_caching.backends.simplecache.SimpleCache",
}


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer, got {value!r}") from exc


def _cache_type(name):
    return CACHE_TYPE_ALIASES.get(name.strip().lower(), name)


def _get_application_version():
    try:
        return metadata.version(APP_DISTRIBUTION_NAME)
    except metadata.PackageNotFoundError as exc:
        raise RuntimeError(
            f"{APP_DISTRIBUTION_NAME!r} is not installed. Install the application "
            "from the repository root with `python -m pip install -r requirements.txt` "
            "or `python -m pip install -e .` so the active Michelin Guide year can "
            "be derived from package metadata."
        ) from exc


def _guide_year_from_version(version):
    major = version.split(".", maxsplit=1)[0]
    if not (major.isdigit() and len(major) == 4):
        raise RuntimeError(
            f"{APP_DISTRIBUTION_NAME!r} version {version!r} must start with a "
            "four-digit Michelin Guide year."
        )
    return int(major)


def _detect_production():
    if os.getenv("DYNO"):
        return True

    app_env = os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or os.getenv("DASH_ENV")
    if app_env:
        return app_env.strip().lower() in {"prod", "production"}
    return False


def _get_secret_key(is_production):
    secret_key = os.getenv("FLASK_SECRET_KEY")
    if secret_key:
        return secret_key

    if is_production:
        raise RuntimeError(
            "FLASK_SECRET_KEY must be set in production. "
            "Generate a stable secret and configure it in the Heroku app config vars."
        )

    LOGGER.warning(
        "FLASK_SECRET_KEY is not set; using a generated development-only secret. "
        "Set FLASK_SECRET_KEY for stable local sessions."
    )
    return secrets.token_urlsafe(32)


@dataclass(frozen=True)
class RuntimeConfig:
    base_dir: Path
    package_dir: Path
    assets_dir: Path
    data_dir: Path
    application_version: str
    guide_year: int
    pages_dir: Path
    is_production: bool
    force_https: bool
    debug: bool
    flask_secret_key: str
    openai_api_key: str | None
    openai_request_limit: int
    cache_type: str
    cache_default_timeout: int

    @property
    def cache_config(self):
        return {
            "CACHE_TYPE": self.cache_type,
            "CACHE_DEFAULT_TIMEOUT": self.cache_default_timeout,
        }

    def asset_path(self, *parts):
        return self.assets_dir.joinpath(*parts)

    def data_path(self, *parts):
        return self.data_dir.joinpath(*parts)

    @property
    def data_year(self):
        return str(self.guide_year)

    def annual_data_path(self, *parts):
        return self.data_dir.joinpath(str(self.guide_year), *parts)

    def browser_title(self, section=None):
        base_title = f"Gastronomic Guide to France {self.guide_year}"
        if section:
            return f"{section} - {base_title}"
        return f"{base_title} - pineapple-bois"


def load_config():
    load_dotenv(BASE_DIR / ".env")

    is_production = _detect_production()
    application_version = _get_application_version()
    guide_year = _guide_year_from_version(application_version)
    return RuntimeConfig(
        base_dir=BASE_DIR,
        package_dir=PACKAGE_DIR,
        assets_dir=ASSETS_DIR,
        data_dir=DATA_DIR,
        application_version=application_version,
        guide_year=guide_year,
        pages_dir=PAGES_DIR,
        is_production=is_production,
        force_https=_env_bool("FORCE_HTTPS", default=is_production),
        debug=_env_bool("DASH_DEBUG", default=False),
        flask_secret_key=_get_secret_key(is_production),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_request_limit=_env_int("OPENAI_REQUEST_LIMIT", 10),
        cache_type=_cache_type(os.getenv("CACHE_TYPE", "simple")),
        cache_default_timeout=_env_int("CACHE_DEFAULT_TIMEOUT", 3600),
    )


CONFIG = load_config()
APPLICATION_VERSION = CONFIG.application_version
GUIDE_YEAR = CONFIG.guide_year
