from __future__ import annotations

import re
from datetime import date
from typing import Any

from flask import g, jsonify, request
from mysql.connector import Error as MySQLError

from src.config.settings import settings
from src.services.account_lockout_service import AccountLockoutService
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.services.user_service import CreateUserData, UserService, is_duplicate_user_error


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
OFFICER_ID_PATTERN = re.compile(r"^OFF\d{3,}$")
PHONE_PATTERN = re.compile(r"^\+?[0-9\s-]{7,20}$")


def bootstrap_admin():
    """
    One-time endpoint to create the first admin user.
    Only works if no admin exists in the system.
    Uses SUPERADMIN_* environment variables.
    """
    # Check if any admin already exists
    admin_exists = UserService.user_exists_with_role("admin")
    if admin_exists:
        return _error("System already initialized with an admin account", 409)

    # Validate required environment variables
    missing_vars = []
    superadmin_email = settings.superadmin_email.strip()
    superadmin_password = settings.superadmin_password.strip()
    superadmin_first_name = settings.superadmin_first_name.strip()
    superadmin_last_name = settings.superadmin_last_name.strip()

    if not superadmin_email:
        missing_vars.append("SUPERADMIN_EMAIL")
    if not superadmin_password:
        missing_vars.append("SUPERADMIN_PASSWORD")
    if not superadmin_first_name:
        missing_vars.append("SUPERADMIN_FIRST_NAME")
    if not superadmin_last_name:
        missing_vars.append("SUPERADMIN_LAST_NAME")

    if missing_vars:
        return _error(
            f"Bootstrap failed: missing environment variables: {', '.join(missing_vars)}",
            500
        )

    # Validate email format
    if not EMAIL_PATTERN.match(superadmin_email):
        return _error("Invalid SUPERADMIN_EMAIL format", 500)

    # Validate password strength
    password_errors = _validate_password_strength(superadmin_password)
    if password_errors:
        return _error(
            f"SUPERADMIN_PASSWORD does not meet requirements: {'; '.join(password_errors)}",
            500
        )

    try:
        admin_user = UserService.create_user(
            CreateUserData(
                officer_id="OFF000",  # Special ID for bootstrap admin
                first_name=superadmin_first_name,
                last_name=superadmin_last_name,
                email=superadmin_email,
                password=superadmin_password,
                phone=None,
                badge_number="ADMIN-BOOTSTRAP",
                rank="System Administrator",
                department="Administration",
                role="admin",
                shift="morning",
                status="active",
                date_joined=date.today(),
            )
        )
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_duplicate_user_error(exc):
            return _error("Bootstrap failed: admin user already exists", 409)
        if isinstance(exc, MySQLError):
            return _error("Database error during bootstrap", 500)
        raise

    AuditService.record(
        action="bootstrap_admin",
        status="success",
        target_user_id=admin_user.id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"officer_id": admin_user.officer_id},
    )

    return jsonify({
        "message": "Bootstrap successful. Admin user created.",
        "user": admin_user.to_dict(),
    }), 201


def register_user():
    payload = _json_payload()
    errors = _validate_register_payload(payload)
    if errors:
        return _error("Validation failed", 400, errors)

    try:
        user = UserService.create_user(
            CreateUserData(
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
        )
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_duplicate_user_error(exc):
            return _error("Officer ID, email, or badge number already exists", 409)
        if isinstance(exc, MySQLError):
            return _error("Database error while creating user", 500)
        raise

    AuditService.record(
        action="admin_created",
        status="success",
        actor_user_id=g.current_user.id,
        target_user_id=user.id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"target_officer_id": user.officer_id, "target_role": user.role},
    )
    return jsonify({"message": "User created successfully", "user": user.to_dict()}), 201


def login():
    payload = _json_payload()
    errors = _validate_login_payload(payload)
    if errors:
        return _error("Validation failed", 400, errors)

    identifier = _login_identifier(payload)
    lockout_state = AccountLockoutService.get_state(identifier)
    if lockout_state.locked:
        AuditService.record(
            action="login_failed",
            status="locked",
            ip_address=_client_ip(),
            user_agent=_user_agent(),
            metadata={"identifier": identifier, "reason": "account_locked"},
        )
        return _error("Account is temporarily locked", 423)

    user = AuthService.authenticate(identifier, payload["password"])
    if user is None:
        existing_user = UserService.get_by_login_identifier(identifier)
        failure_state = AccountLockoutService.record_failure(identifier, existing_user.id if existing_user else None)
        AuditService.record(
            action="login_failed",
            status="failed",
            actor_user_id=existing_user.id if existing_user else None,
            ip_address=_client_ip(),
            user_agent=_user_agent(),
            metadata={
                "identifier": identifier,
                "failed_attempts": failure_state.failed_attempts,
                "locked": failure_state.locked,
                "reason": "invalid_credentials",
            },
        )
        return _error("Invalid email/username or password", 401)

    if user.id is None:
        return _error("User account is missing an ID", 500)

    AccountLockoutService.clear(identifier)
    AuditService.record(
        action="login",
        status="success",
        actor_user_id=user.id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"officer_id": user.officer_id, "role": user.role},
    )
    tokens = AuthService.issue_tokens(user)

    response = jsonify({
        "message": "Login successful",
        "token_type": tokens["token_type"],
        "access_token": tokens["access_token"],
        "expires_in_minutes": settings.access_token_expire_minutes,
        "user": user.to_dict(),
    })

    response.set_cookie(
        "refresh_token",
        tokens["refresh_token"],
        max_age=settings.refresh_token_expire_days * 86400,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="Strict",
        path="/"
    )
    return response


def refresh_token():
    # First check for token in cookie (preferred), then in JSON body (backward compatibility)
    token = request.cookies.get("refresh_token")
    
    if not token:
        payload = _json_payload()
        token = payload.get("refresh_token")
    
    if not isinstance(token, str) or not token.strip():
        return _error("refresh_token is required", 400)

    try:
        refreshed = AuthService.refresh_session(token.strip())
    except (ValueError, TypeError):
        AuditService.record(
            action="token_refresh",
            status="failed",
            ip_address=_client_ip(),
            user_agent=_user_agent(),
            metadata={"reason": "invalid_or_expired"},
        )
        return _error("Invalid or expired refresh token", 401)

    if refreshed is None:
        AuditService.record(
            action="token_refresh",
            status="failed",
            ip_address=_client_ip(),
            user_agent=_user_agent(),
            metadata={"reason": "revoked_or_inactive"},
        )
        return _error("Invalid or revoked refresh token", 401)

    user, tokens = refreshed
    AuditService.record(
        action="token_refresh",
        status="success",
        actor_user_id=user.id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"officer_id": user.officer_id},
    )

    response = jsonify({
        "token_type": "Bearer",
        "access_token": tokens["access_token"],
        "expires_in_minutes": settings.access_token_expire_minutes,
    })
    
    response.set_cookie(
        "refresh_token",
        tokens["refresh_token"],
        max_age=settings.refresh_token_expire_days * 86400,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="Strict",
        path="/"
    )
    return response


def logout():
    revoked_count = AuthService.logout_user(g.current_user.id)
    AuditService.record(
        action="logout",
        status="success",
        actor_user_id=g.current_user.id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"revoked_refresh_tokens": revoked_count},
    )
    return jsonify({"message": "Logout successful", "revoked_refresh_tokens": revoked_count})


def current_user():
    return jsonify({"user": g.current_user.to_dict()})


def list_users():
    users = UserService.get_all_users()
    return jsonify({
        "total": len(users),
        "users": [user.to_dict() for user in users],
    })


def get_staff_user():
    try:
        field, value = _staff_lookup_from_request()
        user = UserService.get_by_staff_lookup(field, value)
    except ValueError as exc:
        return _error(str(exc), 400)

    if user is None:
        return _error("Staff user not found", 404)

    return jsonify({"user": user.to_dict()})


def update_staff_user():
    payload = _json_payload()
    try:
        field, value = _staff_lookup_from_request()
        updates = _staff_update_payload(payload)
        errors = _validate_staff_update_payload(updates)
        if errors:
            return _error("Validation failed", 400, errors)
        user = UserService.update_by_staff_lookup(field, value, updates)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_duplicate_user_error(exc):
            return _error("Officer ID, email, staff ID, username, or badge number already exists", 409)
        if isinstance(exc, MySQLError):
            return _error("Database error while updating user", 500)
        raise

    if user is None:
        return _error("Staff user not found", 404)

    AuditService.record(
        action="staff_updated",
        status="success",
        actor_user_id=g.current_user.id,
        target_user_id=user.id,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={"lookup_field": field, "updated_fields": sorted(updates.keys())},
    )
    return jsonify({"message": "Staff user updated successfully", "user": user.to_dict()})


def delete_staff_user():
    try:
        field, value = _staff_lookup_from_request()
        user = UserService.get_by_staff_lookup(field, value)
    except ValueError as exc:
        return _error(str(exc), 400)

    if user is None:
        return _error("Staff user not found", 404)
    if user.id == g.current_user.id:
        return _error("You cannot delete your own active account", 400)

    try:
        deleted_user = UserService.delete_by_staff_lookup(field, value)
    except MySQLError:
        return _error("Database error while deleting user", 500)

    if deleted_user is None:
        return _error("Staff user not found", 404)

    AuditService.record(
        action="staff_deleted",
        status="success",
        actor_user_id=g.current_user.id,
        target_user_id=None,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata={
            "deleted_user_id": deleted_user.id,
            "lookup_field": field,
            "officer_id": deleted_user.officer_id,
            "staff_id": deleted_user.staff_id,
            "badge_number": deleted_user.badge_number,
            "username": deleted_user.username,
        },
    )
    return jsonify({"message": "Staff user deleted successfully", "user": deleted_user.to_dict()})


def _json_payload() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def _staff_lookup_from_request() -> tuple[str, str]:
    payload = _json_payload()
    query_payload = request.args.to_dict()
    try:
        return _staff_lookup_from_payload(query_payload)
    except ValueError:
        return _staff_lookup_from_payload(payload)


def _staff_lookup_from_payload(payload: dict[str, Any]) -> tuple[str, str]:
    lookup_fields = ("staff_id", "officer_id", "badge_number", "username")
    provided = [
        field
        for field in lookup_fields
        if isinstance(payload.get(field), str) and payload[field].strip()
    ]
    if len(provided) != 1:
        raise ValueError("Provide exactly one lookup field: staff_id, officer_id, badge_number, or username")
    field = provided[0]
    return field, payload[field].strip()


def _staff_update_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        field: value
        for field, value in payload.items()
        if field not in {"lookup_field", "lookup_value"}
    }


def _validate_register_payload(payload: dict[str, Any]) -> dict[str, str]:
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
    if role not in {"admin", "officer", "supervisor", "medical_officer", "records_officer", "visitor_officer"}:
        errors["role"] = "Role must be admin, officer, supervisor, medical_officer, records_officer, or visitor_officer"

    shift = str(payload.get("shift", "")).strip().lower()
    if shift not in {"morning", "afternoon", "night"}:
        errors["shift"] = "Shift must be morning, afternoon, or night"

    status = str(payload.get("status", "active")).strip().lower()
    if status not in {"active", "inactive", "suspended"}:
        errors["status"] = "Status must be active, inactive, or suspended"

    password = payload.get("password")
    if isinstance(password, str):
        password_errors = _validate_password_strength(password)
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


def _validate_login_payload(payload: dict[str, Any]) -> dict[str, str]:
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


def _validate_staff_update_payload(updates: dict[str, Any]) -> dict[str, str]:
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
    if role and role not in {"admin", "officer", "supervisor", "medical_officer", "records_officer", "visitor_officer"}:
        errors["role"] = "Role must be admin, officer, supervisor, medical_officer, records_officer, or visitor_officer"

    shift = str(updates.get("shift", "")).strip().lower()
    if shift and shift not in {"morning", "afternoon", "night"}:
        errors["shift"] = "Shift must be morning, afternoon, or night"

    status = str(updates.get("status", "")).strip().lower()
    if status and status not in {"active", "inactive", "suspended"}:
        errors["status"] = "Status must be active, inactive, or suspended"

    password = updates.get("password")
    if isinstance(password, str) and password:
        password_errors = _validate_password_strength(password)
        if password_errors:
            errors["password"] = "; ".join(password_errors)
        if password in settings.compromised_passwords:
            errors["password"] = "Password is not allowed"

    _validate_optional_date(errors, updates, "dob")
    _validate_optional_date(errors, updates, "employment_date")
    _validate_optional_date(errors, updates, "date_joined")
    _validate_optional_int(errors, updates, "role_id")

    return errors


def _validate_optional_length(errors: dict[str, str], payload: dict[str, Any], field: str, max_length: int) -> None:
    value = payload.get(field)
    if value in {None, ""}:
        return
    if not isinstance(value, str):
        errors[field] = "Must be text"
    elif len(value.strip()) > max_length:
        errors[field] = f"Must be at most {max_length} characters"


def _login_identifier(payload: dict[str, Any]) -> str:
    for field in ("email", "username"):
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return ""


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


def _validate_password_strength(password: str) -> list[str]:
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


def _error(message: str, status_code: int, errors: dict[str, str] | None = None):
    body: dict[str, Any] = {"error": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status_code


def _client_ip() -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.remote_addr


def _user_agent() -> str | None:
    return request.headers.get("User-Agent")
