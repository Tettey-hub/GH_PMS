from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.config.database_config import db_connection
from src.config.settings import settings


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


class RateLimitService:
    @staticmethod
    def check(identifier: str, scope: str, limit: int, window_seconds: int) -> RateLimitResult:
        now = datetime.now(timezone.utc)
        window_start = _window_start(now, window_seconds)
        identifier_hash = _hash_identifier(identifier)

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                INSERT INTO api_rate_limits (scope, identifier_hash, window_start, request_count)
                VALUES (%s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE request_count = request_count + 1
                """,
                (scope, identifier_hash, window_start),
            )
            cursor.execute(
                """
                SELECT request_count
                FROM api_rate_limits
                WHERE scope = %s AND identifier_hash = %s AND window_start = %s
                LIMIT 1
                """,
                (scope, identifier_hash, window_start),
            )
            row = cursor.fetchone()
            _delete_expired_windows(cursor, now, window_seconds)
            connection.commit()
            cursor.close()

        request_count = int(row["request_count"]) if row else limit + 1
        remaining = max(limit - request_count, 0)
        retry_after = max(int((window_start + timedelta(seconds=window_seconds) - now.replace(tzinfo=None)).total_seconds()), 1)

        return RateLimitResult(
            allowed=request_count <= limit,
            limit=limit,
            remaining=remaining,
            retry_after_seconds=retry_after,
        )


def _window_start(now: datetime, window_seconds: int) -> datetime:
    epoch_seconds = int(now.timestamp())
    window_epoch = epoch_seconds - (epoch_seconds % window_seconds)
    return datetime.fromtimestamp(window_epoch, tz=timezone.utc).replace(tzinfo=None)


def _hash_identifier(identifier: str) -> str:
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        identifier.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _delete_expired_windows(cursor, now: datetime, window_seconds: int) -> None:
    retention_seconds = max(window_seconds * 2, settings.rate_limit_window_seconds * 2, settings.auth_rate_limit_window_seconds * 2)
    cutoff = (now - timedelta(seconds=retention_seconds)).replace(tzinfo=None)
    cursor.execute("DELETE FROM api_rate_limits WHERE window_start < %s", (cutoff,))
