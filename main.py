from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask, jsonify
from flask_cors import CORS
from mysql.connector import Error as MySQLError

from src.config.database_config import db_connection
from src.config.settings import settings


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        DEBUG=settings.debug,
        JSON_SORT_KEYS=False,
        TRUSTED_HOSTS=settings.trusted_hosts or None,
        DOCS_ENABLED=settings.docs_enabled,
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
        db_status = "healthy"
        status_code = 200

        try:
            with db_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
        except MySQLError:
            db_status = "unhealthy"
            status_code = 503

        return (
            jsonify(
                {
                    "status": "healthy" if db_status == "healthy" else "degraded",
                    "service": settings.app_name,
                    "version": settings.app_version,
                    "environment": settings.app_env,
                    "database": db_status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            status_code,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
