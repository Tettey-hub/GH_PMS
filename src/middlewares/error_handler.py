from __future__ import annotations

import logging
from typing import Any

from flask import Flask, jsonify

logger = logging.getLogger("pms")


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def handle_bad_request(error: Any):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(401)
    def handle_unauthorized(error: Any):
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(403)
    def handle_forbidden(error: Any):
        return jsonify({"error": "Forbidden"}), 403

    @app.errorhandler(404)
    def handle_not_found(error: Any):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(409)
    def handle_conflict(error: Any):
        return jsonify({"error": "Conflict"}), 409

    @app.errorhandler(429)
    def handle_too_many_requests(error: Any):
        return jsonify({"error": "Too many requests"}), 429

    @app.errorhandler(500)
    def handle_internal_server_error(error: Any):
        logger.error("Internal server error", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_exception(error: Any):
        logger.error("Unhandled exception", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
