from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.database_config import db_connection


SCHEMA_DIR = PROJECT_ROOT / "src" / "schemas"
USERS_SCHEMA_FILE = SCHEMA_DIR / "users.sql"
AUTH_REFRESH_TOKENS_SCHEMA_FILE = SCHEMA_DIR / "auth_refresh_tokens.sql"
RATE_LIMITS_SCHEMA_FILE = SCHEMA_DIR / "rate_limits.sql"
AUTH_ACCOUNT_LOCKOUTS_SCHEMA_FILE = SCHEMA_DIR / "auth_account_lockouts.sql"
AUDIT_LOGS_SCHEMA_FILE = SCHEMA_DIR / "audit_logs.sql"


TARGET_USER_COLUMNS = {
    "id",
    "officer_id",
    "first_name",
    "last_name",
    "email",
    "password",
    "phone",
    "badge_number",
    "rank",
    "department",
    "role",
    "shift",
    "status",
    "date_joined",
    "created_at",
    "updated_at",
}

TARGET_AUDIT_LOG_COLUMNS = {
    "id",
    "actor_user_id",
    "target_user_id",
    "action",
    "status",
    "ip_hash",
    "user_agent",
    "metadata",
    "created_at",
}

LEGACY_USER_COLUMNS = {
    "id",
    "username",
    "email",
    "password_hash",
    "full_name",
    "role",
    "is_active",
    "created_at",
    "updated_at",
}


def create_tables() -> None:
    users_table_sql = _read_schema_sql(USERS_SCHEMA_FILE)
    auth_refresh_tokens_sql = _read_schema_sql(AUTH_REFRESH_TOKENS_SCHEMA_FILE)
    rate_limits_sql = _read_schema_sql(RATE_LIMITS_SCHEMA_FILE)
    auth_account_lockouts_sql = _read_schema_sql(AUTH_ACCOUNT_LOCKOUTS_SCHEMA_FILE)
    audit_logs_sql = _read_schema_sql(AUDIT_LOGS_SCHEMA_FILE)

    with db_connection() as connection:
        cursor = connection.cursor()
        _ensure_users_table(connection, cursor, users_table_sql)
        cursor.execute(auth_refresh_tokens_sql)
        cursor.execute(rate_limits_sql)
        cursor.execute(auth_account_lockouts_sql)
        _ensure_audit_logs_table(cursor, audit_logs_sql)
        connection.commit()
        cursor.close()

    print("Database tables created successfully.")


def _read_schema_sql(schema_file: Path) -> str:
    if not schema_file.exists():
        raise FileNotFoundError(f"Missing schema file: {schema_file}")
    return schema_file.read_text(encoding="utf-8")


def _ensure_users_table(connection, cursor, users_table_sql: str) -> None:
    existing_columns = _get_table_columns(cursor, "users")
    if not existing_columns:
        cursor.execute(users_table_sql)
        return

    if TARGET_USER_COLUMNS.issubset(existing_columns):
        return

    if LEGACY_USER_COLUMNS.issubset(existing_columns):
        _migrate_legacy_users_table(connection, cursor, users_table_sql)
        return

    missing_columns = sorted(TARGET_USER_COLUMNS - existing_columns)
    raise RuntimeError(
        "Existing users table does not match the required prison-officer schema. "
        f"Missing columns: {', '.join(missing_columns)}"
    )


def _get_table_columns(cursor, table_name: str) -> set[str]:
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = %s
        """,
        (table_name,),
    )
    return {row[0] for row in cursor.fetchall()}


def _ensure_audit_logs_table(cursor, audit_logs_sql: str) -> None:
    existing_columns = _get_table_columns(cursor, "audit_logs")
    if not existing_columns:
        cursor.execute(audit_logs_sql)
        return

    if TARGET_AUDIT_LOG_COLUMNS.issubset(existing_columns):
        return

    cursor.execute("SELECT COUNT(*) FROM audit_logs")
    row_count = cursor.fetchone()[0]
    if row_count == 0:
        cursor.execute("DROP TABLE audit_logs")
        cursor.execute(audit_logs_sql)
        return

    backup_table = f"audit_logs_legacy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    cursor.execute(f"RENAME TABLE audit_logs TO {backup_table}")
    cursor.execute(audit_logs_sql)
    print(f"Legacy audit_logs table backed up as {backup_table}.")


def _migrate_legacy_users_table(connection, cursor, users_table_sql: str) -> None:
    backup_table = f"users_legacy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    cursor.execute("DROP TABLE IF EXISTS users_new")
    cursor.execute(users_table_sql.replace("users", "users_new", 1))
    cursor.execute(
        """
        INSERT INTO users_new (
            id,
            officer_id,
            first_name,
            last_name,
            email,
            password,
            phone,
            badge_number,
            `rank`,
            department,
            role,
            shift,
            status,
            date_joined,
            created_at,
            updated_at
        )
        SELECT
            id,
            CONCAT('OFF', LPAD(id, 3, '0')) AS officer_id,
            SUBSTRING_INDEX(TRIM(COALESCE(username, full_name, 'Officer')), ' ', 1) AS first_name,
            CASE
                WHEN LOCATE(' ', TRIM(COALESCE(username, full_name, 'Officer'))) > 0
                    THEN SUBSTRING(TRIM(COALESCE(username, full_name, 'Officer')), LOCATE(' ', TRIM(COALESCE(username, full_name, 'Officer'))) + 1)
                ELSE 'Officer'
            END AS last_name,
            email,
            password_hash AS password,
            NULL AS phone,
            CONCAT('BADGE', LPAD(id, 3, '0')) AS badge_number,
            COALESCE(NULLIF(role, ''), 'Officer') AS `rank`,
            'Administration' AS department,
            CASE
                WHEN LOWER(role) IN ('admin', 'officer', 'supervisor') THEN LOWER(role)
                ELSE 'officer'
            END AS role,
            'morning' AS shift,
            CASE WHEN is_active = 1 THEN 'active' ELSE 'inactive' END AS status,
            DATE(created_at) AS date_joined,
            created_at,
            updated_at
        FROM users
        """
    )
    cursor.execute(f"RENAME TABLE users TO {backup_table}, users_new TO users")
    connection.commit()
    print(f"Legacy users table backed up as {backup_table}.")


if __name__ == "__main__":
    create_tables()
