from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, TypeAlias


MEDICAL_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
MEDICAL_GENOTYPES = {"AA", "AS", "SS", "AC", "SC"}
DISABILITY_STATUSES = {"none", "temporary", "permanent", "unknown"}
SCREENING_TYPES = {"admission", "periodic", "emergency", "referral", "release"}
INFECTIOUS_DISEASE_STATUSES = {"none", "suspected", "confirmed", "under_treatment", "recovered"}
MALARIA_STATUSES = {"not_tested", "negative", "positive", "treated"}
DRUG_TEST_STATUSES = {"not_tested", "negative", "positive", "inconclusive"}
MENTAL_HEALTH_SCREENING_STATUSES = {"stable", "monitoring_required", "urgent_review", "referred"}
DIAGNOSIS_TYPES = {"acute", "chronic", "infectious", "injury", "mental_health", "other"}
SEVERITY_LEVELS = {"low", "moderate", "high", "critical"}
TREATMENT_STATUSES = {"planned", "active", "completed", "cancelled", "referred"}
APPOINTMENT_TYPES = {"infirmary", "prison_hospital_referral", "external_referral", "emergency"}
REFERRAL_STATUSES = {"not_required", "pending", "approved", "completed", "cancelled"}
APPOINTMENT_STATUSES = {"scheduled", "completed", "missed", "cancelled", "referred"}
SUICIDE_RISK_LEVELS = {"low", "moderate", "high", "critical"}


class MedicalEntityMixin:
    @property
    def data(self) -> dict[str, Any]:
        return asdict(self)

    def to_dict(self) -> dict[str, Any]:
        return {key: _serialize(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class InmateMedicalProfile(MedicalEntityMixin):
    id: int | None
    inmate_id: int
    disability_status: str
    created_by: int
    blood_group: str | None = None
    genotype: str | None = None
    allergies: str | None = None
    chronic_illnesses: str | None = None
    disability_description: str | None = None
    emergency_medical_notes: str | None = None
    current_medications: str | None = None
    primary_physician: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "InmateMedicalProfile":
        return cls(
            id=row.get("id"),
            inmate_id=row["inmate_id"],
            blood_group=row.get("blood_group"),
            genotype=row.get("genotype"),
            allergies=row.get("allergies"),
            chronic_illnesses=row.get("chronic_illnesses"),
            disability_status=row["disability_status"],
            disability_description=row.get("disability_description"),
            emergency_medical_notes=row.get("emergency_medical_notes"),
            current_medications=row.get("current_medications"),
            primary_physician=row.get("primary_physician"),
            created_by=row["created_by"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


@dataclass(frozen=True)
class MedicalScreening(MedicalEntityMixin):
    id: int | None
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
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "MedicalScreening":
        return cls(
            id=row.get("id"),
            inmate_id=row["inmate_id"],
            screening_date=row["screening_date"],
            screening_type=row["screening_type"],
            temperature=row.get("temperature"),
            blood_pressure=row.get("blood_pressure"),
            weight_kg=row.get("weight_kg"),
            height_cm=row.get("height_cm"),
            infectious_disease_status=row["infectious_disease_status"],
            malaria_status=row["malaria_status"],
            drug_test_status=row["drug_test_status"],
            mental_health_status=row["mental_health_status"],
            screening_notes=row.get("screening_notes"),
            screened_by=row["screened_by"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


@dataclass(frozen=True)
class Diagnosis(MedicalEntityMixin):
    id: int | None
    inmate_id: int
    diagnosis_name: str
    diagnosis_type: str
    diagnosis_date: date
    severity_level: str
    diagnosed_by: int
    diagnosis_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Diagnosis":
        return cls(
            id=row.get("id"),
            inmate_id=row["inmate_id"],
            diagnosis_name=row["diagnosis_name"],
            diagnosis_type=row["diagnosis_type"],
            diagnosis_date=row["diagnosis_date"],
            severity_level=row["severity_level"],
            diagnosis_notes=row.get("diagnosis_notes"),
            diagnosed_by=row["diagnosed_by"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


@dataclass(frozen=True)
class TreatmentPlan(MedicalEntityMixin):
    id: int | None
    inmate_id: int
    diagnosis_id: int
    treatment_plan: str
    treatment_start_date: date
    treatment_status: str
    attending_medical_officer: int
    treatment_end_date: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "TreatmentPlan":
        return cls(
            id=row.get("id"),
            inmate_id=row["inmate_id"],
            diagnosis_id=row["diagnosis_id"],
            treatment_plan=row["treatment_plan"],
            treatment_start_date=row["treatment_start_date"],
            treatment_end_date=row.get("treatment_end_date"),
            treatment_status=row["treatment_status"],
            attending_medical_officer=row["attending_medical_officer"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


@dataclass(frozen=True)
class Prescription(MedicalEntityMixin):
    id: int | None
    inmate_id: int
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    prescribed_by: int
    prescribed_date: date
    prescription_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Prescription":
        return cls(
            id=row.get("id"),
            inmate_id=row["inmate_id"],
            medication_name=row["medication_name"],
            dosage=row["dosage"],
            frequency=row["frequency"],
            duration=row["duration"],
            prescription_notes=row.get("prescription_notes"),
            prescribed_by=row["prescribed_by"],
            prescribed_date=row["prescribed_date"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


@dataclass(frozen=True)
class MedicationAdministrationLog(MedicalEntityMixin):
    id: int | None
    prescription_id: int
    administered_by: int
    administration_time: datetime
    administration_notes: str | None = None
    created_at: datetime | None = None
    inmate_id: int | None = None
    medication_name: str | None = None
    dosage: str | None = None
    frequency: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "MedicationAdministrationLog":
        return cls(
            id=row.get("id"),
            prescription_id=row["prescription_id"],
            administered_by=row["administered_by"],
            administration_time=row["administration_time"],
            administration_notes=row.get("administration_notes"),
            created_at=row.get("created_at"),
            inmate_id=row.get("inmate_id"),
            medication_name=row.get("medication_name"),
            dosage=row.get("dosage"),
            frequency=row.get("frequency"),
        )


@dataclass(frozen=True)
class MedicalAppointment(MedicalEntityMixin):
    id: int | None
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
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "MedicalAppointment":
        return cls(
            id=row.get("id"),
            inmate_id=row["inmate_id"],
            appointment_type=row["appointment_type"],
            appointment_date=row["appointment_date"],
            appointment_time=row["appointment_time"],
            facility_name=row["facility_name"],
            doctor_name=row.get("doctor_name"),
            referral_status=row["referral_status"],
            appointment_status=row["appointment_status"],
            emergency_case=bool(row["emergency_case"]),
            notes=row.get("notes"),
            created_by=row["created_by"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


@dataclass(frozen=True)
class MentalHealthRecord(MedicalEntityMixin):
    id: int | None
    inmate_id: int
    psychological_assessment: str
    suicide_risk_level: str
    assessed_by: int
    assessment_date: date
    counseling_notes: str | None = None
    behavioral_observations: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "MentalHealthRecord":
        return cls(
            id=row.get("id"),
            inmate_id=row["inmate_id"],
            psychological_assessment=row["psychological_assessment"],
            counseling_notes=row.get("counseling_notes"),
            suicide_risk_level=row["suicide_risk_level"],
            behavioral_observations=row.get("behavioral_observations"),
            assessed_by=row["assessed_by"],
            assessment_date=row["assessment_date"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


MedicalRecord: TypeAlias = (
    InmateMedicalProfile
    | MedicalScreening
    | Diagnosis
    | TreatmentPlan
    | Prescription
    | MedicationAdministrationLog
    | MedicalAppointment
    | MentalHealthRecord
)

MEDICAL_TABLE_MODELS = {
    "inmate_medical_profiles": InmateMedicalProfile,
    "medical_screenings": MedicalScreening,
    "diagnoses": Diagnosis,
    "treatment_plans": TreatmentPlan,
    "prescriptions": Prescription,
    "medication_administration_logs": MedicationAdministrationLog,
    "medical_appointments": MedicalAppointment,
    "mental_health_records": MentalHealthRecord,
}


def medical_record_from_row(table: str, row: dict[str, Any]) -> MedicalRecord:
    model = MEDICAL_TABLE_MODELS.get(table)
    if model is None:
        raise ValueError("Unsupported medical table")
    return model.from_row(row)


def _serialize(value: Any) -> Any:
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value
