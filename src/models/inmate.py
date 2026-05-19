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
