from __future__ import annotations

from typing import Any

from src.config.database_config import DatabaseConnection
from src.integrations.security import decrypt_sensitive_value, protect_record_payload
from src.models.external_integration import ExternalIntegrationRecord, external_integration_record_from_row


class ExternalIntegrationRepository:
    TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
        "court_integrations": ("id", "inmate_id", "external_case_reference", "court_name", "court_api_source", "warrant_status", "hearing_date", "hearing_status", "sentence_status", "synchronization_status", "last_synced_at", "created_at", "updated_at"),
        "nia_integrations": ("id", "inmate_id", "national_id", "verification_status", "biometric_match_status", "demographic_sync_status", "nia_reference_number", "last_verified_at", "created_at", "updated_at"),
        "police_integrations": ("id", "inmate_id", "police_reference_number", "criminal_record_status", "fingerprint_match_status", "recidivism_status", "wanted_person_status", "intelligence_notes", "synchronization_status", "last_synced_at", "created_at", "updated_at"),
        "biometric_integrations": ("id", "inmate_id", "visitor_id", "staff_id", "biometric_type", "biometric_reference_id", "enrollment_status", "verification_status", "captured_device", "captured_at", "created_at", "updated_at"),
        "api_integrations": ("id", "integration_name", "api_provider", "authentication_type", "endpoint_reference", "api_status", "rate_limit_status", "encryption_enabled", "last_health_check", "created_at", "updated_at"),
        "synchronization_logs": ("id", "source_facility", "target_server", "synchronization_type", "synchronization_status", "records_processed", "records_failed", "retry_count", "last_attempt_at", "completed_at", "error_message", "created_at"),
        "cloud_backup_logs": ("id", "backup_reference", "backup_type", "backup_status", "storage_location", "records_backed_up", "backup_started_at", "backup_completed_at", "recovery_test_status", "created_at"),
    }

    @staticmethod
    def create(connection: DatabaseConnection, table: str, data: dict[str, Any]) -> ExternalIntegrationRecord:
        protected_data = protect_record_payload(table, data)
        columns = _insert_columns(table, protected_data)
        row_id = _insert_row(connection, table, columns, protected_data)
        record = ExternalIntegrationRepository.get_by_id(connection, table, row_id)
        if record is None:
            raise RuntimeError(f"{table} record was created but could not be reloaded")
        return record

    @staticmethod
    def get_by_id(connection: DatabaseConnection, table: str, row_id: int) -> ExternalIntegrationRecord | None:
        _validate_table(table)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table} WHERE id = %s LIMIT 1", (row_id,))
        row = cursor.fetchone()
        cursor.close()
        return external_integration_record_from_row(table, row) if row else None

    @staticmethod
    def list_records(connection: DatabaseConnection, table: str, *, filters: dict[str, Any], limit: int, offset: int) -> list[ExternalIntegrationRecord]:
        _validate_table(table)
        allowed = set(ExternalIntegrationRepository.TABLE_COLUMNS[table])
        where_parts: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        for field, value in filters.items():
            if field not in allowed or value in {None, ""}:
                continue
            where_parts.append(f"`{field}` = %({field})s")
            params[field] = value
        where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        order_by = "updated_at" if "updated_at" in allowed else "created_at"
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table} {where_sql} ORDER BY `{order_by}` DESC, id DESC LIMIT %(limit)s OFFSET %(offset)s", params)
        rows = cursor.fetchall()
        cursor.close()
        return [external_integration_record_from_row(table, row) for row in rows]

    @staticmethod
    def inmate_exists(connection: DatabaseConnection, inmate_id: int) -> bool:
        return _exists(connection, "inmates", "id", inmate_id)

    @staticmethod
    def visitor_exists(connection: DatabaseConnection, visitor_id: int) -> bool:
        return _exists(connection, "visitors", "id", visitor_id)

    @staticmethod
    def user_exists(connection: DatabaseConnection, user_id: int) -> bool:
        return _exists(connection, "users", "id", user_id)

    @staticmethod
    def api_integration_name_exists(connection: DatabaseConnection, integration_name: str) -> bool:
        return _exists(connection, "api_integrations", "integration_name", integration_name)

    @staticmethod
    def backup_reference_exists(connection: DatabaseConnection, backup_reference: str) -> bool:
        cursor = connection.cursor()
        cursor.execute("SELECT backup_reference FROM cloud_backup_logs")
        rows = cursor.fetchall()
        cursor.close()
        return any(decrypt_sensitive_value(row[0]) == backup_reference for row in rows)

    @staticmethod
    def synchronization_duplicate_exists(connection: DatabaseConnection, *, source_facility: str, target_server: str, synchronization_type: str, last_attempt_at) -> bool:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT target_server
            FROM synchronization_logs
            WHERE source_facility = %s
              AND synchronization_type = %s
              AND last_attempt_at = %s
            """,
            (source_facility, synchronization_type, last_attempt_at),
        )
        rows = cursor.fetchall()
        cursor.close()
        return any(decrypt_sensitive_value(row["target_server"]) == target_server for row in rows)

    @staticmethod
    def reports(connection: DatabaseConnection) -> dict[str, Any]:
        return {
            "court_synchronization": _rows(connection, "SELECT synchronization_status, COUNT(*) AS total FROM court_integrations GROUP BY synchronization_status", ()),
            "nia_verifications": _rows(connection, "SELECT verification_status, COUNT(*) AS total FROM nia_integrations GROUP BY verification_status", ()),
            "police_synchronization": _rows(connection, "SELECT synchronization_status, COUNT(*) AS total FROM police_integrations GROUP BY synchronization_status", ()),
            "biometric_verifications": _rows(connection, "SELECT verification_status, COUNT(*) AS total FROM biometric_integrations GROUP BY verification_status", ()),
            "api_gateway_health": _rows(connection, "SELECT api_status, COUNT(*) AS total FROM api_integrations GROUP BY api_status", ()),
            "synchronization_resilience": _rows(connection, "SELECT synchronization_type, synchronization_status, SUM(records_processed) AS records_processed, SUM(records_failed) AS records_failed, SUM(retry_count) AS retry_count FROM synchronization_logs GROUP BY synchronization_type, synchronization_status", ()),
            "cloud_backup_status": _rows(connection, "SELECT backup_type, backup_status, COUNT(*) AS total FROM cloud_backup_logs GROUP BY backup_type, backup_status", ()),
        }


def _validate_table(table: str) -> None:
    if table not in ExternalIntegrationRepository.TABLE_COLUMNS:
        raise ValueError("Unsupported external integration table")


def _insert_columns(table: str, data: dict[str, Any]) -> tuple[str, ...]:
    _validate_table(table)
    return tuple(column for column in ExternalIntegrationRepository.TABLE_COLUMNS[table] if column not in {"id", "created_at", "updated_at"} and column in data)


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


def _exists(connection: DatabaseConnection, table: str, field: str, value: Any) -> bool:
    cursor = connection.cursor()
    cursor.execute(f"SELECT 1 FROM {table} WHERE {field} = %s LIMIT 1", (value,))
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists


def _rows(connection: DatabaseConnection, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    cursor.close()
    return list(rows)
