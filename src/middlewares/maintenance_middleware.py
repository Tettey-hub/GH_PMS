from __future__ import annotations

from flask import jsonify, request

from src.config.settings import settings


def register_maintenance_middleware(app) -> None:
    @app.before_request
    def check_maintenance():
        if not settings.maintenance_mode:
            return None
        
        # Get real IP from X-Forwarded-For header (behind proxy) or use remote_addr
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.remote_addr
        
        if client_ip in settings.maintenance_bypass_ips:
            return None
        
        return jsonify({
            "error": "Service under maintenance",
            "message": settings.maintenance_message or "The service is temporarily under maintenance."
        }), 503
