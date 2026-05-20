from __future__ import annotations

from flask import Blueprint

from src.controllers.visitor_controller import (
    blacklist_visitor,
    check_in_visitor,
    check_out_visitor,
    create_visit_schedule,
    get_visitor_history,
    get_visitor_reports,
    monitor_visitor_activity,
    record_visitor_violation,
    register_visitor,
    review_visit_request,
    search_visitors,
    submit_visit_request,
    update_visitor,
    verify_visitor_identity,
)
from src.middlewares.auth_middleware import roles_required
from src.middlewares.permission_middleware import permission_required


visitor_bp = Blueprint("visitors", __name__, url_prefix="/visitors")

VISITOR_ROLES = ("admin", "visitor_officer", "officer")

visitor_bp.post("")(roles_required(*VISITOR_ROLES)(permission_required("visits_create")(register_visitor)))
visitor_bp.get("")(roles_required(*VISITOR_ROLES)(permission_required("visits_read")(search_visitors)))
visitor_bp.patch("/<int:visitor_id>")(roles_required(*VISITOR_ROLES)(permission_required("visits_update")(update_visitor)))
visitor_bp.get("/<int:visitor_id>/history")(roles_required(*VISITOR_ROLES)(permission_required("visits_read")(get_visitor_history)))
visitor_bp.patch("/<int:visitor_id>/blacklist")(roles_required(*VISITOR_ROLES)(permission_required("visits_update")(blacklist_visitor)))

visitor_bp.post("/verifications")(roles_required(*VISITOR_ROLES)(permission_required("visits_create")(verify_visitor_identity)))

visitor_bp.post("/requests")(roles_required(*VISITOR_ROLES)(permission_required("visits_create")(submit_visit_request)))
visitor_bp.patch("/requests/<int:request_id>/review", endpoint="review_visit_request")(roles_required(*VISITOR_ROLES)(permission_required("visits_update")(lambda request_id: review_visit_request(request_id, "review"))))
visitor_bp.patch("/requests/<int:request_id>/approve", endpoint="approve_visit_request")(roles_required(*VISITOR_ROLES)(permission_required("visits_update")(lambda request_id: review_visit_request(request_id, "approve"))))
visitor_bp.patch("/requests/<int:request_id>/reject", endpoint="reject_visit_request")(roles_required(*VISITOR_ROLES)(permission_required("visits_update")(lambda request_id: review_visit_request(request_id, "reject"))))
visitor_bp.patch("/requests/<int:request_id>/reschedule", endpoint="reschedule_visit_request")(roles_required(*VISITOR_ROLES)(permission_required("visits_update")(lambda request_id: review_visit_request(request_id, "reschedule"))))

visitor_bp.post("/schedules")(roles_required(*VISITOR_ROLES)(permission_required("visits_create")(create_visit_schedule)))
visitor_bp.post("/checkins")(roles_required(*VISITOR_ROLES)(permission_required("visits_create")(check_in_visitor)))
visitor_bp.patch("/checkins/<int:checkin_id>/checkout")(roles_required(*VISITOR_ROLES)(permission_required("visits_update")(check_out_visitor)))

visitor_bp.post("/monitoring")(roles_required(*VISITOR_ROLES)(permission_required("visits_create")(monitor_visitor_activity)))
visitor_bp.post("/violations")(roles_required(*VISITOR_ROLES)(permission_required("visits_create")(record_visitor_violation)))
visitor_bp.get("/reports")(roles_required(*VISITOR_ROLES)(permission_required("visits_read")(get_visitor_reports)))
