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
                        middle_name,
                        last_name,
                        gender,
                        dob,
                        email,
                        password,
                        phone,
                        national_id,
                        address,
                        profile_image,
                        staff_id,
                        badge_number,
                        `rank`,
                        department,
                        position,
                        employment_date,
                        branch,
                        username,
                        role_id,
                        role,
                        shift,
                        status,
                        date_joined
                    ) VALUES (
                        %(officer_id)s,
                        %(first_name)s,
                        %(middle_name)s,
                        %(last_name)s,
                        %(gender)s,
                        %(dob)s,
                        %(email)s,
                        %(password)s,
                        %(phone)s,
                        %(national_id)s,
                        %(address)s,
                        %(profile_image)s,
                        %(staff_id)s,
                        %(badge_number)s,
                        %(rank)s,
                        %(department)s,
                        %(position)s,
                        %(employment_date)s,
                        %(branch)s,
                        %(username)s,
                        %(role_id)s,
                        %(role)s,
                        %(shift)s,
                        %(status)s,
                        %(date_joined)s
                    )
                    """,
                    {
                        "officer_id": data.officer_id,
                        "first_name": data.first_name,
                        "middle_name": data.middle_name,
                        "last_name": data.last_name,
                        "gender": data.gender,
                        "dob": data.dob,
                        "email": data.email.lower(),
                        "password": password_hash,
                        "phone": data.phone,
                        "national_id": data.national_id,
                        "address": data.address,
                        "profile_image": data.profile_image,
                        "staff_id": data.staff_id,
                        "badge_number": data.badge_number,
                        "rank": data.rank,
                        "department": data.department,
                        "position": data.position,
                        "employment_date": data.employment_date,
                        "branch": data.branch,
                        "username": data.username.lower() if data.username else None,
                        "role_id": data.role_id,
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
    def get_by_username(username: str) -> User | None:
        return _get_user_by_field("username", username.lower())

    @staticmethod
    def get_by_staff_lookup(field: str, value: str) -> User | None:
        return _get_user_by_field(_validate_staff_lookup_field(field), _normalize_lookup_value(field, value))

    @staticmethod
    def get_by_login_identifier(identifier: str) -> User | None:
        identifier = identifier.strip().lower()
        if not identifier:
            return None

        user = UserService.get_by_email(identifier)
        if user is not None:
            return user

        return UserService.get_by_username(identifier)

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
    def get_all_users() -> list[User]:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT *
                FROM users
                ORDER BY created_at DESC, id DESC
                """
            )
            rows = cursor.fetchall()
            cursor.close()

        return [User.from_row(row) for row in rows]

    @staticmethod
    def update_by_staff_lookup(field: str, value: str, updates: dict[str, object]) -> User | None:
        field = _validate_staff_lookup_field(field)
        value = _normalize_lookup_value(field, value)
        updates = _prepare_user_updates(updates)
        if not updates:
            raise ValueError("No update fields provided")

        existing_user = UserService.get_by_staff_lookup(field, value)
        if existing_user is None:
            return None

        assignments = ", ".join(f"`{column}` = %({column})s" for column in updates)
        updates["user_id"] = existing_user.id

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    f"""
                    UPDATE users
                    SET {assignments}
                    WHERE id = %(user_id)s
                    """,
                    updates,
                )
                connection.commit()
                cursor.execute("SELECT * FROM users WHERE id = %s", (existing_user.id,))
                row = cursor.fetchone()
            except MySQLError:
                connection.rollback()
                raise
            finally:
                cursor.close()

        return User.from_row(row) if row else None

    @staticmethod
    def delete_by_staff_lookup(field: str, value: str) -> User | None:
        field = _validate_staff_lookup_field(field)
        value = _normalize_lookup_value(field, value)
        existing_user = UserService.get_by_staff_lookup(field, value)
        if existing_user is None:
            return None

        with db_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("DELETE FROM users WHERE id = %s", (existing_user.id,))
                connection.commit()
            except MySQLError:
                connection.rollback()
                raise
            finally:
                cursor.close()

        return existing_user

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
    allowed_fields = {"email", "username", "staff_id", "officer_id", "badge_number"}
    if field not in allowed_fields:
        raise ValueError("Unsupported user lookup field")

    with db_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        
        if field == "email":
            cursor.execute("SELECT * FROM users WHERE email = %s LIMIT 1", (value,))
        elif field == "username":
            cursor.execute("SELECT * FROM users WHERE username = %s LIMIT 1", (value,))
        elif field == "staff_id":
            cursor.execute("SELECT * FROM users WHERE staff_id = %s LIMIT 1", (value,))
        elif field == "officer_id":
            cursor.execute("SELECT * FROM users WHERE officer_id = %s LIMIT 1", (value,))
        elif field == "badge_number":
            cursor.execute("SELECT * FROM users WHERE badge_number = %s LIMIT 1", (value,))
        else:
            raise ValueError("Unsupported user lookup field")
        
        row = cursor.fetchone()
        cursor.close()

    return User.from_row(row) if row else None


def _validate_staff_lookup_field(field: str) -> str:
    allowed_fields = {"staff_id", "officer_id", "badge_number", "username"}
    if field not in allowed_fields:
        raise ValueError("Lookup field must be staff_id, officer_id, badge_number, or username")
    return field


def _normalize_lookup_value(field: str, value: str) -> str:
    value = value.strip()
    if field == "username":
        return value.lower()
    if field == "officer_id":
        return value.upper()
    if field == "badge_number":
        return value.upper()
    return value


def _prepare_user_updates(updates: dict[str, object]) -> dict[str, object]:
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
        "staff_id",
        "badge_number",
        "rank",
        "department",
        "position",
        "employment_date",
        "branch",
        "username",
        "role_id",
        "role",
        "shift",
        "status",
        "date_joined",
    }
    prepared: dict[str, object] = {}
    for field, value in updates.items():
        if field not in allowed_fields:
            raise ValueError(f"Unsupported update field: {field}")
        if value == "":
            value = None
        if field == "email" and isinstance(value, str):
            value = value.strip().lower()
        elif field == "username" and isinstance(value, str):
            value = value.strip().lower()
        elif field in {"officer_id", "badge_number"} and isinstance(value, str):
            value = value.strip().upper()
        elif field == "password" and isinstance(value, str):
            value = hash_password(value)
        elif isinstance(value, str):
            value = value.strip()
        prepared[field] = value
    return prepared


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
