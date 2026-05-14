from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from flask import g, jsonify

from src.services.permission_service import PermissionService


F = TypeVar("F", bound=Callable)


def permission_required(*required_permissions: str):
    """
    Decorator to require specific permissions for endpoint access.
    
    Must be used with @token_required decorator.
    
    Usage:
        @permission_required("users_create", "users_read")
        @token_required
        def create_user():
            ...
    
    Args:
        *required_permissions: One or more permission names. If multiple provided,
                               user must have ALL of them.
    """
    def decorator(view: F) -> F:
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not hasattr(g, "current_user") or g.current_user is None:
                return jsonify({"error": "User context required"}), 401

            user_permissions = PermissionService.get_user_permissions(g.current_user.id)
            
            missing_permissions = set(required_permissions) - user_permissions
            if missing_permissions:
                return jsonify({
                    "error": "Insufficient permissions",
                    "missing_permissions": list(missing_permissions),
                }), 403

            return view(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def module_access_required(module_name: str):
    """
    Decorator to require module access for endpoint.
    
    Must be used with @token_required decorator.
    
    Usage:
        @module_access_required("users")
        @token_required
        def list_users():
            ...
    
    Args:
        module_name: Name of the module (e.g., 'users', 'prisons', 'visits')
    """
    def decorator(view: F) -> F:
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not hasattr(g, "current_user") or g.current_user is None:
                return jsonify({"error": "User context required"}), 401

            if not PermissionService.user_has_module_access(g.current_user.id, module_name):
                return jsonify({
                    "error": f"Access denied to {module_name} module",
                }), 403

            return view(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
