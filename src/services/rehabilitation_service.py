from __future__ import annotations

from dataclasses import asdict
from typing import Any

from mysql.connector import Error as MySQLError, IntegrityError

from src.config.database_config import db_connection
from src.dtos.rehabilitation_dto import (
    BehavioralAssessmentDTO,
    CounselingSessionDTO,
    PostReleaseFollowUpDTO,
    ReligiousParticipationDTO,
    SkillCertificationDTO,
    VocationalEnrollmentDTO,
    WorkAssignmentDTO,
)
from src.models.rehabilitation import RehabilitationRecord
from src.repositories.rehabilitation_repository import RehabilitationRepository


class RehabilitationNotFoundError(LookupError):
    pass


class RehabilitationConflictError(ValueError):
    pass


class RehabilitationForeignKeyError(ValueError):
    pass


class RehabilitationWorkflowError(ValueError):
    pass


class RehabilitationService:
    @staticmethod
    def enroll_vocational_program(data: VocationalEnrollmentDTO) -> RehabilitationRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.created_by, "Creator does not exist")
                if data.completion_status in {"ENROLLED", "IN_PROGRESS"} and RehabilitationRepository.active_vocational_enrollment_exists(connection, inmate_id=data.inmate_id, program_name=data.program_name):
                    raise RehabilitationConflictError("Inmate already has an active enrollment for this vocational program")
                record = RehabilitationRepository.create(connection, "vocational_training_enrollments", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def schedule_counseling_session(data: CounselingSessionDTO) -> RehabilitationRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.created_by, "Counseling recorder does not exist")
                record = RehabilitationRepository.create(connection, "counseling_sessions", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def record_behavioral_assessment(data: BehavioralAssessmentDTO) -> RehabilitationRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.assessed_by, "Assessing officer does not exist")
                _validate_behavior_score(data.behavior_score, data.behavior_category)
                record = RehabilitationRepository.create(connection, "behavioral_assessments", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def assign_religious_participation(data: ReligiousParticipationDTO) -> RehabilitationRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                record = RehabilitationRepository.create(connection, "religious_participations", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def assign_work_duties(data: WorkAssignmentDTO) -> RehabilitationRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                record = RehabilitationRepository.create(connection, "work_assignments", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def issue_certification(data: SkillCertificationDTO) -> RehabilitationRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                if RehabilitationRepository.certificate_number_exists(connection, data.certificate_number):
                    raise RehabilitationConflictError("Certificate number already exists")
                record = RehabilitationRepository.create(connection, "skill_certifications", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def track_post_release_followup(data: PostReleaseFollowUpDTO) -> RehabilitationRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                record = RehabilitationRepository.create(connection, "post_release_followups", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def inmate_rehabilitation_history(inmate_id: int) -> dict[str, Any]:
        with db_connection() as connection:
            _require_inmate(connection, inmate_id)
            return RehabilitationRepository.inmate_history(connection, inmate_id)

    @staticmethod
    def rehabilitation_reports() -> dict[str, Any]:
        with db_connection() as connection:
            return RehabilitationRepository.reports(connection)


def _require_inmate(connection, inmate_id: int) -> None:
    if not RehabilitationRepository.inmate_exists(connection, inmate_id):
        raise RehabilitationForeignKeyError("Inmate does not exist")


def _require_user(connection, user_id: int, message: str) -> None:
    if not RehabilitationRepository.user_exists(connection, user_id):
        raise RehabilitationForeignKeyError(message)


def _validate_behavior_score(score: float, category: str) -> None:
    ranges = {
        "Excellent": (80, 100),
        "Good": (60, 100),
        "Fair": (40, 79.99),
        "Poor": (20, 59.99),
        "Violent": (0, 39.99),
    }
    minimum, maximum = ranges[category]
    if score < minimum or score > maximum:
        raise RehabilitationWorkflowError(f"Behavior score is not consistent with {category} category")


def is_duplicate_rehabilitation_error(exc: Exception) -> bool:
    return isinstance(exc, IntegrityError) and getattr(exc, "errno", None) == 1062


def is_mysql_error(exc: Exception) -> bool:
    return isinstance(exc, MySQLError)
