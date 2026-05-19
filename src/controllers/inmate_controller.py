from __future__ import annotations

from typing import Any

from flask import g, jsonify, request

from src.dtos.inmate_dto import CreateInmateRequestDTO, CreateReleaseRequestDTO, CreateTransferRequestDTO, InmateValidationError, ReleaseActionDTO, TransferActionDTO, UpdateInmateRequestDTO
from src.services.audit_service import AuditService
from src.services.inmate_service import (
    InmateConflictError,
    InmateForeignKeyError,
    InmateWorkflowError,
    InmateNotFoundError,
    InmateService,
    is_duplicate_inmate_error,
    is_mysql_error,
)


def create_inmate():
    payload = _json_payload()
    try:
        dto = CreateInmateRequestDTO.from_payload(payload)
        inmate = InmateService.create_inmate(dto)
    except InmateValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except InmateConflictError as exc:
        return _error(str(exc), 409)
    except InmateForeignKeyError as exc:
        return _error(str(exc), 400)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_duplicate_inmate_error(exc):
            return _error("Inmate ID or fingerprint ID already exists", 409)
        if is_mysql_error(exc):
            return _error("Database error while creating inmate", 500)
        raise

    AuditService.record(
        action="inmate_created",
        status="success",
        actor_user_id=g.current_user.id,
        target_user_id=dto.admission_officer_id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"inmate_db_id": inmate.id, "inmate_id": inmate.inmate_id, "case_number": inmate.case_number},
    )
    return jsonify({"message": "Inmate created successfully", "inmate": inmate.to_dict()}), 201


def update_inmate(inmate_db_id: int):
    payload = _json_payload()
    try:
        dto = UpdateInmateRequestDTO.from_payload(payload)
        inmate = InmateService.update_inmate(inmate_db_id, dto)
    except InmateValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except InmateNotFoundError as exc:
        return _error(str(exc), 404)
    except InmateConflictError as exc:
        return _error(str(exc), 409)
    except InmateForeignKeyError as exc:
        return _error(str(exc), 400)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_duplicate_inmate_error(exc):
            return _error("Inmate ID or fingerprint ID already exists", 409)
        if is_mysql_error(exc):
            return _error("Database error while updating inmate", 500)
        raise

    AuditService.record(
        action="inmate_updated",
        status="success",
        actor_user_id=g.current_user.id,
        target_user_id=inmate.admission_officer_id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"inmate_db_id": inmate.id, "inmate_id": inmate.inmate_id, "updated_fields": sorted(dto.updates.keys())},
    )
    return jsonify({"message": "Inmate updated successfully", "inmate": inmate.to_dict()})


def get_inmate(inmate_db_id: int):
    inmate = InmateService.get_by_id(inmate_db_id)
    if inmate is None:
        return _error("Inmate not found", 404)
    return jsonify({"inmate": inmate.to_dict()})


def get_inmate_by_inmate_id(inmate_id: str):
    inmate = InmateService.get_by_inmate_id(inmate_id.strip())
    if inmate is None:
        return _error("Inmate not found", 404)
    return jsonify({"inmate": inmate.to_dict()})


def list_inmates():
    try:
        limit, offset = _pagination()
        filters = _filters_from_args()
    except ValueError as exc:
        return _error(str(exc), 400)
    inmates = InmateService.list_inmates(filters=filters, limit=limit, offset=offset)
    return jsonify({"total": len(inmates), "limit": limit, "offset": offset, "inmates": [inmate.to_dict() for inmate in inmates]})


def search_inmates():
    try:
        limit, offset = _pagination()
        filters = _filters_from_args()
    except ValueError as exc:
        return _error(str(exc), 400)
    query = request.args.get("q", "").strip() or None
    inmates = InmateService.search_inmates(query=query, filters=filters, limit=limit, offset=offset)
    return jsonify({"total": len(inmates), "limit": limit, "offset": offset, "inmates": [inmate.to_dict() for inmate in inmates]})


def update_inmate_status(inmate_db_id: int):
    payload = _json_payload()
    status = payload.get("status")
    if not isinstance(status, str) or not status.strip():
        return _error("Validation failed", 400, {"status": "This field is required"})
    try:
        inmate = InmateService.update_status(inmate_db_id, status)
    except ValueError as exc:
        return _error(str(exc), 400)
    except InmateNotFoundError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while updating inmate status", 500)
        raise

    AuditService.record(
        action="inmate_status_updated",
        status="success",
        actor_user_id=g.current_user.id,
        target_user_id=inmate.admission_officer_id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"inmate_db_id": inmate.id, "inmate_id": inmate.inmate_id, "new_status": inmate.status},
    )
    return jsonify({"message": "Inmate status updated successfully", "inmate": inmate.to_dict()})


def approve_inmate_transfer(inmate_db_id: int):
    return _error("Use the inmate transfer workflow endpoints; transfer is not a direct status update", 400)


def approve_inmate_release(inmate_db_id: int):
    return _error("Use the inmate release workflow endpoints; release is not a direct status update", 400)


def delete_inmate(inmate_db_id: int):
    try:
        inmate = InmateService.delete_inmate(inmate_db_id)
    except InmateNotFoundError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while deleting inmate", 500)
        raise

    AuditService.record(
        action="inmate_deleted",
        status="success",
        actor_user_id=g.current_user.id,
        target_user_id=None,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"inmate_db_id": inmate.id, "inmate_id": inmate.inmate_id, "case_number": inmate.case_number},
    )
    return jsonify({"message": "Inmate deleted successfully", "inmate": inmate.to_dict()})


def create_transfer_request():
    try:
        dto = CreateTransferRequestDTO.from_payload(_json_payload(), actor_user_id=g.current_user.id)
        transfer = InmateService.create_transfer_request(dto)
    except InmateValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except (InmateForeignKeyError, InmateWorkflowError, ValueError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while creating transfer request", 500)
        raise
    _record_workflow_audit("inmate_transfer_created", {"transfer_id": transfer.id, "inmate_db_id": transfer.inmate_id})
    return jsonify({"message": "Transfer request created successfully", "transfer": transfer.to_dict()}), 201


def transfer_action(transfer_id: int, action: str):
    return _workflow_action(
        dto_factory=lambda payload: TransferActionDTO.from_payload(payload, action=action, actor_user_id=g.current_user.id),
        service_method=lambda dto: InmateService.update_transfer_workflow(transfer_id, dto),
        response_key="transfer",
        audit_action=f"inmate_transfer_{action}",
        not_found_message="Transfer not found",
    )


def list_transfers():
    try:
        limit, offset = _pagination()
    except ValueError as exc:
        return _error(str(exc), 400)
    transfers = InmateService.list_transfers(filters=_transfer_filters_from_args(), limit=limit, offset=offset)
    return jsonify({"total": len(transfers), "limit": limit, "offset": offset, "transfers": [transfer.to_dict() for transfer in transfers]})


def get_transfer_history(inmate_db_id: int):
    try:
        transfers = InmateService.transfer_history(inmate_db_id)
    except InmateForeignKeyError as exc:
        return _error(str(exc), 404)
    return jsonify({"inmate_id": inmate_db_id, "transfers": [transfer.to_dict() for transfer in transfers]})


def get_transfer_reports():
    return jsonify({"transfer_reports": InmateService.transfer_report()})


def initiate_release_review():
    try:
        dto = CreateReleaseRequestDTO.from_payload(_json_payload(), actor_user_id=g.current_user.id)
        release = InmateService.initiate_release_review(dto)
    except InmateValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except (InmateForeignKeyError, InmateWorkflowError, ValueError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while initiating release review", 500)
        raise
    _record_workflow_audit("inmate_release_initiated", {"release_id": release.id, "inmate_db_id": release.inmate_id})
    return jsonify({"message": "Release review initiated successfully", "release": release.to_dict()}), 201


def release_action(release_id: int, action: str):
    return _workflow_action(
        dto_factory=lambda payload: ReleaseActionDTO.from_payload(payload, action=action, actor_user_id=g.current_user.id),
        service_method=lambda dto: InmateService.update_release_workflow(release_id, dto),
        response_key="release",
        audit_action=f"inmate_release_{action}",
        not_found_message="Release not found",
    )


def list_releases():
    try:
        limit, offset = _pagination()
    except ValueError as exc:
        return _error(str(exc), 400)
    releases = InmateService.list_releases(filters=_release_filters_from_args(), limit=limit, offset=offset)
    return jsonify({"total": len(releases), "limit": limit, "offset": offset, "releases": [release.to_dict() for release in releases]})


def get_release_history(inmate_db_id: int):
    try:
        releases = InmateService.release_history(inmate_db_id)
    except InmateForeignKeyError as exc:
        return _error(str(exc), 404)
    return jsonify({"inmate_id": inmate_db_id, "releases": [release.to_dict() for release in releases]})


def get_release_reports():
    return jsonify({"release_reports": InmateService.release_report()})


def _workflow_action(*, dto_factory, service_method, response_key: str, audit_action: str, not_found_message: str):
    try:
        dto = dto_factory(_json_payload())
        record = service_method(dto)
    except InmateValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except InmateNotFoundError:
        return _error(not_found_message, 404)
    except (InmateForeignKeyError, InmateWorkflowError, ValueError) as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while processing workflow", 500)
        raise
    _record_workflow_audit(audit_action, {f"{response_key}_id": record.id, "inmate_db_id": record.inmate_id})
    return jsonify({"message": "Workflow updated successfully", response_key: record.to_dict()})


def _record_workflow_audit(action: str, metadata: dict[str, Any]) -> None:
    AuditService.record(
        action=action,
        status="success",
        actor_user_id=g.current_user.id,
        target_user_id=None,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata=metadata,
    )


def _json_payload() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def _filters_from_args() -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for field in ("gender", "nationality", "admission_date", "arrest_date", "status", "sentence_type"):
        value = request.args.get(field)
        if value:
            filters[field] = value.strip().lower() if field in {"gender", "status", "sentence_type"} else value.strip()
    return filters


def _transfer_filters_from_args() -> dict[str, Any]:
    return _workflow_filters_from_args(("inmate_id", "transfer_type", "transfer_status", "facility", "date_from", "date_to", "approved_by"))


def _release_filters_from_args() -> dict[str, Any]:
    return _workflow_filters_from_args(("inmate_id", "release_type", "release_status", "date_from", "date_to", "approved_by"))


def _workflow_filters_from_args(fields: tuple[str, ...]) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for field in fields:
        value = request.args.get(field)
        if not value:
            continue
        if field in {"inmate_id", "approved_by"}:
            try:
                filters[field] = int(value)
            except ValueError:
                continue
        elif field in {"transfer_type", "transfer_status", "release_type", "release_status"}:
            filters[field] = value.strip().upper()
        else:
            filters[field] = value.strip()
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
