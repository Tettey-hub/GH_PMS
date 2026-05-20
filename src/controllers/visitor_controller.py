from __future__ import annotations

from typing import Any, Callable

from flask import g, jsonify, request

from src.dtos.visitor_dto import (
    VisitRequestDTO,
    VisitReviewDTO,
    VisitScheduleDTO,
    VisitorCheckinDTO,
    VisitorCheckoutDTO,
    VisitorMonitoringDTO,
    VisitorRegistrationDTO,
    VisitorUpdateDTO,
    VisitorValidationError,
    VisitorVerificationDTO,
    VisitorViolationDTO,
)
from src.services.audit_service import AuditService
from src.services.visitor_service import (
    VisitorConflictError,
    VisitorForeignKeyError,
    VisitorNotFoundError,
    VisitorService,
    VisitorWorkflowError,
    is_duplicate_visitor_error,
    is_mysql_error,
)


def register_visitor():
    return _create_record(
        dto_factory=lambda payload: VisitorRegistrationDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=VisitorService.register_visitor,
        response_key="visitor",
        audit_action="visitor_registered",
        message="Visitor registered successfully",
    )


def update_visitor(visitor_id: int):
    payload = _json_payload()
    try:
        dto = VisitorUpdateDTO.from_payload(payload)
        record = VisitorService.update_visitor(visitor_id, dto)
    except VisitorValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except VisitorNotFoundError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while updating visitor", 500)
        raise

    _audit("visitor_updated", metadata={"visitor_id": visitor_id, "updated_fields": sorted(dto.updates)})
    return jsonify({"message": "Visitor updated successfully", "visitor": record.to_dict()})


def verify_visitor_identity():
    return _create_record(
        dto_factory=lambda payload: VisitorVerificationDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=VisitorService.verify_visitor_identity,
        response_key="visitor_verification",
        audit_action="visitor_verified",
        message="Visitor verification recorded successfully",
    )


def blacklist_visitor(visitor_id: int):
    payload = _json_payload()
    reason = str(payload.get("blacklist_reason", "")).strip()
    if not reason:
        return _error("Validation failed", 400, {"blacklist_reason": "This field is required"})
    try:
        record = VisitorService.blacklist_visitor(visitor_id, reason=reason)
    except VisitorNotFoundError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while blacklisting visitor", 500)
        raise
    _audit("visitor_blacklisted", metadata={"visitor_id": visitor_id})
    return jsonify({"message": "Visitor blacklisted successfully", "visitor": record.to_dict()})


def submit_visit_request():
    return _create_record(
        dto_factory=VisitRequestDTO.from_payload,
        service_method=VisitorService.submit_visit_request,
        response_key="visitor_request",
        audit_action="visit_request_submitted",
        message="Visit request submitted successfully",
    )


def review_visit_request(request_id: int, action: str = "review"):
    payload = _json_payload()
    try:
        dto = VisitReviewDTO.from_payload(payload, action=action, actor_user_id=g.current_user.id)
        record = VisitorService.review_visit_request(request_id, dto)
    except VisitorValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except VisitorNotFoundError as exc:
        return _error(str(exc), 404)
    except (VisitorForeignKeyError, VisitorWorkflowError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while reviewing visit request", 500)
        raise

    _audit(f"visit_request_{action}", metadata={"visitor_request_id": request_id})
    return jsonify({"message": "Visit request updated successfully", "visitor_request": record.to_dict()})


def create_visit_schedule():
    return _create_record(
        dto_factory=lambda payload: VisitScheduleDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=VisitorService.create_visit_schedule,
        response_key="visitor_schedule",
        audit_action="visit_scheduled",
        message="Visit scheduled successfully",
    )


def check_in_visitor():
    return _create_record(
        dto_factory=lambda payload: VisitorCheckinDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=VisitorService.check_in_visitor,
        response_key="visitor_checkin",
        audit_action="visitor_checked_in",
        message="Visitor checked in successfully",
    )


def check_out_visitor(checkin_id: int):
    payload = _json_payload()
    try:
        dto = VisitorCheckoutDTO.from_payload(payload)
        record = VisitorService.check_out_visitor(checkin_id, dto)
    except VisitorValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except VisitorNotFoundError as exc:
        return _error(str(exc), 404)
    except VisitorWorkflowError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while checking out visitor", 500)
        raise

    _audit("visitor_checked_out", metadata={"visitor_checkin_id": checkin_id})
    return jsonify({"message": "Visitor checked out successfully", "visitor_checkin": record.to_dict()})


def monitor_visitor_activity():
    return _create_record(
        dto_factory=lambda payload: VisitorMonitoringDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=VisitorService.monitor_visitor_activity,
        response_key="visitor_monitoring_log",
        audit_action="visitor_monitored",
        message="Visitor monitoring log recorded successfully",
    )


def record_visitor_violation():
    return _create_record(
        dto_factory=lambda payload: VisitorViolationDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=VisitorService.record_visitor_violation,
        response_key="visitor_violation",
        audit_action="visitor_violation_recorded",
        message="Visitor violation recorded successfully",
    )


def get_visitor_history(visitor_id: int):
    try:
        history = VisitorService.visitor_history(visitor_id)
    except VisitorNotFoundError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while retrieving visitor history", 500)
        raise
    return jsonify({"visitor_history": _serialize(history)})


def search_visitors():
    filters = {
        "q": request.args.get("q"),
        "relationship_to_inmate": request.args.get("relationship_to_inmate"),
        "verification_status": _upper_arg("verification_status"),
        "blacklist_status": _bool_arg("blacklist_status"),
    }
    try:
        limit = min(max(int(request.args.get("limit", 20)), 1), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        return _error("Invalid pagination parameters", 400)

    try:
        visitors = VisitorService.search_visitors(filters=filters, limit=limit, offset=offset)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while searching visitors", 500)
        raise
    return jsonify({"visitors": [visitor.to_dict() for visitor in visitors], "limit": limit, "offset": offset})


def get_visitor_reports():
    try:
        reports = VisitorService.visitor_reports()
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while generating visitor reports", 500)
        raise
    return jsonify({"visitor_reports": _serialize(reports)})


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
    except VisitorValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except VisitorConflictError as exc:
        return _error(str(exc), 409)
    except (VisitorForeignKeyError, VisitorWorkflowError) as exc:
        return _error(str(exc), 400)
    except VisitorNotFoundError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        if is_duplicate_visitor_error(exc):
            return _error("Duplicate visitor record", 409)
        if is_mysql_error(exc):
            return _error("Database error while processing visitor record", 500)
        raise

    _audit(audit_action, metadata={f"{response_key}_id": record.data.get("id")})
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


def _upper_arg(name: str) -> str | None:
    value = request.args.get(name)
    return value.upper() if value else None


def _bool_arg(name: str) -> bool | None:
    value = request.args.get(name)
    if value is None:
        return None
    if value.strip().lower() in {"true", "1", "yes"}:
        return True
    if value.strip().lower() in {"false", "0", "no"}:
        return False
    return None


def _serialize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
