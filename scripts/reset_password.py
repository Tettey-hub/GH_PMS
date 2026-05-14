from __future__ import annotations

import getpass
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.database_config import db_connection
from src.config.settings import settings
from src.services.account_lockout_service import AccountLockoutService
from src.services.user_service import UserService
from src.utils.security import hash_password


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def main() -> int:
    print("Development password reset")
    email = input("User email: ").strip().lower()
    if not EMAIL_PATTERN.match(email):
        print("Invalid email address.")
        return 1

    user = UserService.get_by_email(email)
    if user is None:
        print("User not found.")
        return 1

    password = getpass.getpass("New password: ")
    confirm_password = getpass.getpass("Confirm new password: ")
    if password != confirm_password:
        print("Passwords do not match.")
        return 1

    password_errors = validate_password(password)
    if password_errors:
        print("Password is not valid:")
        for error in password_errors:
            print(f"- {error}")
        return 1

    hashed_password = hash_password(password)
    with db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_password, user.id))
        connection.commit()
        cursor.close()

    AccountLockoutService.clear(email)
    print(f"Password reset successful for {user.full_name} ({user.email}).")
    return 0


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
