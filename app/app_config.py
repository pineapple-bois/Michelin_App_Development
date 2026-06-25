import logging
import os
import secrets
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PACKAGE_DIR = Path(__file__).resolve().parent
BASE_DIR = PACKAGE_DIR.parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = ASSETS_DIR / "Data"
PAGES_DIR = PACKAGE_DIR / "pages"

LOGGER = logging.getLogger(__name__)


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


def load_config():
    load_dotenv(BASE_DIR / ".env")

    is_production = _detect_production()
    return RuntimeConfig(
        base_dir=BASE_DIR,
        package_dir=PACKAGE_DIR,
        assets_dir=ASSETS_DIR,
        data_dir=DATA_DIR,
        pages_dir=PAGES_DIR,
        is_production=is_production,
        force_https=_env_bool("FORCE_HTTPS", default=is_production),
        debug=_env_bool("DASH_DEBUG", default=False),
        flask_secret_key=_get_secret_key(is_production),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_request_limit=_env_int("OPENAI_REQUEST_LIMIT", 10),
        cache_type=os.getenv("CACHE_TYPE", "simple"),
        cache_default_timeout=_env_int("CACHE_DEFAULT_TIMEOUT", 3600),
    )


CONFIG = load_config()
