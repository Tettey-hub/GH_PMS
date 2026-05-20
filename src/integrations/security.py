from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from src.config.settings import settings


ENCRYPTED_PREFIX = "enc:v1:"
SENSITIVE_FIELD_NAMES = {
    "external_case_reference",
    "national_id",
    "nia_reference_number",
    "police_reference_number",
    "biometric_reference_id",
    "endpoint_reference",
    "target_server",
    "backup_reference",
    "storage_location",
}
SECRET_FIELD_PATTERNS = re.compile(r"(token|secret|password|credential|api[_-]?key|authorization)", re.IGNORECASE)
ALLOWED_PROVIDER_OPERATIONS = {
    "warrant_verification",
    "nia_verification",
    "police_synchronization",
    "biometric_verification",
    "health_check",
    "cloud_backup",
}


class IntegrationSecurityError(RuntimeError):
    pass


def encrypt_sensitive_value(value: Any) -> Any:
    if value in {None, ""}:
        return value
    value_text = str(value)
    if value_text.startswith(ENCRYPTED_PREFIX):
        return value_text
    fernet = _get_fernet()
    return ENCRYPTED_PREFIX + fernet.encrypt(value_text.encode("utf-8")).decode("utf-8")


def decrypt_sensitive_value(value: Any) -> Any:
    if value in {None, ""}:
        return value
    value_text = str(value)
    if not value_text.startswith(ENCRYPTED_PREFIX):
        return value_text
    fernet = _get_fernet()
    return fernet.decrypt(value_text.removeprefix(ENCRYPTED_PREFIX).encode("utf-8")).decode("utf-8")


def mask_sensitive_value(value: Any) -> Any:
    if value in {None, ""}:
        return value
    value_text = str(value)
    digest = hmac.new(_key_material(), value_text.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"protected:{digest[:12]}"


def protect_record_payload(table: str, data: dict[str, Any]) -> dict[str, Any]:
    protected = dict(data)
    for field in _sensitive_fields_for_table(table):
        if field in protected and protected[field] not in {None, ""}:
            protected[field] = encrypt_sensitive_value(protected[field])
    return protected


def redact_record(record: dict[str, Any]) -> dict[str, Any]:
    redacted = {}
    for key, value in record.items():
        if key in SENSITIVE_FIELD_NAMES or SECRET_FIELD_PATTERNS.search(key):
            redacted[key] = mask_sensitive_value(value)
        else:
            redacted[key] = value
    return redacted


def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key in SENSITIVE_FIELD_NAMES or SECRET_FIELD_PATTERNS.search(key):
            sanitized[key] = mask_sensitive_value(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_metadata(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_metadata(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    return sanitized


def assert_https_reference(value: str, *, field_name: str) -> None:
    parsed = urlparse(value.strip())
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise IntegrationSecurityError(f"{field_name} must be a valid HTTPS URL")


def assert_no_insecure_url(value: str, *, field_name: str) -> None:
    parsed = urlparse(value.strip())
    if parsed.scheme.lower() == "http":
        raise IntegrationSecurityError(f"{field_name} cannot use insecure HTTP")


def assert_encryption_ready() -> None:
    _get_fernet()


def validate_provider_operation_security(*, provider: str, operation: str, reference: str) -> None:
    if operation not in ALLOWED_PROVIDER_OPERATIONS:
        raise IntegrationSecurityError("Unsupported provider operation")
    if len(provider) > 100 or len(reference) > 255:
        raise IntegrationSecurityError("Provider operation metadata is too large")
    assert_no_insecure_url(reference, field_name="reference")


def verify_request_signature(*, raw_body: bytes, signature: str, timestamp: str, nonce: str) -> None:
    secret = _integration_request_signing_secret()
    if not secret:
        raise IntegrationSecurityError("Integration request signing is not configured")
    if not signature or not timestamp or not nonce:
        raise IntegrationSecurityError("Integration request signature, timestamp, and nonce are required")
    try:
        request_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise IntegrationSecurityError("Invalid integration request timestamp") from exc
    now = datetime.now(timezone.utc)
    if request_time.tzinfo is None:
        request_time = request_time.replace(tzinfo=timezone.utc)
    if abs((now - request_time).total_seconds()) > 300:
        raise IntegrationSecurityError("Integration request timestamp is outside the allowed window")
    message = b".".join([timestamp.encode("utf-8"), nonce.encode("utf-8"), raw_body])
    expected = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    supplied = signature.removeprefix("sha256=").strip()
    if not hmac.compare_digest(expected, supplied):
        raise IntegrationSecurityError("Invalid integration request signature")


def synchronization_checksum(data: dict[str, Any]) -> str:
    stable = json.dumps(data, default=str, separators=(",", ":"), sort_keys=True)
    return hmac.new(_key_material(), stable.encode("utf-8"), hashlib.sha256).hexdigest()


def _sensitive_fields_for_table(table: str) -> set[str]:
    fields_by_table = {
        "court_integrations": {"external_case_reference"},
        "nia_integrations": {"national_id", "nia_reference_number"},
        "police_integrations": {"police_reference_number"},
        "biometric_integrations": {"biometric_reference_id"},
        "api_integrations": {"endpoint_reference"},
        "synchronization_logs": {"target_server"},
        "cloud_backup_logs": {"backup_reference", "storage_location"},
    }
    return fields_by_table.get(table, set())


def _get_fernet():
    try:
        from cryptography.fernet import Fernet, InvalidToken  # noqa: F401
    except ImportError as exc:
        raise IntegrationSecurityError("cryptography package is required for external integration encryption") from exc
    key = _fernet_key()
    return Fernet(key)


def _fernet_key() -> bytes:
    configured = os.getenv("EXTERNAL_INTEGRATION_ENCRYPTION_KEY", "").strip()
    if configured:
        try:
            decoded = base64.urlsafe_b64decode(configured.encode("utf-8"))
        except Exception as exc:
            raise IntegrationSecurityError("EXTERNAL_INTEGRATION_ENCRYPTION_KEY must be a valid urlsafe base64 key") from exc
        if len(decoded) != 32:
            raise IntegrationSecurityError("EXTERNAL_INTEGRATION_ENCRYPTION_KEY must decode to 32 bytes")
        return configured.encode("utf-8")
    material = settings.secret_key.encode("utf-8")
    digest = hashlib.sha256(material).digest()
    return base64.urlsafe_b64encode(digest)


def _key_material() -> bytes:
    configured = os.getenv("EXTERNAL_INTEGRATION_HASH_KEY", "").strip()
    return configured.encode("utf-8") if configured else settings.secret_key.encode("utf-8")


def _integration_request_signing_secret() -> str:
    return os.getenv("EXTERNAL_INTEGRATION_REQUEST_SIGNING_SECRET", "").strip()
