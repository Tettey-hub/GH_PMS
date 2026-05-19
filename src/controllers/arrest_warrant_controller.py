from __future__ import annotations

from typing import Any

from flask import g, jsonify, request

from src.dtos.arrest_warrant_dto import (
    ArrestWarrantValidationError,
    CreateArrestWarrantRequestDTO,
    UpdateArrestWarrantRequestDTO,
)
from src.services.arrest_warrant_service import (
    ArrestWarrantConflictError,
    ArrestWarrantNotFoundError,
    ArrestWarrantService,
    is_duplicate_arrest_warrant_error,
    is_mysql_error,
)
from src.services.audit_service import AuditService


def create_arrest_warrant():
    payload = _json_payload()
    try:
        dto = CreateArrestWarrantRequestDTO.from_payload(payload)
        warrant = ArrestWarrantService.create_warrant(dto)
    except ArrestWarrantValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except ArrestWarrantConflictError as exc:
        return _error(str(exc), 409)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_duplicate_arrest_warrant_error(exc):
            return _error("Warrant number or case number already exists", 409)
        if is_mysql_error(exc):
            return _error("Database error while creating arrest warrant", 500)
        raise

    AuditService.record(
        action="arrest_warrant_created",
        status="success",
        actor_user_id=g.current_user.id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"warrant_db_id": warrant.id, "warrant_number": warrant.warrant_number, "case_number": warrant.case_number},
    )
    return jsonify({"message": "Arrest warrant created successfully", "arrest_warrant": warrant.to_dict()}), 201


def update_arrest_warrant(warrant_db_id: int):
    payload = _json_payload()
    try:
        dto = UpdateArrestWarrantRequestDTO.from_payload(payload)
        warrant = ArrestWarrantService.update_warrant(warrant_db_id, dto)
    except ArrestWarrantValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except ArrestWarrantNotFoundError as exc:
        return _error(str(exc), 404)
    except ArrestWarrantConflictError as exc:
        return _error(str(exc), 409)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_duplicate_arrest_warrant_error(exc):
            return _error("Warrant number or case number already exists", 409)
        if is_mysql_error(exc):
            return _error("Database error while updating arrest warrant", 500)
        raise

    AuditService.record(
        action="arrest_warrant_updated",
        status="success",
        actor_user_id=g.current_user.id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"warrant_db_id": warrant.id, "warrant_number": warrant.warrant_number, "updated_fields": sorted(dto.updates.keys())},
    )
    return jsonify({"message": "Arrest warrant updated successfully", "arrest_warrant": warrant.to_dict()})


def get_arrest_warrant(warrant_db_id: int):
    warrant = ArrestWarrantService.get_by_id(warrant_db_id)
    if warrant is None:
        return _error("Arrest warrant not found", 404)
    return jsonify({"arrest_warrant": warrant.to_dict()})


def get_arrest_warrant_by_warrant_number(warrant_number: str):
    warrant = ArrestWarrantService.get_by_warrant_number(warrant_number.strip())
    if warrant is None:
        return _error("Arrest warrant not found", 404)
    return jsonify({"arrest_warrant": warrant.to_dict()})


def get_arrest_warrant_by_case_number(case_number: str):
    warrant = ArrestWarrantService.get_by_case_number(case_number.strip())
    if warrant is None:
        return _error("Arrest warrant not found", 404)
    return jsonify({"arrest_warrant": warrant.to_dict()})


def list_arrest_warrants():
    try:
        limit, offset = _pagination()
        filters = _filters_from_args()
    except ValueError as exc:
        return _error(str(exc), 400)
    warrants = ArrestWarrantService.list_warrants(filters=filters, limit=limit, offset=offset)
    return jsonify({"total": len(warrants), "limit": limit, "offset": offset, "arrest_warrants": [warrant.to_dict() for warrant in warrants]})


def search_arrest_warrants():
    try:
        limit, offset = _pagination()
        filters = _filters_from_args()
    except ValueError as exc:
        return _error(str(exc), 400)
    query = request.args.get("q", "").strip() or None
    warrants = ArrestWarrantService.search_warrants(query=query, filters=filters, limit=limit, offset=offset)
    return jsonify({"total": len(warrants), "limit": limit, "offset": offset, "arrest_warrants": [warrant.to_dict() for warrant in warrants]})


def update_arrest_warrant_status(warrant_db_id: int):
    payload = _json_payload()
    status = payload.get("status")
    if not isinstance(status, str) or not status.strip():
        return _error("Validation failed", 400, {"status": "This field is required"})
    try:
        warrant = ArrestWarrantService.update_status(warrant_db_id, status)
    except ValueError as exc:
        return _error(str(exc), 400)
    except ArrestWarrantNotFoundError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while updating arrest warrant status", 500)
        raise

    AuditService.record(
        action="arrest_warrant_status_updated",
        status="success",
        actor_user_id=g.current_user.id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"warrant_db_id": warrant.id, "warrant_number": warrant.warrant_number, "new_status": warrant.status},
    )
    return jsonify({"message": "Arrest warrant status updated successfully", "arrest_warrant": warrant.to_dict()})


def delete_arrest_warrant(warrant_db_id: int):
    try:
        warrant = ArrestWarrantService.delete_warrant(warrant_db_id)
    except ArrestWarrantNotFoundError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while deleting arrest warrant", 500)
        raise

    AuditService.record(
        action="arrest_warrant_deleted",
        status="success",
        actor_user_id=g.current_user.id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"warrant_db_id": warrant.id, "warrant_number": warrant.warrant_number, "case_number": warrant.case_number},
    )
    return jsonify({"message": "Arrest warrant deleted successfully", "arrest_warrant": warrant.to_dict()})


def _json_payload() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def _filters_from_args() -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for field in ("gender", "nationality", "arrest_date", "issued_date", "status", "sentence_type"):
        value = request.args.get(field)
        if value:
            filters[field] = value.strip().lower() if field in {"gender", "status", "sentence_type"} else value.strip()
    return filters


def _pagination() -> tuple[int, int]:
    try:
        limit = int(request.args.get("limit", "50"))
        offset = int(request.args.get("offset", "0"))
    except ValueError as exc:
        raise ValueError("Pagination values must be integers") from exc
    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")
    if offset < 0:
        raise ValueError("Offset must not be negative")
    return limit, offset


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
