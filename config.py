import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/fwc_26"


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

    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_REFRESH_EACH_REQUEST = False
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME

    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000")
    RESET_TOKEN_MAX_AGE_SECONDS = 3600
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_LOCKOUT_HOURS = 24
