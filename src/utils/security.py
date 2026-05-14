from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from typing import Any

import bcrypt
import jwt
from jwt import InvalidTokenError

from src.config.settings import settings


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")
    hash_bytes = password_hash.encode("utf-8")
    try:
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except ValueError:
        return False


def hash_identifier(identifier: str) -> str:
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        identifier.strip().lower().encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def hash_ip_address(ip_address: str) -> str:
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        ip_address.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_access_token(user_id: int, officer_id: str, role: str) -> str:
    return _create_token(
        token_type="access",
        user_id=user_id,
        officer_id=officer_id,
        role=role,
        token_id=generate_token_id(),
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: int, officer_id: str, role: str, token_id: str) -> str:
    return _create_token(
        token_type="refresh",
        user_id=user_id,
        officer_id=officer_id,
        role=role,
        token_id=token_id,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def generate_token_id() -> str:
    return uuid4().hex


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
    except InvalidTokenError as exc:
        raise ValueError("Invalid or expired token") from exc

    if payload.get("type") != expected_type:
        raise ValueError("Invalid token type")
    if "sub" not in payload:
        raise ValueError("Invalid token subject")
    if "jti" not in payload:
        raise ValueError("Invalid token ID")
    return payload


def _create_token(
    *,
    token_type: str,
    user_id: int,
    officer_id: str,
    role: str,
    token_id: str,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "officer_id": officer_id,
        "role": role,
        "type": token_type,
        "jti": token_id,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
