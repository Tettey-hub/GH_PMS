from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from src.config.database_config import db_connection
from src.config.settings import settings


class RefreshTokenService:
    @staticmethod
    def store_token(user_id: int, token: str, token_id: str) -> None:
        expires_at = _utc_naive(datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days))
        token_hash = hash_refresh_token(token)

        with db_connection() as connection:
            cursor = connection.cursor()
            
            # Check if user has reached max active sessions
            cursor.execute(
                """
                SELECT COUNT(*) as active_count
                FROM auth_refresh_tokens
                WHERE user_id = %s AND revoked_at IS NULL AND expires_at > %s
                """,
                (user_id, _utc_naive(datetime.now(timezone.utc))),
            )
            result = cursor.fetchone()
            active_count = result[0] if result else 0
            
            # If at or over limit, revoke the oldest token
            if active_count >= settings.max_active_sessions:
                cursor.execute(
                    """
                    UPDATE auth_refresh_tokens
                    SET revoked_at = %s
                    WHERE user_id = %s AND revoked_at IS NULL
                    ORDER BY created_at ASC
                    LIMIT 1
                    """,
                    (_utc_naive(datetime.now(timezone.utc)), user_id),
                )
            
            cursor.execute(
                """
                INSERT INTO auth_refresh_tokens (user_id, token_hash, jti, expires_at)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, token_hash, token_id, expires_at),
            )
            connection.commit()
            cursor.close()

    @staticmethod
    def is_token_active(token: str, token_id: str, user_id: int) -> bool:
        token_hash = hash_refresh_token(token)
        now = _utc_naive(datetime.now(timezone.utc))

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id
                FROM auth_refresh_tokens
                WHERE token_hash = %s
                    AND jti = %s
                    AND user_id = %s
                    AND revoked_at IS NULL
                    AND expires_at > %s
                LIMIT 1
                """,
                (token_hash, token_id, user_id, now),
            )
            row = cursor.fetchone()
            cursor.close()

        return row is not None

    @staticmethod
    def rotate_token(old_token: str, old_token_id: str, new_token_id: str) -> None:
        token_hash = hash_refresh_token(old_token)
        now = _utc_naive(datetime.now(timezone.utc))

        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE auth_refresh_tokens
                SET revoked_at = %s, replaced_by_jti = %s
                WHERE token_hash = %s AND jti = %s AND revoked_at IS NULL
                """,
                (now, new_token_id, token_hash, old_token_id),
            )
            connection.commit()
            cursor.close()

    @staticmethod
    def revoke_user_tokens(user_id: int) -> int:
        now = _utc_naive(datetime.now(timezone.utc))

        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE auth_refresh_tokens
                SET revoked_at = %s
                WHERE user_id = %s AND revoked_at IS NULL
                """,
                (now, user_id),
            )
            revoked_count = cursor.rowcount
            connection.commit()
            cursor.close()

        return revoked_count


def hash_refresh_token(token: str) -> str:
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _utc_naive(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None)
