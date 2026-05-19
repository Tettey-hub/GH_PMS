from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any

from src.models.medical import (
    APPOINTMENT_STATUSES,
    APPOINTMENT_TYPES,
    DIAGNOSIS_TYPES,
    DISABILITY_STATUSES,
    DRUG_TEST_STATUSES,
    INFECTIOUS_DISEASE_STATUSES,
    MALARIA_STATUSES,
    MEDICAL_BLOOD_GROUPS,
    MEDICAL_GENOTYPES,
    MENTAL_HEALTH_SCREENING_STATUSES,
    REFERRAL_STATUSES,
    SCREENING_TYPES,
    SEVERITY_LEVELS,
    SUICIDE_RISK_LEVELS,
    TREATMENT_STATUSES,
)


class MedicalValidationError(ValueError):
    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Validation failed")
        self.errors = errors


@dataclass(frozen=True)
class MedicalProfileDTO:
    inmate_id: int
    created_by: int
    blood_group: str | None = None
    genotype: str | None = None
    allergies: str | None = None
    chronic_illnesses: str | None = None
    disability_status: str = "none"
    disability_description: str | None = None
    emergency_medical_notes: str | None = None
    current_medications: str | None = None
    primary_physician: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "MedicalProfileDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _optional_enum(errors, payload, "blood_group", MEDICAL_BLOOD_GROUPS, normalize=False)
        _optional_enum(errors, payload, "genotype", MEDICAL_GENOTYPES, normalize=False)
        _optional_enum(errors, payload, "disability_status", DISABILITY_STATUSES)
        _optional_texts(errors, payload, ("allergies", "chronic_illnesses", "disability_description", "emergency_medical_notes", "current_medications"))
        _optional_text(errors, payload, "primary_physician", max_length=100)
        if errors:
            raise MedicalValidationError(errors)
        disability_status = _optional_string(payload.get("disability_status"))
        return cls(
            inmate_id=int(payload["inmate_id"]),
            created_by=actor_user_id,
            blood_group=_optional_string(payload.get("blood_group")),
            genotype=_optional_string(payload.get("genotype")),
            allergies=_optional_string(payload.get("allergies")),
            chronic_illnesses=_optional_string(payload.get("chronic_illnesses")),
            disability_status=(disability_status or "none").lower(),
            disability_description=_optional_string(payload.get("disability_description")),
            emergency_medical_notes=_optional_string(payload.get("emergency_medical_notes")),
            current_medications=_optional_string(payload.get("current_medications")),
            primary_physician=_optional_string(payload.get("primary_physician")),
        )


@dataclass(frozen=True)
class MedicalProfileUpdateDTO:
    updates: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "MedicalProfileUpdateDTO":
        allowed = {
            "blood_group",
            "genotype",
            "allergies",
            "chronic_illnesses",
            "disability_status",
            "disability_description",
            "emergency_medical_notes",
            "current_medications",
            "primary_physician",
        }
        errors = _reject_unknown_fields(payload, allowed)
        clean_payload = {key: value for key, value in payload.items() if key in allowed}
        _optional_enum(errors, clean_payload, "blood_group", MEDICAL_BLOOD_GROUPS, normalize=False)
        _optional_enum(errors, clean_payload, "genotype", MEDICAL_GENOTYPES, normalize=False)
        _optional_enum(errors, clean_payload, "disability_status", DISABILITY_STATUSES)
        _optional_texts(errors, clean_payload, ("allergies", "chronic_illnesses", "disability_description", "emergency_medical_notes", "current_medications"))
        _optional_text(errors, clean_payload, "primary_physician", max_length=100)
        updates = _normalize_update_values(clean_payload, lower_fields={"disability_status"})
        if not updates:
            errors["request"] = "At least one medical profile field is required"
        if errors:
            raise MedicalValidationError(errors)
        return cls(updates=updates)


@dataclass(frozen=True)
class ScreeningDTO:
    inmate_id: int
    screening_date: date
    screening_type: str
    infectious_disease_status: str
    malaria_status: str
    drug_test_status: str
    mental_health_status: str
    screened_by: int
    temperature: Decimal | None = None
    blood_pressure: str | None = None
    weight_kg: Decimal | None = None
    height_cm: Decimal | None = None
    screening_notes: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "ScreeningDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_date(errors, payload, "screening_date")
        _require_enum(errors, payload, "screening_type", SCREENING_TYPES)
        _require_enum(errors, payload, "infectious_disease_status", INFECTIOUS_DISEASE_STATUSES)
        _require_enum(errors, payload, "malaria_status", MALARIA_STATUSES)
        _require_enum(errors, payload, "drug_test_status", DRUG_TEST_STATUSES)
        _require_enum(errors, payload, "mental_health_status", MENTAL_HEALTH_SCREENING_STATUSES)
        _optional_decimal_range(errors, payload, "temperature", minimum=Decimal("30.0"), maximum=Decimal("45.0"))
        _optional_decimal_range(errors, payload, "weight_kg", minimum=Decimal("20.0"), maximum=Decimal("300.0"))
        _optional_decimal_range(errors, payload, "height_cm", minimum=Decimal("80.0"), maximum=Decimal("250.0"))
        _optional_text(errors, payload, "blood_pressure", max_length=20)
        if payload.get("blood_pressure") not in {None, ""} and not re.fullmatch(r"\d{2,3}/\d{2,3}", str(payload["blood_pressure"]).strip()):
            errors["blood_pressure"] = "Must use systolic/diastolic format, for example 120/80"
        _optional_text(errors, payload, "screening_notes")
        if errors:
            raise MedicalValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            screening_date=date.fromisoformat(str(payload["screening_date"]).strip()),
            screening_type=str(payload["screening_type"]).strip().lower(),
            temperature=_optional_decimal(payload.get("temperature")),
            blood_pressure=_optional_string(payload.get("blood_pressure")),
            weight_kg=_optional_decimal(payload.get("weight_kg")),
            height_cm=_optional_decimal(payload.get("height_cm")),
            infectious_disease_status=str(payload["infectious_disease_status"]).strip().lower(),
            malaria_status=str(payload["malaria_status"]).strip().lower(),
            drug_test_status=str(payload["drug_test_status"]).strip().lower(),
            mental_health_status=str(payload["mental_health_status"]).strip().lower(),
            screening_notes=_optional_string(payload.get("screening_notes")),
            screened_by=actor_user_id,
        )


@dataclass(frozen=True)
class DiagnosisDTO:
    inmate_id: int
    diagnosis_name: str
    diagnosis_type: str
    diagnosis_date: date
    severity_level: str
    diagnosed_by: int
    diagnosis_notes: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "DiagnosisDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_text(errors, payload, "diagnosis_name", max_length=150)
        _require_enum(errors, payload, "diagnosis_type", DIAGNOSIS_TYPES)
        _require_date(errors, payload, "diagnosis_date")
        _require_enum(errors, payload, "severity_level", SEVERITY_LEVELS)
        _optional_text(errors, payload, "diagnosis_notes")
        if errors:
            raise MedicalValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            diagnosis_name=str(payload["diagnosis_name"]).strip(),
            diagnosis_type=str(payload["diagnosis_type"]).strip().lower(),
            diagnosis_date=date.fromisoformat(str(payload["diagnosis_date"]).strip()),
            severity_level=str(payload["severity_level"]).strip().lower(),
            diagnosis_notes=_optional_string(payload.get("diagnosis_notes")),
            diagnosed_by=actor_user_id,
        )


@dataclass(frozen=True)
class TreatmentPlanDTO:
    inmate_id: int
    diagnosis_id: int
    treatment_plan: str
    treatment_start_date: date
    treatment_status: str
    attending_medical_officer: int
    treatment_end_date: date | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "TreatmentPlanDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_int(errors, payload, "diagnosis_id")
        _require_text(errors, payload, "treatment_plan")
        _require_date(errors, payload, "treatment_start_date")
        _optional_date(errors, payload, "treatment_end_date")
        _require_enum(errors, payload, "treatment_status", TREATMENT_STATUSES)
        start = _safe_date(payload.get("treatment_start_date"))
        end = _safe_date(payload.get("treatment_end_date"))
        if start and end and end < start:
            errors["treatment_end_date"] = "Treatment end date cannot be before start date"
        if errors:
            raise MedicalValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            diagnosis_id=int(payload["diagnosis_id"]),
            treatment_plan=str(payload["treatment_plan"]).strip(),
            treatment_start_date=date.fromisoformat(str(payload["treatment_start_date"]).strip()),
            treatment_end_date=_safe_date(payload.get("treatment_end_date")),
            treatment_status=str(payload["treatment_status"]).strip().lower(),
            attending_medical_officer=actor_user_id,
        )


@dataclass(frozen=True)
class PrescriptionDTO:
    inmate_id: int
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    prescribed_by: int
    prescribed_date: date
    prescription_notes: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "PrescriptionDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        for field in ("medication_name", "dosage", "frequency", "duration"):
            _require_text(errors, payload, field, max_length=150 if field == "medication_name" else 80)
        _require_date(errors, payload, "prescribed_date")
        _optional_text(errors, payload, "prescription_notes")
        if errors:
            raise MedicalValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            medication_name=str(payload["medication_name"]).strip(),
            dosage=str(payload["dosage"]).strip(),
            frequency=str(payload["frequency"]).strip(),
            duration=str(payload["duration"]).strip(),
            prescription_notes=_optional_string(payload.get("prescription_notes")),
            prescribed_by=actor_user_id,
            prescribed_date=date.fromisoformat(str(payload["prescribed_date"]).strip()),
        )


@dataclass(frozen=True)
class MedicationAdministrationDTO:
    prescription_id: int
    administered_by: int
    administration_time: datetime
    administration_notes: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "MedicationAdministrationDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "prescription_id")
        _require_datetime(errors, payload, "administration_time")
        _optional_text(errors, payload, "administration_notes")
        if errors:
            raise MedicalValidationError(errors)
        return cls(
            prescription_id=int(payload["prescription_id"]),
            administered_by=actor_user_id,
            administration_time=datetime.fromisoformat(str(payload["administration_time"]).strip()),
            administration_notes=_optional_string(payload.get("administration_notes")),
        )


@dataclass(frozen=True)
class AppointmentDTO:
    inmate_id: int
    appointment_type: str
    appointment_date: date
    appointment_time: time
    facility_name: str
    referral_status: str
    appointment_status: str
    emergency_case: bool
    created_by: int
    doctor_name: str | None = None
    notes: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "AppointmentDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_enum(errors, payload, "appointment_type", APPOINTMENT_TYPES)
        _require_date(errors, payload, "appointment_date")
        _require_time(errors, payload, "appointment_time")
        _require_text(errors, payload, "facility_name", max_length=150)
        _optional_text(errors, payload, "doctor_name", max_length=100)
        _require_enum(errors, payload, "referral_status", REFERRAL_STATUSES)
        _require_enum(errors, payload, "appointment_status", APPOINTMENT_STATUSES)
        _require_bool(errors, payload, "emergency_case")
        _optional_text(errors, payload, "notes")
        appointment_type = str(payload.get("appointment_type", "")).strip().lower()
        referral_status = str(payload.get("referral_status", "")).strip().lower()
        emergency = _safe_bool(payload.get("emergency_case"))
        if appointment_type in {"prison_hospital_referral", "external_referral"} and referral_status == "not_required":
            errors["referral_status"] = "Referral appointments require a referral status"
        if appointment_type == "emergency" and emergency is False:
            errors["emergency_case"] = "Emergency appointments must be flagged as emergency cases"
        if errors:
            raise MedicalValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            appointment_type=appointment_type,
            appointment_date=date.fromisoformat(str(payload["appointment_date"]).strip()),
            appointment_time=time.fromisoformat(str(payload["appointment_time"]).strip()),
            facility_name=str(payload["facility_name"]).strip(),
            doctor_name=_optional_string(payload.get("doctor_name")),
            referral_status=referral_status,
            appointment_status=str(payload["appointment_status"]).strip().lower(),
            emergency_case=bool(emergency),
            notes=_optional_string(payload.get("notes")),
            created_by=actor_user_id,
        )


@dataclass(frozen=True)
class MentalHealthRecordDTO:
    inmate_id: int
    psychological_assessment: str
    suicide_risk_level: str
    assessed_by: int
    assessment_date: date
    counseling_notes: str | None = None
    behavioral_observations: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, actor_user_id: int) -> "MentalHealthRecordDTO":
        errors: dict[str, str] = {}
        _require_int(errors, payload, "inmate_id")
        _require_text(errors, payload, "psychological_assessment")
        _optional_text(errors, payload, "counseling_notes")
        _require_enum(errors, payload, "suicide_risk_level", SUICIDE_RISK_LEVELS)
        _optional_text(errors, payload, "behavioral_observations")
        _require_date(errors, payload, "assessment_date")
        if errors:
            raise MedicalValidationError(errors)
        return cls(
            inmate_id=int(payload["inmate_id"]),
            psychological_assessment=str(payload["psychological_assessment"]).strip(),
            counseling_notes=_optional_string(payload.get("counseling_notes")),
            suicide_risk_level=str(payload["suicide_risk_level"]).strip().lower(),
            behavioral_observations=_optional_string(payload.get("behavioral_observations")),
            assessed_by=actor_user_id,
            assessment_date=date.fromisoformat(str(payload["assessment_date"]).strip()),
        )


def _reject_unknown_fields(payload: dict[str, Any], allowed: set[str]) -> dict[str, str]:
    return {field: "This field cannot be updated" for field in payload if field not in allowed}


def _normalize_update_values(payload: dict[str, Any], *, lower_fields: set[str]) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    for field, value in payload.items():
        if value is None:
            updates[field] = None
            continue
        if isinstance(value, str):
            value = value.strip()
            updates[field] = value.lower() if field in lower_fields and value else value or None
        else:
            updates[field] = value
    return updates


def _require_text(errors: dict[str, str], payload: dict[str, Any], field: str, *, max_length: int | None = None) -> None:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        errors[field] = "This field is required"
    elif max_length is not None and len(value.strip()) > max_length:
        errors[field] = f"Must be at most {max_length} characters"


def _optional_texts(errors: dict[str, str], payload: dict[str, Any], fields: tuple[str, ...]) -> None:
    for field in fields:
        _optional_text(errors, payload, field)


def _optional_text(errors: dict[str, str], payload: dict[str, Any], field: str, *, max_length: int | None = None) -> None:
    value = payload.get(field)
    if value in {None, ""}:
        return
    if not isinstance(value, str):
        errors[field] = "Must be text"
    elif max_length is not None and len(value.strip()) > max_length:
        errors[field] = f"Must be at most {max_length} characters"


def _require_int(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    try:
        value = int(payload.get(field))
    except (TypeError, ValueError):
        errors[field] = "Must be an integer"
        return
    if value < 1:
        errors[field] = "Must be greater than zero"


def _require_bool(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if _safe_bool(payload.get(field)) is None:
        errors[field] = "Must be true or false"


def _safe_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    return None


def _require_date(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if _safe_date(payload.get(field)) is None:
        errors[field] = "Must use YYYY-MM-DD"


def _optional_date(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if payload.get(field) not in {None, ""} and _safe_date(payload.get(field)) is None:
        errors[field] = "Must use YYYY-MM-DD"


def _require_time(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    try:
        time.fromisoformat(str(payload.get(field)).strip())
    except ValueError:
        errors[field] = "Must use HH:MM or HH:MM:SS"


def _require_datetime(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    try:
        datetime.fromisoformat(str(payload.get(field)).strip())
    except ValueError:
        errors[field] = "Must use ISO datetime format"


def _require_enum(errors: dict[str, str], payload: dict[str, Any], field: str, allowed: set[str]) -> None:
    value = payload.get(field)
    if not isinstance(value, str) or value.strip().lower() not in allowed:
        errors[field] = f"Must be one of: {', '.join(sorted(allowed))}"


def _optional_enum(errors: dict[str, str], payload: dict[str, Any], field: str, allowed: set[str], *, normalize: bool = True) -> None:
    value = payload.get(field)
    if value in {None, ""}:
        return
    if not isinstance(value, str):
        errors[field] = "Must be text"
        return
    comparable = value.strip().lower() if normalize else value.strip().upper()
    allowed_values = {item.lower() for item in allowed} if normalize else allowed
    if comparable not in allowed_values:
        errors[field] = f"Must be one of: {', '.join(sorted(allowed))}"


def _optional_decimal_range(
    errors: dict[str, str],
    payload: dict[str, Any],
    field: str,
    *,
    minimum: Decimal,
    maximum: Decimal,
) -> None:
    value = payload.get(field)
    if value in {None, ""}:
        return
    decimal_value = _optional_decimal(value)
    if decimal_value is None:
        errors[field] = "Must be a decimal number"
    elif decimal_value < minimum or decimal_value > maximum:
        errors[field] = f"Must be between {minimum} and {maximum}"


def _optional_decimal(value: Any) -> Decimal | None:
    if value in {None, ""}:
        return None
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _safe_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None
