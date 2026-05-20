from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from src.models.rehabilitation import (
    BEHAVIOR_CATEGORIES,
    CERTIFICATION_LEVELS,
    CERTIFICATION_VALIDITY_STATUSES,
    COUNSELING_SESSION_TYPES,
    REHABILITATION_RISK_LEVELS,
    RELIGIOUS_ACTIVITY_TYPES,
    RELIGIOUS_ATTENDANCE_STATUSES,
    VOCATIONAL_COMPLETION_STATUSES,
    VOCATIONAL_PROGRAM_TYPES,
    WORK_TYPES,
)


class RehabilitationValidationError(ValueError):
    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Validation failed")
        self.errors = errors


@dataclass(frozen=True)
class VocationalEnrollmentDTO:
    inmate_id: int
    program_name: str
    skill_category: str
    training_center: str
    instructor_name: str
    enrollment_date: date
    completion_status: str
    progress_percentage: float
    assessment_score: float | None
    certification_eligible: bool
    created_by: int

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "VocationalEnrollmentDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_enum(errors, payload, "program_name", VOCATIONAL_PROGRAM_TYPES)
        for field in ("skill_category", "training_center", "instructor_name"):
            _require_text(errors, payload, field, max_length=120)
        _require_date(errors, payload, "enrollment_date")
        _require_upper_enum(errors, payload, "completion_status", VOCATIONAL_COMPLETION_STATUSES)
        _require_number(errors, payload, "progress_percentage", minimum=0, maximum=100)
        _optional_number(errors, payload, "assessment_score", minimum=0, maximum=100)
        _require_bool(errors, payload, "certification_eligible")
        if errors:
            raise RehabilitationValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            program_name=_required_string(payload, "program_name"),
            skill_category=_required_string(payload, "skill_category"),
            training_center=_required_string(payload, "training_center"),
            instructor_name=_required_string(payload, "instructor_name"),
            enrollment_date=_required_date(payload, "enrollment_date"),
            completion_status=_required_string(payload, "completion_status").upper(),
            progress_percentage=float(payload["progress_percentage"]),
            assessment_score=_optional_float(payload.get("assessment_score")),
            certification_eligible=_required_bool(payload, "certification_eligible"),
            created_by=actor_user_id,
        )


@dataclass(frozen=True)
class CounselingSessionDTO:
    inmate_id: int
    counselor_name: str
    session_type: str
    session_date: date
    session_notes: str
    behavioral_observation: str
    risk_level: str
    follow_up_required: bool
    created_by: int

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "CounselingSessionDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_text(errors, payload, "counselor_name", max_length=120)
        _require_enum(errors, payload, "session_type", COUNSELING_SESSION_TYPES)
        _require_date(errors, payload, "session_date")
        _require_text(errors, payload, "session_notes")
        _require_text(errors, payload, "behavioral_observation")
        _require_upper_enum(errors, payload, "risk_level", REHABILITATION_RISK_LEVELS)
        _require_bool(errors, payload, "follow_up_required")
        if errors:
            raise RehabilitationValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            counselor_name=_required_string(payload, "counselor_name"),
            session_type=_required_string(payload, "session_type"),
            session_date=_required_date(payload, "session_date"),
            session_notes=_required_string(payload, "session_notes"),
            behavioral_observation=_required_string(payload, "behavioral_observation"),
            risk_level=_required_string(payload, "risk_level").upper(),
            follow_up_required=_required_bool(payload, "follow_up_required"),
            created_by=actor_user_id,
        )


@dataclass(frozen=True)
class BehavioralAssessmentDTO:
    inmate_id: int
    behavior_score: float
    behavior_category: str
    observation_notes: str
    incident_count: int
    improvement_level: str
    assessed_by: int
    assessment_date: date

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "BehavioralAssessmentDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_number(errors, payload, "behavior_score", minimum=0, maximum=100)
        _require_enum(errors, payload, "behavior_category", BEHAVIOR_CATEGORIES)
        _require_text(errors, payload, "observation_notes")
        _require_int(errors, payload, "incident_count", minimum=0)
        _require_text(errors, payload, "improvement_level", max_length=50)
        _require_date(errors, payload, "assessment_date")
        if errors:
            raise RehabilitationValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            behavior_score=float(payload["behavior_score"]),
            behavior_category=_required_string(payload, "behavior_category"),
            observation_notes=_required_string(payload, "observation_notes"),
            incident_count=int(payload["incident_count"]),
            improvement_level=_required_string(payload, "improvement_level"),
            assessed_by=actor_user_id,
            assessment_date=_required_date(payload, "assessment_date"),
        )


@dataclass(frozen=True)
class ReligiousParticipationDTO:
    inmate_id: int
    religion: str
    activity_type: str
    participation_date: date
    attendance_status: str
    religious_leader: str
    notes: str | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ReligiousParticipationDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_text(errors, payload, "religion", max_length=80)
        _require_enum(errors, payload, "activity_type", RELIGIOUS_ACTIVITY_TYPES)
        _require_date(errors, payload, "participation_date")
        _require_upper_enum(errors, payload, "attendance_status", RELIGIOUS_ATTENDANCE_STATUSES)
        _require_text(errors, payload, "religious_leader", max_length=120)
        _optional_text(errors, payload, "notes")
        if errors:
            raise RehabilitationValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            religion=_required_string(payload, "religion"),
            activity_type=_required_string(payload, "activity_type"),
            participation_date=_required_date(payload, "participation_date"),
            attendance_status=_required_string(payload, "attendance_status").upper(),
            religious_leader=_required_string(payload, "religious_leader"),
            notes=_optional_string(payload.get("notes")),
        )


@dataclass(frozen=True)
class WorkAssignmentDTO:
    inmate_id: int
    work_type: str
    assignment_location: str
    supervisor_name: str
    start_date: date
    end_date: date | None
    performance_rating: float | None
    attendance_record: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "WorkAssignmentDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_enum(errors, payload, "work_type", WORK_TYPES)
        _require_text(errors, payload, "assignment_location", max_length=120)
        _require_text(errors, payload, "supervisor_name", max_length=120)
        _require_date(errors, payload, "start_date")
        _optional_date(errors, payload, "end_date")
        _optional_number(errors, payload, "performance_rating", minimum=0, maximum=100)
        _require_text(errors, payload, "attendance_record")
        start_date = _safe_date(payload.get("start_date"))
        end_date = _safe_date(payload.get("end_date"))
        if start_date and end_date and end_date < start_date:
            errors["end_date"] = "End date cannot be earlier than start date"
        if errors:
            raise RehabilitationValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            work_type=_required_string(payload, "work_type"),
            assignment_location=_required_string(payload, "assignment_location"),
            supervisor_name=_required_string(payload, "supervisor_name"),
            start_date=_required_date(payload, "start_date"),
            end_date=_optional_date_value(payload.get("end_date")),
            performance_rating=_optional_float(payload.get("performance_rating")),
            attendance_record=_required_string(payload, "attendance_record"),
        )


@dataclass(frozen=True)
class SkillCertificationDTO:
    inmate_id: int
    certification_name: str
    skill_area: str
    issuing_authority: str
    issue_date: date
    certificate_number: str
    grade: str
    validity_status: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SkillCertificationDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        for field in ("certification_name", "skill_area", "issuing_authority"):
            _require_text(errors, payload, field, max_length=120)
        _require_date(errors, payload, "issue_date")
        _require_text(errors, payload, "certificate_number", max_length=80)
        _require_enum(errors, payload, "grade", CERTIFICATION_LEVELS)
        _require_upper_enum(errors, payload, "validity_status", CERTIFICATION_VALIDITY_STATUSES)
        if errors:
            raise RehabilitationValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            certification_name=_required_string(payload, "certification_name"),
            skill_area=_required_string(payload, "skill_area"),
            issuing_authority=_required_string(payload, "issuing_authority"),
            issue_date=_required_date(payload, "issue_date"),
            certificate_number=_required_string(payload, "certificate_number"),
            grade=_required_string(payload, "grade"),
            validity_status=_required_string(payload, "validity_status").upper(),
        )


@dataclass(frozen=True)
class PostReleaseFollowUpDTO:
    inmate_id: int
    release_date: date
    follow_up_date: date
    employment_status: str
    housing_status: str
    reintegration_score: float
    recidivism_risk_level: str
    notes: str | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PostReleaseFollowUpDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_date(errors, payload, "release_date")
        _require_date(errors, payload, "follow_up_date")
        _require_text(errors, payload, "employment_status", max_length=80)
        _require_text(errors, payload, "housing_status", max_length=80)
        _require_number(errors, payload, "reintegration_score", minimum=0, maximum=100)
        _require_upper_enum(errors, payload, "recidivism_risk_level", REHABILITATION_RISK_LEVELS)
        _optional_text(errors, payload, "notes")
        release_date = _safe_date(payload.get("release_date"))
        follow_up_date = _safe_date(payload.get("follow_up_date"))
        if release_date and follow_up_date and follow_up_date < release_date:
            errors["follow_up_date"] = "Follow-up date cannot be earlier than release date"
        if errors:
            raise RehabilitationValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            release_date=_required_date(payload, "release_date"),
            follow_up_date=_required_date(payload, "follow_up_date"),
            employment_status=_required_string(payload, "employment_status"),
            housing_status=_required_string(payload, "housing_status"),
            reintegration_score=float(payload["reintegration_score"]),
            recidivism_risk_level=_required_string(payload, "recidivism_risk_level").upper(),
            notes=_optional_string(payload.get("notes")),
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


def _require_int(errors: dict[str, str], payload: dict[str, Any], field: str, *, minimum: int = 1) -> None:
    try:
        value = int(payload.get(field))
    except (TypeError, ValueError):
        errors[field] = "Must be an integer"
        return
    if value < minimum:
        errors[field] = f"Must be at least {minimum}"


def _require_number(errors: dict[str, str], payload: dict[str, Any], field: str, *, minimum: float, maximum: float) -> None:
    try:
        value = float(payload.get(field))
    except (TypeError, ValueError):
        errors[field] = "Must be a number"
        return
    if value < minimum or value > maximum:
        errors[field] = f"Must be between {minimum:g} and {maximum:g}"


def _optional_number(errors: dict[str, str], payload: dict[str, Any], field: str, *, minimum: float, maximum: float) -> None:
    if payload.get(field) in {None, ""}:
        return
    _require_number(errors, payload, field, minimum=minimum, maximum=maximum)


def _require_bool(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if _safe_bool(payload.get(field)) is None:
        errors[field] = "Must be true or false"


def _require_enum(errors: dict[str, str], payload: dict[str, Any], field: str, allowed: set[str]) -> None:
    value = payload.get(field)
    if not isinstance(value, str) or value.strip() not in allowed:
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


def _required_string(payload: dict[str, Any], field: str) -> str:
    return str(payload[field]).strip()


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _required_date(payload: dict[str, Any], field: str) -> date:
    return date.fromisoformat(str(payload[field]).strip())


def _optional_date_value(value: Any) -> date | None:
    if value in {None, ""}:
        return None
    return date.fromisoformat(str(value).strip())


def _safe_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _required_bool(payload: dict[str, Any], field: str) -> bool:
    value = _safe_bool(payload.get(field))
    return bool(value)


def _safe_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    return None


def _optional_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)
