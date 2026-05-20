from __future__ import annotations

from typing import Any

from src.config.database_config import DatabaseConnection
from src.models.rehabilitation import RehabilitationRecord, rehabilitation_record_from_row


class RehabilitationRepository:
    TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
        "vocational_training_enrollments": ("id", "inmate_id", "program_name", "skill_category", "training_center", "instructor_name", "enrollment_date", "completion_status", "progress_percentage", "assessment_score", "certification_eligible", "created_by", "created_at", "updated_at"),
        "counseling_sessions": ("id", "inmate_id", "counselor_name", "session_type", "session_date", "session_notes", "behavioral_observation", "risk_level", "follow_up_required", "created_by", "created_at"),
        "behavioral_assessments": ("id", "inmate_id", "behavior_score", "behavior_category", "observation_notes", "incident_count", "improvement_level", "assessed_by", "assessment_date", "created_at"),
        "religious_participations": ("id", "inmate_id", "religion", "activity_type", "participation_date", "attendance_status", "religious_leader", "notes", "created_at"),
        "work_assignments": ("id", "inmate_id", "work_type", "assignment_location", "supervisor_name", "start_date", "end_date", "performance_rating", "attendance_record", "created_at"),
        "skill_certifications": ("id", "inmate_id", "certification_name", "skill_area", "issuing_authority", "issue_date", "certificate_number", "grade", "validity_status", "created_at"),
        "post_release_followups": ("id", "inmate_id", "release_date", "follow_up_date", "employment_status", "housing_status", "reintegration_score", "recidivism_risk_level", "notes", "created_at"),
    }

    @staticmethod
    def create(connection: DatabaseConnection, table: str, data: dict[str, Any]) -> RehabilitationRecord:
        columns = _insert_columns(table, data)
        row_id = _insert_row(connection, table, columns, data)
        record = RehabilitationRepository.get_by_id(connection, table, row_id)
        if record is None:
            raise RuntimeError(f"{table} record was created but could not be reloaded")
        return record

    @staticmethod
    def get_by_id(connection: DatabaseConnection, table: str, row_id: int) -> RehabilitationRecord | None:
        _validate_table(table)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table} WHERE id = %s LIMIT 1", (row_id,))
        row = cursor.fetchone()
        cursor.close()
        return rehabilitation_record_from_row(table, row) if row else None

    @staticmethod
    def inmate_exists(connection: DatabaseConnection, inmate_id: int) -> bool:
        return _exists(connection, "inmates", "id", inmate_id)

    @staticmethod
    def user_exists(connection: DatabaseConnection, user_id: int) -> bool:
        return _exists(connection, "users", "id", user_id)

    @staticmethod
    def active_vocational_enrollment_exists(connection: DatabaseConnection, *, inmate_id: int, program_name: str) -> bool:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM vocational_training_enrollments
            WHERE inmate_id = %s
              AND program_name = %s
              AND completion_status IN ('ENROLLED', 'IN_PROGRESS')
            LIMIT 1
            """,
            (inmate_id, program_name),
        )
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists

    @staticmethod
    def certificate_number_exists(connection: DatabaseConnection, certificate_number: str) -> bool:
        return _exists(connection, "skill_certifications", "certificate_number", certificate_number)

    @staticmethod
    def inmate_history(connection: DatabaseConnection, inmate_id: int) -> dict[str, list[dict[str, Any]]]:
        return {
            "vocational_training": _rows(connection, "SELECT * FROM vocational_training_enrollments WHERE inmate_id = %s ORDER BY enrollment_date DESC, id DESC", (inmate_id,)),
            "counseling_sessions": _rows(connection, "SELECT * FROM counseling_sessions WHERE inmate_id = %s ORDER BY session_date DESC, id DESC", (inmate_id,)),
            "behavioral_assessments": _rows(connection, "SELECT * FROM behavioral_assessments WHERE inmate_id = %s ORDER BY assessment_date DESC, id DESC", (inmate_id,)),
            "religious_participations": _rows(connection, "SELECT * FROM religious_participations WHERE inmate_id = %s ORDER BY participation_date DESC, id DESC", (inmate_id,)),
            "work_assignments": _rows(connection, "SELECT * FROM work_assignments WHERE inmate_id = %s ORDER BY start_date DESC, id DESC", (inmate_id,)),
            "skill_certifications": _rows(connection, "SELECT * FROM skill_certifications WHERE inmate_id = %s ORDER BY issue_date DESC, id DESC", (inmate_id,)),
            "post_release_followups": _rows(connection, "SELECT * FROM post_release_followups WHERE inmate_id = %s ORDER BY follow_up_date DESC, id DESC", (inmate_id,)),
        }

    @staticmethod
    def reports(connection: DatabaseConnection) -> dict[str, Any]:
        return {
            "inmate_rehabilitation_progress_report": _rows(connection, "SELECT inmate_id, AVG(progress_percentage) AS average_progress, MAX(assessment_score) AS highest_assessment_score FROM vocational_training_enrollments GROUP BY inmate_id", ()),
            "vocational_training_performance_report": _rows(connection, "SELECT program_name, COUNT(*) AS total_enrollments, AVG(progress_percentage) AS average_progress, AVG(assessment_score) AS average_assessment_score FROM vocational_training_enrollments GROUP BY program_name", ()),
            "counseling_effectiveness_report": _rows(connection, "SELECT session_type, risk_level, COUNT(*) AS total_sessions, SUM(CASE WHEN follow_up_required = 1 THEN 1 ELSE 0 END) AS follow_up_required_total FROM counseling_sessions GROUP BY session_type, risk_level", ()),
            "behavioral_improvement_report": _rows(connection, "SELECT behavior_category, AVG(behavior_score) AS average_behavior_score, SUM(incident_count) AS total_incidents FROM behavioral_assessments GROUP BY behavior_category", ()),
            "work_assignment_productivity_report": _rows(connection, "SELECT work_type, COUNT(*) AS total_assignments, AVG(performance_rating) AS average_performance_rating FROM work_assignments GROUP BY work_type", ()),
            "post_release_reintegration_report": _rows(connection, "SELECT recidivism_risk_level, COUNT(*) AS total_followups, AVG(reintegration_score) AS average_reintegration_score FROM post_release_followups GROUP BY recidivism_risk_level", ()),
        }


def _validate_table(table: str) -> None:
    if table not in RehabilitationRepository.TABLE_COLUMNS:
        raise ValueError("Unsupported rehabilitation table")


def _insert_columns(table: str, data: dict[str, Any]) -> tuple[str, ...]:
    _validate_table(table)
    return tuple(column for column in RehabilitationRepository.TABLE_COLUMNS[table] if column not in {"id", "created_at", "updated_at"} and column in data)


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
