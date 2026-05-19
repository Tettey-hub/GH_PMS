from __future__ import annotations

from flask import Blueprint

from src.controllers.medical_controller import (
    administer_medication,
    create_diagnosis,
    create_medical_profile,
    create_mental_health_record,
    create_prescription,
    create_treatment_plan,
    get_inmate_medical_history,
    get_inmate_treatment_history,
    get_medical_reports,
    get_referral_facilities,
    record_screening,
    schedule_appointment,
    update_medical_profile,
)
from src.middlewares.auth_middleware import roles_required
from src.middlewares.permission_middleware import permission_required


medical_bp = Blueprint("medical", __name__, url_prefix="/medical")

MEDICAL_ROLES = ("admin", "medical_officer")

medical_bp.post("/profiles")(roles_required(*MEDICAL_ROLES)(permission_required("medical_create")(create_medical_profile)))
medical_bp.patch("/profiles/<int:inmate_id>")(roles_required(*MEDICAL_ROLES)(permission_required("medical_update")(update_medical_profile)))
medical_bp.post("/screenings")(roles_required(*MEDICAL_ROLES)(permission_required("medical_create")(record_screening)))
medical_bp.post("/diagnoses")(roles_required(*MEDICAL_ROLES)(permission_required("medical_create")(create_diagnosis)))
medical_bp.post("/treatment-plans")(roles_required(*MEDICAL_ROLES)(permission_required("medical_create")(create_treatment_plan)))
medical_bp.post("/prescriptions")(roles_required(*MEDICAL_ROLES)(permission_required("medical_create")(create_prescription)))
medical_bp.post("/medication-administrations")(roles_required(*MEDICAL_ROLES)(permission_required("medical_create")(administer_medication)))
medical_bp.post("/appointments")(roles_required(*MEDICAL_ROLES)(permission_required("medical_create")(schedule_appointment)))
medical_bp.post("/mental-health-records")(roles_required(*MEDICAL_ROLES)(permission_required("medical_create")(create_mental_health_record)))
medical_bp.get("/inmates/<int:inmate_id>/history")(roles_required(*MEDICAL_ROLES)(permission_required("medical_read")(get_inmate_medical_history)))
medical_bp.get("/inmates/<int:inmate_id>/treatments")(roles_required(*MEDICAL_ROLES)(permission_required("medical_read")(get_inmate_treatment_history)))
medical_bp.get("/reports")(roles_required(*MEDICAL_ROLES)(permission_required("medical_reports")(get_medical_reports)))
medical_bp.get("/referral-facilities")(roles_required(*MEDICAL_ROLES)(permission_required("medical_read")(get_referral_facilities)))
