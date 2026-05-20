from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any

from src.models.visitor import (
    VISIT_TYPES,
    VISITOR_MONITORING_LEVELS,
    VISITOR_RELATIONSHIPS,
    VISITOR_SCHEDULING_STATUSES,
    VISITOR_SECURITY_SCREENING_STATUSES,
    VISITOR_VIOLATION_SEVERITIES,
)


class VisitorValidationError(ValueError):
    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Validation failed")
        self.errors = errors


@dataclass(frozen=True)
class VisitorRegistrationDTO:
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
    created_by: int
    other_names: str | None = None
    email: str | None = None
    occupation: str | None = None
    photo: str | None = None
    biometric_id: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "VisitorRegistrationDTO":
        errors: dict[str, str] = {}
        for field, max_length in {
            "visitor_id": 30,
            "first_name": 50,
            "last_name": 50,
            "gender": 10,
            "nationality": 50,
            "national_id": 50,
            "phone": 20,
        }.items():
            _require_text(errors, payload, field, max_length=max_length)
        _require_text(errors, payload, "address")
        _require_date(errors, payload, "date_of_birth")
        _require_enum(errors, payload, "relationship_to_inmate", VISITOR_RELATIONSHIPS)
        _optional_text(errors, payload, "other_names", max_length=100)
        _optional_text(errors, payload, "email", max_length=120)
        _optional_text(errors, payload, "occupation", max_length=100)
        _optional_text(errors, payload, "photo", max_length=255)
        _optional_text(errors, payload, "biometric_id", max_length=100)
        if errors:
            raise VisitorValidationError(errors)
        return cls(
            visitor_id=_required_string(payload, "visitor_id"),
            first_name=_required_string(payload, "first_name"),
            last_name=_required_string(payload, "last_name"),
            other_names=_optional_string(payload.get("other_names")),
            gender=_required_string(payload, "gender").lower(),
            date_of_birth=_required_date(payload, "date_of_birth"),
            nationality=_required_string(payload, "nationality"),
            national_id=_required_string(payload, "national_id"),
            phone=_required_string(payload, "phone"),
            email=_optional_string(payload.get("email")),
            address=_required_string(payload, "address"),
            relationship_to_inmate=_required_string(payload, "relationship_to_inmate").lower(),
            occupation=_optional_string(payload.get("occupation")),
            photo=_optional_string(payload.get("photo")),
            biometric_id=_optional_string(payload.get("biometric_id")),
            created_by=actor_user_id,
        )


@dataclass(frozen=True)
class VisitorUpdateDTO:
    updates: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "VisitorUpdateDTO":
        allowed = {"first_name", "last_name", "other_names", "gender", "date_of_birth", "nationality", "phone", "email", "address", "relationship_to_inmate", "occupation", "photo", "biometric_id"}
        errors = {field: "This field cannot be updated" for field in payload if field not in allowed}
        clean = {key: value for key, value in payload.items() if key in allowed}
        for field, value in clean.items():
            if field == "date_of_birth":
                _optional_date(errors, clean, field)
            elif field == "relationship_to_inmate":
                _optional_enum(errors, clean, field, VISITOR_RELATIONSHIPS)
            elif field in {"first_name", "last_name", "gender", "nationality", "phone", "address"}:
                _require_text(errors, clean, field)
            else:
                _optional_text(errors, clean, field)
        updates = _normalize_updates(clean, lower_fields={"gender", "relationship_to_inmate"}, date_fields={"date_of_birth"})
        if not updates:
            errors["request"] = "At least one visitor field is required"
        if errors:
            raise VisitorValidationError(errors)
        return cls(updates=updates)


@dataclass(frozen=True)
class VisitorVerificationDTO:
    visitor_id: int
    national_id_verified: bool
    biometric_verified: bool
    blacklist_checked: bool
    security_screening_status: str
    verified_by: int
    verification_date: date
    verification_notes: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "VisitorVerificationDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "visitor_id")
        for field in ("national_id_verified", "biometric_verified", "blacklist_checked"):
            _require_bool(errors, payload, field)
        _require_upper_enum(errors, payload, "security_screening_status", VISITOR_SECURITY_SCREENING_STATUSES)
        _require_date(errors, payload, "verification_date")
        _optional_text(errors, payload, "verification_notes")
        if errors:
            raise VisitorValidationError(errors)
        return cls(
            visitor_id=int(payload["visitor_id"]),
            national_id_verified=_required_bool(payload, "national_id_verified"),
            biometric_verified=_required_bool(payload, "biometric_verified"),
            blacklist_checked=_required_bool(payload, "blacklist_checked"),
            security_screening_status=_required_string(payload, "security_screening_status").upper(),
            verification_notes=_optional_string(payload.get("verification_notes")),
            verified_by=actor_user_id,
            verification_date=_required_date(payload, "verification_date"),
        )


@dataclass(frozen=True)
class VisitRequestDTO:
    visitor_id: int
    inmate_id: int
    requested_visit_date: date
    requested_time_slot: str
    purpose_of_visit: str
    visit_type: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "VisitRequestDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "visitor_id")
        _require_int(errors, payload, "inmate_id")
        _require_date(errors, payload, "requested_visit_date")
        _require_text(errors, payload, "requested_time_slot", max_length=50)
        _require_text(errors, payload, "purpose_of_visit")
        _require_upper_enum(errors, payload, "visit_type", VISIT_TYPES)
        if errors:
            raise VisitorValidationError(errors)
        return cls(
            visitor_id=int(payload["visitor_id"]),
            inmate_id=int(payload["inmate_id"]),
            requested_visit_date=_required_date(payload, "requested_visit_date"),
            requested_time_slot=_required_string(payload, "requested_time_slot"),
            purpose_of_visit=_required_string(payload, "purpose_of_visit"),
            visit_type=_required_string(payload, "visit_type").upper(),
        )


@dataclass(frozen=True)
class VisitReviewDTO:
    updates: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, action: str, actor_user_id: int) -> "VisitReviewDTO":
        errors: dict[str, str] = {}
        updates: dict[str, Any] = {"reviewed_by": actor_user_id}
        if action == "review":
            updates["approval_status"] = "UNDER_REVIEW"
            updates["review_notes"] = _optional_string(payload.get("review_notes"))
        elif action == "approve":
            updates["approval_status"] = "APPROVED"
            updates["approved_date"] = _required_date(payload, "approved_date") if _date_present(payload, "approved_date") else date.today()
            updates["review_notes"] = _optional_string(payload.get("review_notes"))
        elif action == "reject":
            _require_text(errors, payload, "review_notes")
            updates["approval_status"] = "REJECTED"
            updates["review_notes"] = _optional_string(payload.get("review_notes"))
        elif action == "reschedule":
            _require_date(errors, payload, "rescheduled_date")
            updates["approval_status"] = "RESCHEDULED"
            updates["rescheduled_date"] = _required_date(payload, "rescheduled_date") if "rescheduled_date" not in errors else None
            updates["review_notes"] = _optional_string(payload.get("review_notes"))
        else:
            errors["action"] = "Unsupported visit request action"
        if errors:
            raise VisitorValidationError(errors)
        return cls(updates={key: value for key, value in updates.items() if value is not None})


@dataclass(frozen=True)
class VisitScheduleDTO:
    visitor_request_id: int
    visit_date: date
    start_time: time
    end_time: time
    visit_duration_minutes: int
    visit_room: str
    daily_capacity_slot: int
    scheduled_by: int

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "VisitScheduleDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "visitor_request_id")
        _require_date(errors, payload, "visit_date")
        _require_time(errors, payload, "start_time")
        _require_time(errors, payload, "end_time")
        _require_int(errors, payload, "visit_duration_minutes")
        _require_text(errors, payload, "visit_room", max_length=80)
        _require_int(errors, payload, "daily_capacity_slot")
        start_time = _safe_time(payload.get("start_time"))
        end_time = _safe_time(payload.get("end_time"))
        if start_time and end_time and end_time <= start_time:
            errors["end_time"] = "End time must be after start time"
        if errors:
            raise VisitorValidationError(errors)
        return cls(
            visitor_request_id=int(payload["visitor_request_id"]),
            visit_date=_required_date(payload, "visit_date"),
            start_time=_required_time(payload, "start_time"),
            end_time=_required_time(payload, "end_time"),
            visit_duration_minutes=int(payload["visit_duration_minutes"]),
            visit_room=_required_string(payload, "visit_room"),
            daily_capacity_slot=int(payload["daily_capacity_slot"]),
            scheduled_by=actor_user_id,
        )


@dataclass(frozen=True)
class VisitorCheckinDTO:
    visitor_schedule_id: int
    inmate_id: int
    arrival_time: datetime
    security_clearance_status: str
    belongings_checked: bool
    handled_by: int
    checkin_notes: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "VisitorCheckinDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "visitor_schedule_id")
        _require_int(errors, payload, "inmate_id")
        _require_datetime(errors, payload, "arrival_time")
        _require_upper_enum(errors, payload, "security_clearance_status", VISITOR_SECURITY_SCREENING_STATUSES)
        _require_bool(errors, payload, "belongings_checked")
        _optional_text(errors, payload, "checkin_notes")
        if errors:
            raise VisitorValidationError(errors)
        return cls(
            visitor_schedule_id=int(payload["visitor_schedule_id"]),
            inmate_id=int(payload["inmate_id"]),
            arrival_time=_required_datetime(payload, "arrival_time"),
            security_clearance_status=_required_string(payload, "security_clearance_status").upper(),
            belongings_checked=_required_bool(payload, "belongings_checked"),
            handled_by=actor_user_id,
            checkin_notes=_optional_string(payload.get("checkin_notes")),
        )


@dataclass(frozen=True)
class VisitorCheckoutDTO:
    exit_time: datetime
    checkout_notes: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "VisitorCheckoutDTO":
        errors: dict[str, str] = {}
        _require_datetime(errors, payload, "exit_time")
        _optional_text(errors, payload, "checkout_notes")
        if errors:
            raise VisitorValidationError(errors)
        return cls(exit_time=_required_datetime(payload, "exit_time"), checkout_notes=_optional_string(payload.get("checkout_notes")))


@dataclass(frozen=True)
class VisitorMonitoringDTO:
    visitor_id: int
    inmate_id: int
    suspicious_activity: str
    monitoring_level: str
    officer_notes: str
    action_taken: str
    monitored_by: int
    monitoring_date: date

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "VisitorMonitoringDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "visitor_id")
        _require_int(errors, payload, "inmate_id")
        for field in ("suspicious_activity", "officer_notes", "action_taken"):
            _require_text(errors, payload, field)
        _require_upper_enum(errors, payload, "monitoring_level", VISITOR_MONITORING_LEVELS)
        _require_date(errors, payload, "monitoring_date")
        if errors:
            raise VisitorValidationError(errors)
        return cls(
            visitor_id=int(payload["visitor_id"]),
            inmate_id=int(payload["inmate_id"]),
            suspicious_activity=_required_string(payload, "suspicious_activity"),
            monitoring_level=_required_string(payload, "monitoring_level").upper(),
            officer_notes=_required_string(payload, "officer_notes"),
            action_taken=_required_string(payload, "action_taken"),
            monitored_by=actor_user_id,
            monitoring_date=_required_date(payload, "monitoring_date"),
        )


@dataclass(frozen=True)
class VisitorViolationDTO:
    visitor_id: int
    violation_type: str
    violation_description: str
    action_taken: str
    violation_severity: str
    reported_by: int
    violation_date: date

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "VisitorViolationDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "visitor_id")
        _require_text(errors, payload, "violation_type", max_length=80)
        _require_text(errors, payload, "violation_description")
        _require_text(errors, payload, "action_taken")
        _require_upper_enum(errors, payload, "violation_severity", VISITOR_VIOLATION_SEVERITIES)
        _require_date(errors, payload, "violation_date")
        if errors:
            raise VisitorValidationError(errors)
        return cls(
            visitor_id=int(payload["visitor_id"]),
            violation_type=_required_string(payload, "violation_type"),
            violation_description=_required_string(payload, "violation_description"),
            action_taken=_required_string(payload, "action_taken"),
            violation_severity=_required_string(payload, "violation_severity").upper(),
            reported_by=actor_user_id,
            violation_date=_required_date(payload, "violation_date"),
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


def _require_enum(errors: dict[str, str], payload: dict[str, Any], field: str, allowed: set[str]) -> None:
    value = payload.get(field)
    if not isinstance(value, str) or value.strip().lower() not in allowed:
        errors[field] = f"Must be one of: {', '.join(sorted(allowed))}"


def _optional_enum(errors: dict[str, str], payload: dict[str, Any], field: str, allowed: set[str]) -> None:
    value = payload.get(field)
    if value in {None, ""}:
        return
    if not isinstance(value, str) or value.strip().lower() not in allowed:
        errors[field] = f"Must be one of: {', '.join(sorted(allowed))}"


def _require_upper_enum(errors: dict[str, str], payload: dict[str, Any], field: str, allowed: set[str]) -> None:
    value = payload.get(field)
    if not isinstance(value, str) or value.strip().upper() not in allowed:
        errors[field] = f"Must be one of: {', '.join(sorted(allowed))}"


def _require_date(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if _safe_date(payload.get(field)) is None:
        errors[field] = "Must use YYYY-MM-DD"


def _optional_date(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if payload.get(field) not in {None, ""} and _safe_date(payload.get(field)) is None:
        errors[field] = "Must use YYYY-MM-DD"


def _require_time(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if _safe_time(payload.get(field)) is None:
        errors[field] = "Must use HH:MM or HH:MM:SS"


def _require_datetime(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if _safe_datetime(payload.get(field)) is None:
        errors[field] = "Must use ISO datetime format"


def _required_string(payload: dict[str, Any], field: str) -> str:
    return str(payload[field]).strip()


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _required_date(payload: dict[str, Any], field: str) -> date:
    return date.fromisoformat(str(payload[field]).strip())


def _required_time(payload: dict[str, Any], field: str) -> time:
    return time.fromisoformat(str(payload[field]).strip())


def _required_datetime(payload: dict[str, Any], field: str) -> datetime:
    return datetime.fromisoformat(str(payload[field]).strip())


def _safe_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _safe_time(value: Any) -> time | None:
    if isinstance(value, time):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return time.fromisoformat(value.strip())
    except ValueError:
        return None


def _safe_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip())
    except ValueError:
        return None


def _date_present(payload: dict[str, Any], field: str) -> bool:
    return payload.get(field) not in {None, ""}


def _normalize_updates(payload: dict[str, Any], *, lower_fields: set[str], date_fields: set[str]) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    for field, value in payload.items():
        if value in {None, ""}:
            updates[field] = None
        elif field in date_fields:
            updates[field] = _required_date(payload, field)
        elif isinstance(value, str):
            value = value.strip()
            updates[field] = value.lower() if field in lower_fields else value
        else:
            updates[field] = value
    return updates
