from __future__ import annotations

from flask import Blueprint

from src.controllers.rehabilitation_controller import (
    assign_religious_participation,
    assign_work_duties,
    enroll_vocational_program,
    get_inmate_rehabilitation_history,
    get_rehabilitation_reports,
    issue_certification,
    record_behavioral_assessment,
    schedule_counseling_session,
    track_post_release_followup,
)
from src.middlewares.auth_middleware import roles_required
from src.middlewares.permission_middleware import permission_required


rehabilitation_bp = Blueprint("rehabilitation", __name__, url_prefix="/rehabilitation")

REHABILITATION_ROLES = ("admin", "rehabilitation_officer", "counselor", "officer")
REHABILITATION_WRITE_ROLES = ("admin", "rehabilitation_officer", "counselor")

rehabilitation_bp.post("/vocational-training")(roles_required(*REHABILITATION_WRITE_ROLES)(permission_required("records_create")(enroll_vocational_program)))
rehabilitation_bp.post("/counseling-sessions")(roles_required(*REHABILITATION_WRITE_ROLES)(permission_required("records_create")(schedule_counseling_session)))
rehabilitation_bp.post("/behavioral-assessments")(roles_required(*REHABILITATION_WRITE_ROLES)(permission_required("records_create")(record_behavioral_assessment)))
rehabilitation_bp.post("/religious-participation")(roles_required(*REHABILITATION_WRITE_ROLES)(permission_required("records_create")(assign_religious_participation)))
rehabilitation_bp.post("/work-assignments")(roles_required(*REHABILITATION_WRITE_ROLES)(permission_required("records_create")(assign_work_duties)))
rehabilitation_bp.post("/skill-certifications")(roles_required(*REHABILITATION_WRITE_ROLES)(permission_required("records_create")(issue_certification)))
rehabilitation_bp.post("/post-release-followups")(roles_required(*REHABILITATION_WRITE_ROLES)(permission_required("records_create")(track_post_release_followup)))

rehabilitation_bp.get("/inmates/<int:inmate_id>/history")(roles_required(*REHABILITATION_ROLES)(permission_required("records_read")(get_inmate_rehabilitation_history)))
rehabilitation_bp.get("/reports")(roles_required(*REHABILITATION_ROLES)(permission_required("records_read")(get_rehabilitation_reports)))
