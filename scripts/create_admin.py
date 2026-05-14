from __future__ import annotations

import sys
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import settings
from src.services.user_service import CreateUserData, UserService, is_duplicate_user_error


ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "@Admin1234"


def main() -> int:
    print("Create admin account")
    print(f"Email: {ADMIN_EMAIL}")
    print("Password: configured in this script")

    existing_user = UserService.get_by_email(ADMIN_EMAIL)
    if existing_user is not None:
        print(f"Admin email already exists: {existing_user.full_name} ({existing_user.email})")
        print("No changes were made.")
        return 1

    password_errors = validate_password(ADMIN_PASSWORD)
    if password_errors:
        print("Configured admin password is not valid:")
        for error in password_errors:
            print(f"- {error}")
        return 1

    print("\nEnter the real required staff details for this admin.")
    officer_id = prompt_required("Officer ID (OFF001 format)").upper()
    first_name = prompt_required("First name")
    last_name = prompt_required("Last name")
    username = prompt_required("Username")
    badge_number = prompt_required("Badge number").upper()
    position = prompt_required("Position / rank")
    department = prompt_required("Department")
    shift = prompt_choice("Shift", ["morning", "afternoon", "night"])
    date_joined = prompt_date("Date joined (YYYY-MM-DD)")

    try:
        user = UserService.create_user(
            CreateUserData(
                officer_id=officer_id,
                first_name=first_name,
                last_name=last_name,
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD,
                phone=None,
                badge_number=badge_number,
                rank=position,
                department=department,
                position=position,
                role="admin",
                shift=shift,
                status="active",
                date_joined=date_joined,
                employment_date=date_joined,
                username=username,
            )
        )
    except ValueError as exc:
        print(f"Admin creation failed: {exc}")
        return 1
    except Exception as exc:
        if is_duplicate_user_error(exc):
            print("Admin creation failed: officer ID, email, or badge number already exists.")
            return 1
        raise

    print(f"Admin created successfully: {user.full_name} ({user.email})")
    return 0


def prompt_required(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print(f"{label} is required.")


def prompt_choice(label: str, choices: list[str]) -> str:
    allowed = set(choices)
    while True:
        value = input(f"{label} ({'/'.join(choices)}): ").strip().lower()
        if value in allowed:
            return value
        print(f"{label} must be one of: {', '.join(choices)}")


def prompt_date(label: str) -> date:
    while True:
        value = input(f"{label}: ").strip()
        try:
            return date.fromisoformat(value)
        except ValueError:
            print("Use YYYY-MM-DD.")


def validate_password(password: str) -> list[str]:
    errors: list[str] = []
    if len(password) < settings.password_min_length:
        errors.append(f"Password must be at least {settings.password_min_length} characters")
    if len(password) > settings.password_max_length:
        errors.append(f"Password must be at most {settings.password_max_length} characters")
    if settings.password_require_uppercase and not any(char.isupper() for char in password):
        errors.append("Password must include an uppercase letter")
    if settings.password_require_lowercase and not any(char.islower() for char in password):
        errors.append("Password must include a lowercase letter")
    if settings.password_require_number and not any(char.isdigit() for char in password):
        errors.append("Password must include a number")
    if settings.password_require_special and not any(not char.isalnum() for char in password):
        errors.append("Password must include a special character")
    if password in settings.compromised_passwords:
        errors.append("Password is not allowed")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
