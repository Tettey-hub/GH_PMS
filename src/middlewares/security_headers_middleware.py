from __future__ import annotations

from flask import redirect, request

from src.config.settings import settings


def register_security_headers_middleware(app) -> None:
    @app.before_request
    def enforce_https():
        if settings.app_env == "production" and not request.is_secure:
            url = request.url.replace("http://", "https://", 1)
            return redirect(url, code=301)

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        return response
