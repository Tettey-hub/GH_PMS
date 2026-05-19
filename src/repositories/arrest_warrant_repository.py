from __future__ import annotations

from typing import Any

from src.config.database_config import DatabaseConnection
from src.models.arrest_warrant import ArrestWarrant


class ArrestWarrantRepository:
    COLUMNS = (
        "id",
        "warrant_number",
        "case_number",
        "first_name",
        "last_name",
        "other_names",
        "date_of_birth",
        "gender",
        "nationality",
        "national_id",
        "offense",
        "offense_description",
        "arrest_date",
        "arresting_officer",
        "arresting_agency",
        "court",
        "judge",
        "sentence_type",
        "sentence_duration",
        "status",
        "issued_date",
        "created_at",
        "updated_at",
    )
    INSERT_COLUMNS = tuple(column for column in COLUMNS if column not in {"id", "created_at", "updated_at"})

    @staticmethod
    def create(connection: DatabaseConnection, data: dict[str, Any]) -> ArrestWarrant:
        cursor = connection.cursor(dictionary=True)
        columns = ArrestWarrantRepository.INSERT_COLUMNS
        column_list = ", ".join(f"`{column}`" for column in columns)
        placeholders = ", ".join(f"%({column})s" for column in columns)
        cursor.execute(
            f"INSERT INTO arrest_warrants ({column_list}) VALUES ({placeholders})",
            {column: data.get(column) for column in columns},
        )
        warrant_db_id = cursor.lastrowid
        cursor.execute("SELECT * FROM arrest_warrants WHERE id = %s", (warrant_db_id,))
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            raise RuntimeError("Arrest warrant was created but could not be reloaded")
        return ArrestWarrant.from_row(row)

    @staticmethod
    def update(connection: DatabaseConnection, warrant_db_id: int, updates: dict[str, Any]) -> ArrestWarrant | None:
        cursor = connection.cursor(dictionary=True)
        assignments = ", ".join(f"`{column}` = %({column})s" for column in updates)
        params = dict(updates)
        params["id"] = warrant_db_id
        cursor.execute(f"UPDATE arrest_warrants SET {assignments} WHERE id = %(id)s", params)
        cursor.execute("SELECT * FROM arrest_warrants WHERE id = %s", (warrant_db_id,))
        row = cursor.fetchone()
        cursor.close()
        return ArrestWarrant.from_row(row) if row else None

    @staticmethod
    def delete(connection: DatabaseConnection, warrant_db_id: int) -> bool:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM arrest_warrants WHERE id = %s", (warrant_db_id,))
        deleted = cursor.rowcount > 0
        cursor.close()
        return deleted

    @staticmethod
    def get_by_id(connection: DatabaseConnection, warrant_db_id: int) -> ArrestWarrant | None:
        return ArrestWarrantRepository._get_one(connection, "id", warrant_db_id)

    @staticmethod
    def get_by_warrant_number(connection: DatabaseConnection, warrant_number: str) -> ArrestWarrant | None:
        return ArrestWarrantRepository._get_one(connection, "warrant_number", warrant_number)

    @staticmethod
    def get_by_case_number(connection: DatabaseConnection, case_number: str) -> ArrestWarrant | None:
        return ArrestWarrantRepository._get_one(connection, "case_number", case_number)

    @staticmethod
    def exists_by_warrant_number(connection: DatabaseConnection, warrant_number: str, *, exclude_id: int | None = None) -> bool:
        return ArrestWarrantRepository._exists(connection, "warrant_number", warrant_number, exclude_id=exclude_id)

    @staticmethod
    def exists_by_case_number(connection: DatabaseConnection, case_number: str, *, exclude_id: int | None = None) -> bool:
        return ArrestWarrantRepository._exists(connection, "case_number", case_number, exclude_id=exclude_id)

    @staticmethod
    def list(connection: DatabaseConnection, *, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0) -> list[ArrestWarrant]:
        where_sql, params = _build_filter_clause(filters or {})
        params["limit"] = limit
        params["offset"] = offset
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT *
            FROM arrest_warrants
            {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )
        rows = cursor.fetchall()
        cursor.close()
        return [ArrestWarrant.from_row(row) for row in rows]

    @staticmethod
    def search(connection: DatabaseConnection, *, query: str | None, filters: dict[str, Any], limit: int, offset: int) -> list[ArrestWarrant]:
        where_parts: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if query:
            params["query"] = f"%{query}%"
            where_parts.append(
                """
                (
                    warrant_number LIKE %(query)s OR
                    case_number LIKE %(query)s OR
                    first_name LIKE %(query)s OR
                    last_name LIKE %(query)s OR
                    offense LIKE %(query)s OR
                    status LIKE %(query)s OR
                    sentence_type LIKE %(query)s
                )
                """
            )
        filter_sql, filter_params = _build_filter_clause(filters, leading_where=False)
        if filter_sql:
            where_parts.append(filter_sql)
            params.update(filter_params)
        where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT *
            FROM arrest_warrants
            {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )
        rows = cursor.fetchall()
        cursor.close()
        return [ArrestWarrant.from_row(row) for row in rows]

    @staticmethod
    def _get_one(connection: DatabaseConnection, field: str, value: Any) -> ArrestWarrant | None:
        if field not in {"id", "warrant_number", "case_number"}:
            raise ValueError("Unsupported arrest warrant lookup field")
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM arrest_warrants WHERE `{field}` = %s LIMIT 1", (value,))
        row = cursor.fetchone()
        cursor.close()
        return ArrestWarrant.from_row(row) if row else None

    @staticmethod
    def _exists(connection: DatabaseConnection, field: str, value: Any, *, exclude_id: int | None) -> bool:
        if field not in {"warrant_number", "case_number"}:
            raise ValueError("Unsupported arrest warrant uniqueness field")
        cursor = connection.cursor()
        if exclude_id is None:
            cursor.execute(f"SELECT 1 FROM arrest_warrants WHERE `{field}` = %s LIMIT 1", (value,))
        else:
            cursor.execute(f"SELECT 1 FROM arrest_warrants WHERE `{field}` = %s AND id <> %s LIMIT 1", (value, exclude_id))
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists


def _build_filter_clause(filters: dict[str, Any], *, leading_where: bool = True) -> tuple[str, dict[str, Any]]:
    allowed_filters = {"gender", "nationality", "arrest_date", "issued_date", "status", "sentence_type"}
    where_parts: list[str] = []
    params: dict[str, Any] = {}
    for field, value in filters.items():
        if field not in allowed_filters or value in {None, ""}:
            continue
        where_parts.append(f"`{field}` = %({field})s")
        params[field] = value
    if not where_parts:
        return "", params
    prefix = "WHERE " if leading_where else ""
    return f"{prefix}{' AND '.join(where_parts)}", params
