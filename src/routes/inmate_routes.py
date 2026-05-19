from __future__ import annotations

from flask import Blueprint

from src.controllers.inmate_controller import (
    approve_inmate_release,
    approve_inmate_transfer,
    create_inmate,
    create_transfer_request,
    delete_inmate,
    get_inmate,
    get_inmate_by_inmate_id,
    get_release_history,
    get_release_reports,
    get_transfer_history,
    get_transfer_reports,
    initiate_release_review,
    list_inmates,
    list_releases,
    list_transfers,
    release_action,
    search_inmates,
    transfer_action,
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

inmate_bp.post("/transfers")(roles_required(*WRITE_ROLES)(permission_required("records_create")(create_transfer_request)))
inmate_bp.get("/transfers")(roles_required(*READ_ROLES)(permission_required("records_read")(list_transfers)))
inmate_bp.get("/transfers/reports")(roles_required(*READ_ROLES)(permission_required("records_read")(get_transfer_reports)))
inmate_bp.get("/<int:inmate_db_id>/transfers")(roles_required(*READ_ROLES)(permission_required("records_read")(get_transfer_history)))
inmate_bp.patch("/transfers/<int:transfer_id>/review", endpoint="review_transfer")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda transfer_id: transfer_action(transfer_id, "review"))))
inmate_bp.patch("/transfers/<int:transfer_id>/legal-verification", endpoint="legal_verify_transfer")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda transfer_id: transfer_action(transfer_id, "legal_verification"))))
inmate_bp.patch("/transfers/<int:transfer_id>/security-assessment", endpoint="security_assess_transfer")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda transfer_id: transfer_action(transfer_id, "security_assessment"))))
inmate_bp.patch("/transfers/<int:transfer_id>/medical-clearance", endpoint="medical_clear_transfer")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda transfer_id: transfer_action(transfer_id, "medical_clearance"))))
inmate_bp.patch("/transfers/<int:transfer_id>/approve", endpoint="approve_transfer_workflow")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda transfer_id: transfer_action(transfer_id, "approve"))))
inmate_bp.patch("/transfers/<int:transfer_id>/reject", endpoint="reject_transfer")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda transfer_id: transfer_action(transfer_id, "reject"))))
inmate_bp.patch("/transfers/<int:transfer_id>/transportation", endpoint="assign_transfer_transportation")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda transfer_id: transfer_action(transfer_id, "transportation"))))
inmate_bp.patch("/transfers/<int:transfer_id>/authorize-movement", endpoint="authorize_transfer_movement")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda transfer_id: transfer_action(transfer_id, "authorize_movement"))))
inmate_bp.patch("/transfers/<int:transfer_id>/execute", endpoint="execute_transfer")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda transfer_id: transfer_action(transfer_id, "execute"))))
inmate_bp.patch("/transfers/<int:transfer_id>/confirm-arrival", endpoint="confirm_transfer_arrival")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda transfer_id: transfer_action(transfer_id, "confirm_arrival"))))
inmate_bp.patch("/transfers/<int:transfer_id>/complete", endpoint="complete_transfer")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda transfer_id: transfer_action(transfer_id, "complete"))))
inmate_bp.patch("/transfers/<int:transfer_id>/cancel", endpoint="cancel_transfer")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda transfer_id: transfer_action(transfer_id, "cancel"))))

inmate_bp.post("/releases")(roles_required(*WRITE_ROLES)(permission_required("records_create")(initiate_release_review)))
inmate_bp.get("/releases")(roles_required(*READ_ROLES)(permission_required("records_read")(list_releases)))
inmate_bp.get("/releases/reports")(roles_required(*READ_ROLES)(permission_required("records_read")(get_release_reports)))
inmate_bp.get("/<int:inmate_db_id>/releases")(roles_required(*READ_ROLES)(permission_required("records_read")(get_release_history)))
inmate_bp.patch("/releases/<int:release_id>/legal-verification", endpoint="legal_verify_release")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda release_id: release_action(release_id, "legal_verification"))))
inmate_bp.patch("/releases/<int:release_id>/sentence-validation", endpoint="sentence_validate_release")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda release_id: release_action(release_id, "sentence_validation"))))
inmate_bp.patch("/releases/<int:release_id>/medical-clearance", endpoint="medical_clear_release")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda release_id: release_action(release_id, "medical_clearance"))))
inmate_bp.patch("/releases/<int:release_id>/property-clearance", endpoint="property_clear_release")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda release_id: release_action(release_id, "property_clearance"))))
inmate_bp.patch("/releases/<int:release_id>/identity-verification", endpoint="identity_verify_release")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda release_id: release_action(release_id, "identity_verification"))))
inmate_bp.patch("/releases/<int:release_id>/approve", endpoint="approve_release_workflow")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda release_id: release_action(release_id, "approve"))))
inmate_bp.patch("/releases/<int:release_id>/reject", endpoint="reject_release")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda release_id: release_action(release_id, "reject"))))
inmate_bp.patch("/releases/<int:release_id>/documents", endpoint="generate_release_documents")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda release_id: release_action(release_id, "documents"))))
inmate_bp.patch("/releases/<int:release_id>/execute", endpoint="execute_release")(roles_required(*WRITE_ROLES)(permission_required("records_update")(lambda release_id: release_action(release_id, "execute"))))
