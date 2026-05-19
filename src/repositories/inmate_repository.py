from __future__ import annotations

from typing import Any

from src.config.database_config import DatabaseConnection
from src.models.inmate import Inmate, InmateRelease, InmateTransfer


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
    TRANSFER_COLUMNS = (
        "id",
        "inmate_id",
        "current_facility",
        "destination_facility",
        "transfer_type",
        "reason",
        "security_level",
        "medical_clearance",
        "legal_verified",
        "security_assessed",
        "transfer_status",
        "urgency_level",
        "requested_date",
        "departure_date",
        "arrival_date",
        "escort_officers",
        "transport_vehicle",
        "route_details",
        "movement_authorized_by",
        "approved_by",
        "receiving_officer",
        "receiving_confirmation",
        "transfer_completion_notes",
        "created_by",
        "created_at",
        "updated_at",
    )
    RELEASE_COLUMNS = (
        "id",
        "inmate_id",
        "release_type",
        "release_reason",
        "sentence_validated",
        "legal_verified",
        "medical_cleared",
        "property_cleared",
        "identity_verified",
        "release_certificate_number",
        "approved_by",
        "release_date",
        "release_time",
        "release_status",
        "discharge_notes",
        "property_release_notes",
        "medical_discharge_summary",
        "created_by",
        "created_at",
        "updated_at",
    )

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
    def create_transfer(connection: DatabaseConnection, data: dict[str, Any]) -> InmateTransfer:
        columns = tuple(column for column in InmateRepository.TRANSFER_COLUMNS if column not in {"id", "created_at", "updated_at"} and column in data)
        transfer_id = _insert_row(connection, "inmate_transfers", columns, data)
        transfer = InmateRepository.get_transfer_by_id(connection, transfer_id)
        if transfer is None:
            raise RuntimeError("Transfer was created but could not be reloaded")
        return transfer

    @staticmethod
    def update_transfer(connection: DatabaseConnection, transfer_id: int, updates: dict[str, Any]) -> InmateTransfer | None:
        _update_row(connection, "inmate_transfers", transfer_id, updates, set(InmateRepository.TRANSFER_COLUMNS))
        return InmateRepository.get_transfer_by_id(connection, transfer_id)

    @staticmethod
    def get_transfer_by_id(connection: DatabaseConnection, transfer_id: int) -> InmateTransfer | None:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM inmate_transfers WHERE id = %s LIMIT 1", (transfer_id,))
        row = cursor.fetchone()
        cursor.close()
        return InmateTransfer.from_row(row) if row else None

    @staticmethod
    def list_transfers(connection: DatabaseConnection, *, filters: dict[str, Any], limit: int, offset: int) -> list[InmateTransfer]:
        where_sql, params = _build_transfer_filter_clause(filters)
        params["limit"] = limit
        params["offset"] = offset
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT *
            FROM inmate_transfers
            {where_sql}
            ORDER BY requested_date DESC, id DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )
        rows = cursor.fetchall()
        cursor.close()
        return [InmateTransfer.from_row(row) for row in rows]

    @staticmethod
    def transfer_report(connection: DatabaseConnection) -> list[dict[str, Any]]:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT transfer_type, transfer_status, urgency_level, COUNT(*) AS total
            FROM inmate_transfers
            GROUP BY transfer_type, transfer_status, urgency_level
            ORDER BY total DESC, transfer_type
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return list(rows)

    @staticmethod
    def create_release(connection: DatabaseConnection, data: dict[str, Any]) -> InmateRelease:
        columns = tuple(column for column in InmateRepository.RELEASE_COLUMNS if column not in {"id", "created_at", "updated_at"} and column in data)
        release_id = _insert_row(connection, "inmate_releases", columns, data)
        release = InmateRepository.get_release_by_id(connection, release_id)
        if release is None:
            raise RuntimeError("Release was created but could not be reloaded")
        return release

    @staticmethod
    def update_release(connection: DatabaseConnection, release_id: int, updates: dict[str, Any]) -> InmateRelease | None:
        _update_row(connection, "inmate_releases", release_id, updates, set(InmateRepository.RELEASE_COLUMNS))
        return InmateRepository.get_release_by_id(connection, release_id)

    @staticmethod
    def get_release_by_id(connection: DatabaseConnection, release_id: int) -> InmateRelease | None:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM inmate_releases WHERE id = %s LIMIT 1", (release_id,))
        row = cursor.fetchone()
        cursor.close()
        return InmateRelease.from_row(row) if row else None

    @staticmethod
    def list_releases(connection: DatabaseConnection, *, filters: dict[str, Any], limit: int, offset: int) -> list[InmateRelease]:
        where_sql, params = _build_release_filter_clause(filters)
        params["limit"] = limit
        params["offset"] = offset
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT *
            FROM inmate_releases
            {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )
        rows = cursor.fetchall()
        cursor.close()
        return [InmateRelease.from_row(row) for row in rows]

    @staticmethod
    def release_report(connection: DatabaseConnection) -> list[dict[str, Any]]:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT release_type, release_status, COUNT(*) AS total
            FROM inmate_releases
            GROUP BY release_type, release_status
            ORDER BY total DESC, release_type
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return list(rows)

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


def _insert_row(connection: DatabaseConnection, table: str, columns: tuple[str, ...], data: dict[str, Any]) -> int:
    if not columns:
        raise ValueError("No insert fields provided")
    cursor = connection.cursor()
    column_list = ", ".join(f"`{column}`" for column in columns)
    placeholders = ", ".join(f"%({column})s" for column in columns)
    cursor.execute(f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})", {column: data.get(column) for column in columns})
    row_id = int(cursor.lastrowid)
    cursor.close()
    return row_id


def _update_row(connection: DatabaseConnection, table: str, row_id: int, updates: dict[str, Any], allowed_columns: set[str]) -> None:
    if not updates:
        raise ValueError("No update fields provided")
    invalid = set(updates) - (allowed_columns - {"id", "created_at", "updated_at", "created_by", "inmate_id"})
    if invalid:
        raise ValueError(f"Unsupported update fields: {', '.join(sorted(invalid))}")
    assignments = ", ".join(f"`{column}` = %({column})s" for column in updates)
    params = dict(updates)
    params["id"] = row_id
    cursor = connection.cursor()
    cursor.execute(f"UPDATE {table} SET {assignments} WHERE id = %(id)s", params)
    cursor.close()


def _build_transfer_filter_clause(filters: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    allowed_exact = {"inmate_id", "transfer_type", "transfer_status", "approved_by"}
    where_parts: list[str] = []
    params: dict[str, Any] = {}
    for field in allowed_exact:
        value = filters.get(field)
        if value not in {None, ""}:
            where_parts.append(f"`{field}` = %({field})s")
            params[field] = value
    facility = filters.get("facility")
    if facility not in {None, ""}:
        where_parts.append("(current_facility LIKE %(facility)s OR destination_facility LIKE %(facility)s)")
        params["facility"] = f"%{facility}%"
    _date_range_clause(where_parts, params, filters, "requested_date")
    return (f"WHERE {' AND '.join(where_parts)}" if where_parts else "", params)


def _build_release_filter_clause(filters: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    allowed_exact = {"inmate_id", "release_type", "release_status", "approved_by"}
    where_parts: list[str] = []
    params: dict[str, Any] = {}
    for field in allowed_exact:
        value = filters.get(field)
        if value not in {None, ""}:
            where_parts.append(f"`{field}` = %({field})s")
            params[field] = value
    _date_range_clause(where_parts, params, filters, "release_date")
    return (f"WHERE {' AND '.join(where_parts)}" if where_parts else "", params)


def _date_range_clause(where_parts: list[str], params: dict[str, Any], filters: dict[str, Any], field: str) -> None:
    date_from = filters.get("date_from")
    date_to = filters.get("date_to")
    if date_from not in {None, ""}:
        where_parts.append(f"`{field}` >= %(date_from)s")
        params["date_from"] = date_from
    if date_to not in {None, ""}:
        where_parts.append(f"`{field}` <= %(date_to)s")
        params["date_to"] = date_to
