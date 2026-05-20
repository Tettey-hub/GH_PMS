from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any, TypeAlias


VOCATIONAL_PROGRAM_TYPES = {"Carpentry", "Welding", "Tailoring", "Agriculture", "ICT Training", "Plumbing", "Electrical Installation", "Art & Craft"}
VOCATIONAL_COMPLETION_STATUSES = {"ENROLLED", "IN_PROGRESS", "COMPLETED", "WITHDRAWN"}
COUNSELING_SESSION_TYPES = {"Individual Counseling", "Group Therapy", "Trauma Counseling", "Addiction Recovery", "Anger Management"}
REHABILITATION_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
BEHAVIOR_CATEGORIES = {"Excellent", "Good", "Fair", "Poor", "Violent"}
RELIGIOUS_ACTIVITY_TYPES = {"Church Service", "Islamic Prayer Session", "Bible Study", "Quran Study", "Spiritual Counseling"}
RELIGIOUS_ATTENDANCE_STATUSES = {"REGISTERED", "ATTENDED", "MISSED"}
WORK_TYPES = {"Kitchen Duties", "Farming", "Cleaning Services", "Maintenance Work", "Construction Assistance"}
CERTIFICATION_LEVELS = {"Basic", "Intermediate", "Advanced", "Professional"}
CERTIFICATION_VALIDITY_STATUSES = {"VALID", "EXPIRED", "REVOKED"}


class RehabilitationEntityMixin:
    @property
    def data(self) -> dict[str, Any]:
        return asdict(self)

    def to_dict(self) -> dict[str, Any]:
        return {key: _serialize(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class VocationalTrainingEnrollment(RehabilitationEntityMixin):
    id: int | None
    inmate_id: int
    program_name: str
    skill_category: str
    training_center: str
    instructor_name: str
    enrollment_date: date
    completion_status: str
    progress_percentage: float
    certification_eligible: bool
    created_by: int
    assessment_score: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "VocationalTrainingEnrollment":
        data = dict(row)
        data["progress_percentage"] = float(data["progress_percentage"])
        data["assessment_score"] = float(data["assessment_score"]) if data.get("assessment_score") is not None else None
        data["certification_eligible"] = bool(data["certification_eligible"])
        return cls(**data)


@dataclass(frozen=True)
class CounselingSession(RehabilitationEntityMixin):
    id: int | None
    inmate_id: int
    counselor_name: str
    session_type: str
    session_date: date
    session_notes: str
    behavioral_observation: str
    risk_level: str
    follow_up_required: bool
    created_by: int
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "CounselingSession":
        data = dict(row)
        data["follow_up_required"] = bool(data["follow_up_required"])
        return cls(**data)


@dataclass(frozen=True)
class BehavioralAssessment(RehabilitationEntityMixin):
    id: int | None
    inmate_id: int
    behavior_score: float
    behavior_category: str
    observation_notes: str
    incident_count: int
    improvement_level: str
    assessed_by: int
    assessment_date: date
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "BehavioralAssessment":
        data = dict(row)
        data["behavior_score"] = float(data["behavior_score"])
        return cls(**data)


@dataclass(frozen=True)
class ReligiousParticipation(RehabilitationEntityMixin):
    id: int | None
    inmate_id: int
    religion: str
    activity_type: str
    participation_date: date
    attendance_status: str
    religious_leader: str
    notes: str | None = None
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ReligiousParticipation":
        return cls(**dict(row))


@dataclass(frozen=True)
class WorkAssignment(RehabilitationEntityMixin):
    id: int | None
    inmate_id: int
    work_type: str
    assignment_location: str
    supervisor_name: str
    start_date: date
    attendance_record: str
    end_date: date | None = None
    performance_rating: float | None = None
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "WorkAssignment":
        data = dict(row)
        data["performance_rating"] = float(data["performance_rating"]) if data.get("performance_rating") is not None else None
        return cls(**data)


@dataclass(frozen=True)
class SkillCertification(RehabilitationEntityMixin):
    id: int | None
    inmate_id: int
    certification_name: str
    skill_area: str
    issuing_authority: str
    issue_date: date
    certificate_number: str
    grade: str
    validity_status: str
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SkillCertification":
        return cls(**dict(row))


@dataclass(frozen=True)
class PostReleaseFollowUp(RehabilitationEntityMixin):
    id: int | None
    inmate_id: int
    release_date: date
    follow_up_date: date
    employment_status: str
    housing_status: str
    reintegration_score: float
    recidivism_risk_level: str
    notes: str | None = None
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "PostReleaseFollowUp":
        data = dict(row)
        data["reintegration_score"] = float(data["reintegration_score"])
        return cls(**data)


RehabilitationRecord: TypeAlias = VocationalTrainingEnrollment | CounselingSession | BehavioralAssessment | ReligiousParticipation | WorkAssignment | SkillCertification | PostReleaseFollowUp

REHABILITATION_TABLE_MODELS = {
    "vocational_training_enrollments": VocationalTrainingEnrollment,
    "counseling_sessions": CounselingSession,
    "behavioral_assessments": BehavioralAssessment,
    "religious_participations": ReligiousParticipation,
    "work_assignments": WorkAssignment,
    "skill_certifications": SkillCertification,
    "post_release_followups": PostReleaseFollowUp,
}


def rehabilitation_record_from_row(table: str, row: dict[str, Any]) -> RehabilitationRecord:
    model = REHABILITATION_TABLE_MODELS.get(table)
    if model is None:
        raise ValueError("Unsupported rehabilitation table")
    return model.from_row(row)


def _serialize(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value
