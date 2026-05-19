from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from src.models.arrest_warrant import (
    ARREST_WARRANT_ALLOWED_UPDATE_FIELDS,
    ARREST_WARRANT_DATE_FIELDS,
    ARREST_WARRANT_ENUM_FIELD_VALUES,
    ARREST_WARRANT_OPTIONAL_TEXT_FIELD_LENGTHS,
    ARREST_WARRANT_REQUIRED_TEXT_FIELD_LENGTHS,
    ARREST_WARRANT_TEXT_AREA_FIELDS,
    ArrestWarrant,
)


class ArrestWarrantValidationError(ValueError):
    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Validation failed")
        self.errors = errors


@dataclass(frozen=True)
class CreateArrestWarrantRequestDTO:
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

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CreateArrestWarrantRequestDTO":
        errors: dict[str, str] = {}
        _validate_create_payload(errors, payload)
        if errors:
            raise ArrestWarrantValidationError(errors)

        return cls(
            warrant_number=_required_string(payload, "warrant_number"),
            case_number=_required_string(payload, "case_number"),
            first_name=_required_string(payload, "first_name"),
            last_name=_required_string(payload, "last_name"),
            other_names=_optional_string(payload.get("other_names")),
            date_of_birth=_required_date(payload, "date_of_birth"),
            gender=_required_string(payload, "gender").lower(),
            nationality=_required_string(payload, "nationality"),
            national_id=_required_string(payload, "national_id"),
            offense=_required_string(payload, "offense"),
            offense_description=_required_string(payload.get("offense_description")),
            arrest_date=_required_date(payload, "arrest_date"),
            arresting_officer=_required_string(payload, "arresting_officer"),
            arresting_agency=_required_string(payload, "arresting_agency"),
            court=_required_string(payload, "court"),
            judge=_required_string(payload.get("judge")),
            sentence_type=_required_string(payload, "sentence_type").lower(),
            sentence_duration=_required_string(payload.get("sentence_duration")),
            status=_required_string(payload, "status").lower(),
            issued_date=_required_date(payload, "issued_date"),
        )


@dataclass(frozen=True)
class UpdateArrestWarrantRequestDTO:
    updates: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "UpdateArrestWarrantRequestDTO":
        errors: dict[str, str] = {}
        updates = _prepare_update_payload(errors, payload)
        if not updates:
            errors["request"] = "At least one arrest warrant field is required"
        if errors:
            raise ArrestWarrantValidationError(errors)
        return cls(updates=updates)


@dataclass(frozen=True)
class ArrestWarrantResponseDTO:
    arrest_warrant: ArrestWarrant

    def to_dict(self) -> dict[str, Any]:
        return self.arrest_warrant.to_dict()


def _validate_create_payload(errors: dict[str, str], payload: dict[str, Any]) -> None:
    for field, max_length in ARREST_WARRANT_REQUIRED_TEXT_FIELD_LENGTHS.items():
        _require_text(errors, payload, field, max_length=max_length)
    for field, max_length in ARREST_WARRANT_OPTIONAL_TEXT_FIELD_LENGTHS.items():
        _optional_text(errors, payload, field, max_length=max_length)
    for field in ARREST_WARRANT_TEXT_AREA_FIELDS:
        _optional_text(errors, payload, field)
    for field in ARREST_WARRANT_DATE_FIELDS:
        _require_date(errors, payload, field)
    _validate_enums(errors, payload)


def _prepare_update_payload(errors: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    for field, value in payload.items():
        if field not in ARREST_WARRANT_ALLOWED_UPDATE_FIELDS:
            errors[field] = "This field cannot be updated"
            continue
        if field in ARREST_WARRANT_REQUIRED_TEXT_FIELD_LENGTHS:
            _validate_required_text_value(errors, field, value, ARREST_WARRANT_REQUIRED_TEXT_FIELD_LENGTHS[field])
            if field not in errors:
                updates[field] = str(value).strip().lower() if field in ARREST_WARRANT_ENUM_FIELD_VALUES else str(value).strip()
        elif field in ARREST_WARRANT_OPTIONAL_TEXT_FIELD_LENGTHS:
            _validate_optional_text_value(errors, field, value, ARREST_WARRANT_OPTIONAL_TEXT_FIELD_LENGTHS[field])
            if field not in errors:
                updates[field] = _optional_string(value)
        elif field in ARREST_WARRANT_TEXT_AREA_FIELDS:
            _validate_optional_text_value(errors, field, value, None)
            if field not in errors:
                updates[field] = _optional_string(value)
        elif field in ARREST_WARRANT_DATE_FIELDS:
            updates[field] = _required_date_from_value(errors, field, value)
    _validate_enums(errors, {**payload, **updates}, partial=True)
    return {field: value for field, value in updates.items() if field not in errors}


def _validate_enums(errors: dict[str, str], payload: dict[str, Any], *, partial: bool = False) -> None:
    for field, allowed_values in ARREST_WARRANT_ENUM_FIELD_VALUES.items():
        if partial and field not in payload:
            continue
        value = payload.get(field)
        if value in {None, ""}:
            continue
        if not isinstance(value, str) or value.strip().lower() not in allowed_values:
            errors[field] = f"Must be one of: {', '.join(sorted(allowed_values))}"


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


def _required_date_from_value(errors: dict[str, str], field: str, value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        errors[field] = "This field is required"
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        errors[field] = "Must use YYYY-MM-DD"
        return None


def _required_string(payload: dict[str, Any], field: str) -> str:
    return str(payload[field]).strip()


def _required_date(payload: dict[str, Any], field: str) -> date:
    return date.fromisoformat(str(payload[field]).strip())


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None
