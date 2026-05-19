from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from src.config.settings import settings
from src.models.user import USER_ROLES, USER_SHIFTS, USER_STATUSES
from src.services.user_service import CreateUserData


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
OFFICER_ID_PATTERN = re.compile(r"^OFF\d{3,}$")
PHONE_PATTERN = re.compile(r"^\+?[0-9\s-]{7,20}$")


class UserValidationError(ValueError):
    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Validation failed")
        self.errors = errors


@dataclass(frozen=True)
class CreateUserRequestDTO:
    officer_id: str
    first_name: str
    last_name: str
    email: str
    password: str
    badge_number: str
    rank: str
    department: str
    shift: str
    date_joined: date
    phone: str | None = None
    middle_name: str | None = None
    gender: str | None = None
    dob: date | None = None
    national_id: str | None = None
    address: str | None = None
    profile_image: str | None = None
    staff_id: str | None = None
    position: str | None = None
    employment_date: date | None = None
    branch: str | None = None
    username: str | None = None
    role_id: int | None = None
    role: str = "officer"
    status: str = "active"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CreateUserRequestDTO":
        errors = validate_create_user_payload(payload)
        if errors:
            raise UserValidationError(errors)

        return cls(
            officer_id=payload["officer_id"].strip().upper(),
            first_name=payload["first_name"].strip(),
            middle_name=_optional_string(payload.get("middle_name")),
            last_name=payload["last_name"].strip(),
            gender=_optional_string(payload.get("gender")),
            dob=_optional_date(payload.get("dob")),
            email=payload["email"].strip().lower(),
            password=payload["password"],
            phone=_optional_string(payload.get("phone")),
            national_id=_optional_string(payload.get("national_id")),
            address=_optional_string(payload.get("address")),
            profile_image=_optional_string(payload.get("profile_image")),
            staff_id=_optional_string(payload.get("staff_id")),
            badge_number=payload["badge_number"].strip().upper(),
            rank=payload["rank"].strip(),
            department=payload["department"].strip(),
            position=_optional_string(payload.get("position")),
            employment_date=_optional_date(payload.get("employment_date")),
            branch=_optional_string(payload.get("branch")),
            username=_optional_string(payload.get("username")),
            role_id=_optional_int(payload.get("role_id")),
            role=payload.get("role", "officer").strip().lower(),
            shift=payload["shift"].strip().lower(),
            status=payload.get("status", "active").strip().lower(),
            date_joined=date.fromisoformat(payload["date_joined"]),
        )

    def to_service_data(self) -> CreateUserData:
        return CreateUserData(
            officer_id=self.officer_id,
            first_name=self.first_name,
            middle_name=self.middle_name,
            last_name=self.last_name,
            gender=self.gender,
            dob=self.dob,
            email=self.email,
            password=self.password,
            phone=self.phone,
            national_id=self.national_id,
            address=self.address,
            profile_image=self.profile_image,
            staff_id=self.staff_id,
            badge_number=self.badge_number,
            rank=self.rank,
            department=self.department,
            position=self.position,
            employment_date=self.employment_date,
            branch=self.branch,
            username=self.username,
            role_id=self.role_id,
            role=self.role,
            shift=self.shift,
            status=self.status,
            date_joined=self.date_joined,
        )


@dataclass(frozen=True)
class LoginRequestDTO:
    identifier: str
    password: str
    login_field: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "LoginRequestDTO":
        errors = validate_login_payload(payload)
        if errors:
            raise UserValidationError(errors)

        has_email = isinstance(payload.get("email"), str) and payload["email"].strip()
        login_field = "email" if has_email else "username"
        return cls(
            identifier=payload[login_field].strip().lower(),
            password=payload["password"],
            login_field=login_field,
        )


@dataclass(frozen=True)
class UpdateStaffUserRequestDTO:
    updates: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "UpdateStaffUserRequestDTO":
        updates = {
            field: value
            for field, value in payload.items()
            if field not in {"lookup_field", "lookup_value"}
        }
        errors = validate_update_staff_payload(updates)
        if errors:
            raise UserValidationError(errors)
        return cls(updates=updates)


def validate_create_user_payload(payload: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    _require_text(errors, payload, "officer_id", max_length=20)
    _require_text(errors, payload, "first_name", max_length=50)
    _require_text(errors, payload, "last_name", max_length=50)
    _require_text(errors, payload, "email", max_length=100)
    _require_text(errors, payload, "password", min_length=settings.password_min_length, max_length=settings.password_max_length)
    _require_text(errors, payload, "badge_number", max_length=30)
    _require_text(errors, payload, "rank", max_length=50)
    _require_text(errors, payload, "department", max_length=50)
    _require_text(errors, payload, "shift", max_length=20)
    _require_text(errors, payload, "date_joined")

    _optional_text(errors, payload, "middle_name", max_length=50)
    _optional_text(errors, payload, "gender", max_length=20)
    _optional_text(errors, payload, "national_id", max_length=50)
    _optional_text(errors, payload, "address")
    _optional_text(errors, payload, "profile_image", max_length=255)
    _optional_text(errors, payload, "staff_id", max_length=50)
    _optional_text(errors, payload, "position", max_length=100)
    _optional_text(errors, payload, "branch", max_length=100)
    _optional_text(errors, payload, "username", max_length=100)

    email = payload.get("email")
    if isinstance(email, str) and not EMAIL_PATTERN.match(email.strip()):
        errors["email"] = "Enter a valid email address"

    officer_id = payload.get("officer_id")
    if isinstance(officer_id, str) and not OFFICER_ID_PATTERN.match(officer_id.strip().upper()):
        errors["officer_id"] = "Officer ID must use the format OFF001"

    phone = payload.get("phone")
    if phone not in {None, ""} and (not isinstance(phone, str) or not PHONE_PATTERN.match(phone.strip())):
        errors["phone"] = "Enter a valid phone number"

    role = str(payload.get("role", "officer")).strip().lower()
    if role not in USER_ROLES:
        errors["role"] = "Role must be admin, officer, supervisor, medical_officer, records_officer, or visitor_officer"

    shift = str(payload.get("shift", "")).strip().lower()
    if shift not in USER_SHIFTS:
        errors["shift"] = "Shift must be morning, afternoon, or night"

    status = str(payload.get("status", "active")).strip().lower()
    if status not in USER_STATUSES:
        errors["status"] = "Status must be active, inactive, or suspended"

    password = payload.get("password")
    if isinstance(password, str):
        password_errors = validate_password_strength(password)
        if password_errors:
            errors["password"] = "; ".join(password_errors)
        if password in settings.compromised_passwords:
            errors["password"] = "Password is not allowed"

    try:
        date.fromisoformat(str(payload.get("date_joined", "")))
    except ValueError:
        errors["date_joined"] = "Date joined must use YYYY-MM-DD"

    _validate_optional_date(errors, payload, "dob")
    _validate_optional_date(errors, payload, "employment_date")
    _validate_optional_int(errors, payload, "role_id")

    return errors


def validate_login_payload(payload: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    has_email = isinstance(payload.get("email"), str) and payload["email"].strip()
    has_username = isinstance(payload.get("username"), str) and payload["username"].strip()

    if has_email and has_username:
        errors["login"] = "Provide either email or username, not both"
    elif not has_email and not has_username:
        errors["login"] = "Email or username is required"

    if has_email:
        email = payload["email"].strip()
        if len(email) > 100:
            errors["email"] = "Must be at most 100 characters"
        elif not EMAIL_PATTERN.match(email):
            errors["email"] = "Enter a valid email address"

    if has_username:
        username = payload["username"].strip()
        if len(username) > 100:
            errors["username"] = "Must be at most 100 characters"

    _require_text(errors, payload, "password", min_length=1, max_length=settings.password_max_length)

    return errors


def validate_update_staff_payload(updates: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    allowed_fields = {
        "officer_id",
        "first_name",
        "middle_name",
        "last_name",
        "gender",
        "dob",
        "email",
        "password",
        "phone",
        "national_id",
        "address",
        "profile_image",
        "rank",
        "department",
        "position",
        "employment_date",
        "branch",
        "role_id",
        "role",
        "shift",
        "status",
        "date_joined",
    }
    for field in updates:
        if field not in allowed_fields:
            errors[field] = "This field cannot be updated here"

    _validate_optional_length(errors, updates, "officer_id", 20)
    _validate_optional_length(errors, updates, "first_name", 50)
    _validate_optional_length(errors, updates, "middle_name", 50)
    _validate_optional_length(errors, updates, "last_name", 50)
    _validate_optional_length(errors, updates, "gender", 20)
    _validate_optional_length(errors, updates, "email", 100)
    _validate_optional_length(errors, updates, "phone", 20)
    _validate_optional_length(errors, updates, "national_id", 50)
    _validate_optional_length(errors, updates, "profile_image", 255)
    _validate_optional_length(errors, updates, "rank", 50)
    _validate_optional_length(errors, updates, "department", 50)
    _validate_optional_length(errors, updates, "position", 100)
    _validate_optional_length(errors, updates, "branch", 100)

    email = updates.get("email")
    if isinstance(email, str) and email.strip() and not EMAIL_PATTERN.match(email.strip()):
        errors["email"] = "Enter a valid email address"

    officer_id = updates.get("officer_id")
    if isinstance(officer_id, str) and officer_id.strip() and not OFFICER_ID_PATTERN.match(officer_id.strip().upper()):
        errors["officer_id"] = "Officer ID must use the format OFF001"

    phone = updates.get("phone")
    if phone not in {None, ""} and "phone" in updates and (not isinstance(phone, str) or not PHONE_PATTERN.match(phone.strip())):
        errors["phone"] = "Enter a valid phone number"

    role = str(updates.get("role", "")).strip().lower()
    if role and role not in USER_ROLES:
        errors["role"] = "Role must be admin, officer, supervisor, medical_officer, records_officer, or visitor_officer"

    shift = str(updates.get("shift", "")).strip().lower()
    if shift and shift not in USER_SHIFTS:
        errors["shift"] = "Shift must be morning, afternoon, or night"

    status = str(updates.get("status", "")).strip().lower()
    if status and status not in USER_STATUSES:
        errors["status"] = "Status must be active, inactive, or suspended"

    password = updates.get("password")
    if isinstance(password, str) and password:
        password_errors = validate_password_strength(password)
        if password_errors:
            errors["password"] = "; ".join(password_errors)
        if password in settings.compromised_passwords:
            errors["password"] = "Password is not allowed"

    _validate_optional_date(errors, updates, "dob")
    _validate_optional_date(errors, updates, "employment_date")
    _validate_optional_date(errors, updates, "date_joined")
    _validate_optional_int(errors, updates, "role_id")

    return errors


def validate_password_strength(password: str) -> list[str]:
    errors: list[str] = []
    if settings.password_require_uppercase and not any(char.isupper() for char in password):
        errors.append("Password must include an uppercase letter")
    if settings.password_require_lowercase and not any(char.islower() for char in password):
        errors.append("Password must include a lowercase letter")
    if settings.password_require_number and not any(char.isdigit() for char in password):
        errors.append("Password must include a number")
    if settings.password_require_special and not any(not char.isalnum() for char in password):
        errors.append("Password must include a special character")
    return errors


def _require_text(
    errors: dict[str, str],
    payload: dict[str, Any],
    field: str,
    *,
    min_length: int = 1,
    max_length: int | None = None,
) -> None:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        errors[field] = "This field is required"
        return
    if len(value.strip()) < min_length:
        errors[field] = f"Must be at least {min_length} characters"
    if max_length is not None and len(value.strip()) > max_length:
        errors[field] = f"Must be at most {max_length} characters"


def _optional_text(
    errors: dict[str, str],
    payload: dict[str, Any],
    field: str,
    *,
    max_length: int | None = None,
) -> None:
    value = payload.get(field)
    if value in {None, ""}:
        return
    if not isinstance(value, str):
        errors[field] = "Must be text"
        return
    if max_length is not None and len(value.strip()) > max_length:
        errors[field] = f"Must be at most {max_length} characters"


def _validate_optional_length(errors: dict[str, str], payload: dict[str, Any], field: str, max_length: int) -> None:
    value = payload.get(field)
    if value in {None, ""}:
        return
    if not isinstance(value, str):
        errors[field] = "Must be text"
    elif len(value.strip()) > max_length:
        errors[field] = f"Must be at most {max_length} characters"


def _validate_optional_date(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    value = payload.get(field)
    if value in {None, ""}:
        return
    if not isinstance(value, str):
        errors[field] = "Must use YYYY-MM-DD"
        return
    try:
        date.fromisoformat(value.strip())
    except ValueError:
        errors[field] = "Must use YYYY-MM-DD"


def _validate_optional_int(errors: dict[str, str], payload: dict[str, Any], field: str) -> None:
    value = payload.get(field)
    if value in {None, ""}:
        return
    try:
        int(value)
    except (TypeError, ValueError):
        errors[field] = "Must be an integer"


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _optional_date(value: Any) -> date | None:
    value = _optional_string(value)
    if value is None:
        return None
    return date.fromisoformat(value)


def _optional_int(value: Any) -> int | None:
    value = _optional_string(value)
    if value is None:
        return None
    return int(value)
