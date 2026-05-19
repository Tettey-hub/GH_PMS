from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


ARREST_WARRANT_GENDERS = {"male", "female"}
ARREST_WARRANT_SENTENCE_TYPES = {"remand", "convicted", "life", "death"}
ARREST_WARRANT_STATUSES = {"pending", "executed", "cancelled"}
ARREST_WARRANT_REQUIRED_TEXT_FIELD_LENGTHS = {
    "warrant_number": 30,
    "case_number": 30,
    "first_name": 50,
    "last_name": 50,
    "gender": 10,
    "nationality": 50,
    "offense": 100,
    "arresting_officer": 100,
    "arresting_agency": 100,
    "court": 100,
    "sentence_type": 30,
    "status": 20,
}
ARREST_WARRANT_OPTIONAL_TEXT_FIELD_LENGTHS = {
    "other_names": 100,
    "national_id": 50,
    "judge": 100,
    "sentence_duration": 50,
}
ARREST_WARRANT_TEXT_AREA_FIELDS = {"offense_description"}
ARREST_WARRANT_DATE_FIELDS = {"date_of_birth", "arrest_date", "issued_date"}
ARREST_WARRANT_ENUM_FIELD_VALUES = {
    "gender": ARREST_WARRANT_GENDERS,
    "sentence_type": ARREST_WARRANT_SENTENCE_TYPES,
    "status": ARREST_WARRANT_STATUSES,
}
ARREST_WARRANT_ALLOWED_UPDATE_FIELDS = (
    set(ARREST_WARRANT_REQUIRED_TEXT_FIELD_LENGTHS)
    | set(ARREST_WARRANT_OPTIONAL_TEXT_FIELD_LENGTHS)
    | ARREST_WARRANT_TEXT_AREA_FIELDS
    | ARREST_WARRANT_DATE_FIELDS
)


@dataclass(frozen=True)
class ArrestWarrant:
    id: int | None
    warrant_number: str
    case_number: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    nationality: str
    offense: str
    arrest_date: date
    arresting_officer: str
    arresting_agency: str
    court: str
    sentence_type: str
    status: str
    issued_date: date
    other_names: str | None = None
    national_id: str | None = None
    offense_description: str | None = None
    judge: str | None = None
    sentence_duration: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "warrant_number": self.warrant_number,
            "case_number": self.case_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "other_names": self.other_names,
            "date_of_birth": self.date_of_birth.isoformat(),
            "gender": self.gender,
            "nationality": self.nationality,
            "national_id": self.national_id,
            "offense": self.offense,
            "offense_description": self.offense_description,
            "arrest_date": self.arrest_date.isoformat(),
            "arresting_officer": self.arresting_officer,
            "arresting_agency": self.arresting_agency,
            "court": self.court,
            "judge": self.judge,
            "sentence_type": self.sentence_type,
            "sentence_duration": self.sentence_duration,
            "status": self.status,
            "issued_date": self.issued_date.isoformat(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ArrestWarrant":
        return cls(
            id=row.get("id"),
            warrant_number=row["warrant_number"],
            case_number=row["case_number"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            other_names=row.get("other_names"),
            date_of_birth=row["date_of_birth"],
            gender=row["gender"],
            nationality=row["nationality"],
            national_id=row.get("national_id"),
            offense=row["offense"],
            offense_description=row.get("offense_description"),
            arrest_date=row["arrest_date"],
            arresting_officer=row["arresting_officer"],
            arresting_agency=row["arresting_agency"],
            court=row["court"],
            judge=row.get("judge"),
            sentence_type=row["sentence_type"],
            sentence_duration=row.get("sentence_duration"),
            status=row["status"],
            issued_date=row["issued_date"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
