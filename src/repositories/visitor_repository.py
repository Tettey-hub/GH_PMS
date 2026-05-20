from __future__ import annotations

from typing import Any

from src.config.database_config import DatabaseConnection
from src.models.visitor import Visitor, VisitorCheckin, VisitorRecord, VisitorRequest, VisitorSchedule, visitor_record_from_row


class VisitorRepository:
    TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
        "visitors": ("id", "visitor_id", "first_name", "last_name", "other_names", "gender", "date_of_birth", "nationality", "national_id", "phone", "email", "address", "relationship_to_inmate", "occupation", "photo", "biometric_id", "blacklist_status", "blacklist_reason", "verification_status", "created_by", "created_at", "updated_at"),
        "visitor_requests": ("id", "visitor_id", "inmate_id", "requested_visit_date", "requested_time_slot", "purpose_of_visit", "visit_type", "approval_status", "reviewed_by", "review_notes", "approved_date", "rescheduled_date", "created_at", "updated_at"),
        "visitor_verifications": ("id", "visitor_id", "national_id_verified", "biometric_verified", "blacklist_checked", "security_screening_status", "verification_notes", "verified_by", "verification_date", "created_at"),
        "visitor_schedules": ("id", "visitor_request_id", "visit_date", "start_time", "end_time", "visit_duration_minutes", "visit_room", "daily_capacity_slot", "scheduling_status", "scheduled_by", "created_at", "updated_at"),
        "visitor_checkins": ("id", "visitor_schedule_id", "inmate_id", "arrival_time", "exit_time", "security_clearance_status", "belongings_checked", "handled_by", "checkin_notes", "checkout_notes", "created_at"),
        "visitor_monitoring_logs": ("id", "visitor_id", "inmate_id", "suspicious_activity", "monitoring_level", "officer_notes", "action_taken", "monitored_by", "monitoring_date", "created_at"),
        "visitor_violations": ("id", "visitor_id", "violation_type", "violation_description", "action_taken", "violation_severity", "reported_by", "violation_date", "created_at"),
    }

    @staticmethod
    def create(connection: DatabaseConnection, table: str, data: dict[str, Any]) -> VisitorRecord:
        columns = _insert_columns(table, data)
        row_id = _insert_row(connection, table, columns, data)
        record = VisitorRepository.get_by_id(connection, table, row_id)
        if record is None:
            raise RuntimeError(f"{table} record was created but could not be reloaded")
        return record

    @staticmethod
    def update(connection: DatabaseConnection, table: str, row_id: int, updates: dict[str, Any]) -> VisitorRecord | None:
        _validate_table(table)
        _update_row(connection, table, row_id, updates, set(VisitorRepository.TABLE_COLUMNS[table]))
        return VisitorRepository.get_by_id(connection, table, row_id)

    @staticmethod
    def get_by_id(connection: DatabaseConnection, table: str, row_id: int) -> VisitorRecord | None:
        _validate_table(table)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table} WHERE id = %s LIMIT 1", (row_id,))
        row = cursor.fetchone()
        cursor.close()
        return visitor_record_from_row(table, row) if row else None

    @staticmethod
    def get_visitor_by_national_id(connection: DatabaseConnection, national_id: str) -> Visitor | None:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM visitors WHERE national_id = %s LIMIT 1", (national_id,))
        row = cursor.fetchone()
        cursor.close()
        return Visitor.from_row(row) if row else None

    @staticmethod
    def visitor_id_exists(connection: DatabaseConnection, visitor_id: str, *, exclude_id: int | None = None) -> bool:
        return _exists(connection, "visitors", "visitor_id", visitor_id, exclude_id=exclude_id)

    @staticmethod
    def national_id_exists(connection: DatabaseConnection, national_id: str, *, exclude_id: int | None = None) -> bool:
        return _exists(connection, "visitors", "national_id", national_id, exclude_id=exclude_id)

    @staticmethod
    def inmate_exists(connection: DatabaseConnection, inmate_id: int) -> bool:
        return _exists_simple(connection, "inmates", "id", inmate_id)

    @staticmethod
    def user_exists(connection: DatabaseConnection, user_id: int) -> bool:
        return _exists_simple(connection, "users", "id", user_id)

    @staticmethod
    def latest_verification(connection: DatabaseConnection, visitor_id: int):
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM visitor_verifications WHERE visitor_id = %s ORDER BY verification_date DESC, id DESC LIMIT 1", (visitor_id,))
        row = cursor.fetchone()
        cursor.close()
        return visitor_record_from_row("visitor_verifications", row) if row else None

    @staticmethod
    def get_request(connection: DatabaseConnection, request_id: int) -> VisitorRequest | None:
        record = VisitorRepository.get_by_id(connection, "visitor_requests", request_id)
        return record if isinstance(record, VisitorRequest) else None

    @staticmethod
    def get_schedule(connection: DatabaseConnection, schedule_id: int) -> VisitorSchedule | None:
        record = VisitorRepository.get_by_id(connection, "visitor_schedules", schedule_id)
        return record if isinstance(record, VisitorSchedule) else None

    @staticmethod
    def get_checkin(connection: DatabaseConnection, checkin_id: int) -> VisitorCheckin | None:
        record = VisitorRepository.get_by_id(connection, "visitor_checkins", checkin_id)
        return record if isinstance(record, VisitorCheckin) else None

    @staticmethod
    def schedule_has_overlap(connection: DatabaseConnection, *, visit_date, visit_room: str, start_time, end_time) -> bool:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM visitor_schedules
            WHERE visit_date = %s
              AND visit_room = %s
              AND scheduling_status = 'SCHEDULED'
              AND start_time < %s
              AND end_time > %s
            LIMIT 1
            """,
            (visit_date, visit_room, end_time, start_time),
        )
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists

    @staticmethod
    def schedule_slot_used(connection: DatabaseConnection, *, visit_date, daily_capacity_slot: int) -> bool:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM visitor_schedules
            WHERE visit_date = %s AND daily_capacity_slot = %s AND scheduling_status = 'SCHEDULED'
            LIMIT 1
            """,
            (visit_date, daily_capacity_slot),
        )
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists

    @staticmethod
    def active_checkin_for_schedule(connection: DatabaseConnection, schedule_id: int) -> bool:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM visitor_checkins WHERE visitor_schedule_id = %s AND exit_time IS NULL LIMIT 1", (schedule_id,))
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists

    @staticmethod
    def visitor_history(connection: DatabaseConnection, visitor_id: int) -> dict[str, list[dict[str, Any]]]:
        return {
            "requests": _rows(connection, "SELECT * FROM visitor_requests WHERE visitor_id = %s ORDER BY created_at DESC, id DESC", (visitor_id,)),
            "verifications": _rows(connection, "SELECT * FROM visitor_verifications WHERE visitor_id = %s ORDER BY verification_date DESC, id DESC", (visitor_id,)),
            "monitoring_logs": _rows(connection, "SELECT * FROM visitor_monitoring_logs WHERE visitor_id = %s ORDER BY monitoring_date DESC, id DESC", (visitor_id,)),
            "violations": _rows(connection, "SELECT * FROM visitor_violations WHERE visitor_id = %s ORDER BY violation_date DESC, id DESC", (visitor_id,)),
        }

    @staticmethod
    def search_visitors(connection: DatabaseConnection, *, filters: dict[str, Any], limit: int, offset: int) -> list[Visitor]:
        where_parts: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        for field in ("relationship_to_inmate", "verification_status", "blacklist_status"):
            value = filters.get(field)
            if value not in {None, ""}:
                where_parts.append(f"{field} = %({field})s")
                params[field] = value
        query = filters.get("q")
        if query:
            where_parts.append("(visitor_id LIKE %(q)s OR first_name LIKE %(q)s OR last_name LIKE %(q)s OR national_id LIKE %(q)s OR phone LIKE %(q)s)")
            params["q"] = f"%{query}%"
        where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM visitors {where_sql} ORDER BY created_at DESC, id DESC LIMIT %(limit)s OFFSET %(offset)s", params)
        rows = cursor.fetchall()
        cursor.close()
        return [Visitor.from_row(row) for row in rows]

    @staticmethod
    def reports(connection: DatabaseConnection) -> dict[str, Any]:
        return {
            "daily_visitor_reports": _rows(connection, "SELECT visit_date, COUNT(*) AS total FROM visitor_schedules GROUP BY visit_date ORDER BY visit_date DESC", ()),
            "visitor_violation_reports": _rows(connection, "SELECT violation_severity, COUNT(*) AS total FROM visitor_violations GROUP BY violation_severity", ()),
            "suspicious_visitor_reports": _rows(connection, "SELECT monitoring_level, COUNT(*) AS total FROM visitor_monitoring_logs GROUP BY monitoring_level", ()),
            "blacklist_reports": _rows(connection, "SELECT blacklist_status, COUNT(*) AS total FROM visitors GROUP BY blacklist_status", ()),
            "visitation_frequency_reports": _rows(connection, "SELECT visitor_id, COUNT(*) AS total FROM visitor_requests GROUP BY visitor_id ORDER BY total DESC", ()),
            "inmate_visitation_reports": _rows(connection, "SELECT inmate_id, COUNT(*) AS total FROM visitor_requests GROUP BY inmate_id ORDER BY total DESC", ()),
        }


def _validate_table(table: str) -> None:
    if table not in VisitorRepository.TABLE_COLUMNS:
        raise ValueError("Unsupported visitor table")


def _insert_columns(table: str, data: dict[str, Any]) -> tuple[str, ...]:
    _validate_table(table)
    return tuple(column for column in VisitorRepository.TABLE_COLUMNS[table] if column not in {"id", "created_at", "updated_at"} and column in data)


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
    invalid = set(updates) - (allowed_columns - {"id", "created_at", "updated_at"})
    if invalid:
        raise ValueError(f"Unsupported update fields: {', '.join(sorted(invalid))}")
    assignments = ", ".join(f"`{column}` = %({column})s" for column in updates)
    params = dict(updates)
    params["id"] = row_id
    cursor = connection.cursor()
    cursor.execute(f"UPDATE {table} SET {assignments} WHERE id = %(id)s", params)
    cursor.close()


def _exists(connection: DatabaseConnection, table: str, field: str, value: Any, *, exclude_id: int | None) -> bool:
    cursor = connection.cursor()
    if exclude_id is None:
        cursor.execute(f"SELECT 1 FROM {table} WHERE {field} = %s LIMIT 1", (value,))
    else:
        cursor.execute(f"SELECT 1 FROM {table} WHERE {field} = %s AND id <> %s LIMIT 1", (value, exclude_id))
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists


def _exists_simple(connection: DatabaseConnection, table: str, field: str, value: Any) -> bool:
    return _exists(connection, table, field, value, exclude_id=None)


def _rows(connection: DatabaseConnection, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    cursor.close()
    return list(rows)
