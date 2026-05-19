from __future__ import annotations

from typing import Any, Callable

from flask import g, jsonify, request

from src.config.settings import settings
from src.dtos.medical_dto import (
    AppointmentDTO,
    DiagnosisDTO,
    MedicalProfileDTO,
    MedicalProfileUpdateDTO,
    MedicalValidationError,
    MedicationAdministrationDTO,
    MentalHealthRecordDTO,
    PrescriptionDTO,
    ScreeningDTO,
    TreatmentPlanDTO,
)
from src.services.audit_service import AuditService
from src.services.medical_service import (
    MedicalConflictError,
    MedicalForeignKeyError,
    MedicalNotFoundError,
    MedicalService,
    is_duplicate_medical_error,
    is_mysql_error,
)


def create_medical_profile():
    return _create_record(
        dto_factory=lambda payload: MedicalProfileDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=MedicalService.create_medical_profile,
        response_key="medical_profile",
        audit_action="medical_profile_created",
        message="Medical profile created successfully",
    )


def update_medical_profile(inmate_id: int):
    payload = _json_payload()
    try:
        dto = MedicalProfileUpdateDTO.from_payload(payload)
        record = MedicalService.update_medical_profile(inmate_id, dto)
    except MedicalValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except MedicalNotFoundError as exc:
        return _error(str(exc), 404)
    except MedicalForeignKeyError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while updating medical profile", 500)
        raise

    _audit("medical_profile_updated", inmate_id=inmate_id, metadata={"updated_fields": sorted(dto.updates)})
    return jsonify({"message": "Medical profile updated successfully", "medical_profile": record.to_dict()})


def record_screening():
    return _create_record(
        dto_factory=lambda payload: ScreeningDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=MedicalService.record_screening,
        response_key="screening",
        audit_action="medical_screening_recorded",
        message="Medical screening recorded successfully",
    )


def create_diagnosis():
    return _create_record(
        dto_factory=lambda payload: DiagnosisDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=MedicalService.create_diagnosis,
        response_key="diagnosis",
        audit_action="medical_diagnosis_created",
        message="Diagnosis created successfully",
    )


def create_treatment_plan():
    return _create_record(
        dto_factory=lambda payload: TreatmentPlanDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=MedicalService.create_treatment_plan,
        response_key="treatment_plan",
        audit_action="medical_treatment_plan_created",
        message="Treatment plan created successfully",
    )


def create_prescription():
    return _create_record(
        dto_factory=lambda payload: PrescriptionDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=MedicalService.create_prescription,
        response_key="prescription",
        audit_action="medical_prescription_created",
        message="Prescription created successfully",
    )


def administer_medication():
    return _create_record(
        dto_factory=lambda payload: MedicationAdministrationDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=MedicalService.administer_medication,
        response_key="medication_administration_log",
        audit_action="medication_administered",
        message="Medication administration recorded successfully",
    )


def schedule_appointment():
    return _create_record(
        dto_factory=lambda payload: AppointmentDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=MedicalService.schedule_appointment,
        response_key="appointment",
        audit_action="medical_appointment_scheduled",
        message="Medical appointment scheduled successfully",
    )


def create_mental_health_record():
    return _create_record(
        dto_factory=lambda payload: MentalHealthRecordDTO.from_payload(payload, actor_user_id=g.current_user.id),
        service_method=MedicalService.create_mental_health_record,
        response_key="mental_health_record",
        audit_action="mental_health_record_created",
        message="Mental health record created successfully",
    )


def get_inmate_medical_history(inmate_id: int):
    try:
        history = MedicalService.retrieve_inmate_medical_history(inmate_id)
    except MedicalForeignKeyError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while retrieving medical history", 500)
        raise
    return jsonify({"inmate_id": inmate_id, "medical_history": history})


def get_inmate_treatment_history(inmate_id: int):
    try:
        history = MedicalService.retrieve_inmate_treatment_history(inmate_id)
    except MedicalForeignKeyError as exc:
        return _error(str(exc), 404)
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while retrieving treatment history", 500)
        raise
    return jsonify({"inmate_id": inmate_id, "treatment_history": history})


def get_medical_reports():
    try:
        reports = MedicalService.generate_medical_reports()
    except Exception as exc:
        if is_mysql_error(exc):
            return _error("Database error while generating medical reports", 500)
        raise
    return jsonify({"medical_reports": reports})


def get_referral_facilities():
    return jsonify({"referral_facilities": settings.medical_referral_facilities})


def _create_record(
    *,
    dto_factory: Callable[[dict[str, Any]], Any],
    service_method: Callable[[Any], Any],
    response_key: str,
    audit_action: str,
    message: str,
):
    payload = _json_payload()
    try:
        dto = dto_factory(payload)
        record = service_method(dto)
    except MedicalValidationError as exc:
        return _error("Validation failed", 400, exc.errors)
    except MedicalConflictError as exc:
        return _error(str(exc), 409)
    except MedicalForeignKeyError as exc:
        return _error(str(exc), 400)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        if is_duplicate_medical_error(exc):
            return _error("Duplicate medical record", 409)
        if is_mysql_error(exc):
            return _error("Database error while processing medical record", 500)
        raise

    inmate_id = getattr(dto, "inmate_id", None)
    _audit(audit_action, inmate_id=inmate_id, metadata={f"{response_key}_id": record.data.get("id")})
    return jsonify({"message": message, response_key: record.to_dict()}), 201


def _audit(action: str, *, inmate_id: int | None, metadata: dict[str, Any] | None = None) -> None:
    audit_metadata = dict(metadata or {})
    if inmate_id is not None:
        audit_metadata["inmate_db_id"] = inmate_id
    AuditService.record(
        action=action,
        status="success",
        actor_user_id=g.current_user.id,
        target_user_id=None,
        ip_address=_client_ip(),
        user_agent=_user_agent(),
        metadata=audit_metadata,
    )


def _json_payload() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def _error(message: str, status_code: int, errors: dict[str, str] | None = None):
    body: dict[str, Any] = {"error": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status_code


def _client_ip() -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.remote_addr


def _user_agent() -> str | None:
    return request.headers.get("User-Agent")
