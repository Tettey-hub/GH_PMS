from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal, InvalidOperation
from pathlib import PurePath
from typing import Any

from src.models.inmate import (
    INMATE_ALLOWED_PHOTO_EXTENSIONS,
    INMATE_ALLOWED_UPDATE_FIELDS,
    INMATE_DATE_FIELDS,
    INMATE_DECIMAL_FIELDS,
    INMATE_ENUM_FIELD_VALUES,
    INMATE_INT_FIELDS,
    INMATE_OPTIONAL_TEXT_FIELD_LENGTHS,
    INMATE_REQUIRED_TEXT_FIELD_LENGTHS,
    INMATE_TEXT_AREA_FIELDS,
    Inmate,
)


class InmateValidationError(ValueError):
    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Validation failed")
        self.errors = errors


@dataclass(frozen=True)
class CreateInmateRequestDTO:
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

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CreateInmateRequestDTO":
        errors: dict[str, str] = {}
        _validate_create_payload(errors, payload)
        if errors:
            raise InmateValidationError(errors)

        return cls(
            inmate_id=_required_string(payload, "inmate_id"),
            warrant_id=_required_int(payload, "warrant_id"),
            first_name=_required_string(payload, "first_name"),
            last_name=_required_string(payload, "last_name"),
            other_names=_optional_string(payload.get("other_names")),
            date_of_birth=_required_date(payload, "date_of_birth"),
            age=_required_int(payload, "age"),
            gender=_required_string(payload, "gender").lower(),
            nationality=_required_string(payload, "nationality"),
            national_id=_optional_string(payload.get("national_id")),
            phone=_optional_string(payload.get("phone")),
            address=_optional_string(payload.get("address")),
            marital_status=_required_string(payload, "marital_status").lower(),
            photo=_optional_string(payload.get("photo")),
            fingerprint_id=_optional_string(payload.get("fingerprint_id")),
            height_cm=_optional_decimal(payload.get("height_cm")),
            weight_kg=_optional_decimal(payload.get("weight_kg")),
            eye_color=_optional_string(payload.get("eye_color")),
            hair_color=_optional_string(payload.get("hair_color")),
            distinguishing_marks=_optional_string(payload.get("distinguishing_marks")),
            religion=_optional_string(payload.get("religion")),
            occupation=_optional_string(payload.get("occupation")),
            education_level=_optional_string(payload.get("education_level")),
            next_of_kin_name=_required_string(payload, "next_of_kin_name"),
            next_of_kin_relation=_required_string(payload, "next_of_kin_relation").lower(),
            next_of_kin_contact=_optional_string(payload.get("next_of_kin_contact")),
            next_of_kin_address=_optional_string(payload.get("next_of_kin_address")),
            case_number=_required_string(payload, "case_number"),
            offense=_required_string(payload, "offense"),
            offense_description=_optional_string(payload.get("offense_description")),
            arrest_date=_required_date(payload, "arrest_date"),
            arresting_officer=_required_string(payload, "arresting_officer"),
            arresting_agency=_required_string(payload, "arresting_agency"),
            court=_required_string(payload, "court"),
            judge=_optional_string(payload.get("judge")),
            sentence_type=_required_string(payload, "sentence_type").lower(),
            sentence_duration=_optional_string(payload.get("sentence_duration")),
            expected_release_date=_optional_date(payload.get("expected_release_date")),
            status=_required_string(payload, "status").lower(),
            admission_date=_required_date(payload, "admission_date"),
            admission_time=_required_time(payload, "admission_time"),
            admission_officer_id=_required_int(payload, "admission_officer_id"),
        )


@dataclass(frozen=True)
class UpdateInmateRequestDTO:
    updates: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "UpdateInmateRequestDTO":
        errors: dict[str, str] = {}
        updates = _prepare_update_payload(errors, payload)
        if not updates:
            errors["request"] = "At least one inmate field is required"
        if errors:
            raise InmateValidationError(errors)
        return cls(updates=updates)


@dataclass(frozen=True)
class InmateResponseDTO:
    inmate: Inmate

    def to_dict(self) -> dict[str, Any]:
        return self.inmate.to_dict()


def _validate_create_payload(errors: dict[str, str], payload: dict[str, Any]) -> None:
    for field, max_length in INMATE_REQUIRED_TEXT_FIELD_LENGTHS.items():
        _require_text(errors, payload, field, max_length=max_length)
    _require_date(errors, payload, "date_of_birth")
    _require_date(errors, payload, "arrest_date")
    _require_date(errors, payload, "admission_date")
    _require_time(errors, payload, "admission_time")
    for field in INMATE_INT_FIELDS:
        _require_int(errors, payload, field)
    _validate_optional_fields(errors, payload)
    _validate_payload_business_rules(errors, payload)


def _prepare_update_payload(errors: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    for field, value in payload.items():
        if field not in INMATE_ALLOWED_UPDATE_FIELDS:
            errors[field] = "This field cannot be updated"
            continue
        if field in INMATE_REQUIRED_TEXT_FIELD_LENGTHS:
            _validate_required_text_value(errors, field, value, INMATE_REQUIRED_TEXT_FIELD_LENGTHS[field])
            if field not in errors:
                updates[field] = str(value).strip().lower() if field in _enum_fields() else str(value).strip()
        elif field in INMATE_OPTIONAL_TEXT_FIELD_LENGTHS:
            _validate_optional_text_value(errors, field, value, INMATE_OPTIONAL_TEXT_FIELD_LENGTHS[field])
            if field not in errors:
                updates[field] = _optional_string(value)
        elif field in INMATE_TEXT_AREA_FIELDS:
            _validate_optional_text_value(errors, field, value, None)
            if field not in errors:
                updates[field] = _optional_string(value)
        elif field in INMATE_DATE_FIELDS:
            if field == "expected_release_date":
                updates[field] = _optional_date(value)
            else:
                updates[field] = _required_date_from_value(errors, field, value)
        elif field in INMATE_INT_FIELDS:
            updates[field] = _required_int_from_value(errors, field, value)
        elif field in INMATE_DECIMAL_FIELDS:
            try:
                updates[field] = _optional_decimal(value)
            except ValueError:
                errors[field] = "Must be a decimal number"
        elif field == "admission_time":
            updates[field] = _required_time_from_value(errors, field, value)

    _validate_payload_business_rules(errors, {**payload, **updates}, partial=True)
    return {field: value for field, value in updates.items() if field not in errors}


def _validate_optional_fields(errors: dict[str, str], payload: dict[str, Any]) -> None:
    for field, max_length in INMATE_OPTIONAL_TEXT_FIELD_LENGTHS.items():
        _optional_text(errors, payload, field, max_length=max_length)
    for field in INMATE_TEXT_AREA_FIELDS:
        _optional_text(errors, payload, field)
    _optional_date_field(errors, payload, "expected_release_date")
    for field in INMATE_DECIMAL_FIELDS:
        _optional_decimal_field(errors, payload, field)


def _validate_payload_business_rules(errors: dict[str, str], payload: dict[str, Any], *, partial: bool = False) -> None:
    for field, allowed_values in INMATE_ENUM_FIELD_VALUES.items():
        _validate_enum(errors, payload, field, allowed_values, partial=partial)

    age = payload.get("age")
    if age not in {None, ""}:
        try:
            if int(age) < 0:
                errors["age"] = "Age must not be negative"
        except (TypeError, ValueError):
            errors["age"] = "Must be an integer"

    arrest_date = _safe_date(payload.get("arrest_date"))
    admission_date = _safe_date(payload.get("admission_date"))
    expected_release_date = _safe_date(payload.get("expected_release_date"))
    if arrest_date and admission_date and arrest_date > admission_date:
        errors["arrest_date"] = "Arrest date cannot be after admission date"
    if expected_release_date and admission_date and expected_release_date < admission_date:
        errors["expected_release_date"] = "Expected release date cannot be earlier than admission date"

    photo = _optional_string(payload.get("photo"))
    if photo and not _is_safe_upload_path(photo):
        errors["photo"] = "Photo path is not safe"


def _enum_fields() -> set[str]:
    return set(INMATE_ENUM_FIELD_VALUES)


def _validate_enum(errors: dict[str, str], payload: dict[str, Any], field: str, allowed: set[str], *, partial: bool) -> None:
    if partial and field not in payload:
        return
    value = payload.get(field)
    if value in {None, ""}:
        return
    if not isinstance(value, str) or value.strip().lower() not in allowed:
        errors[field] = f"Must be one of: {', '.join(sorted(allowed))}"


def _require_text(errors: dict[str, str], payload: dict[str, Any], field: str, *, max_length: int) -> None:
    _validate_required_text_value(errors, field, payload.get(field), max_length)


def _validate_required_text_value(errors: dict[str, str], field: str, value: Any, max_length: int) -> None:
    if not isinstance(value, str) or not value.strip():
        errors[field] = "This field is required"
    elif len(value.strip()) > max_length:
        errors[field] = f"Must be at most {max_length} characters"


def _optional_text(errors: dict[str, str], payload: dict[str, Any], field: str, *, max_length: int | None = None) -> None:
    _validate_optional_text_value(errors, field, payload.get(field), max_length)


def _validate_optional_text_value(errors: dict[str, str], field: str, value: Any, max_length: int | None) -> None:
    if value in {None, ""}:
        return
    if not isinstance(value, str):
        errors[field] = "Must be text"
    elif max_length is not None and len(value.strip()) > max_length:
        errors[field] = f"Must be at most {max_length} characters"


def _require_date(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    _required_date_from_value(errors, field, payload.get(field))


def _optional_date_field(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if payload.get(field) in {None, ""}:
        return
    _required_date_from_value(errors, field, payload.get(field))


def _required_date_from_value(errors: dict[str, str], field: str, value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        errors[field] = "This field is required"
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        errors[field] = "Must use YYYY-MM-DD"
        return None


def _require_time(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    _required_time_from_value(errors, field, payload.get(field))


def _required_time_from_value(errors: dict[str, str], field: str, value: Any) -> time | None:
    if not isinstance(value, str) or not value.strip():
        errors[field] = "This field is required"
        return None
    try:
        return time.fromisoformat(value.strip())
    except ValueError:
        errors[field] = "Must use HH:MM or HH:MM:SS"
        return None


def _require_int(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    _required_int_from_value(errors, field, payload.get(field))


def _required_int_from_value(errors: dict[str, str], field: str, value: Any) -> int | None:
    if value in {None, ""}:
        errors[field] = "This field is required"
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        errors[field] = "Must be an integer"
        return None


def _optional_decimal_field(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    if payload.get(field) in {None, ""}:
        return
    try:
        _optional_decimal(payload.get(field))
    except ValueError:
        errors[field] = "Must be a decimal number"


def _required_string(payload: dict[str, Any], field: str) -> str:
    return str(payload[field]).strip()


def _required_date(payload: dict[str, Any], field: str) -> date:
    return date.fromisoformat(str(payload[field]).strip())


def _required_time(payload: dict[str, Any], field: str) -> time:
    return time.fromisoformat(str(payload[field]).strip())


def _required_int(payload: dict[str, Any], field: str) -> int:
    return int(payload[field])


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _optional_date(value: Any) -> date | None:
    value = _optional_string(value)
    return date.fromisoformat(value) if value else None


def _optional_decimal(value: Any) -> Decimal | None:
    value = _optional_string(value)
    if value is None:
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid decimal value") from exc


def _safe_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _is_safe_upload_path(path: str) -> bool:
    if "\x00" in path or "\\" in path:
        return False
    pure_path = PurePath(path)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        return False
    return pure_path.suffix.lower() in INMATE_ALLOWED_PHOTO_EXTENSIONS
