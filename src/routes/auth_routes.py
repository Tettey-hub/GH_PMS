from __future__ import annotations

from flask import Blueprint

from src.controllers.auth_controller import bootstrap_admin, current_user, login, logout, refresh_token, register_user
from src.middlewares.auth_middleware import roles_required, token_required
from src.middlewares.permission_middleware import permission_required


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

auth_bp.post("/bootstrap")(bootstrap_admin)
auth_bp.post("/register")(permission_required("users_create")(roles_required("admin", "supervisor")(register_user)))
auth_bp.post("/login")(login)
auth_bp.post("/logout")(token_required(logout))
auth_bp.post("/refresh")(refresh_token)
auth_bp.get("/me")(token_required(current_user))
