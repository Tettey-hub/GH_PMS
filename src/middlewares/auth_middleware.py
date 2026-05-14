from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from flask import g, jsonify, request

from src.services.user_service import UserService
from src.utils.security import decode_token


F = TypeVar("F", bound=Callable)


def token_required(view: F) -> F:
    @wraps(view)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header must be Bearer token"}), 401

        token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            return jsonify({"error": "Bearer token is required"}), 401

        try:
            payload = decode_token(token, expected_type="access")
            user = UserService.get_by_id(int(payload["sub"]))
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid or expired token"}), 401

        if user is None or user.status != "active":
            return jsonify({"error": "Invalid or inactive user"}), 401

        g.current_user = user
        return view(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def roles_required(*allowed_roles: str):
    def decorator(view: F) -> F:
        @wraps(view)
        @token_required
        def wrapper(*args, **kwargs):
            if g.current_user.role not in allowed_roles:
                return jsonify({"error": "You do not have permission to perform this action"}), 403
            return view(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
