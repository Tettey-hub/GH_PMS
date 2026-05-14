from __future__ import annotations

from fnmatch import fnmatch

from flask import jsonify, request

from src.config.settings import settings


def register_host_validation_middleware(app) -> None:
    @app.before_request
    def enforce_trusted_hosts():
        if not settings.trusted_hosts:
            return None

        host = _normalize_host(request.host)
        if _is_trusted_host(host):
            return None

        return jsonify({"error": "Untrusted host"}), 400


def _normalize_host(host: str) -> str:
    if not host:
        return ""
    host_without_port = host.rsplit(":", 1)[0] if ":" in host and not host.startswith("[") else host
    return host_without_port.lower().strip("[]")


def _is_trusted_host(host: str) -> bool:
    for trusted_host in settings.trusted_hosts:
        candidate = trusted_host.lower().strip()
        if candidate == host or fnmatch(host, candidate):
            return True
    return False
