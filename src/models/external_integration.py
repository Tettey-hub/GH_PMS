from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, TypeAlias

from src.integrations.security import redact_record


WARRANT_STATUSES = {"PENDING", "VERIFIED", "INVALID", "EXPIRED", "REVOKED"}
HEARING_STATUSES = {"PENDING", "SCHEDULED", "COMPLETED", "ADJOURNED", "CANCELLED"}
SENTENCE_STATUSES = {"PENDING", "CONFIRMED", "MODIFIED", "BAIL_APPROVED", "ACQUITTED", "RELEASE_AUTHORIZED"}
INTEGRATION_SYNC_STATUSES = {"PENDING", "IN_PROGRESS", "SYNCED", "FAILED", "RETRY_SCHEDULED"}

NIA_VERIFICATION_STATUSES = {"PENDING", "VERIFIED", "FAILED", "RETRY_SCHEDULED"}
BIOMETRIC_MATCH_STATUSES = {"PENDING", "MATCHED", "NOT_MATCHED", "NOT_AVAILABLE"}
DEMOGRAPHIC_SYNC_STATUSES = {"PENDING", "SYNCED", "FAILED", "NOT_REQUESTED"}

CRIMINAL_RECORD_STATUSES = {"PENDING", "FOUND", "NOT_FOUND", "FAILED"}
RECIDIVISM_STATUSES = {"PENDING", "REPEAT_OFFENDER", "NO_MATCH", "UNKNOWN"}
WANTED_PERSON_STATUSES = {"PENDING", "MATCHED", "CLEAR", "UNKNOWN"}

BIOMETRIC_TYPES = {"FINGERPRINT", "FACIAL", "WEBCAM", "TERMINAL"}
BIOMETRIC_ENROLLMENT_STATUSES = {"PENDING", "ENROLLED", "FAILED", "REVOKED"}
BIOMETRIC_VERIFICATION_STATUSES = {"PENDING", "VERIFIED", "FAILED", "NOT_REQUESTED"}

AUTHENTICATION_TYPES = {"OAUTH2", "JWT", "API_KEY", "MFA"}
API_STATUSES = {"ACTIVE", "INACTIVE", "DEGRADED", "FAILED"}
RATE_LIMIT_STATUSES = {"NORMAL", "THROTTLED", "EXCEEDED", "DISABLED"}

SYNCHRONIZATION_TYPES = {"REAL_TIME", "BATCH", "OFFLINE"}
BACKUP_TYPES = {"FULL", "INCREMENTAL", "EMERGENCY_RECOVERY", "RECOVERY_TEST"}
BACKUP_STATUSES = {"PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "RESTORED"}
RECOVERY_TEST_STATUSES = {"PENDING", "PASSED", "FAILED", "NOT_TESTED"}


class ExternalIntegrationEntityMixin:
    @property
    def data(self) -> dict[str, Any]:
        return asdict(self)

    def to_dict(self) -> dict[str, Any]:
        return redact_record({key: _serialize(value) for key, value in asdict(self).items()})


@dataclass(frozen=True)
class CourtIntegration(ExternalIntegrationEntityMixin):
    id: int | None
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
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "CourtIntegration":
        return cls(**dict(row))


@dataclass(frozen=True)
class NIAIntegration(ExternalIntegrationEntityMixin):
    id: int | None
    inmate_id: int
    national_id: str
    verification_status: str
    biometric_match_status: str
    demographic_sync_status: str
    nia_reference_number: str | None = None
    last_verified_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "NIAIntegration":
        return cls(**dict(row))


@dataclass(frozen=True)
class PoliceIntegration(ExternalIntegrationEntityMixin):
    id: int | None
    inmate_id: int
    police_reference_number: str
    criminal_record_status: str
    fingerprint_match_status: str
    recidivism_status: str
    wanted_person_status: str
    synchronization_status: str
    intelligence_notes: str | None = None
    last_synced_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "PoliceIntegration":
        return cls(**dict(row))


@dataclass(frozen=True)
class BiometricIntegration(ExternalIntegrationEntityMixin):
    id: int | None
    biometric_type: str
    biometric_reference_id: str
    enrollment_status: str
    verification_status: str
    captured_device: str
    captured_at: datetime
    inmate_id: int | None = None
    visitor_id: int | None = None
    staff_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "BiometricIntegration":
        return cls(**dict(row))


@dataclass(frozen=True)
class APIIntegration(ExternalIntegrationEntityMixin):
    id: int | None
    integration_name: str
    api_provider: str
    authentication_type: str
    endpoint_reference: str
    api_status: str
    rate_limit_status: str
    encryption_enabled: bool
    last_health_check: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "APIIntegration":
        data = dict(row)
        data["encryption_enabled"] = bool(data["encryption_enabled"])
        return cls(**data)


@dataclass(frozen=True)
class SynchronizationLog(ExternalIntegrationEntityMixin):
    id: int | None
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
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SynchronizationLog":
        return cls(**dict(row))


@dataclass(frozen=True)
class CloudBackupLog(ExternalIntegrationEntityMixin):
    id: int | None
    backup_reference: str
    backup_type: str
    backup_status: str
    storage_location: str
    records_backed_up: int
    backup_started_at: datetime
    recovery_test_status: str
    backup_completed_at: datetime | None = None
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "CloudBackupLog":
        return cls(**dict(row))


ExternalIntegrationRecord: TypeAlias = (
    CourtIntegration
    | NIAIntegration
    | PoliceIntegration
    | BiometricIntegration
    | APIIntegration
    | SynchronizationLog
    | CloudBackupLog
)

EXTERNAL_INTEGRATION_TABLE_MODELS = {
    "court_integrations": CourtIntegration,
    "nia_integrations": NIAIntegration,
    "police_integrations": PoliceIntegration,
    "biometric_integrations": BiometricIntegration,
    "api_integrations": APIIntegration,
    "synchronization_logs": SynchronizationLog,
    "cloud_backup_logs": CloudBackupLog,
}


def external_integration_record_from_row(table: str, row: dict[str, Any]) -> ExternalIntegrationRecord:
    model = EXTERNAL_INTEGRATION_TABLE_MODELS.get(table)
    if model is None:
        raise ValueError("Unsupported external integration table")
    return model.from_row(row)


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value
