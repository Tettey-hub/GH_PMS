from __future__ import annotations

from flask import Blueprint

from src.controllers.arrest_warrant_controller import (
    create_arrest_warrant,
    delete_arrest_warrant,
    get_arrest_warrant,
    get_arrest_warrant_by_case_number,
    get_arrest_warrant_by_warrant_number,
    list_arrest_warrants,
    search_arrest_warrants,
    update_arrest_warrant,
    update_arrest_warrant_status,
)
from src.middlewares.auth_middleware import roles_required
from src.middlewares.permission_middleware import permission_required


arrest_warrant_bp = Blueprint("arrest_warrants", __name__, url_prefix="/arrest-warrants")

READ_ROLES = ("admin", "supervisor", "records_officer", "officer")
WRITE_ROLES = ("admin", "supervisor", "records_officer")

arrest_warrant_bp.post("")(roles_required(*WRITE_ROLES)(permission_required("records_create")(create_arrest_warrant)))
arrest_warrant_bp.get("")(roles_required(*READ_ROLES)(permission_required("records_read")(list_arrest_warrants)))
arrest_warrant_bp.get("/search")(roles_required(*READ_ROLES)(permission_required("records_read")(search_arrest_warrants)))
arrest_warrant_bp.get("/warrant-number/<string:warrant_number>")(roles_required(*READ_ROLES)(permission_required("records_read")(get_arrest_warrant_by_warrant_number)))
arrest_warrant_bp.get("/case-number/<string:case_number>")(roles_required(*READ_ROLES)(permission_required("records_read")(get_arrest_warrant_by_case_number)))
arrest_warrant_bp.get("/<int:warrant_db_id>")(roles_required(*READ_ROLES)(permission_required("records_read")(get_arrest_warrant)))
arrest_warrant_bp.put("/<int:warrant_db_id>", endpoint="replace_arrest_warrant")(roles_required(*WRITE_ROLES)(permission_required("records_update")(update_arrest_warrant)))
arrest_warrant_bp.patch("/<int:warrant_db_id>", endpoint="patch_arrest_warrant")(roles_required(*WRITE_ROLES)(permission_required("records_update")(update_arrest_warrant)))
arrest_warrant_bp.patch("/<int:warrant_db_id>/status")(roles_required(*WRITE_ROLES)(permission_required("records_update")(update_arrest_warrant_status)))
arrest_warrant_bp.delete("/<int:warrant_db_id>")(roles_required(*WRITE_ROLES)(permission_required("records_delete")(delete_arrest_warrant)))
