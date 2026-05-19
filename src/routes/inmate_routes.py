from __future__ import annotations

from flask import Blueprint

from src.controllers.inmate_controller import (
    approve_inmate_release,
    approve_inmate_transfer,
    create_inmate,
    delete_inmate,
    get_inmate,
    get_inmate_by_inmate_id,
    list_inmates,
    search_inmates,
    update_inmate,
    update_inmate_status,
)
from src.middlewares.auth_middleware import roles_required
from src.middlewares.permission_middleware import permission_required


inmate_bp = Blueprint("inmates", __name__, url_prefix="/inmates")

READ_ROLES = ("admin", "supervisor", "records_officer", "officer")
WRITE_ROLES = ("admin", "supervisor", "records_officer")

inmate_bp.post("")(roles_required(*WRITE_ROLES)(permission_required("records_create")(create_inmate)))
inmate_bp.get("")(roles_required(*READ_ROLES)(permission_required("records_read")(list_inmates)))
inmate_bp.get("/search")(roles_required(*READ_ROLES)(permission_required("records_read")(search_inmates)))
inmate_bp.get("/inmate-id/<string:inmate_id>")(roles_required(*READ_ROLES)(permission_required("records_read")(get_inmate_by_inmate_id)))
inmate_bp.get("/<int:inmate_db_id>")(roles_required(*READ_ROLES)(permission_required("records_read")(get_inmate)))
inmate_bp.put("/<int:inmate_db_id>", endpoint="replace_inmate")(roles_required(*WRITE_ROLES)(permission_required("records_update")(update_inmate)))
inmate_bp.patch("/<int:inmate_db_id>", endpoint="patch_inmate")(roles_required(*WRITE_ROLES)(permission_required("records_update")(update_inmate)))
inmate_bp.patch("/<int:inmate_db_id>/status")(roles_required(*WRITE_ROLES)(permission_required("records_update")(update_inmate_status)))
inmate_bp.patch("/<int:inmate_db_id>/approve-transfer")(roles_required(*WRITE_ROLES)(permission_required("records_update")(approve_inmate_transfer)))
inmate_bp.patch("/<int:inmate_db_id>/approve-release")(roles_required(*WRITE_ROLES)(permission_required("records_update")(approve_inmate_release)))
inmate_bp.delete("/<int:inmate_db_id>")(roles_required(*WRITE_ROLES)(permission_required("records_delete")(delete_inmate)))
