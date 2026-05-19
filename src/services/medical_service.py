from __future__ import annotations

from dataclasses import asdict
from typing import Any

from mysql.connector import Error as MySQLError, IntegrityError

from src.config.settings import settings
from src.config.database_config import db_connection
from src.dtos.medical_dto import (
    AppointmentDTO,
    DiagnosisDTO,
    MedicalProfileDTO,
    MedicalProfileUpdateDTO,
    MedicationAdministrationDTO,
    MentalHealthRecordDTO,
    PrescriptionDTO,
    ScreeningDTO,
    TreatmentPlanDTO,
)
from src.models.medical import MedicalRecord
from src.repositories.medical_repository import MedicalRepository


class MedicalNotFoundError(LookupError):
    pass


class MedicalConflictError(ValueError):
    pass


class MedicalForeignKeyError(ValueError):
    pass


class MedicalService:
    @staticmethod
    def create_medical_profile(data: MedicalProfileDTO) -> MedicalRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.created_by, "Creator does not exist")
                if MedicalRepository.get_profile_by_inmate(connection, data.inmate_id):
                    raise MedicalConflictError("Medical profile already exists for this inmate")
                record = MedicalRepository.create(connection, "inmate_medical_profiles", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def update_medical_profile(inmate_id: int, data: MedicalProfileUpdateDTO) -> MedicalRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, inmate_id)
                existing = MedicalRepository.get_profile_by_inmate(connection, inmate_id)
                if existing is None:
                    raise MedicalNotFoundError("Medical profile not found")
                updated = MedicalRepository.update(connection, "inmate_medical_profiles", int(existing.data["id"]), data.updates)
                connection.commit()
                if updated is None:
                    raise MedicalNotFoundError("Medical profile not found")
                return updated
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def record_screening(data: ScreeningDTO) -> MedicalRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.screened_by, "Screening officer does not exist")
                record = MedicalRepository.create(connection, "medical_screenings", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def create_diagnosis(data: DiagnosisDTO) -> MedicalRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.diagnosed_by, "Diagnosing officer does not exist")
                record = MedicalRepository.create(connection, "diagnoses", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def create_treatment_plan(data: TreatmentPlanDTO) -> MedicalRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.attending_medical_officer, "Attending medical officer does not exist")
                if not MedicalRepository.diagnosis_belongs_to_inmate(connection, data.diagnosis_id, data.inmate_id):
                    raise MedicalForeignKeyError("Diagnosis does not exist for this inmate")
                record = MedicalRepository.create(connection, "treatment_plans", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def create_prescription(data: PrescriptionDTO) -> MedicalRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.prescribed_by, "Prescribing officer does not exist")
                record = MedicalRepository.create(connection, "prescriptions", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def administer_medication(data: MedicationAdministrationDTO) -> MedicalRecord:
        with db_connection() as connection:
            try:
                _require_user(connection, data.administered_by, "Medication administrator does not exist")
                if not MedicalRepository.prescription_exists(connection, data.prescription_id):
                    raise MedicalForeignKeyError("Prescription does not exist")
                record = MedicalRepository.create(connection, "medication_administration_logs", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def schedule_appointment(data: AppointmentDTO) -> MedicalRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.created_by, "Appointment creator does not exist")
                _validate_referral_facility(data.appointment_type, data.facility_name)
                record = MedicalRepository.create(connection, "medical_appointments", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def create_mental_health_record(data: MentalHealthRecordDTO) -> MedicalRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.assessed_by, "Assessing officer does not exist")
                record = MedicalRepository.create(connection, "mental_health_records", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def retrieve_inmate_medical_history(inmate_id: int) -> dict[str, Any]:
        with db_connection() as connection:
            _require_inmate(connection, inmate_id)
            profile = MedicalRepository.get_profile_by_inmate(connection, inmate_id)
            return {
                "profile": profile.to_dict() if profile else None,
                "screenings": _records(MedicalRepository.list_by_inmate(connection, "medical_screenings", inmate_id, order_by="screening_date")),
                "diagnoses": _records(MedicalRepository.list_by_inmate(connection, "diagnoses", inmate_id, order_by="diagnosis_date")),
                "treatment_plans": _records(MedicalRepository.list_by_inmate(connection, "treatment_plans", inmate_id, order_by="treatment_start_date")),
                "prescriptions": _records(MedicalRepository.list_by_inmate(connection, "prescriptions", inmate_id, order_by="prescribed_date")),
                "medication_administration_logs": _records(MedicalRepository.medication_logs_for_inmate(connection, inmate_id)),
                "appointments": _records(MedicalRepository.list_by_inmate(connection, "medical_appointments", inmate_id, order_by="appointment_date")),
                "mental_health_records": _records(MedicalRepository.list_by_inmate(connection, "mental_health_records", inmate_id, order_by="assessment_date")),
            }

    @staticmethod
    def retrieve_inmate_treatment_history(inmate_id: int) -> dict[str, Any]:
        with db_connection() as connection:
            _require_inmate(connection, inmate_id)
            return {
                "diagnoses": _records(MedicalRepository.list_by_inmate(connection, "diagnoses", inmate_id, order_by="diagnosis_date")),
                "treatment_plans": _records(MedicalRepository.list_by_inmate(connection, "treatment_plans", inmate_id, order_by="treatment_start_date")),
                "prescriptions": _records(MedicalRepository.list_by_inmate(connection, "prescriptions", inmate_id, order_by="prescribed_date")),
                "medication_administration_logs": _records(MedicalRepository.medication_logs_for_inmate(connection, inmate_id)),
            }

    @staticmethod
    def generate_medical_reports() -> dict[str, Any]:
        with db_connection() as connection:
            return {
                "disease_outbreak_monitoring": MedicalRepository.disease_outbreak_report(connection),
                "medication_reports": MedicalRepository.medication_report(connection),
                "appointment_reports": MedicalRepository.appointment_report(connection),
                "chronic_illness_statistics": MedicalRepository.chronic_illness_statistics(connection),
                "mental_health_monitoring": MedicalRepository.mental_health_monitoring(connection),
                "treatment_progress_reports": MedicalRepository.treatment_progress_report(connection),
            }


def _require_inmate(connection, inmate_id: int) -> None:
    if not MedicalRepository.inmate_exists(connection, inmate_id):
        raise MedicalForeignKeyError("Inmate does not exist")


def _require_user(connection, user_id: int, message: str) -> None:
    if not MedicalRepository.user_exists(connection, user_id):
        raise MedicalForeignKeyError(message)


def _records(records: list[MedicalRecord]) -> list[dict[str, Any]]:
    return [record.to_dict() for record in records]


def _validate_referral_facility(appointment_type: str, facility_name: str) -> None:
    if appointment_type not in {"prison_hospital_referral", "external_referral", "emergency"}:
        return
    configured_facilities = {facility.strip().lower() for facility in settings.medical_referral_facilities if facility.strip()}
    if configured_facilities and facility_name.strip().lower() not in configured_facilities:
        raise ValueError("Referral facility is not configured")


def is_duplicate_medical_error(exc: Exception) -> bool:
    return isinstance(exc, IntegrityError) and getattr(exc, "errno", None) == 1062


def is_mysql_error(exc: Exception) -> bool:
    return isinstance(exc, MySQLError)
