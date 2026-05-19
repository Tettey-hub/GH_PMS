from __future__ import annotations

from typing import Any

from src.config.database_config import DatabaseConnection
from src.models.inmate import Inmate


class InmateRepository:
    COLUMNS = (
        "id",
        "inmate_id",
        "warrant_id",
        "first_name",
        "last_name",
        "other_names",
        "date_of_birth",
        "age",
        "gender",
        "nationality",
        "national_id",
        "phone",
        "address",
        "marital_status",
        "photo",
        "fingerprint_id",
        "height_cm",
        "weight_kg",
        "eye_color",
        "hair_color",
        "distinguishing_marks",
        "religion",
        "occupation",
        "education_level",
        "next_of_kin_name",
        "next_of_kin_relation",
        "next_of_kin_contact",
        "next_of_kin_address",
        "case_number",
        "offense",
        "offense_description",
        "arrest_date",
        "arresting_officer",
        "arresting_agency",
        "court",
        "judge",
        "sentence_type",
        "sentence_duration",
        "expected_release_date",
        "status",
        "admission_date",
        "admission_time",
        "admission_officer_id",
        "created_at",
        "updated_at",
    )

    INSERT_COLUMNS = tuple(column for column in COLUMNS if column not in {"id", "created_at", "updated_at"})

    @staticmethod
    def create(connection: DatabaseConnection, data: dict[str, Any]) -> Inmate:
        cursor = connection.cursor(dictionary=True)
        columns = InmateRepository.INSERT_COLUMNS
        column_list = ", ".join(f"`{column}`" for column in columns)
        placeholders = ", ".join(f"%({column})s" for column in columns)
        cursor.execute(
            f"INSERT INTO inmates ({column_list}) VALUES ({placeholders})",
            {column: data.get(column) for column in columns},
        )
        inmate_id = cursor.lastrowid
        cursor.execute("SELECT * FROM inmates WHERE id = %s", (inmate_id,))
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            raise RuntimeError("Inmate was created but could not be reloaded")
        return Inmate.from_row(row)

    @staticmethod
    def update(connection: DatabaseConnection, inmate_db_id: int, updates: dict[str, Any]) -> Inmate | None:
        if not updates:
            raise ValueError("No update fields provided")
        cursor = connection.cursor(dictionary=True)
        assignments = ", ".join(f"`{column}` = %({column})s" for column in updates)
        params = dict(updates)
        params["id"] = inmate_db_id
        cursor.execute(f"UPDATE inmates SET {assignments} WHERE id = %(id)s", params)
        cursor.execute("SELECT * FROM inmates WHERE id = %s", (inmate_db_id,))
        row = cursor.fetchone()
        cursor.close()
        return Inmate.from_row(row) if row else None

    @staticmethod
    def delete(connection: DatabaseConnection, inmate_db_id: int) -> bool:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM inmates WHERE id = %s", (inmate_db_id,))
        deleted = cursor.rowcount > 0
        cursor.close()
        return deleted

    @staticmethod
    def get_by_id(connection: DatabaseConnection, inmate_db_id: int) -> Inmate | None:
        return InmateRepository._get_one(connection, "id", inmate_db_id)

    @staticmethod
    def get_by_inmate_id(connection: DatabaseConnection, inmate_id: str) -> Inmate | None:
        return InmateRepository._get_one(connection, "inmate_id", inmate_id)

    @staticmethod
    def exists_by_inmate_id(connection: DatabaseConnection, inmate_id: str, *, exclude_id: int | None = None) -> bool:
        return InmateRepository._exists(connection, "inmate_id", inmate_id, exclude_id=exclude_id)

    @staticmethod
    def exists_by_fingerprint_id(connection: DatabaseConnection, fingerprint_id: str, *, exclude_id: int | None = None) -> bool:
        return InmateRepository._exists(connection, "fingerprint_id", fingerprint_id, exclude_id=exclude_id)

    @staticmethod
    def warrant_exists(connection: DatabaseConnection, warrant_id: int) -> bool:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM arrest_warrants WHERE id = %s LIMIT 1", (warrant_id,))
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists

    @staticmethod
    def user_exists(connection: DatabaseConnection, user_id: int) -> bool:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM users WHERE id = %s LIMIT 1", (user_id,))
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists

    @staticmethod
    def list(connection: DatabaseConnection, *, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0) -> list[Inmate]:
        filters = filters or {}
        where_sql, params = _build_filter_clause(filters)
        params["limit"] = limit
        params["offset"] = offset
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT *
            FROM inmates
            {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )
        rows = cursor.fetchall()
        cursor.close()
        return [Inmate.from_row(row) for row in rows]

    @staticmethod
    def search(connection: DatabaseConnection, *, query: str | None, filters: dict[str, Any], limit: int, offset: int) -> list[Inmate]:
        where_parts: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if query:
            params["query"] = f"%{query}%"
            where_parts.append(
                """
                (
                    inmate_id LIKE %(query)s OR
                    first_name LIKE %(query)s OR
                    last_name LIKE %(query)s OR
                    case_number LIKE %(query)s OR
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
            FROM inmates
            {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )
        rows = cursor.fetchall()
        cursor.close()
        return [Inmate.from_row(row) for row in rows]

    @staticmethod
    def _get_one(connection: DatabaseConnection, field: str, value: Any) -> Inmate | None:
        if field not in {"id", "inmate_id"}:
            raise ValueError("Unsupported inmate lookup field")
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM inmates WHERE `{field}` = %s LIMIT 1", (value,))
        row = cursor.fetchone()
        cursor.close()
        return Inmate.from_row(row) if row else None

    @staticmethod
    def _exists(connection: DatabaseConnection, field: str, value: Any, *, exclude_id: int | None) -> bool:
        if field not in {"inmate_id", "fingerprint_id"}:
            raise ValueError("Unsupported uniqueness field")
        cursor = connection.cursor()
        if exclude_id is None:
            cursor.execute(f"SELECT 1 FROM inmates WHERE `{field}` = %s LIMIT 1", (value,))
        else:
            cursor.execute(f"SELECT 1 FROM inmates WHERE `{field}` = %s AND id <> %s LIMIT 1", (value, exclude_id))
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists


def _build_filter_clause(filters: dict[str, Any], *, leading_where: bool = True) -> tuple[str, dict[str, Any]]:
    allowed_filters = {"gender", "nationality", "admission_date", "arrest_date", "status", "sentence_type"}
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
