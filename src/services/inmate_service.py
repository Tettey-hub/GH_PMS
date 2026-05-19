from __future__ import annotations

from dataclasses import asdict
from typing import Any

from mysql.connector import Error as MySQLError, IntegrityError

from src.config.database_config import db_connection
from src.dtos.inmate_dto import CreateInmateRequestDTO, UpdateInmateRequestDTO
from src.models.inmate import INMATE_STATUSES, Inmate
from src.repositories.inmate_repository import InmateRepository


class InmateNotFoundError(LookupError):
    pass


class InmateConflictError(ValueError):
    pass


class InmateForeignKeyError(ValueError):
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


def _validate_create_uniqueness_and_references(connection, data: CreateInmateRequestDTO) -> None:
    if InmateRepository.exists_by_inmate_id(connection, data.inmate_id):
        raise InmateConflictError("Inmate ID already exists")
    if data.fingerprint_id and InmateRepository.exists_by_fingerprint_id(connection, data.fingerprint_id):
        raise InmateConflictError("Fingerprint ID already exists")
    if not InmateRepository.warrant_exists(connection, data.warrant_id):
        raise InmateForeignKeyError("Arrest warrant does not exist")
    if not InmateRepository.user_exists(connection, data.admission_officer_id):
        raise InmateForeignKeyError("Admission officer does not exist")


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
