from __future__ import annotations

from typing import Any, Callable

import os

from flask import g, jsonify, request

from src.dtos.external_integration_dto import (
    APIIntegrationDTO,
    BiometricIntegrationDTO,
    CloudBackupLogDTO,
    CourtIntegrationDTO,
    ExternalIntegrationValidationError,
    NIAIntegrationDTO,
    PoliceIntegrationDTO,
    SynchronizationLogDTO,
)
from src.integrations.adapters import IntegrationProviderNotConfigured
from src.integrations.security import IntegrationSecurityError, sanitize_metadata, verify_request_signature
from src.services.audit_service import AuditService
from src.services.external_integration_service import (
    ExternalIntegrationConflictError,
    ExternalIntegrationForeignKeyError,
    ExternalIntegrationService,
    ExternalIntegrationWorkflowError,
    is_duplicate_external_integration_error,
    is_mysql_error,
)


LIST_TABLES = {
    "court": "court_integrations",
    "nia": "nia_integrations",
    "police": "police_integrations",
    "biometrics": "biometric_integrations",
    "apis": "api_integrations",
    "synchronizations": "synchronization_logs",
    "backups": "cloud_backup_logs",
}


def record_court_integration():
    access_error = _validate_gateway_access()
    if access_error:
        return access_error
    return _create_record(
        dto_factory=CourtIntegrationDTO.from_payload,
        service_method=ExternalIntegrationService.record_court_integration,
        response_key="court_integration",
        audit_action="external_court_integration_recorded",
        message="Court integration recorded successfully",
    )


def record_nia_integration():
    access_error = _validate_gateway_access()
    if access_error:
        return access_error
    return _create_record(
        dto_factory=NIAIntegrationDTO.from_payload,
        service_method=ExternalIntegrationService.record_nia_integration,
        response_key="nia_integration",
        audit_action="external_nia_integration_recorded",
        message="NIA integration recorded successfully",
    )


def record_police_integration():
    access_error = _validate_gateway_access()
    if access_error:
        return access_error
    return _create_record(
        dto_factory=PoliceIntegrationDTO.from_payload,
        service_method=ExternalIntegrationService.record_police_integration,
        response_key="police_integration",
        audit_action="external_police_integration_recorded",
        message="Police integration recorded successfully",
    )


def record_biometric_integration():
    access_error = _validate_gateway_access()
    if access_error:
        return access_error
    return _create_record(
        dto_factory=BiometricIntegrationDTO.from_payload,
        service_method=ExternalIntegrationService.record_biometric_integration,
        response_key="biometric_integration",
        audit_action="external_biometric_integration_recorded",
        message="Biometric integration recorded successfully",
    )


def register_api_integration():
    access_error = _validate_gateway_access()
    if access_error:
        return access_error
    return _create_record(
        dto_factory=APIIntegrationDTO.from_payload,
        service_method=ExternalIntegrationService.register_api_integration,
        response_key="api_integration",
        audit_action="external_api_integration_registered",
        message="API integration registered successfully",
    )


def record_synchronization():
    access_error = _validate_gateway_access()
    if access_error:
        return access_error
    return _create_record(
        dto_factory=SynchronizationLogDTO.from_payload,
        service_method=ExternalIntegrationService.record_synchronization,
        response_key="synchronization_log",
        audit_action="external_synchronization_recorded",
        message="Synchronization log recorded successfully",
    )


def record_cloud_backup():
    access_error = _validate_gateway_access()
    if access_error:
        return access_error
    return _create_record(
        dto_factory=CloudBackupLogDTO.from_payload,
        service_method=ExternalIntegrationService.record_cloud_backup,
        response_key="cloud_backup_log",
        audit_action="external_cloud_backup_recorded",
        message="Cloud backup log recorded successfully",
    )


def list_integration_records(record_type: str):
    access_error = _validate_gateway_access(require_signature=False)
    if access_error:
        return access_error
    table = LIST_TABLES.get(record_type)
    if table is None:
        return _error("Unsupported integration record type", 404)
    try:
        limit = min(max(int(request.args.get("limit", 20)), 1), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        return _error("Invalid pagination parameters", 400)
    filters = {key: value for key, value in request.args.items() if key not in {"limit", "offset"}}
    try:
        records = ExternalIntegrationService.list_records(table, filters=filters, limit=limit, offset=offset)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while retrieving integration records", 500)
        raise
    return jsonify({"records": [record.to_dict() for record in records], "limit": limit, "offset": offset})


def get_integration_reports():
    access_error = _validate_gateway_access(require_signature=False)
    if access_error:
        return access_error
    try:
        reports = ExternalIntegrationService.get_reports()
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while generating integration reports", 500)
        raise
    return jsonify({"external_integration_reports": _serialize(reports)})


def execute_provider_operation():
    access_error = _validate_gateway_access()
    if access_error:
        return access_error
    payload = _json_payload()
    provider = str(payload.get("provider", "")).strip()
    operation = str(payload.get("operation", "")).strip()
    reference = str(payload.get("reference", "")).strip()
    errors: dict[str, str] = {}
    if not provider:
        errors["provider"] = "This field is required"
    if not operation:
        errors["operation"] = "This field is required"
    if not reference:
        errors["reference"] = "This field is required"
    if errors:
        return _error("Validation failed", 400, errors)

    try:
        result = ExternalIntegrationService.execute_provider_operation(provider=provider, operation=operation, reference=reference)
    except IntegrationProviderNotConfigured as exc:
        _audit("external_provider_operation_blocked", status="failed", metadata={"provider": provider, "operation": operation, "reference": reference, "error_code": "provider_not_configured"})
        return _error("External provider is not configured", 503)
    except IntegrationSecurityError as exc:
        _audit("external_provider_operation_blocked", status="failed", metadata={"provider": provider, "operation": operation, "reference": reference, "error_code": "security_policy"})
        return _error(str(exc), 400)
    except ExternalIntegrationWorkflowError as exc:
        return _error(str(exc), 400)

    _audit("external_provider_operation_executed", metadata={"provider": provider, "operation": operation, "reference": reference})
    return jsonify({"message": "External provider operation executed successfully", "result": result})


def _create_record(
    *,
    dto_factory: Callable[[dict[str, Any]], Any],
    service_method: Callable[[Any], Any],
    response_key: str,
    audit_action: str,
    message: str,
):
    payload = _json_payload()
    try:
        dto = dto_factory(payload)
        record = service_method(dto)
    except ExternalIntegrationValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except ExternalIntegrationConflictError as exc:
        return _error(str(exc), 409)
    except (ExternalIntegrationForeignKeyError, ExternalIntegrationWorkflowError) as exc:
        return _error(str(exc), 400)
    except IntegrationSecurityError as exc:
        _audit(audit_action, status="failed", metadata={"error_code": "security_policy"})
        return _error(str(exc), 400)
    except Exception as exc:
        if is_duplicate_external_integration_error(exc):
            return _error("Duplicate external integration record", 409)
        if is_mysql_error(exc):
            return _error("Database error while processing external integration record", 500)
        raise

    _audit(audit_action, metadata={f"{response_key}_id": record.data.get("id")})
    return jsonify({"message": message, response_key: record.to_dict()}), 201


def _audit(action: str, *, metadata: dict[str, Any] | None = None, status: str = "success") -> None:
    AuditService.record(
        action=action,
        status=status,
        actor_user_id=g.current_user.id,
        target_user_id=None,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata=sanitize_metadata(metadata or {}),
    )


def _json_payload() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def _error(message: str, status_code: int, errors: dict[str, str] | None = None):
    body: dict[str, Any] = {"error": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status_code


def _client_ip() -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.remote_addr


def _user_agent() -> str | None:
    return request.headers.get("User-Agent")


def _validate_gateway_access(*, require_signature: bool = True):
    if not _ip_allowed(_client_ip()):
        _audit("external_integration_access_blocked", status="failed", metadata={"error_code": "ip_not_allowed"})
        return _error("External integration access is not allowed from this source", 403)
    if not require_signature or not _signature_required():
        return None
    try:
        verify_request_signature(
            raw_body=request.get_data(cache=True),
            signature=request.headers.get("X-Integration-Signature", ""),
            timestamp=request.headers.get("X-Integration-Timestamp", ""),
            nonce=request.headers.get("X-Integration-Nonce", ""),
        )
    except IntegrationSecurityError as exc:
        _audit("external_integration_signature_failed", status="failed", metadata={"error_code": "invalid_signature"})
        return _error(str(exc), 401)
    return None


def _ip_allowed(ip_address: str | None) -> bool:
    allowed = [item.strip() for item in os.getenv("EXTERNAL_INTEGRATION_ALLOWED_IPS", "").split(",") if item.strip()]
    if not allowed:
        return True
    return bool(ip_address and ip_address in allowed)


def _signature_required() -> bool:
    return os.getenv("EXTERNAL_INTEGRATION_REQUIRE_SIGNATURE", "false").strip().lower() in {"1", "true", "yes", "on"}


def _serialize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
