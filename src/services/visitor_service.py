from __future__ import annotations

from dataclasses import asdict
from typing import Any

from mysql.connector import Error as MySQLError, IntegrityError

from src.config.database_config import db_connection
from src.dtos.visitor_dto import (
    VisitRequestDTO,
    VisitReviewDTO,
    VisitScheduleDTO,
    VisitorCheckinDTO,
    VisitorCheckoutDTO,
    VisitorMonitoringDTO,
    VisitorRegistrationDTO,
    VisitorUpdateDTO,
    VisitorVerificationDTO,
    VisitorViolationDTO,
)
from src.models.visitor import Visitor, VisitorCheckin, VisitorRecord, VisitorRequest, VisitorSchedule
from src.repositories.visitor_repository import VisitorRepository


class VisitorNotFoundError(LookupError):
    pass


class VisitorConflictError(ValueError):
    pass


class VisitorForeignKeyError(ValueError):
    pass


class VisitorWorkflowError(ValueError):
    pass


class VisitorService:
    @staticmethod
    def register_visitor(data: VisitorRegistrationDTO) -> VisitorRecord:
        with db_connection() as connection:
            try:
                _require_user(connection, data.created_by, "Creator does not exist")
                if VisitorRepository.visitor_id_exists(connection, data.visitor_id):
                    raise VisitorConflictError("Visitor ID already exists")
                if VisitorRepository.national_id_exists(connection, data.national_id):
                    raise VisitorConflictError("Visitor national ID already exists")
                visitor = VisitorRepository.create(connection, "visitors", {**asdict(data), "blacklist_status": False, "verification_status": "PENDING"})
                connection.commit()
                return visitor
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def update_visitor(visitor_id: int, data: VisitorUpdateDTO) -> VisitorRecord:
        with db_connection() as connection:
            try:
                _require_visitor(connection, visitor_id)
                visitor = VisitorRepository.update(connection, "visitors", visitor_id, data.updates)
                connection.commit()
                if visitor is None:
                    raise VisitorNotFoundError("Visitor not found")
                return visitor
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def verify_visitor_identity(data: VisitorVerificationDTO) -> VisitorRecord:
        with db_connection() as connection:
            try:
                visitor = _require_visitor(connection, data.visitor_id)
                _require_user(connection, data.verified_by, "Verification officer does not exist")
                verification = VisitorRepository.create(connection, "visitor_verifications", asdict(data))
                verification_status = _verification_status(visitor, data)
                VisitorRepository.update(connection, "visitors", data.visitor_id, {"verification_status": verification_status})
                connection.commit()
                return verification
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def blacklist_visitor(visitor_id: int, *, reason: str) -> VisitorRecord:
        with db_connection() as connection:
            try:
                _require_visitor(connection, visitor_id)
                visitor = VisitorRepository.update(connection, "visitors", visitor_id, {"blacklist_status": True, "blacklist_reason": reason, "verification_status": "FAILED"})
                connection.commit()
                if visitor is None:
                    raise VisitorNotFoundError("Visitor not found")
                return visitor
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def submit_visit_request(data: VisitRequestDTO) -> VisitorRecord:
        with db_connection() as connection:
            try:
                visitor = _require_visitor(connection, data.visitor_id)
                _require_inmate(connection, data.inmate_id)
                if visitor.blacklist_status:
                    raise VisitorWorkflowError("Blacklisted visitors cannot create visit requests")
                request = VisitorRepository.create(connection, "visitor_requests", {**asdict(data), "approval_status": "PENDING"})
                connection.commit()
                return request
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def review_visit_request(request_id: int, data: VisitReviewDTO) -> VisitorRecord:
        with db_connection() as connection:
            try:
                request = _require_request(connection, request_id)
                _require_user(connection, data.updates["reviewed_by"], "Reviewing officer does not exist")
                _validate_request_review(connection, request, data.updates)
                updated = VisitorRepository.update(connection, "visitor_requests", request_id, data.updates)
                connection.commit()
                if updated is None:
                    raise VisitorNotFoundError("Visit request not found")
                return updated
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def create_visit_schedule(data: VisitScheduleDTO) -> VisitorRecord:
        with db_connection() as connection:
            try:
                request = _require_request(connection, data.visitor_request_id)
                _require_user(connection, data.scheduled_by, "Scheduling officer does not exist")
                if request.approval_status != "APPROVED":
                    raise VisitorWorkflowError("Visit scheduling requires approved request")
                if VisitorRepository.schedule_has_overlap(connection, visit_date=data.visit_date, visit_room=data.visit_room, start_time=data.start_time, end_time=data.end_time):
                    raise VisitorConflictError("Visit schedule overlaps an existing schedule for this room")
                if VisitorRepository.schedule_slot_used(connection, visit_date=data.visit_date, daily_capacity_slot=data.daily_capacity_slot):
                    raise VisitorConflictError("Daily visitation capacity slot is already used")
                schedule = VisitorRepository.create(connection, "visitor_schedules", {**asdict(data), "scheduling_status": "SCHEDULED"})
                connection.commit()
                return schedule
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def check_in_visitor(data: VisitorCheckinDTO) -> VisitorRecord:
        with db_connection() as connection:
            try:
                schedule = _require_schedule(connection, data.visitor_schedule_id)
                request = _require_request(connection, schedule.visitor_request_id)
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.handled_by, "Check-in officer does not exist")
                if schedule.scheduling_status != "SCHEDULED":
                    raise VisitorWorkflowError("Check-in requires an approved scheduled visit")
                if request.inmate_id != data.inmate_id:
                    raise VisitorWorkflowError("Check-in inmate must match the approved visit request")
                if data.security_clearance_status != "CLEARED":
                    raise VisitorWorkflowError("Visitor check-in requires cleared security screening")
                if not data.belongings_checked:
                    raise VisitorWorkflowError("Visitor belongings must be checked before check-in")
                if VisitorRepository.active_checkin_for_schedule(connection, data.visitor_schedule_id):
                    raise VisitorConflictError("Visitor is already checked in for this schedule")
                checkin = VisitorRepository.create(connection, "visitor_checkins", asdict(data))
                connection.commit()
                return checkin
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def check_out_visitor(checkin_id: int, data: VisitorCheckoutDTO) -> VisitorRecord:
        with db_connection() as connection:
            try:
                checkin = _require_checkin(connection, checkin_id)
                if checkin.exit_time is not None:
                    raise VisitorWorkflowError("Visitor has already checked out")
                if data.exit_time < checkin.arrival_time:
                    raise VisitorWorkflowError("Exit time cannot be earlier than arrival time")
                updated = VisitorRepository.update(connection, "visitor_checkins", checkin_id, asdict(data))
                VisitorRepository.update(connection, "visitor_schedules", checkin.visitor_schedule_id, {"scheduling_status": "COMPLETED"})
                connection.commit()
                if updated is None:
                    raise VisitorNotFoundError("Check-in record not found")
                return updated
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def monitor_visitor_activity(data: VisitorMonitoringDTO) -> VisitorRecord:
        with db_connection() as connection:
            try:
                _require_visitor(connection, data.visitor_id)
                _require_inmate(connection, data.inmate_id)
                _require_user(connection, data.monitored_by, "Monitoring officer does not exist")
                record = VisitorRepository.create(connection, "visitor_monitoring_logs", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def record_visitor_violation(data: VisitorViolationDTO) -> VisitorRecord:
        with db_connection() as connection:
            try:
                _require_visitor(connection, data.visitor_id)
                _require_user(connection, data.reported_by, "Reporting officer does not exist")
                violation = VisitorRepository.create(connection, "visitor_violations", asdict(data))
                if data.violation_severity == "CRITICAL":
                    VisitorRepository.update(connection, "visitors", data.visitor_id, {"blacklist_status": True, "blacklist_reason": data.violation_description, "verification_status": "FAILED"})
                connection.commit()
                return violation
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def visitor_history(visitor_id: int) -> dict[str, Any]:
        with db_connection() as connection:
            visitor = _require_visitor(connection, visitor_id)
            return {"visitor": visitor.to_dict(), **VisitorRepository.visitor_history(connection, visitor_id)}

    @staticmethod
    def search_visitors(*, filters: dict[str, Any], limit: int, offset: int) -> list[Visitor]:
        with db_connection() as connection:
            return VisitorRepository.search_visitors(connection, filters=filters, limit=limit, offset=offset)

    @staticmethod
    def visitor_reports() -> dict[str, Any]:
        with db_connection() as connection:
            return VisitorRepository.reports(connection)


def _require_visitor(connection, visitor_id: int) -> Visitor:
    visitor = VisitorRepository.get_by_id(connection, "visitors", visitor_id)
    if not isinstance(visitor, Visitor):
        raise VisitorNotFoundError("Visitor not found")
    return visitor


def _require_request(connection, request_id: int) -> VisitorRequest:
    request = VisitorRepository.get_request(connection, request_id)
    if request is None:
        raise VisitorNotFoundError("Visit request not found")
    return request


def _require_schedule(connection, schedule_id: int) -> VisitorSchedule:
    schedule = VisitorRepository.get_schedule(connection, schedule_id)
    if schedule is None:
        raise VisitorNotFoundError("Visit schedule not found")
    return schedule


def _require_checkin(connection, checkin_id: int) -> VisitorCheckin:
    checkin = VisitorRepository.get_checkin(connection, checkin_id)
    if checkin is None:
        raise VisitorNotFoundError("Check-in record not found")
    return checkin


def _require_inmate(connection, inmate_id: int) -> None:
    if not VisitorRepository.inmate_exists(connection, inmate_id):
        raise VisitorForeignKeyError("Inmate does not exist")


def _require_user(connection, user_id: int, message: str) -> None:
    if not VisitorRepository.user_exists(connection, user_id):
        raise VisitorForeignKeyError(message)


def _verification_status(visitor: Visitor, data: VisitorVerificationDTO) -> str:
    if data.security_screening_status == "DENIED":
        return "FAILED"
    biometric_ok = data.biometric_verified if visitor.biometric_id else True
    if data.national_id_verified and biometric_ok and data.blacklist_checked and not visitor.blacklist_status and data.security_screening_status == "CLEARED":
        return "VERIFIED"
    return "PENDING"


def _validate_request_review(connection, request: VisitorRequest, updates: dict[str, Any]) -> None:
    approval_status = updates.get("approval_status")
    if approval_status == "APPROVED":
        visitor = _require_visitor(connection, request.visitor_id)
        latest = VisitorRepository.latest_verification(connection, request.visitor_id)
        if visitor.blacklist_status:
            raise VisitorWorkflowError("Blacklisted visitors cannot be approved")
        if visitor.verification_status != "VERIFIED" or latest is None:
            raise VisitorWorkflowError("Approved visit requests require completed verification")
    if approval_status == "REJECTED" and not updates.get("review_notes"):
        raise VisitorWorkflowError("Rejected requests require review notes")


def is_duplicate_visitor_error(exc: Exception) -> bool:
    return isinstance(exc, IntegrityError) and getattr(exc, "errno", None) == 1062


def is_mysql_error(exc: Exception) -> bool:
    return isinstance(exc, MySQLError)
