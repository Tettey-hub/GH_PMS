from __future__ import annotations

from flask import jsonify, request

from src.config.settings import settings
from src.services.rate_limit_service import RateLimitService


def register_rate_limit_middleware(app) -> None:
    @app.before_request
    def enforce_rate_limit():
        if not settings.rate_limit_enabled:
            return None

        identifier = _request_identifier()
        scope, limit, window_seconds = _limit_for_request()
        result = RateLimitService.check(identifier, scope, limit, window_seconds)

        if result.allowed:
            return None

        response = jsonify(
            {
                "error": "Rate limit exceeded",
                "limit": result.limit,
                "retry_after_seconds": result.retry_after_seconds,
            }
        )
        response.status_code = 429
        response.headers["Retry-After"] = str(result.retry_after_seconds)
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        return response


def _limit_for_request() -> tuple[str, int, int]:
    endpoint = request.endpoint or request.path
    if endpoint.startswith("auth."):
        return "auth", settings.auth_rate_limit_requests, settings.auth_rate_limit_window_seconds
    return "global", settings.rate_limit_requests, settings.rate_limit_window_seconds


def _request_identifier() -> str:
    return request.remote_addr or "unknown"
