from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def _get_env(key: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.getenv(key, default)
    if required and (value is None or value.strip() == ""):
        raise RuntimeError(f"Missing required environment variable: {key}")
    return "" if value is None else value.strip()


def _get_bool(key: str, default: bool = False) -> bool:
    value = _get_env(key, str(default)).lower()
    return value in {"1", "true", "yes", "y", "on"}


def _get_int(key: str, default: int) -> int:
    value = _get_env(key, str(default))
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {key} must be an integer") from exc


def _get_float(key: str, default: float) -> float:
    value = _get_env(key, str(default))
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {key} must be a number") from exc


def _get_list(key: str, default: Iterable[str] | None = None) -> list[str]:
    fallback = ",".join(default or [])
    value = _get_env(key, fallback)
    return [item.strip() for item in value.split(",") if item.strip()]


def _build_mysql_database_url() -> str:
    driver = _get_env("MYSQL_DRIVER", "mysql+mysqlconnector")
    user = quote(_get_env("MYSQL_USER", "root"), safe="")
    password = quote(_get_env("MYSQL_PASSWORD", ""), safe="")
    host = _get_env("MYSQL_HOST", "127.0.0.1")
    port = _get_int("MYSQL_PORT", 3306)
    database = _get_env("MYSQL_DATABASE", "pms_db")
    return f"{driver}://{user}:{password}@{host}:{port}/{database}"


@dataclass(frozen=True)
class Settings:
    app_name: str = _get_env("APP_NAME", "Prison Management System")
    app_version: str = _get_env("APP_VERSION", "v1.0.0")
    app_env: str = _get_env("APP_ENV", "development")
    debug: bool = _get_bool("DEBUG", False)
    api_prefix: str = _get_env("API_PREFIX", "/api/v1")
    docs_enabled: bool = _get_bool("DOCS_ENABLED", False)

    host: str = _get_env("HOST", "127.0.0.1")
    port: int = _get_int("PORT", 8000)
    workers: int = _get_int("WORKERS", 1)

    allowed_origins: list[str] = field(init=False, default_factory=list)
    allowed_methods: list[str] = field(init=False, default_factory=list)
    allowed_headers: list[str] = field(init=False, default_factory=list)
    allow_credentials: bool = _get_bool("ALLOW_CREDENTIALS", True)
    trusted_hosts: list[str] = field(init=False, default_factory=list)

    mysql_driver: str = _get_env("MYSQL_DRIVER", "mysql+mysqlconnector")
    mysql_host: str = _get_env("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = _get_int("MYSQL_PORT", 3306)
    mysql_user: str = _get_env("MYSQL_USER", "root")
    mysql_password: str = _get_env("MYSQL_PASSWORD", "")
    mysql_database: str = _get_env("MYSQL_DATABASE", "pms_db")
    database_url: str = _get_env("DATABASE_URL", _build_mysql_database_url())
    db_pool_size: int = _get_int("DB_POOL_SIZE", 20)
    db_max_overflow: int = _get_int("DB_MAX_OVERFLOW", 10)
    db_pool_timeout: int = _get_int("DB_POOL_TIMEOUT", 30)
    db_pool_recycle: int = _get_int("DB_POOL_RECYCLE", 1800)
    db_echo: bool = _get_bool("DB_ECHO", False)

    secret_key: str = _get_env("SECRET_KEY", required=True)
    jwt_algorithm: str = _get_env("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = _get_int("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    refresh_token_expire_days: int = _get_int("REFRESH_TOKEN_EXPIRE_DAYS", 7)
    bcrypt_rounds: int = _get_int("BCRYPT_ROUNDS", 12)

    base_country: str = _get_env("BASE_COUNTRY", "GH")
    base_currency: str = _get_env("BASE_CURRENCY", "GHS")
    base_timezone: str = _get_env("BASE_TIMEZONE", "Africa/Accra")

    log_level: str = _get_env("LOG_LEVEL", "INFO")
    maintenance_mode: bool = _get_bool("MAINTENANCE_MODE", False)
    maintenance_message: str = _get_env("MAINTENANCE_MESSAGE", "")

    default_page_size: int = _get_int("DEFAULT_PAGE_SIZE", 20)
    max_page_size: int = _get_int("MAX_PAGE_SIZE", 100)

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_origins", _get_list("ALLOWED_ORIGINS"))
        object.__setattr__(self, "allowed_methods", _get_list("ALLOWED_METHODS", ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]))
        object.__setattr__(self, "allowed_headers", _get_list("ALLOWED_HEADERS", ["*"]))
        object.__setattr__(self, "trusted_hosts", _get_list("TRUSTED_HOSTS"))


settings = Settings()
