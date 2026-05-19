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


def _get_positive_int(key: str, default: int) -> int:
    value = _get_int(key, default)
    if value < 1:
        raise RuntimeError(f"Environment variable {key} must be greater than zero")
    return value


def _validate_secret_key_entropy(secret_key: str) -> str:
    if len(secret_key) < 32:
        raise RuntimeError(
            "SECRET_KEY must be at least 32 characters for HS256 JWT algorithm. "
            "Generate a strong key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    return secret_key


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


def _validate_debug_mode(app_env: str, debug: bool) -> bool:
    if app_env == "production" and debug:
        raise RuntimeError("DEBUG mode cannot be enabled in production environment. Set DEBUG=false or APP_ENV=development.")
    return debug


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
    mysql_ssl_disabled: bool = _get_bool("MYSQL_SSL_DISABLED", True)
    database_url: str = _get_env("DATABASE_URL", _build_mysql_database_url())
    db_pool_size: int = _get_positive_int("DB_POOL_SIZE", 20)
    database_connection_timeout: int = _get_positive_int("DATABASE_CONNECTION_TIMEOUT", 30)
    startup_schema_validation_timeout_seconds: int = _get_positive_int("STARTUP_SCHEMA_VALIDATION_TIMEOUT_SECONDS", 5)

    secret_key: str = _validate_secret_key_entropy(_get_env("SECRET_KEY", required=True))
    jwt_algorithm: str = _get_env("JWT_ALGORITHM", "HS256")
    jwt_issuer: str = _get_env("JWT_ISSUER", "ghana-prison-service-api")
    jwt_audience: str = _get_env("JWT_AUDIENCE", "ghana-prison-service-clients")
    access_token_expire_minutes: int = _get_int("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    refresh_token_expire_days: int = _get_int("REFRESH_TOKEN_EXPIRE_DAYS", 7)
    bcrypt_rounds: int = _get_int("BCRYPT_ROUNDS", 12)
    password_min_length: int = _get_positive_int("PASSWORD_MIN_LENGTH", 8)
    password_max_length: int = _get_positive_int("PASSWORD_MAX_LENGTH", 128)
    password_require_special: bool = _get_bool("PASSWORD_REQUIRE_SPECIAL", True)
    password_require_uppercase: bool = _get_bool("PASSWORD_REQUIRE_UPPERCASE", True)
    password_require_lowercase: bool = _get_bool("PASSWORD_REQUIRE_LOWERCASE", True)
    password_require_number: bool = _get_bool("PASSWORD_REQUIRE_NUMBER", True)
    compromised_passwords: list[str] = field(init=False, default_factory=list)
    max_active_sessions: int = _get_positive_int("MAX_ACTIVE_SESSIONS", 5)
    account_lockout_enabled: bool = _get_bool("ACCOUNT_LOCKOUT_ENABLED", True)
    account_lockout_max_failed_attempts: int = _get_positive_int("ACCOUNT_LOCKOUT_MAX_FAILED_ATTEMPTS", 5)
    account_lockout_window_seconds: int = _get_positive_int("ACCOUNT_LOCKOUT_WINDOW_SECONDS", 900)
    account_lockout_duration_seconds: int = _get_positive_int("ACCOUNT_LOCKOUT_DURATION_SECONDS", 900)

    superadmin_email: str = _get_env("SUPERADMIN_EMAIL", "")
    superadmin_password: str = _get_env("SUPERADMIN_PASSWORD", "")
    superadmin_first_name: str = _get_env("SUPERADMIN_FIRST_NAME", "")
    superadmin_last_name: str = _get_env("SUPERADMIN_LAST_NAME", "")

    mail_provider: str = _get_env("MAIL_PROVIDER", "smtp")
    mail_from: str = _get_env("MAIL_FROM", "")
    mail_from_name: str = _get_env("MAIL_FROM_NAME", "Prison Management System")
    smtp_host: str = _get_env("SMTP_HOST", "")
    smtp_port: int = _get_int("SMTP_PORT", 587)
    smtp_user: str = _get_env("SMTP_USER", "")
    smtp_password: str = _get_env("SMTP_PASSWORD", "")
    smtp_tls: bool = _get_bool("SMTP_TLS", True)
    smtp_ssl: bool = _get_bool("SMTP_SSL", False)
    email_retry_attempts: int = _get_positive_int("EMAIL_RETRY_ATTEMPTS", 3)
    email_retry_delay_seconds: float = _get_float("EMAIL_RETRY_DELAY_SECONDS", 0.25)

    sms_provider: str = _get_env("SMS_PROVIDER", "termii")
    termii_api_key: str = _get_env("TERMII_API_KEY", "")
    termii_from: str = _get_env("TERMII_FROM", "")
    termii_sms_url: str = _get_env("TERMII_SMS_URL", "")
    sms_message_type: str = _get_env("SMS_MESSAGE_TYPE", "plain")
    sms_channel: str = _get_env("SMS_CHANNEL", "generic")
    sms_retry_attempts: int = _get_positive_int("SMS_RETRY_ATTEMPTS", 3)
    sms_retry_delay_seconds: float = _get_float("SMS_RETRY_DELAY_SECONDS", 0.25)
    outbound_http_timeout_seconds: int = _get_positive_int("OUTBOUND_HTTP_TIMEOUT_SECONDS", 10)

    storage_provider: str = _get_env("STORAGE_PROVIDER", "local")
    local_upload_dir: str = _get_env("LOCAL_UPLOAD_DIR", "uploads")
    max_upload_size_mb: int = _get_positive_int("MAX_UPLOAD_SIZE_MB", 10)
    upload_chunk_size_bytes: int = _get_positive_int("UPLOAD_CHUNK_SIZE_BYTES", 1048576)
    max_request_body_size_mb: int = _get_positive_int("MAX_REQUEST_BODY_SIZE_MB", 10)
    allowed_image_types: list[str] = field(init=False, default_factory=list)
    allowed_doc_types: list[str] = field(init=False, default_factory=list)

    rate_limit_enabled: bool = _get_bool("RATE_LIMIT_ENABLED", True)
    rate_limit_requests: int = _get_positive_int("RATE_LIMIT_REQUESTS", 100)
    rate_limit_window_seconds: int = _get_positive_int("RATE_LIMIT_WINDOW_SECONDS", 60)
    auth_rate_limit_requests: int = _get_positive_int("AUTH_RATE_LIMIT_REQUESTS", 10)
    auth_rate_limit_window_seconds: int = _get_positive_int("AUTH_RATE_LIMIT_WINDOW_SECONDS", 60)

    base_country: str = _get_env("BASE_COUNTRY", "GH")
    base_currency: str = _get_env("BASE_CURRENCY", "GHS")
    base_timezone: str = _get_env("BASE_TIMEZONE", "Africa/Accra")

    log_level: str = _get_env("LOG_LEVEL", "INFO")
    maintenance_mode: bool = _get_bool("MAINTENANCE_MODE", False)
    maintenance_message: str = _get_env("MAINTENANCE_MESSAGE", "")
    maintenance_bypass_ips: list[str] = field(init=False, default_factory=list)

    default_page_size: int = _get_int("DEFAULT_PAGE_SIZE", 20)
    max_page_size: int = _get_int("MAX_PAGE_SIZE", 100)
    csv_filename_prefix: str = _get_env("CSV_FILENAME_PREFIX", "pms_export")
    csv_timestamp_format: str = _get_env("CSV_TIMESTAMP_FORMAT", "%Y%m%d_%H%M%S")

    background_scheduler_enabled: bool = _get_bool("BACKGROUND_SCHEDULER_ENABLED", False)
    background_scheduler_timezone: str = _get_env("BACKGROUND_SCHEDULER_TIMEZONE", "UTC")
    background_job_max_attempts: int = _get_positive_int("BACKGROUND_JOB_MAX_ATTEMPTS", 3)
    background_job_retry_delay_seconds: int = _get_positive_int("BACKGROUND_JOB_RETRY_DELAY_SECONDS", 5)

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_origins", _get_list("ALLOWED_ORIGINS"))
        object.__setattr__(self, "allowed_methods", _get_list("ALLOWED_METHODS", ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]))
        object.__setattr__(self, "allowed_headers", _get_list("ALLOWED_HEADERS", ["*"]))
        object.__setattr__(self, "trusted_hosts", _get_list("TRUSTED_HOSTS"))
        object.__setattr__(self, "compromised_passwords", _get_list("COMPROMISED_PASSWORDS"))
        object.__setattr__(
            self,
            "allowed_image_types",
            _get_list("ALLOWED_IMAGE_TYPES", ["image/jpeg", "image/png", "image/webp"]),
        )
        object.__setattr__(
            self,
            "allowed_doc_types",
            _get_list("ALLOWED_DOC_TYPES", ["application/pdf", "image/jpeg", "image/png"]),
        )
        object.__setattr__(self, "maintenance_bypass_ips", _get_list("MAINTENANCE_BYPASS_IPS", ["127.0.0.1", "localhost"]))
        
        # Validate DEBUG mode not enabled in production
        _validate_debug_mode(self.app_env, self.debug)


settings = Settings()
