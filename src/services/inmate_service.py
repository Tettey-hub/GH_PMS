from __future__ import annotations

from dataclasses import asdict
from typing import Any

from mysql.connector import Error as MySQLError, IntegrityError

from src.config.database_config import db_connection
from src.dtos.inmate_dto import CreateInmateRequestDTO, CreateReleaseRequestDTO, CreateTransferRequestDTO, ReleaseActionDTO, TransferActionDTO, UpdateInmateRequestDTO
from src.models.inmate import INMATE_RELEASE_STATUSES, INMATE_STATUSES, INMATE_TRANSFER_STATUSES, Inmate, InmateRelease, InmateTransfer
from src.repositories.inmate_repository import InmateRepository


class InmateNotFoundError(LookupError):
    pass


class InmateConflictError(ValueError):
    pass


class InmateForeignKeyError(ValueError):
    pass


class InmateWorkflowError(ValueError):
    pass


class InmateService:
    @staticmethod
    def create_inmate(data: CreateInmateRequestDTO) -> Inmate:
        with db_connection() as connection:
            try:
                _validate_create_uniqueness_and_references(connection, data)
                inmate = InmateRepository.create(connection, asdict(data))
                connection.commit()
                return inmate
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def update_inmate(inmate_db_id: int, data: UpdateInmateRequestDTO) -> Inmate:
        with db_connection() as connection:
            try:
                existing = InmateRepository.get_by_id(connection, inmate_db_id)
                if existing is None:
                    raise InmateNotFoundError("Inmate not found")
                _validate_update_dates(existing, data.updates)
                _validate_update_uniqueness_and_references(connection, inmate_db_id, data.updates)
                updated = InmateRepository.update(connection, inmate_db_id, data.updates)
                connection.commit()
                if updated is None:
                    raise InmateNotFoundError("Inmate not found")
                return updated
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def get_by_id(inmate_db_id: int) -> Inmate | None:
        with db_connection() as connection:
            return InmateRepository.get_by_id(connection, inmate_db_id)

    @staticmethod
    def get_by_inmate_id(inmate_id: str) -> Inmate | None:
        with db_connection() as connection:
            return InmateRepository.get_by_inmate_id(connection, inmate_id)

    @staticmethod
    def list_inmates(*, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0) -> list[Inmate]:
        with db_connection() as connection:
            return InmateRepository.list(connection, filters=filters, limit=limit, offset=offset)

    @staticmethod
    def search_inmates(*, query: str | None, filters: dict[str, Any], limit: int = 50, offset: int = 0) -> list[Inmate]:
        with db_connection() as connection:
            return InmateRepository.search(connection, query=query, filters=filters, limit=limit, offset=offset)

    @staticmethod
    def update_status(inmate_db_id: int, status: str) -> Inmate:
        status = status.strip().lower()
        if status not in INMATE_STATUSES:
            raise ValueError("Invalid inmate status")
        return InmateService.update_inmate(inmate_db_id, UpdateInmateRequestDTO(updates={"status": status}))

    @staticmethod
    def delete_inmate(inmate_db_id: int) -> Inmate:
        with db_connection() as connection:
            try:
                existing = InmateRepository.get_by_id(connection, inmate_db_id)
                if existing is None:
                    raise InmateNotFoundError("Inmate not found")
                deleted = InmateRepository.delete(connection, inmate_db_id)
                connection.commit()
                if not deleted:
                    raise InmateNotFoundError("Inmate not found")
                return existing
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def create_transfer_request(data: CreateTransferRequestDTO) -> InmateTransfer:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.created_by, "Creator does not exist")
                transfer = InmateRepository.create_transfer(connection, {**asdict(data), "transfer_status": "PENDING"})
                connection.commit()
                return transfer
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def update_transfer_workflow(transfer_id: int, data: TransferActionDTO) -> InmateTransfer:
        with db_connection() as connection:
            try:
                transfer = _require_transfer(connection, transfer_id)
                _validate_transfer_update(connection, transfer, data.updates)
                updated = InmateRepository.update_transfer(connection, transfer_id, data.updates)
                if updated is None:
                    raise InmateNotFoundError("Transfer not found")
                if updated.transfer_status == "COMPLETED":
                    InmateRepository.update(connection, updated.inmate_id, {"status": "transferred"})
                    updated = InmateRepository.get_transfer_by_id(connection, transfer_id) or updated
                connection.commit()
                return updated
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def list_transfers(*, filters: dict[str, Any], limit: int, offset: int) -> list[InmateTransfer]:
        with db_connection() as connection:
            return InmateRepository.list_transfers(connection, filters=filters, limit=limit, offset=offset)

    @staticmethod
    def transfer_history(inmate_id: int) -> list[InmateTransfer]:
        with db_connection() as connection:
            _require_inmate(connection, inmate_id)
            return InmateRepository.list_transfers(connection, filters={"inmate_id": inmate_id}, limit=100, offset=0)

    @staticmethod
    def transfer_report() -> list[dict[str, Any]]:
        with db_connection() as connection:
            return InmateRepository.transfer_report(connection)

    @staticmethod
    def initiate_release_review(data: CreateReleaseRequestDTO) -> InmateRelease:
        with db_connection() as connection:
            try:
                inmate = _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.created_by, "Creator does not exist")
                _validate_release_initiation(inmate, data)
                release = InmateRepository.create_release(connection, {**asdict(data), "release_status": "PENDING_REVIEW"})
                connection.commit()
                return release
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def update_release_workflow(release_id: int, data: ReleaseActionDTO) -> InmateRelease:
        with db_connection() as connection:
            try:
                release = _require_release(connection, release_id)
                inmate = _require_inmate(connection, release.inmate_id)
                if data.updates.get("approved_by") is not None:
                    _require_user(connection, data.updates["approved_by"], "Approving officer does not exist")
                _validate_release_update(inmate, release, data.updates)
                updated = InmateRepository.update_release(connection, release_id, data.updates)
                if updated is None:
                    raise InmateNotFoundError("Release not found")
                if updated.release_status == "RELEASED":
                    InmateRepository.update(connection, updated.inmate_id, {"status": "released"})
                    updated = InmateRepository.get_release_by_id(connection, release_id) or updated
                connection.commit()
                return updated
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def list_releases(*, filters: dict[str, Any], limit: int, offset: int) -> list[InmateRelease]:
        with db_connection() as connection:
            return InmateRepository.list_releases(connection, filters=filters, limit=limit, offset=offset)

    @staticmethod
    def release_history(inmate_id: int) -> list[InmateRelease]:
        with db_connection() as connection:
            _require_inmate(connection, inmate_id)
            return InmateRepository.list_releases(connection, filters={"inmate_id": inmate_id}, limit=100, offset=0)

    @staticmethod
    def release_report() -> list[dict[str, Any]]:
        with db_connection() as connection:
            return InmateRepository.release_report(connection)


def _validate_create_uniqueness_and_references(connection, data: CreateInmateRequestDTO) -> None:
    if InmateRepository.exists_by_inmate_id(connection, data.inmate_id):
        raise InmateConflictError("Inmate ID already exists")
    if data.fingerprint_id and InmateRepository.exists_by_fingerprint_id(connection, data.fingerprint_id):
        raise InmateConflictError("Fingerprint ID already exists")
    if not InmateRepository.warrant_exists(connection, data.warrant_id):
        raise InmateForeignKeyError("Arrest warrant does not exist")
    if not InmateRepository.user_exists(connection, data.admission_officer_id):
        raise InmateForeignKeyError("Admission officer does not exist")


def _require_inmate(connection, inmate_id: int) -> Inmate:
    inmate = InmateRepository.get_by_id(connection, inmate_id)
    if inmate is None:
        raise InmateForeignKeyError("Inmate does not exist")
    return inmate


def _require_user(connection, user_id: int, message: str) -> None:
    if not InmateRepository.user_exists(connection, user_id):
        raise InmateForeignKeyError(message)


def _require_transfer(connection, transfer_id: int) -> InmateTransfer:
    transfer = InmateRepository.get_transfer_by_id(connection, transfer_id)
    if transfer is None:
        raise InmateNotFoundError("Transfer not found")
    return transfer


def _require_release(connection, release_id: int) -> InmateRelease:
    release = InmateRepository.get_release_by_id(connection, release_id)
    if release is None:
        raise InmateNotFoundError("Release not found")
    return release


def _validate_transfer_update(connection, transfer: InmateTransfer, updates: dict[str, Any]) -> None:
    next_status = updates.get("transfer_status", transfer.transfer_status)
    if next_status not in INMATE_TRANSFER_STATUSES:
        raise InmateWorkflowError("Invalid transfer status")
    approved_by = updates.get("approved_by")
    if approved_by is not None:
        _require_user(connection, approved_by, "Approving officer does not exist")
    movement_authorized_by = updates.get("movement_authorized_by")
    if movement_authorized_by is not None:
        _require_user(connection, movement_authorized_by, "Movement authorizing officer does not exist")
    departure_date = updates.get("departure_date", transfer.departure_date)
    arrival_date = updates.get("arrival_date", transfer.arrival_date)
    if departure_date and departure_date < transfer.requested_date:
        raise InmateWorkflowError("Departure date cannot be earlier than requested date")
    if arrival_date and not departure_date:
        raise InmateWorkflowError("Arrival date requires a departure date")
    if arrival_date and departure_date and arrival_date < departure_date:
        raise InmateWorkflowError("Arrival date cannot be earlier than departure date")
    if next_status == "APPROVED" and not all([
        updates.get("legal_verified", transfer.legal_verified),
        updates.get("security_assessed", transfer.security_assessed),
        updates.get("medical_clearance", transfer.medical_clearance),
    ]):
        raise InmateWorkflowError("Approved transfer requires legal verification, security assessment, and medical clearance")
    if next_status == "IN_TRANSIT" and not all([
        departure_date,
        updates.get("escort_officers", transfer.escort_officers),
        updates.get("transport_vehicle", transfer.transport_vehicle),
        transfer.movement_authorized_by or movement_authorized_by,
    ]):
        raise InmateWorkflowError("In-transit transfer requires departure date, escort officers, transport assignment, and movement authorization")
    if next_status == "COMPLETED" and not all([
        arrival_date,
        updates.get("receiving_officer", transfer.receiving_officer),
        updates.get("receiving_confirmation", transfer.receiving_confirmation),
    ]):
        raise InmateWorkflowError("Completed transfer requires arrival date, receiving officer, and receiving confirmation")
    if next_status in {"REJECTED", "CANCELLED"} and not updates.get("transfer_completion_notes"):
        raise InmateWorkflowError(f"{next_status.title()} transfer requires a reason")


def _validate_release_initiation(inmate: Inmate, data: CreateReleaseRequestDTO) -> None:
    if data.release_type == "SENTENCE_COMPLETION" and not inmate.sentence_duration and not inmate.expected_release_date:
        raise InmateWorkflowError("Sentence completion release requires sentence duration or expected release date on the inmate record")
    if data.release_type == "BAIL_RELEASE" and "court" not in data.release_reason.lower():
        raise InmateWorkflowError("Bail release requires court release authorization in the release reason")
    if data.release_type == "MEDICAL_RELEASE" and not data.release_reason.strip():
        raise InmateWorkflowError("Medical release requires a medical release reason")


def _validate_release_update(inmate: Inmate, release: InmateRelease, updates: dict[str, Any]) -> None:
    next_status = updates.get("release_status", release.release_status)
    if next_status not in INMATE_RELEASE_STATUSES:
        raise InmateWorkflowError("Invalid release status")
    if updates.get("approved_by") is not None and updates["approved_by"] < 1:
        raise InmateWorkflowError("Approving officer is invalid")
    sentence_validated = updates.get("sentence_validated", release.sentence_validated)
    legal_verified = updates.get("legal_verified", release.legal_verified)
    medical_cleared = updates.get("medical_cleared", release.medical_cleared)
    property_cleared = updates.get("property_cleared", release.property_cleared)
    identity_verified = updates.get("identity_verified", release.identity_verified)
    release_date = updates.get("release_date", release.release_date)
    release_time = updates.get("release_time", release.release_time)
    medical_summary = updates.get("medical_discharge_summary", release.medical_discharge_summary)
    if release.release_type == "SENTENCE_COMPLETION" and sentence_validated and not inmate.sentence_duration and not inmate.expected_release_date:
        raise InmateWorkflowError("Cannot validate sentence completion without sentence duration or expected release date")
    if release.release_type == "MEDICAL_RELEASE" and medical_cleared and not medical_summary:
        raise InmateWorkflowError("Medical release requires medical discharge summary")
    if next_status == "APPROVED" and not legal_verified:
        raise InmateWorkflowError("Release approval requires legal verification")
    if next_status == "REJECTED" and not updates.get("discharge_notes"):
        raise InmateWorkflowError("Rejected release requires rejection reason")
    if next_status == "READY_FOR_RELEASE" and not updates.get("release_certificate_number", release.release_certificate_number):
        raise InmateWorkflowError("Release documents require a release certificate number")
    if next_status == "RELEASED":
        if not all([legal_verified, sentence_validated, identity_verified, property_cleared, medical_cleared, release_date, release_time]):
            raise InmateWorkflowError("Released status requires legal verification, sentence validation, identity verification, property clearance, medical clearance, and release date/time")
        approval_date = release.updated_at.date() if release.approved_by and release.updated_at else None
        if approval_date and release_date < approval_date:
            raise InmateWorkflowError("Release date cannot be earlier than approval date")


def _validate_update_uniqueness_and_references(connection, inmate_db_id: int, updates: dict[str, Any]) -> None:
    inmate_id = updates.get("inmate_id")
    if inmate_id and InmateRepository.exists_by_inmate_id(connection, inmate_id, exclude_id=inmate_db_id):
        raise InmateConflictError("Inmate ID already exists")
    fingerprint_id = updates.get("fingerprint_id")
    if fingerprint_id and InmateRepository.exists_by_fingerprint_id(connection, fingerprint_id, exclude_id=inmate_db_id):
        raise InmateConflictError("Fingerprint ID already exists")
    warrant_id = updates.get("warrant_id")
    if warrant_id is not None and not InmateRepository.warrant_exists(connection, warrant_id):
        raise InmateForeignKeyError("Arrest warrant does not exist")
    admission_officer_id = updates.get("admission_officer_id")
    if admission_officer_id is not None and not InmateRepository.user_exists(connection, admission_officer_id):
        raise InmateForeignKeyError("Admission officer does not exist")


def _validate_update_dates(existing: Inmate, updates: dict[str, Any]) -> None:
    admission_date = updates.get("admission_date", existing.admission_date)
    arrest_date = updates.get("arrest_date", existing.arrest_date)
    expected_release_date = updates.get("expected_release_date", existing.expected_release_date)
    if arrest_date > admission_date:
        raise ValueError("Arrest date cannot be after admission date")
    if expected_release_date is not None and expected_release_date < admission_date:
        raise ValueError("Expected release date cannot be earlier than admission date")


def is_duplicate_inmate_error(exc: Exception) -> bool:
    return isinstance(exc, IntegrityError) and getattr(exc, "errno", None) == 1062


def is_mysql_error(exc: Exception) -> bool:
    return isinstance(exc, MySQLError)
