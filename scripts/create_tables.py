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
PERMISSIONS_SCHEMA_FILE = SCHEMA_DIR / "permissions.sql"
ARREST_WARRANTS_SCHEMA_FILE = SCHEMA_DIR / "arrest_warrants.sql"
INMATES_SCHEMA_FILE = SCHEMA_DIR / "inmates.sql"


TARGET_USER_COLUMNS = {
    "id",
    "officer_id",
    "first_name",
    "middle_name",
    "last_name",
    "gender",
    "dob",
    "email",
    "password",
    "phone",
    "national_id",
    "address",
    "profile_image",
    "staff_id",
    "badge_number",
    "rank",
    "department",
    "position",
    "employment_date",
    "branch",
    "username",
    "role_id",
    "role",
    "shift",
    "status",
    "date_joined",
    "created_at",
    "updated_at",
}

USER_SCHEMA_ADDITIVE_COLUMNS = {
    "middle_name": "ADD COLUMN middle_name VARCHAR(50) NULL AFTER first_name",
    "gender": "ADD COLUMN gender VARCHAR(20) NULL AFTER last_name",
    "dob": "ADD COLUMN dob DATE NULL AFTER gender",
    "national_id": "ADD COLUMN national_id VARCHAR(50) NULL AFTER phone",
    "address": "ADD COLUMN address TEXT NULL AFTER national_id",
    "profile_image": "ADD COLUMN profile_image VARCHAR(255) NULL AFTER address",
    "staff_id": "ADD COLUMN staff_id VARCHAR(50) NULL AFTER profile_image",
    "position": "ADD COLUMN position VARCHAR(100) NULL AFTER department",
    "employment_date": "ADD COLUMN employment_date DATE NULL AFTER position",
    "branch": "ADD COLUMN branch VARCHAR(100) NULL AFTER employment_date",
    "username": "ADD COLUMN username VARCHAR(100) NULL AFTER branch",
    "role_id": "ADD COLUMN role_id INT NULL AFTER username",
}

USER_SCHEMA_INDEXES = {
    "idx_users_national_id": "CREATE INDEX idx_users_national_id ON users (national_id)",
    "idx_users_staff_id": "CREATE INDEX idx_users_staff_id ON users (staff_id)",
    "idx_users_username": "CREATE INDEX idx_users_username ON users (username)",
    "idx_users_role_id": "CREATE INDEX idx_users_role_id ON users (role_id)",
}

USER_ROLE_CHECK_SQL = (
    "CONSTRAINT chk_users_role CHECK "
    "(role IN ('admin', 'officer', 'supervisor', 'medical_officer', 'records_officer', 'visitor_officer'))"
)

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

TARGET_ARREST_WARRANT_COLUMNS = {
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
}

TARGET_INMATE_COLUMNS = {
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
    permissions_sql = _read_schema_sql(PERMISSIONS_SCHEMA_FILE)
    arrest_warrants_sql = _read_schema_sql(ARREST_WARRANTS_SCHEMA_FILE)
    inmates_sql = _read_schema_sql(INMATES_SCHEMA_FILE)

    with db_connection() as connection:
        cursor = connection.cursor()
        _ensure_users_table(connection, cursor, users_table_sql)
        cursor.execute(auth_refresh_tokens_sql)
        cursor.execute(rate_limits_sql)
        cursor.execute(auth_account_lockouts_sql)
        _ensure_audit_logs_table(cursor, audit_logs_sql)
        _execute_schema_statements(cursor, permissions_sql)
        _ensure_arrest_warrants_table(cursor, arrest_warrants_sql)
        _ensure_inmates_table(cursor, inmates_sql)
        connection.commit()
        cursor.close()

    print("Database tables created successfully.")


def _read_schema_sql(schema_file: Path) -> str:
    if not schema_file.exists():
        raise FileNotFoundError(f"Missing schema file: {schema_file}")
    return schema_file.read_text(encoding="utf-8")


def _execute_schema_statements(cursor, schema_sql: str) -> None:
    for statement in schema_sql.split(";"):
        statement = statement.strip()
        if statement:
            cursor.execute(statement)


def _ensure_users_table(connection, cursor, users_table_sql: str) -> None:
    existing_columns = _get_table_columns(cursor, "users")
    if not existing_columns:
        cursor.execute(users_table_sql)
        return

    if TARGET_USER_COLUMNS.issubset(existing_columns):
        _ensure_user_indexes(cursor)
        _ensure_user_role_constraint(cursor)
        return

    if LEGACY_USER_COLUMNS.issubset(existing_columns):
        _migrate_legacy_users_table(connection, cursor, users_table_sql)
        return

    missing_columns = sorted(TARGET_USER_COLUMNS - existing_columns)
    if set(missing_columns).issubset(USER_SCHEMA_ADDITIVE_COLUMNS):
        for column in USER_SCHEMA_ADDITIVE_COLUMNS:
            if column not in missing_columns:
                continue
            cursor.execute(f"ALTER TABLE users {USER_SCHEMA_ADDITIVE_COLUMNS[column]}")
        _ensure_user_indexes(cursor)
        _ensure_user_role_constraint(cursor)
        return

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


def _ensure_user_indexes(cursor) -> None:
    cursor.execute(
        """
        SELECT INDEX_NAME
        FROM information_schema.statistics
        WHERE table_schema = DATABASE() AND table_name = 'users'
        """
    )
    existing_indexes = {row[0] for row in cursor.fetchall()}
    for index_name, index_sql in USER_SCHEMA_INDEXES.items():
        if index_name not in existing_indexes:
            cursor.execute(index_sql)


def _ensure_user_role_constraint(cursor) -> None:
    cursor.execute(
        """
        SELECT CHECK_CLAUSE
        FROM information_schema.check_constraints
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND CONSTRAINT_NAME = 'chk_users_role'
        """
    )
    row = cursor.fetchone()
    check_clause = row[0].lower() if row else ""
    expected_roles = {
        "admin",
        "officer",
        "supervisor",
        "medical_officer",
        "records_officer",
        "visitor_officer",
    }
    if expected_roles.issubset({role for role in expected_roles if role in check_clause}):
        return

    if row:
        cursor.execute("ALTER TABLE users DROP CHECK chk_users_role")
    cursor.execute(f"ALTER TABLE users ADD {USER_ROLE_CHECK_SQL}")


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


def _ensure_arrest_warrants_table(cursor, arrest_warrants_sql: str) -> None:
    existing_columns = _get_table_columns(cursor, "arrest_warrants")
    if not existing_columns:
        cursor.execute(arrest_warrants_sql)
        return

    if TARGET_ARREST_WARRANT_COLUMNS.issubset(existing_columns):
        return

    missing_columns = sorted(TARGET_ARREST_WARRANT_COLUMNS - existing_columns)
    raise RuntimeError(
        "Existing arrest_warrants table does not match the required arrest warrant schema. "
        f"Missing columns: {', '.join(missing_columns)}"
    )


def _ensure_inmates_table(cursor, inmates_sql: str) -> None:
    if not _table_exists(cursor, "arrest_warrants"):
        raise RuntimeError("Cannot create inmates table because arrest_warrants table does not exist.")

    existing_columns = _get_table_columns(cursor, "inmates")
    if not existing_columns:
        cursor.execute(inmates_sql)
        return

    if TARGET_INMATE_COLUMNS.issubset(existing_columns):
        return

    missing_columns = sorted(TARGET_INMATE_COLUMNS - existing_columns)
    raise RuntimeError(
        "Existing inmates table does not match the required inmate schema. "
        f"Missing columns: {', '.join(missing_columns)}"
    )


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = DATABASE() AND table_name = %s
        LIMIT 1
        """,
        (table_name,),
    )
    return cursor.fetchone() is not None


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
            middle_name,
            last_name,
            gender,
            dob,
            email,
            password,
            phone,
            national_id,
            address,
            profile_image,
            staff_id,
            badge_number,
            `rank`,
            department,
            position,
            employment_date,
            branch,
            username,
            role_id,
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
            NULL AS middle_name,
            CASE
                WHEN LOCATE(' ', TRIM(COALESCE(username, full_name, 'Officer'))) > 0
                    THEN SUBSTRING(TRIM(COALESCE(username, full_name, 'Officer')), LOCATE(' ', TRIM(COALESCE(username, full_name, 'Officer'))) + 1)
                ELSE 'Officer'
            END AS last_name,
            NULL AS gender,
            NULL AS dob,
            email,
            password_hash AS password,
            NULL AS phone,
            NULL AS national_id,
            NULL AS address,
            NULL AS profile_image,
            NULL AS staff_id,
            CONCAT('BADGE', LPAD(id, 3, '0')) AS badge_number,
            COALESCE(NULLIF(role, ''), 'Officer') AS `rank`,
            'Administration' AS department,
            NULL AS position,
            NULL AS employment_date,
            NULL AS branch,
            username,
            NULL AS role_id,
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
