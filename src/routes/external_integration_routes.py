from __future__ import annotations

from flask import Blueprint

from src.controllers.external_integration_controller import (
    execute_provider_operation,
    get_integration_reports,
    list_integration_records,
    record_biometric_integration,
    record_cloud_backup,
    record_court_integration,
    record_nia_integration,
    record_police_integration,
    record_synchronization,
    register_api_integration,
)
from src.middlewares.auth_middleware import roles_required
from src.middlewares.permission_middleware import permission_required


external_integration_bp = Blueprint("external_integrations", __name__, url_prefix="/external-integrations")

INTEGRATION_ROLES = ("admin", "supervisor")

external_integration_bp.post("/court")(roles_required(*INTEGRATION_ROLES)(permission_required("records_update")(record_court_integration)))
external_integration_bp.post("/nia")(roles_required(*INTEGRATION_ROLES)(permission_required("records_update")(record_nia_integration)))
external_integration_bp.post("/police")(roles_required(*INTEGRATION_ROLES)(permission_required("records_update")(record_police_integration)))
external_integration_bp.post("/biometrics")(roles_required(*INTEGRATION_ROLES)(permission_required("records_update")(record_biometric_integration)))
external_integration_bp.post("/apis")(roles_required(*INTEGRATION_ROLES)(permission_required("records_update")(register_api_integration)))
external_integration_bp.post("/synchronizations")(roles_required(*INTEGRATION_ROLES)(permission_required("records_update")(record_synchronization)))
external_integration_bp.post("/backups")(roles_required(*INTEGRATION_ROLES)(permission_required("records_update")(record_cloud_backup)))
external_integration_bp.post("/provider-operations")(roles_required(*INTEGRATION_ROLES)(permission_required("records_update")(execute_provider_operation)))

external_integration_bp.get("/reports")(roles_required(*INTEGRATION_ROLES)(permission_required("records_read")(get_integration_reports)))
external_integration_bp.get("/<string:record_type>")(roles_required(*INTEGRATION_ROLES)(permission_required("records_read")(list_integration_records)))
