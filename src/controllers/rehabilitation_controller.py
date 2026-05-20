from __future__ import annotations

from typing import Any, Callable

from flask import g, jsonify, request

from src.dtos.rehabilitation_dto import (
    BehavioralAssessmentDTO,
    CounselingSessionDTO,
    PostReleaseFollowUpDTO,
    RehabilitationValidationError,
    ReligiousParticipationDTO,
    SkillCertificationDTO,
    VocationalEnrollmentDTO,
    WorkAssignmentDTO,
)
from src.services.audit_service import AuditService
from src.services.rehabilitation_service import (
    RehabilitationConflictError,
    RehabilitationForeignKeyError,
    RehabilitationNotFoundError,
    RehabilitationService,
    RehabilitationWorkflowError,
    is_duplicate_rehabilitation_error,
    is_mysql_error,
)


def enroll_vocational_program():
    return _create_record(
        dto_factory=lambda payload: VocationalEnrollmentDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=RehabilitationService.enroll_vocational_program,
        response_key="vocational_training",
        audit_action="rehabilitation_vocational_enrollment_created",
        message="Vocational training enrollment created successfully",
    )


def schedule_counseling_session():
    return _create_record(
        dto_factory=lambda payload: CounselingSessionDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=RehabilitationService.schedule_counseling_session,
        response_key="counseling_session",
        audit_action="rehabilitation_counseling_session_recorded",
        message="Counseling session recorded successfully",
    )


def record_behavioral_assessment():
    return _create_record(
        dto_factory=lambda payload: BehavioralAssessmentDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=RehabilitationService.record_behavioral_assessment,
        response_key="behavioral_assessment",
        audit_action="rehabilitation_behavioral_assessment_recorded",
        message="Behavioral assessment recorded successfully",
    )


def assign_religious_participation():
    return _create_record(
        dto_factory=ReligiousParticipationDTO.from_payload,
        service_method=RehabilitationService.assign_religious_participation,
        response_key="religious_participation",
        audit_action="rehabilitation_religious_participation_recorded",
        message="Religious participation recorded successfully",
    )


def assign_work_duties():
    return _create_record(
        dto_factory=WorkAssignmentDTO.from_payload,
        service_method=RehabilitationService.assign_work_duties,
        response_key="work_assignment",
        audit_action="rehabilitation_work_assignment_created",
        message="Work assignment created successfully",
    )


def issue_certification():
    return _create_record(
        dto_factory=SkillCertificationDTO.from_payload,
        service_method=RehabilitationService.issue_certification,
        response_key="skill_certification",
        audit_action="rehabilitation_skill_certification_issued",
        message="Skill certification issued successfully",
    )


def track_post_release_followup():
    return _create_record(
        dto_factory=PostReleaseFollowUpDTO.from_payload,
        service_method=RehabilitationService.track_post_release_followup,
        response_key="post_release_followup",
        audit_action="rehabilitation_post_release_followup_recorded",
        message="Post-release follow-up recorded successfully",
    )


def get_inmate_rehabilitation_history(inmate_id: int):
    try:
        history = RehabilitationService.inmate_rehabilitation_history(inmate_id)
    except RehabilitationForeignKeyError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while retrieving rehabilitation history", 500)
        raise
    return jsonify({"rehabilitation_history": _serialize(history)})


def get_rehabilitation_reports():
    try:
        reports = RehabilitationService.rehabilitation_reports()
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while generating rehabilitation reports", 500)
        raise
    _audit("rehabilitation_reports_generated")
    return jsonify({"rehabilitation_reports": _serialize(reports)})


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
    except RehabilitationValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except RehabilitationConflictError as exc:
        return _error(str(exc), 409)
    except (RehabilitationForeignKeyError, RehabilitationWorkflowError) as exc:
        return _error(str(exc), 400)
    except RehabilitationNotFoundError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        if is_duplicate_rehabilitation_error(exc):
            return _error("Duplicate rehabilitation record", 409)
        if is_mysql_error(exc):
            return _error("Database error while processing rehabilitation record", 500)
        raise

    _audit(audit_action, metadata={f"{response_key}_id": record.data.get("id"), "inmate_id": record.data.get("inmate_id")})
    return jsonify({"message": message, response_key: record.to_dict()}), 201


def _audit(action: str, *, metadata: dict[str, Any] | None = None) -> None:
    AuditService.record(
        action=action,
        status="success",
        actor_user_id=g.current_user.id,
        target_user_id=None,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata=metadata or {},
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


def _serialize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
