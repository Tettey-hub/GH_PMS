from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.models.external_integration import (
    API_STATUSES,
    AUTHENTICATION_TYPES,
    BACKUP_STATUSES,
    BACKUP_TYPES,
    BIOMETRIC_ENROLLMENT_STATUSES,
    BIOMETRIC_MATCH_STATUSES,
    BIOMETRIC_TYPES,
    BIOMETRIC_VERIFICATION_STATUSES,
    CRIMINAL_RECORD_STATUSES,
    DEMOGRAPHIC_SYNC_STATUSES,
    HEARING_STATUSES,
    INTEGRATION_SYNC_STATUSES,
    NIA_VERIFICATION_STATUSES,
    RATE_LIMIT_STATUSES,
    RECIDIVISM_STATUSES,
    RECOVERY_TEST_STATUSES,
    SENTENCE_STATUSES,
    SYNCHRONIZATION_TYPES,
    WANTED_PERSON_STATUSES,
    WARRANT_STATUSES,
)


class ExternalIntegrationValidationError(ValueError):
    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Validation failed")
        self.errors = errors


@dataclass(frozen=True)
class CourtIntegrationDTO:
    inmate_id: int
    external_case_reference: str
    court_name: str
    court_api_source: str
    warrant_status: str
    hearing_status: str
    sentence_status: str
    synchronization_status: str
    hearing_date: datetime | None = None
    last_synced_at: datetime | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CourtIntegrationDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_text(errors, payload, "external_case_reference", max_length=100)
        _require_text(errors, payload, "court_name", max_length=150)
        _require_text(errors, payload, "court_api_source", max_length=100)
        _require_upper_enum(errors, payload, "warrant_status", WARRANT_STATUSES)
        _require_upper_enum(errors, payload, "hearing_status", HEARING_STATUSES)
        _require_upper_enum(errors, payload, "sentence_status", SENTENCE_STATUSES)
        _require_upper_enum(errors, payload, "synchronization_status", INTEGRATION_SYNC_STATUSES)
        _optional_datetime(errors, payload, "hearing_date")
        _optional_datetime(errors, payload, "last_synced_at")
        if errors:
            raise ExternalIntegrationValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            external_case_reference=_required_string(payload, "external_case_reference"),
            court_name=_required_string(payload, "court_name"),
            court_api_source=_required_string(payload, "court_api_source"),
            warrant_status=_required_string(payload, "warrant_status").upper(),
            hearing_date=_safe_datetime(payload.get("hearing_date")),
            hearing_status=_required_string(payload, "hearing_status").upper(),
            sentence_status=_required_string(payload, "sentence_status").upper(),
            synchronization_status=_required_string(payload, "synchronization_status").upper(),
            last_synced_at=_safe_datetime(payload.get("last_synced_at")),
        )


@dataclass(frozen=True)
class NIAIntegrationDTO:
    inmate_id: int
    national_id: str
    verification_status: str
    biometric_match_status: str
    demographic_sync_status: str
    nia_reference_number: str | None = None
    last_verified_at: datetime | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "NIAIntegrationDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_text(errors, payload, "national_id", max_length=50)
        _require_upper_enum(errors, payload, "verification_status", NIA_VERIFICATION_STATUSES)
        _require_upper_enum(errors, payload, "biometric_match_status", BIOMETRIC_MATCH_STATUSES)
        _require_upper_enum(errors, payload, "demographic_sync_status", DEMOGRAPHIC_SYNC_STATUSES)
        _optional_text(errors, payload, "nia_reference_number", max_length=100)
        _optional_datetime(errors, payload, "last_verified_at")
        if errors:
            raise ExternalIntegrationValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            national_id=_required_string(payload, "national_id"),
            verification_status=_required_string(payload, "verification_status").upper(),
            biometric_match_status=_required_string(payload, "biometric_match_status").upper(),
            demographic_sync_status=_required_string(payload, "demographic_sync_status").upper(),
            nia_reference_number=_optional_string(payload.get("nia_reference_number")),
            last_verified_at=_safe_datetime(payload.get("last_verified_at")),
        )


@dataclass(frozen=True)
class PoliceIntegrationDTO:
    inmate_id: int
    police_reference_number: str
    criminal_record_status: str
    fingerprint_match_status: str
    recidivism_status: str
    wanted_person_status: str
    synchronization_status: str
    intelligence_notes: str | None = None
    last_synced_at: datetime | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PoliceIntegrationDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_text(errors, payload, "police_reference_number", max_length=100)
        _require_upper_enum(errors, payload, "criminal_record_status", CRIMINAL_RECORD_STATUSES)
        _require_upper_enum(errors, payload, "fingerprint_match_status", BIOMETRIC_MATCH_STATUSES)
        _require_upper_enum(errors, payload, "recidivism_status", RECIDIVISM_STATUSES)
        _require_upper_enum(errors, payload, "wanted_person_status", WANTED_PERSON_STATUSES)
        _require_upper_enum(errors, payload, "synchronization_status", INTEGRATION_SYNC_STATUSES)
        _optional_text(errors, payload, "intelligence_notes")
        _optional_datetime(errors, payload, "last_synced_at")
        if errors:
            raise ExternalIntegrationValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            police_reference_number=_required_string(payload, "police_reference_number"),
            criminal_record_status=_required_string(payload, "criminal_record_status").upper(),
            fingerprint_match_status=_required_string(payload, "fingerprint_match_status").upper(),
            recidivism_status=_required_string(payload, "recidivism_status").upper(),
            wanted_person_status=_required_string(payload, "wanted_person_status").upper(),
            intelligence_notes=_optional_string(payload.get("intelligence_notes")),
            synchronization_status=_required_string(payload, "synchronization_status").upper(),
            last_synced_at=_safe_datetime(payload.get("last_synced_at")),
        )


@dataclass(frozen=True)
class BiometricIntegrationDTO:
    biometric_type: str
    biometric_reference_id: str
    enrollment_status: str
    verification_status: str
    captured_device: str
    captured_at: datetime
    inmate_id: int | None = None
    visitor_id: int | None = None
    staff_id: int | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "BiometricIntegrationDTO":
        errors: dict[str, str] = {}
        subject_fields = ("inmate_id", "visitor_id", "staff_id")
        present_subjects = [field for field in subject_fields if payload.get(field) not in {None, ""}]
        if len(present_subjects) != 1:
            errors["subject"] = "Exactly one of inmate_id, visitor_id, or staff_id is required"
        for field in present_subjects:
            _require_int(errors, payload, field)
        _require_upper_enum(errors, payload, "biometric_type", BIOMETRIC_TYPES)
        _require_text(errors, payload, "biometric_reference_id", max_length=100)
        _require_upper_enum(errors, payload, "enrollment_status", BIOMETRIC_ENROLLMENT_STATUSES)
        _require_upper_enum(errors, payload, "verification_status", BIOMETRIC_VERIFICATION_STATUSES)
        _require_text(errors, payload, "captured_device", max_length=80)
        _require_datetime(errors, payload, "captured_at")
        if errors:
            raise ExternalIntegrationValidationError(errors)
        return cls(
            inmate_id=_optional_int(payload.get("inmate_id")),
            visitor_id=_optional_int(payload.get("visitor_id")),
            staff_id=_optional_int(payload.get("staff_id")),
            biometric_type=_required_string(payload, "biometric_type").upper(),
            biometric_reference_id=_required_string(payload, "biometric_reference_id"),
            enrollment_status=_required_string(payload, "enrollment_status").upper(),
            verification_status=_required_string(payload, "verification_status").upper(),
            captured_device=_required_string(payload, "captured_device"),
            captured_at=_required_datetime(payload, "captured_at"),
        )


@dataclass(frozen=True)
class APIIntegrationDTO:
    integration_name: str
    api_provider: str
    authentication_type: str
    endpoint_reference: str
    api_status: str
    rate_limit_status: str
    encryption_enabled: bool
    last_health_check: datetime | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "APIIntegrationDTO":
        errors: dict[str, str] = {}
        _require_text(errors, payload, "integration_name", max_length=100)
        _require_text(errors, payload, "api_provider", max_length=100)
        _require_upper_enum(errors, payload, "authentication_type", AUTHENTICATION_TYPES)
        _require_text(errors, payload, "endpoint_reference", max_length=255)
        _require_upper_enum(errors, payload, "api_status", API_STATUSES)
        _require_upper_enum(errors, payload, "rate_limit_status", RATE_LIMIT_STATUSES)
        _require_bool(errors, payload, "encryption_enabled")
        _optional_datetime(errors, payload, "last_health_check")
        if errors:
            raise ExternalIntegrationValidationError(errors)
        return cls(
            integration_name=_required_string(payload, "integration_name"),
            api_provider=_required_string(payload, "api_provider"),
            authentication_type=_required_string(payload, "authentication_type").upper(),
            endpoint_reference=_required_string(payload, "endpoint_reference"),
            api_status=_required_string(payload, "api_status").upper(),
            rate_limit_status=_required_string(payload, "rate_limit_status").upper(),
            encryption_enabled=_required_bool(payload, "encryption_enabled"),
            last_health_check=_safe_datetime(payload.get("last_health_check")),
        )


@dataclass(frozen=True)
class SynchronizationLogDTO:
    source_facility: str
    target_server: str
    synchronization_type: str
    synchronization_status: str
    records_processed: int
    records_failed: int
    retry_count: int
    last_attempt_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SynchronizationLogDTO":
        errors: dict[str, str] = {}
        _require_text(errors, payload, "source_facility", max_length=100)
        _require_text(errors, payload, "target_server", max_length=150)
        _require_upper_enum(errors, payload, "synchronization_type", SYNCHRONIZATION_TYPES)
        _require_upper_enum(errors, payload, "synchronization_status", INTEGRATION_SYNC_STATUSES)
        for field in ("records_processed", "records_failed", "retry_count"):
            _require_non_negative_int(errors, payload, field)
        _require_datetime(errors, payload, "last_attempt_at")
        _optional_datetime(errors, payload, "completed_at")
        _optional_text(errors, payload, "error_message")
        started = _safe_datetime(payload.get("last_attempt_at"))
        completed = _safe_datetime(payload.get("completed_at"))
        if started and completed and completed < started:
            errors["completed_at"] = "Completed time cannot be earlier than last attempt time"
        if errors:
            raise ExternalIntegrationValidationError(errors)
        return cls(
            source_facility=_required_string(payload, "source_facility"),
            target_server=_required_string(payload, "target_server"),
            synchronization_type=_required_string(payload, "synchronization_type").upper(),
            synchronization_status=_required_string(payload, "synchronization_status").upper(),
            records_processed=int(payload["records_processed"]),
            records_failed=int(payload["records_failed"]),
            retry_count=int(payload["retry_count"]),
            last_attempt_at=_required_datetime(payload, "last_attempt_at"),
            completed_at=_safe_datetime(payload.get("completed_at")),
            error_message=_optional_string(payload.get("error_message")),
        )


@dataclass(frozen=True)
class CloudBackupLogDTO:
    backup_reference: str
    backup_type: str
    backup_status: str
    storage_location: str
    records_backed_up: int
    backup_started_at: datetime
    recovery_test_status: str
    backup_completed_at: datetime | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CloudBackupLogDTO":
        errors: dict[str, str] = {}
        _require_text(errors, payload, "backup_reference", max_length=100)
        _require_upper_enum(errors, payload, "backup_type", BACKUP_TYPES)
        _require_upper_enum(errors, payload, "backup_status", BACKUP_STATUSES)
        _require_text(errors, payload, "storage_location", max_length=150)
        _require_non_negative_int(errors, payload, "records_backed_up")
        _require_datetime(errors, payload, "backup_started_at")
        _optional_datetime(errors, payload, "backup_completed_at")
        _require_upper_enum(errors, payload, "recovery_test_status", RECOVERY_TEST_STATUSES)
        started = _safe_datetime(payload.get("backup_started_at"))
        completed = _safe_datetime(payload.get("backup_completed_at"))
        if started and completed and completed < started:
            errors["backup_completed_at"] = "Backup completion cannot be earlier than backup start"
        if errors:
            raise ExternalIntegrationValidationError(errors)
        return cls(
            backup_reference=_required_string(payload, "backup_reference"),
            backup_type=_required_string(payload, "backup_type").upper(),
            backup_status=_required_string(payload, "backup_status").upper(),
            storage_location=_required_string(payload, "storage_location"),
            records_backed_up=int(payload["records_backed_up"]),
            backup_started_at=_required_datetime(payload, "backup_started_at"),
            backup_completed_at=_safe_datetime(payload.get("backup_completed_at")),
            recovery_test_status=_required_string(payload, "recovery_test_status").upper(),
        )


def _require_text(errors: dict[str, str], payload: dict[str, Any], field: str, *, max_length: int | None = None) -> None:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        errors[field] = "This field is required"
    elif max_length is not None and len(value.strip()) > max_length:
        errors[field] = f"Must be at most {max_length} characters"


def _optional_text(errors: dict[str, str], payload: dict[str, Any], field: str, *, max_length: int | None = None) -> None:
    value = payload.get(field)
    if value in {None, ""}:
        return
    if not isinstance(value, str):
        errors[field] = "Must be text"
    elif max_length is not None and len(value.strip()) > max_length:
        errors[field] = f"Must be at most {max_length} characters"


def _require_int(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    try:
        value = int(payload.get(field))
    except (TypeError, ValueError):
        errors[field] = "Must be an integer"
        return
    if value < 1:
        errors[field] = "Must be greater than zero"


def _require_non_negative_int(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    try:
        value = int(payload.get(field))
    except (TypeError, ValueError):
        errors[field] = "Must be an integer"
        return
    if value < 0:
        errors[field] = "Must be zero or greater"


def _optional_int(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    return int(value)


def _require_bool(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if _safe_bool(payload.get(field)) is None:
        errors[field] = "Must be true or false"


def _required_bool(payload: dict[str, Any], field: str) -> bool:
    return bool(_safe_bool(payload.get(field)))


def _safe_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    return None


def _require_upper_enum(errors: dict[str, str], payload: dict[str, Any], field: str, allowed: set[str]) -> None:
    value = payload.get(field)
    if not isinstance(value, str) or value.strip().upper() not in allowed:
        errors[field] = f"Must be one of: {', '.join(sorted(allowed))}"


def _require_datetime(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if _safe_datetime(payload.get(field)) is None:
        errors[field] = "Must use ISO datetime format"


def _optional_datetime(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if payload.get(field) not in {None, ""} and _safe_datetime(payload.get(field)) is None:
        errors[field] = "Must use ISO datetime format"


def _required_string(payload: dict[str, Any], field: str) -> str:
    return str(payload[field]).strip()


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _required_datetime(payload: dict[str, Any], field: str) -> datetime:
    return datetime.fromisoformat(str(payload[field]).strip())


def _safe_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip())
    except ValueError:
        return None
