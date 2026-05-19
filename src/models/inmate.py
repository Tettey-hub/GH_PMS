from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any


INMATE_GENDERS = {"male", "female"}
INMATE_MARITAL_STATUSES = {"single", "married", "divorced", "widowed"}
INMATE_NEXT_OF_KIN_RELATIONS = {"spouse", "parent", "sibling", "child", "other"}
INMATE_SENTENCE_TYPES = {"remand", "convicted", "life", "death"}
INMATE_STATUSES = {"active", "released", "transferred", "deceased"}
INMATE_TRANSFER_TYPES = {
    "INTERNAL_TRANSFER",
    "INTER_PRISON_TRANSFER",
    "MEDICAL_TRANSFER",
    "COURT_TRANSFER",
    "REHABILITATION_TRANSFER",
    "EMERGENCY_TRANSFER",
}
INMATE_TRANSFER_STATUSES = {"PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED", "IN_TRANSIT", "COMPLETED", "CANCELLED"}
INMATE_RELEASE_TYPES = {
    "SENTENCE_COMPLETION",
    "BAIL_RELEASE",
    "PAROLE",
    "PRESIDENTIAL_PARDON",
    "MEDICAL_RELEASE",
    "COURT_ACQUITTAL",
}
INMATE_RELEASE_STATUSES = {"PENDING_REVIEW", "LEGAL_VERIFICATION", "APPROVED", "REJECTED", "READY_FOR_RELEASE", "RELEASED"}

INMATE_REQUIRED_TEXT_FIELD_LENGTHS = {
    "inmate_id": 20,
    "first_name": 50,
    "last_name": 50,
    "gender": 10,
    "nationality": 50,
    "marital_status": 20,
    "next_of_kin_name": 100,
    "next_of_kin_relation": 30,
    "case_number": 30,
    "offense": 100,
    "arresting_officer": 100,
    "arresting_agency": 100,
    "court": 100,
    "sentence_type": 30,
    "status": 20,
}

INMATE_OPTIONAL_TEXT_FIELD_LENGTHS = {
    "other_names": 100,
    "national_id": 50,
    "phone": 20,
    "photo": 255,
    "fingerprint_id": 50,
    "eye_color": 20,
    "hair_color": 20,
    "religion": 50,
    "occupation": 100,
    "education_level": 50,
    "next_of_kin_contact": 20,
    "judge": 100,
    "sentence_duration": 50,
}

INMATE_TEXT_AREA_FIELDS = {"address", "distinguishing_marks", "next_of_kin_address", "offense_description"}
INMATE_DATE_FIELDS = {"date_of_birth", "arrest_date", "admission_date", "expected_release_date"}
INMATE_INT_FIELDS = {"warrant_id", "age", "admission_officer_id"}
INMATE_DECIMAL_FIELDS = {"height_cm", "weight_kg"}
INMATE_ENUM_FIELD_VALUES = {
    "gender": INMATE_GENDERS,
    "marital_status": INMATE_MARITAL_STATUSES,
    "next_of_kin_relation": INMATE_NEXT_OF_KIN_RELATIONS,
    "sentence_type": INMATE_SENTENCE_TYPES,
    "status": INMATE_STATUSES,
}
INMATE_ALLOWED_UPDATE_FIELDS = (
    set(INMATE_REQUIRED_TEXT_FIELD_LENGTHS)
    | set(INMATE_OPTIONAL_TEXT_FIELD_LENGTHS)
    | INMATE_TEXT_AREA_FIELDS
    | INMATE_DATE_FIELDS
    | INMATE_INT_FIELDS
    | INMATE_DECIMAL_FIELDS
    | {"admission_time"}
)
INMATE_ALLOWED_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class Inmate:
    id: int | None
    inmate_id: str
    warrant_id: int
    first_name: str
    last_name: str
    date_of_birth: date
    age: int
    gender: str
    nationality: str
    marital_status: str
    next_of_kin_name: str
    next_of_kin_relation: str
    case_number: str
    offense: str
    arrest_date: date
    arresting_officer: str
    arresting_agency: str
    court: str
    sentence_type: str
    status: str
    admission_date: date
    admission_time: time
    admission_officer_id: int
    other_names: str | None = None
    national_id: str | None = None
    phone: str | None = None
    address: str | None = None
    photo: str | None = None
    fingerprint_id: str | None = None
    height_cm: Decimal | None = None
    weight_kg: Decimal | None = None
    eye_color: str | None = None
    hair_color: str | None = None
    distinguishing_marks: str | None = None
    religion: str | None = None
    occupation: str | None = None
    education_level: str | None = None
    next_of_kin_contact: str | None = None
    next_of_kin_address: str | None = None
    offense_description: str | None = None
    judge: str | None = None
    sentence_duration: str | None = None
    expected_release_date: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "inmate_id": self.inmate_id,
            "warrant_id": self.warrant_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "other_names": self.other_names,
            "date_of_birth": self.date_of_birth.isoformat(),
            "age": self.age,
            "gender": self.gender,
            "nationality": self.nationality,
            "national_id": self.national_id,
            "phone": self.phone,
            "address": self.address,
            "marital_status": self.marital_status,
            "photo": self.photo,
            "fingerprint_id": self.fingerprint_id,
            "height_cm": float(self.height_cm) if self.height_cm is not None else None,
            "weight_kg": float(self.weight_kg) if self.weight_kg is not None else None,
            "eye_color": self.eye_color,
            "hair_color": self.hair_color,
            "distinguishing_marks": self.distinguishing_marks,
            "religion": self.religion,
            "occupation": self.occupation,
            "education_level": self.education_level,
            "next_of_kin_name": self.next_of_kin_name,
            "next_of_kin_relation": self.next_of_kin_relation,
            "next_of_kin_contact": self.next_of_kin_contact,
            "next_of_kin_address": self.next_of_kin_address,
            "case_number": self.case_number,
            "offense": self.offense,
            "offense_description": self.offense_description,
            "arrest_date": self.arrest_date.isoformat(),
            "arresting_officer": self.arresting_officer,
            "arresting_agency": self.arresting_agency,
            "court": self.court,
            "judge": self.judge,
            "sentence_type": self.sentence_type,
            "sentence_duration": self.sentence_duration,
            "expected_release_date": self.expected_release_date.isoformat() if self.expected_release_date else None,
            "status": self.status,
            "admission_date": self.admission_date.isoformat(),
            "admission_time": self.admission_time.isoformat(),
            "admission_officer_id": self.admission_officer_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Inmate":
        return cls(
            id=row.get("id"),
            inmate_id=row["inmate_id"],
            warrant_id=row["warrant_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            other_names=row.get("other_names"),
            date_of_birth=row["date_of_birth"],
            age=row["age"],
            gender=row["gender"],
            nationality=row["nationality"],
            national_id=row.get("national_id"),
            phone=row.get("phone"),
            address=row.get("address"),
            marital_status=row["marital_status"],
            photo=row.get("photo"),
            fingerprint_id=row.get("fingerprint_id"),
            height_cm=row.get("height_cm"),
            weight_kg=row.get("weight_kg"),
            eye_color=row.get("eye_color"),
            hair_color=row.get("hair_color"),
            distinguishing_marks=row.get("distinguishing_marks"),
            religion=row.get("religion"),
            occupation=row.get("occupation"),
            education_level=row.get("education_level"),
            next_of_kin_name=row["next_of_kin_name"],
            next_of_kin_relation=row["next_of_kin_relation"],
            next_of_kin_contact=row.get("next_of_kin_contact"),
            next_of_kin_address=row.get("next_of_kin_address"),
            case_number=row["case_number"],
            offense=row["offense"],
            offense_description=row.get("offense_description"),
            arrest_date=row["arrest_date"],
            arresting_officer=row["arresting_officer"],
            arresting_agency=row["arresting_agency"],
            court=row["court"],
            judge=row.get("judge"),
            sentence_type=row["sentence_type"],
            sentence_duration=row.get("sentence_duration"),
            expected_release_date=row.get("expected_release_date"),
            status=row["status"],
            admission_date=row["admission_date"],
            admission_time=row["admission_time"],
            admission_officer_id=row["admission_officer_id"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


@dataclass(frozen=True)
class InmateTransfer:
    id: int | None
    inmate_id: int
    current_facility: str
    destination_facility: str
    transfer_type: str
    reason: str
    security_level: str
    medical_clearance: bool
    legal_verified: bool
    security_assessed: bool
    transfer_status: str
    urgency_level: str
    requested_date: date
    created_by: int
    departure_date: date | None = None
    arrival_date: date | None = None
    escort_officers: str | None = None
    transport_vehicle: str | None = None
    route_details: str | None = None
    movement_authorized_by: int | None = None
    approved_by: int | None = None
    receiving_officer: str | None = None
    receiving_confirmation: bool = False
    transfer_completion_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "inmate_id": self.inmate_id,
            "current_facility": self.current_facility,
            "destination_facility": self.destination_facility,
            "transfer_type": self.transfer_type,
            "reason": self.reason,
            "security_level": self.security_level,
            "medical_clearance": self.medical_clearance,
            "legal_verified": self.legal_verified,
            "security_assessed": self.security_assessed,
            "transfer_status": self.transfer_status,
            "urgency_level": self.urgency_level,
            "requested_date": self.requested_date.isoformat(),
            "departure_date": self.departure_date.isoformat() if self.departure_date else None,
            "arrival_date": self.arrival_date.isoformat() if self.arrival_date else None,
            "escort_officers": self.escort_officers,
            "transport_vehicle": self.transport_vehicle,
            "route_details": self.route_details,
            "movement_authorized_by": self.movement_authorized_by,
            "approved_by": self.approved_by,
            "receiving_officer": self.receiving_officer,
            "receiving_confirmation": self.receiving_confirmation,
            "transfer_completion_notes": self.transfer_completion_notes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "InmateTransfer":
        return cls(
            id=row.get("id"),
            inmate_id=row["inmate_id"],
            current_facility=row["current_facility"],
            destination_facility=row["destination_facility"],
            transfer_type=row["transfer_type"],
            reason=row["reason"],
            security_level=row["security_level"],
            medical_clearance=bool(row["medical_clearance"]),
            legal_verified=bool(row["legal_verified"]),
            security_assessed=bool(row["security_assessed"]),
            transfer_status=row["transfer_status"],
            urgency_level=row["urgency_level"],
            requested_date=row["requested_date"],
            departure_date=row.get("departure_date"),
            arrival_date=row.get("arrival_date"),
            escort_officers=row.get("escort_officers"),
            transport_vehicle=row.get("transport_vehicle"),
            route_details=row.get("route_details"),
            movement_authorized_by=row.get("movement_authorized_by"),
            approved_by=row.get("approved_by"),
            receiving_officer=row.get("receiving_officer"),
            receiving_confirmation=bool(row["receiving_confirmation"]),
            transfer_completion_notes=row.get("transfer_completion_notes"),
            created_by=row["created_by"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


@dataclass(frozen=True)
class InmateRelease:
    id: int | None
    inmate_id: int
    release_type: str
    release_reason: str
    sentence_validated: bool
    legal_verified: bool
    medical_cleared: bool
    property_cleared: bool
    identity_verified: bool
    release_status: str
    created_by: int
    release_certificate_number: str | None = None
    approved_by: int | None = None
    release_date: date | None = None
    release_time: time | None = None
    discharge_notes: str | None = None
    property_release_notes: str | None = None
    medical_discharge_summary: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "inmate_id": self.inmate_id,
            "release_type": self.release_type,
            "release_reason": self.release_reason,
            "sentence_validated": self.sentence_validated,
            "legal_verified": self.legal_verified,
            "medical_cleared": self.medical_cleared,
            "property_cleared": self.property_cleared,
            "identity_verified": self.identity_verified,
            "release_certificate_number": self.release_certificate_number,
            "approved_by": self.approved_by,
            "release_date": self.release_date.isoformat() if self.release_date else None,
            "release_time": self.release_time.isoformat() if self.release_time else None,
            "release_status": self.release_status,
            "discharge_notes": self.discharge_notes,
            "property_release_notes": self.property_release_notes,
            "medical_discharge_summary": self.medical_discharge_summary,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "InmateRelease":
        return cls(
            id=row.get("id"),
            inmate_id=row["inmate_id"],
            release_type=row["release_type"],
            release_reason=row["release_reason"],
            sentence_validated=bool(row["sentence_validated"]),
            legal_verified=bool(row["legal_verified"]),
            medical_cleared=bool(row["medical_cleared"]),
            property_cleared=bool(row["property_cleared"]),
            identity_verified=bool(row["identity_verified"]),
            release_certificate_number=row.get("release_certificate_number"),
            approved_by=row.get("approved_by"),
            release_date=row.get("release_date"),
            release_time=row.get("release_time"),
            release_status=row["release_status"],
            discharge_notes=row.get("discharge_notes"),
            property_release_notes=row.get("property_release_notes"),
            medical_discharge_summary=row.get("medical_discharge_summary"),
            created_by=row["created_by"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
