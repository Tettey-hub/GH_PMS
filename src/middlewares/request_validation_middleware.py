from __future__ import annotations

from flask import jsonify, request

from src.config.settings import settings


def register_request_validation_middleware(app) -> None:
    @app.before_request
    def validate_content_type():
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("Content-Type", "").lower()
            
            if not content_type:
                return jsonify({"error": "Content-Type header is required"}), 400
            
            if "application/json" not in content_type:
                return jsonify({
                    "error": "Invalid Content-Type",
                    "message": "Content-Type must be application/json"
                }), 400
    
    @app.before_request
    def validate_request_size():
        max_size = settings.max_request_body_size_mb * 1024 * 1024
        content_length = request.content_length
        
        if content_length and content_length > max_size:
            return jsonify({
                "error": "Request entity too large",
                "message": f"Maximum request size is {settings.max_request_body_size_mb} MB"
            }), 413
