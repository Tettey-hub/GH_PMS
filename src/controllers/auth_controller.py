from __future__ import annotations

import re
from datetime import date
from typing import Any

from flask import g, jsonify, request
from mysql.connector import Error as MySQLError

from src.config.settings import settings
from src.dtos.user_dto import (
    CreateUserRequestDTO,
    LoginRequestDTO,
    UpdateStaffUserRequestDTO,
    UserValidationError,
    validate_password_strength,
)
from src.services.account_lockout_service import AccountLockoutService
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.services.user_service import CreateUserData, UserService, is_duplicate_user_error


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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
    password_errors = validate_password_strength(superadmin_password)
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

    try:
        dto = CreateUserRequestDTO.from_payload(payload)
        user = UserService.create_user(dto.to_service_data())
    except UserValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
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
    try:
        dto = LoginRequestDTO.from_payload(payload)
    except UserValidationError as exc:
        return _error("Validation failed", 400, exc.errors)

    identifier = dto.identifier
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

    user = AuthService.authenticate(identifier, dto.password)
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
        dto = UpdateStaffUserRequestDTO.from_payload(payload)
        updates = dto.updates
        user = UserService.update_by_staff_lookup(field, value, updates)
    except UserValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
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
