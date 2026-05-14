from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from mysql.connector import Error as MySQLError, IntegrityError

from src.config.database_config import db_connection
from src.models.user import USER_ROLES, USER_SHIFTS, USER_STATUSES, User
from src.utils.security import hash_password


@dataclass(frozen=True)
class CreateUserData:
    officer_id: str
    first_name: str
    last_name: str
    email: str
    password: str
    phone: str | None
    badge_number: str
    rank: str
    department: str
    role: str
    shift: str
    status: str
    date_joined: date


class UserService:
    @staticmethod
    def create_user(data: CreateUserData) -> User:
        _validate_user_data(data)
        password_hash = hash_password(data.password)

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    INSERT INTO users (
                        officer_id,
                        first_name,
                        last_name,
                        email,
                        password,
                        phone,
                        badge_number,
                        `rank`,
                        department,
                        role,
                        shift,
                        status,
                        date_joined
                    ) VALUES (
                        %(officer_id)s,
                        %(first_name)s,
                        %(last_name)s,
                        %(email)s,
                        %(password)s,
                        %(phone)s,
                        %(badge_number)s,
                        %(rank)s,
                        %(department)s,
                        %(role)s,
                        %(shift)s,
                        %(status)s,
                        %(date_joined)s
                    )
                    """,
                    {
                        "officer_id": data.officer_id,
                        "first_name": data.first_name,
                        "last_name": data.last_name,
                        "email": data.email.lower(),
                        "password": password_hash,
                        "phone": data.phone,
                        "badge_number": data.badge_number,
                        "rank": data.rank,
                        "department": data.department,
                        "role": data.role,
                        "shift": data.shift,
                        "status": data.status,
                        "date_joined": data.date_joined,
                    },
                )
                user_id = cursor.lastrowid
                connection.commit()
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                row = cursor.fetchone()
            except MySQLError:
                connection.rollback()
                raise
            finally:
                cursor.close()

        if row is None:
            raise RuntimeError("User was created but could not be reloaded")
        return User.from_row(row)

    @staticmethod
    def get_by_email(email: str) -> User | None:
        return _get_user_by_field("email", email.lower())

    @staticmethod
    def get_by_officer_id(officer_id: str) -> User | None:
        return _get_user_by_field("officer_id", officer_id)

    @staticmethod
    def get_by_id(user_id: int) -> User | None:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id = %s LIMIT 1", (user_id,))
            row = cursor.fetchone()
            cursor.close()

        return User.from_row(row) if row else None

    @staticmethod
    def user_exists_with_role(role: str) -> bool:
        """Check if any user with the given role exists."""
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1 FROM users WHERE role = %s LIMIT 1", (role,))
            exists = cursor.fetchone() is not None
            cursor.close()

        return exists


def _get_user_by_field(field: str, value: str) -> User | None:
    allowed_fields = {"email", "officer_id", "badge_number"}
    if field not in allowed_fields:
        raise ValueError("Unsupported user lookup field")

    with db_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        
        if field == "email":
            cursor.execute("SELECT * FROM users WHERE email = %s LIMIT 1", (value,))
        elif field == "officer_id":
            cursor.execute("SELECT * FROM users WHERE officer_id = %s LIMIT 1", (value,))
        elif field == "badge_number":
            cursor.execute("SELECT * FROM users WHERE badge_number = %s LIMIT 1", (value,))
        else:
            raise ValueError("Unsupported user lookup field")
        
        row = cursor.fetchone()
        cursor.close()

    return User.from_row(row) if row else None


def _validate_user_data(data: CreateUserData) -> None:
    required_values = {
        "officer_id": data.officer_id,
        "first_name": data.first_name,
        "last_name": data.last_name,
        "email": data.email,
        "password": data.password,
        "badge_number": data.badge_number,
        "rank": data.rank,
        "department": data.department,
        "role": data.role,
        "shift": data.shift,
        "status": data.status,
        "date_joined": data.date_joined,
    }
    missing = [field for field, value in required_values.items() if value in {None, ""}]
    if missing:
        raise ValueError(f"Missing required user fields: {', '.join(missing)}")
    if data.role not in USER_ROLES:
        raise ValueError("Invalid user role")
    if data.shift not in USER_SHIFTS:
        raise ValueError("Invalid user shift")
    if data.status not in USER_STATUSES:
        raise ValueError("Invalid user status")


def is_duplicate_user_error(exc: Exception) -> bool:
    return isinstance(exc, IntegrityError) and getattr(exc, "errno", None) == 1062
