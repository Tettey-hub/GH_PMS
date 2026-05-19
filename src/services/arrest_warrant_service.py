from __future__ import annotations

from dataclasses import asdict
from typing import Any

from mysql.connector import Error as MySQLError, IntegrityError

from src.config.database_config import db_connection
from src.dtos.arrest_warrant_dto import CreateArrestWarrantRequestDTO, UpdateArrestWarrantRequestDTO
from src.models.arrest_warrant import ARREST_WARRANT_STATUSES, ArrestWarrant
from src.repositories.arrest_warrant_repository import ArrestWarrantRepository


class ArrestWarrantNotFoundError(LookupError):
    pass


class ArrestWarrantConflictError(ValueError):
    pass


class ArrestWarrantService:
    @staticmethod
    def create_warrant(data: CreateArrestWarrantRequestDTO) -> ArrestWarrant:
        with db_connection() as connection:
            try:
                _validate_create_uniqueness(connection, data)
                warrant = ArrestWarrantRepository.create(connection, asdict(data))
                connection.commit()
                return warrant
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def update_warrant(warrant_db_id: int, data: UpdateArrestWarrantRequestDTO) -> ArrestWarrant:
        with db_connection() as connection:
            try:
                existing = ArrestWarrantRepository.get_by_id(connection, warrant_db_id)
                if existing is None:
                    raise ArrestWarrantNotFoundError("Arrest warrant not found")
                _validate_update_uniqueness(connection, warrant_db_id, data.updates)
                updated = ArrestWarrantRepository.update(connection, warrant_db_id, data.updates)
                connection.commit()
                if updated is None:
                    raise ArrestWarrantNotFoundError("Arrest warrant not found")
                return updated
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def get_by_id(warrant_db_id: int) -> ArrestWarrant | None:
        with db_connection() as connection:
            return ArrestWarrantRepository.get_by_id(connection, warrant_db_id)

    @staticmethod
    def get_by_warrant_number(warrant_number: str) -> ArrestWarrant | None:
        with db_connection() as connection:
            return ArrestWarrantRepository.get_by_warrant_number(connection, warrant_number)

    @staticmethod
    def get_by_case_number(case_number: str) -> ArrestWarrant | None:
        with db_connection() as connection:
            return ArrestWarrantRepository.get_by_case_number(connection, case_number)

    @staticmethod
    def list_warrants(*, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0) -> list[ArrestWarrant]:
        with db_connection() as connection:
            return ArrestWarrantRepository.list(connection, filters=filters, limit=limit, offset=offset)

    @staticmethod
    def search_warrants(*, query: str | None, filters: dict[str, Any], limit: int = 50, offset: int = 0) -> list[ArrestWarrant]:
        with db_connection() as connection:
            return ArrestWarrantRepository.search(connection, query=query, filters=filters, limit=limit, offset=offset)

    @staticmethod
    def update_status(warrant_db_id: int, status: str) -> ArrestWarrant:
        status = status.strip().lower()
        if status not in ARREST_WARRANT_STATUSES:
            raise ValueError("Invalid arrest warrant status")
        return ArrestWarrantService.update_warrant(warrant_db_id, UpdateArrestWarrantRequestDTO(updates={"status": status}))

    @staticmethod
    def delete_warrant(warrant_db_id: int) -> ArrestWarrant:
        with db_connection() as connection:
            try:
                existing = ArrestWarrantRepository.get_by_id(connection, warrant_db_id)
                if existing is None:
                    raise ArrestWarrantNotFoundError("Arrest warrant not found")
                deleted = ArrestWarrantRepository.delete(connection, warrant_db_id)
                connection.commit()
                if not deleted:
                    raise ArrestWarrantNotFoundError("Arrest warrant not found")
                return existing
            except Exception:
                connection.rollback()
                raise


def _validate_create_uniqueness(connection, data: CreateArrestWarrantRequestDTO) -> None:
    if ArrestWarrantRepository.exists_by_warrant_number(connection, data.warrant_number):
        raise ArrestWarrantConflictError("Warrant number already exists")
    if ArrestWarrantRepository.exists_by_case_number(connection, data.case_number):
        raise ArrestWarrantConflictError("Case number already exists")


def _validate_update_uniqueness(connection, warrant_db_id: int, updates: dict[str, Any]) -> None:
    warrant_number = updates.get("warrant_number")
    if warrant_number and ArrestWarrantRepository.exists_by_warrant_number(connection, warrant_number, exclude_id=warrant_db_id):
        raise ArrestWarrantConflictError("Warrant number already exists")
    case_number = updates.get("case_number")
    if case_number and ArrestWarrantRepository.exists_by_case_number(connection, case_number, exclude_id=warrant_db_id):
        raise ArrestWarrantConflictError("Case number already exists")


def is_duplicate_arrest_warrant_error(exc: Exception) -> bool:
    return isinstance(exc, IntegrityError) and getattr(exc, "errno", None) == 1062


def is_mysql_error(exc: Exception) -> bool:
    return isinstance(exc, MySQLError)
