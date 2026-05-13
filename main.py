from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask, jsonify
from flask_cors import CORS

from src.config.settings import settings


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        DEBUG=settings.debug,
        JSON_SORT_KEYS=False,
    )

    CORS(
        app,
        origins=settings.allowed_origins or [],
        methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
        supports_credentials=settings.allow_credentials,
    )

    @app.get("/")
    def root():
        return jsonify(
            {
                "message": f"{settings.app_name} API",
                "status": "running",
                "version": settings.app_version,
                "health_url": f"{settings.api_prefix}/health",
            }
        )

    @app.get("/health")
    @app.get(f"{settings.api_prefix}/health")
    def health_check():
        return jsonify(
            {
                "status": "healthy",
                "service": settings.app_name,
                "version": settings.app_version,
                "environment": settings.app_env,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
