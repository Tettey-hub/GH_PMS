from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.config.database_config import db_connection
from src.config.settings import settings
from src.utils.security import hash_identifier


@dataclass(frozen=True)
class LockoutState:
    locked: bool
    locked_until: datetime | None
    failed_attempts: int


class AccountLockoutService:
    @staticmethod
    def get_state(identifier: str) -> LockoutState:
        if not settings.account_lockout_enabled:
            return LockoutState(locked=False, locked_until=None, failed_attempts=0)

        identifier_hash = hash_identifier(identifier)
        now = _utc_naive(datetime.now(timezone.utc))

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT failed_attempts, locked_until
                FROM auth_account_lockouts
                WHERE identifier_hash = %s
                LIMIT 1
                """,
                (identifier_hash,),
            )
            row = cursor.fetchone()
            cursor.close()

        if not row:
            return LockoutState(locked=False, locked_until=None, failed_attempts=0)

        locked_until = row.get("locked_until")
        locked = bool(locked_until and locked_until > now)
        return LockoutState(locked=locked, locked_until=locked_until, failed_attempts=int(row["failed_attempts"]))

    @staticmethod
    def record_failure(identifier: str, user_id: int | None) -> LockoutState:
        if not settings.account_lockout_enabled:
            return LockoutState(locked=False, locked_until=None, failed_attempts=0)

        identifier_hash = hash_identifier(identifier)
        now = _utc_naive(datetime.now(timezone.utc))
        window_start_cutoff = now - timedelta(seconds=settings.account_lockout_window_seconds)

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT failed_attempts, first_failed_at
                FROM auth_account_lockouts
                WHERE identifier_hash = %s
                LIMIT 1
                """,
                (identifier_hash,),
            )
            row = cursor.fetchone()

            if not row or row["first_failed_at"] is None or row["first_failed_at"] < window_start_cutoff:
                failed_attempts = 1
                first_failed_at = now
            else:
                failed_attempts = int(row["failed_attempts"]) + 1
                first_failed_at = row["first_failed_at"]

            locked_until = None
            if failed_attempts >= settings.account_lockout_max_failed_attempts:
                locked_until = now + timedelta(seconds=settings.account_lockout_duration_seconds)

            cursor.execute(
                """
                INSERT INTO auth_account_lockouts (
                    identifier_hash,
                    user_id,
                    failed_attempts,
                    first_failed_at,
                    last_failed_at,
                    locked_until
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    user_id = VALUES(user_id),
                    failed_attempts = VALUES(failed_attempts),
                    first_failed_at = VALUES(first_failed_at),
                    last_failed_at = VALUES(last_failed_at),
                    locked_until = VALUES(locked_until)
                """,
                (identifier_hash, user_id, failed_attempts, first_failed_at, now, locked_until),
            )
            connection.commit()
            cursor.close()

        return LockoutState(locked=locked_until is not None, locked_until=locked_until, failed_attempts=failed_attempts)

    @staticmethod
    def clear(identifier: str) -> None:
        if not settings.account_lockout_enabled:
            return

        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM auth_account_lockouts WHERE identifier_hash = %s", (hash_identifier(identifier),))
            connection.commit()
            cursor.close()


def _utc_naive(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None)
