from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from typing import Any, TypeAlias


VISITOR_RELATIONSHIPS = {"parent", "spouse", "sibling", "child", "lawyer", "religious_representative", "friend", "guardian", "other"}
VISITOR_APPROVAL_STATUSES = {"PENDING", "APPROVED", "REJECTED", "RESCHEDULED", "UNDER_REVIEW"}
VISITOR_VERIFICATION_STATUSES = {"VERIFIED", "PENDING", "FAILED"}
VISITOR_SECURITY_SCREENING_STATUSES = {"CLEARED", "FLAGGED", "DENIED"}
VISITOR_SCHEDULING_STATUSES = {"SCHEDULED", "COMPLETED", "CANCELLED", "EXPIRED"}
VISITOR_MONITORING_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VISITOR_VIOLATION_SEVERITIES = {"MINOR", "MODERATE", "MAJOR", "CRITICAL"}
VISIT_TYPES = {"FAMILY", "LEGAL", "RELIGIOUS", "MEDICAL", "OFFICIAL"}


class VisitorEntityMixin:
    @property
    def data(self) -> dict[str, Any]:
        return asdict(self)

    def to_dict(self) -> dict[str, Any]:
        return {key: _serialize(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class Visitor(VisitorEntityMixin):
    id: int | None
    visitor_id: str
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    nationality: str
    national_id: str
    phone: str
    address: str
    relationship_to_inmate: str
    blacklist_status: bool
    verification_status: str
    created_by: int
    other_names: str | None = None
    email: str | None = None
    occupation: str | None = None
    photo: str | None = None
    biometric_id: str | None = None
    blacklist_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Visitor":
        return cls(
            id=row.get("id"),
            visitor_id=row["visitor_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            other_names=row.get("other_names"),
            gender=row["gender"],
            date_of_birth=row["date_of_birth"],
            nationality=row["nationality"],
            national_id=row["national_id"],
            phone=row["phone"],
            email=row.get("email"),
            address=row["address"],
            relationship_to_inmate=row["relationship_to_inmate"],
            occupation=row.get("occupation"),
            photo=row.get("photo"),
            biometric_id=row.get("biometric_id"),
            blacklist_status=bool(row["blacklist_status"]),
            blacklist_reason=row.get("blacklist_reason"),
            verification_status=row["verification_status"],
            created_by=row["created_by"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


@dataclass(frozen=True)
class VisitorRequest(VisitorEntityMixin):
    id: int | None
    visitor_id: int
    inmate_id: int
    requested_visit_date: date
    requested_time_slot: str
    purpose_of_visit: str
    visit_type: str
    approval_status: str
    reviewed_by: int | None = None
    review_notes: str | None = None
    approved_date: date | None = None
    rescheduled_date: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "VisitorRequest":
        return cls(**dict(row))


@dataclass(frozen=True)
class VisitorVerification(VisitorEntityMixin):
    id: int | None
    visitor_id: int
    national_id_verified: bool
    biometric_verified: bool
    blacklist_checked: bool
    security_screening_status: str
    verified_by: int
    verification_date: date
    verification_notes: str | None = None
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "VisitorVerification":
        data = dict(row)
        data["national_id_verified"] = bool(data["national_id_verified"])
        data["biometric_verified"] = bool(data["biometric_verified"])
        data["blacklist_checked"] = bool(data["blacklist_checked"])
        return cls(**data)


@dataclass(frozen=True)
class VisitorSchedule(VisitorEntityMixin):
    id: int | None
    visitor_request_id: int
    visit_date: date
    start_time: time
    end_time: time
    visit_duration_minutes: int
    visit_room: str
    daily_capacity_slot: int
    scheduling_status: str
    scheduled_by: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "VisitorSchedule":
        return cls(**dict(row))


@dataclass(frozen=True)
class VisitorCheckin(VisitorEntityMixin):
    id: int | None
    visitor_schedule_id: int
    inmate_id: int
    arrival_time: datetime
    security_clearance_status: str
    belongings_checked: bool
    handled_by: int
    exit_time: datetime | None = None
    checkin_notes: str | None = None
    checkout_notes: str | None = None
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "VisitorCheckin":
        data = dict(row)
        data["belongings_checked"] = bool(data["belongings_checked"])
        return cls(**data)


@dataclass(frozen=True)
class VisitorMonitoringLog(VisitorEntityMixin):
    id: int | None
    visitor_id: int
    inmate_id: int
    suspicious_activity: str
    monitoring_level: str
    officer_notes: str
    action_taken: str
    monitored_by: int
    monitoring_date: date
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "VisitorMonitoringLog":
        return cls(**dict(row))


@dataclass(frozen=True)
class VisitorViolation(VisitorEntityMixin):
    id: int | None
    visitor_id: int
    violation_type: str
    violation_description: str
    action_taken: str
    violation_severity: str
    reported_by: int
    violation_date: date
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "VisitorViolation":
        return cls(**dict(row))


VisitorRecord: TypeAlias = Visitor | VisitorRequest | VisitorVerification | VisitorSchedule | VisitorCheckin | VisitorMonitoringLog | VisitorViolation

VISITOR_TABLE_MODELS = {
    "visitors": Visitor,
    "visitor_requests": VisitorRequest,
    "visitor_verifications": VisitorVerification,
    "visitor_schedules": VisitorSchedule,
    "visitor_checkins": VisitorCheckin,
    "visitor_monitoring_logs": VisitorMonitoringLog,
    "visitor_violations": VisitorViolation,
}


def visitor_record_from_row(table: str, row: dict[str, Any]) -> VisitorRecord:
    model = VISITOR_TABLE_MODELS.get(table)
    if model is None:
        raise ValueError("Unsupported visitor table")
    return model.from_row(row)


def _serialize(value: Any) -> Any:
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    return value
