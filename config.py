import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/fwc_26"


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def env_list(name):
    value = os.getenv(name, "")
    items = [item.strip() for item in value.split(",")]
    return [item for item in items if item]


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA", "app")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_ENGINE_OPTIONS = (
        {"connect_args": {"options": f"-csearch_path={POSTGRES_SCHEMA}"}}
        if DATABASE_URL.startswith("postgresql") and POSTGRES_SCHEMA
        else {}
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TRUSTED_HOSTS = env_list("TRUSTED_HOSTS") or None
    MAX_CONTENT_LENGTH = env_int("MAX_CONTENT_LENGTH", 1024 * 1024)

    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_REFRESH_EACH_REQUEST = False
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
    PREFERRED_URL_SCHEME = "https" if SESSION_COOKIE_SECURE else "http"

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = env_bool("MAIL_USE_TLS", True)
    MAIL_USE_SSL = env_bool("MAIL_USE_SSL", False)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME

    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000")
    RESET_TOKEN_MAX_AGE_SECONDS = 3600
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200 per minute; 2000 per hour")
    RATELIMIT_HEADERS_ENABLED = True

    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_LOCKOUT_HOURS = 24

    PROXY_FIX_X_FOR = env_int("PROXY_FIX_X_FOR", 0)
    PROXY_FIX_X_PROTO = env_int("PROXY_FIX_X_PROTO", 0)
    PROXY_FIX_X_HOST = env_int("PROXY_FIX_X_HOST", 0)

    SECURITY_HEADERS = env_bool("SECURITY_HEADERS", True)
    CONTENT_SECURITY_POLICY = os.getenv(
        "CONTENT_SECURITY_POLICY",
        "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
    )
