from __future__ import annotations

import json
from typing import Any

from src.config.database_config import db_connection
from src.utils.security import hash_ip_address


class AuditService:
    @staticmethod
    def record(
        *,
        action: str,
        status: str,
        actor_user_id: int | None = None,
        target_user_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ip_hash = hash_ip_address(ip_address) if ip_address else None
        metadata_json = json.dumps(metadata or {}, separators=(",", ":"), sort_keys=True)

        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO audit_logs (
                    actor_user_id,
                    target_user_id,
                    action,
                    status,
                    ip_hash,
                    user_agent,
                    metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    actor_user_id,
                    target_user_id,
                    action,
                    status,
                    ip_hash,
                    _truncate_user_agent(user_agent),
                    metadata_json,
                ),
            )
            connection.commit()
            cursor.close()


def _truncate_user_agent(user_agent: str | None) -> str | None:
    if not user_agent:
        return None
    return user_agent[:255]
