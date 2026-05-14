from __future__ import annotations

from flask import Blueprint

from src.controllers.test_controller import (
    test_module_access,
    test_permission_check,
    test_role_permissions,
    test_user_permissions,
)
from src.middlewares.auth_middleware import token_required

# Test blueprint for permission system verification
test_bp = Blueprint("test", __name__, url_prefix="/test")

test_bp.get("/permission")(token_required(test_permission_check))
test_bp.get("/module-access")(token_required(test_module_access))
test_bp.get("/my-permissions")(token_required(test_user_permissions))
test_bp.get("/role-permissions")(token_required(test_role_permissions))
