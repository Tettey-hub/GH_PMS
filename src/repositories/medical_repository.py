from __future__ import annotations

from typing import Any

from src.config.database_config import DatabaseConnection
from src.models.medical import MedicalRecord, medical_record_from_row


class MedicalRepository:
    TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
        "inmate_medical_profiles": (
            "id",
            "inmate_id",
            "blood_group",
            "genotype",
            "allergies",
            "chronic_illnesses",
            "disability_status",
            "disability_description",
            "emergency_medical_notes",
            "current_medications",
            "primary_physician",
            "created_by",
            "created_at",
            "updated_at",
        ),
        "medical_screenings": (
            "id",
            "inmate_id",
            "screening_date",
            "screening_type",
            "temperature",
            "blood_pressure",
            "weight_kg",
            "height_cm",
            "infectious_disease_status",
            "malaria_status",
            "drug_test_status",
            "mental_health_status",
            "screening_notes",
            "screened_by",
            "created_at",
            "updated_at",
        ),
        "diagnoses": (
            "id",
            "inmate_id",
            "diagnosis_name",
            "diagnosis_type",
            "diagnosis_date",
            "severity_level",
            "diagnosis_notes",
            "diagnosed_by",
            "created_at",
            "updated_at",
        ),
        "treatment_plans": (
            "id",
            "inmate_id",
            "diagnosis_id",
            "treatment_plan",
            "treatment_start_date",
            "treatment_end_date",
            "treatment_status",
            "attending_medical_officer",
            "created_at",
            "updated_at",
        ),
        "prescriptions": (
            "id",
            "inmate_id",
            "medication_name",
            "dosage",
            "frequency",
            "duration",
            "prescription_notes",
            "prescribed_by",
            "prescribed_date",
            "created_at",
            "updated_at",
        ),
        "medication_administration_logs": (
            "id",
            "prescription_id",
            "administered_by",
            "administration_time",
            "administration_notes",
            "created_at",
        ),
        "medical_appointments": (
            "id",
            "inmate_id",
            "appointment_type",
            "appointment_date",
            "appointment_time",
            "facility_name",
            "doctor_name",
            "referral_status",
            "appointment_status",
            "emergency_case",
            "notes",
            "created_by",
            "created_at",
            "updated_at",
        ),
        "mental_health_records": (
            "id",
            "inmate_id",
            "psychological_assessment",
            "counseling_notes",
            "suicide_risk_level",
            "behavioral_observations",
            "assessed_by",
            "assessment_date",
            "created_at",
            "updated_at",
        ),
    }

    @staticmethod
    def create(connection: DatabaseConnection, table: str, data: dict[str, Any]) -> MedicalRecord:
        columns = _insert_columns(table, data)
        column_list = ", ".join(f"`{column}`" for column in columns)
        placeholders = ", ".join(f"%({column})s" for column in columns)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"INSERT INTO `{table}` ({column_list}) VALUES ({placeholders})", {column: data.get(column) for column in columns})
        record_id = cursor.lastrowid
        cursor.execute(f"SELECT * FROM `{table}` WHERE id = %s", (record_id,))
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            raise RuntimeError(f"{table} record was created but could not be reloaded")
        return medical_record_from_row(table, row)

    @staticmethod
    def update(connection: DatabaseConnection, table: str, record_id: int, updates: dict[str, Any]) -> MedicalRecord | None:
        if not updates:
            raise ValueError("No update fields provided")
        _validate_table(table)
        allowed = set(MedicalRepository.TABLE_COLUMNS[table]) - {"id", "created_at", "updated_at", "created_by", "inmate_id"}
        invalid = set(updates) - allowed
        if invalid:
            raise ValueError(f"Unsupported update fields: {', '.join(sorted(invalid))}")
        assignments = ", ".join(f"`{column}` = %({column})s" for column in updates)
        params = dict(updates)
        params["id"] = record_id
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"UPDATE `{table}` SET {assignments} WHERE id = %(id)s", params)
        cursor.execute(f"SELECT * FROM `{table}` WHERE id = %s", (record_id,))
        row = cursor.fetchone()
        cursor.close()
        return medical_record_from_row(table, row) if row else None

    @staticmethod
    def get_by_id(connection: DatabaseConnection, table: str, record_id: int) -> MedicalRecord | None:
        _validate_table(table)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM `{table}` WHERE id = %s LIMIT 1", (record_id,))
        row = cursor.fetchone()
        cursor.close()
        return medical_record_from_row(table, row) if row else None

    @staticmethod
    def get_profile_by_inmate(connection: DatabaseConnection, inmate_id: int) -> MedicalRecord | None:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM inmate_medical_profiles WHERE inmate_id = %s LIMIT 1", (inmate_id,))
        row = cursor.fetchone()
        cursor.close()
        return medical_record_from_row("inmate_medical_profiles", row) if row else None

    @staticmethod
    def inmate_exists(connection: DatabaseConnection, inmate_id: int) -> bool:
        return _exists(connection, "inmates", "id", inmate_id)

    @staticmethod
    def user_exists(connection: DatabaseConnection, user_id: int) -> bool:
        return _exists(connection, "users", "id", user_id)

    @staticmethod
    def diagnosis_belongs_to_inmate(connection: DatabaseConnection, diagnosis_id: int, inmate_id: int) -> bool:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM diagnoses WHERE id = %s AND inmate_id = %s LIMIT 1", (diagnosis_id, inmate_id))
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists

    @staticmethod
    def prescription_exists(connection: DatabaseConnection, prescription_id: int) -> bool:
        return _exists(connection, "prescriptions", "id", prescription_id)

    @staticmethod
    def list_by_inmate(connection: DatabaseConnection, table: str, inmate_id: int, *, order_by: str = "created_at") -> list[MedicalRecord]:
        _validate_table(table)
        if "inmate_id" not in MedicalRepository.TABLE_COLUMNS[table]:
            raise ValueError("Table does not support inmate history lookup")
        if order_by not in MedicalRepository.TABLE_COLUMNS[table]:
            order_by = "created_at"
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"SELECT * FROM `{table}` WHERE inmate_id = %s ORDER BY `{order_by}` DESC, id DESC",
            (inmate_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [medical_record_from_row(table, row) for row in rows]

    @staticmethod
    def medication_logs_for_inmate(connection: DatabaseConnection, inmate_id: int) -> list[MedicalRecord]:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT mal.*, p.inmate_id, p.medication_name, p.dosage, p.frequency
            FROM medication_administration_logs mal
            INNER JOIN prescriptions p ON p.id = mal.prescription_id
            WHERE p.inmate_id = %s
            ORDER BY mal.administration_time DESC, mal.id DESC
            """,
            (inmate_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [medical_record_from_row("medication_administration_logs", row) for row in rows]

    @staticmethod
    def disease_outbreak_report(connection: DatabaseConnection) -> list[dict[str, Any]]:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT infectious_disease_status, malaria_status, COUNT(*) AS total
            FROM medical_screenings
            WHERE infectious_disease_status IN ('suspected', 'confirmed', 'under_treatment')
               OR malaria_status = 'positive'
            GROUP BY infectious_disease_status, malaria_status
            ORDER BY total DESC
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return list(rows)

    @staticmethod
    def medication_report(connection: DatabaseConnection) -> list[dict[str, Any]]:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT p.medication_name, COUNT(*) AS prescriptions, COUNT(mal.id) AS administrations
            FROM prescriptions p
            LEFT JOIN medication_administration_logs mal ON mal.prescription_id = p.id
            GROUP BY p.medication_name
            ORDER BY prescriptions DESC, p.medication_name
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return list(rows)

    @staticmethod
    def appointment_report(connection: DatabaseConnection) -> list[dict[str, Any]]:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT appointment_type, referral_status, appointment_status, emergency_case, COUNT(*) AS total
            FROM medical_appointments
            GROUP BY appointment_type, referral_status, appointment_status, emergency_case
            ORDER BY total DESC
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return list(rows)

    @staticmethod
    def chronic_illness_statistics(connection: DatabaseConnection) -> dict[str, Any]:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT COUNT(*) AS profiles_with_chronic_illness
            FROM inmate_medical_profiles
            WHERE chronic_illnesses IS NOT NULL AND TRIM(chronic_illnesses) <> ''
            """
        )
        row = cursor.fetchone()
        cursor.close()
        return dict(row or {"profiles_with_chronic_illness": 0})

    @staticmethod
    def mental_health_monitoring(connection: DatabaseConnection) -> list[dict[str, Any]]:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT suicide_risk_level, COUNT(*) AS total
            FROM mental_health_records
            GROUP BY suicide_risk_level
            ORDER BY FIELD(suicide_risk_level, 'critical', 'high', 'moderate', 'low')
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return list(rows)

    @staticmethod
    def treatment_progress_report(connection: DatabaseConnection) -> list[dict[str, Any]]:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT treatment_status, COUNT(*) AS total
            FROM treatment_plans
            GROUP BY treatment_status
            ORDER BY total DESC
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return list(rows)


def _validate_table(table: str) -> None:
    if table not in MedicalRepository.TABLE_COLUMNS:
        raise ValueError("Unsupported medical table")


def _insert_columns(table: str, data: dict[str, Any]) -> tuple[str, ...]:
    _validate_table(table)
    allowed = set(MedicalRepository.TABLE_COLUMNS[table]) - {"id", "created_at", "updated_at"}
    columns = tuple(column for column in MedicalRepository.TABLE_COLUMNS[table] if column in allowed and column in data)
    if not columns:
        raise ValueError("No insert fields provided")
    return columns


def _exists(connection: DatabaseConnection, table: str, field: str, value: Any) -> bool:
    cursor = connection.cursor()
    cursor.execute(f"SELECT 1 FROM `{table}` WHERE `{field}` = %s LIMIT 1", (value,))
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists
