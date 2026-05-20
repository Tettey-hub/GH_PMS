from __future__ import annotations

from dataclasses import asdict
from typing import Any

from mysql.connector import Error as MySQLError, IntegrityError

from src.config.database_config import db_connection
from src.dtos.external_integration_dto import (
    APIIntegrationDTO,
    BiometricIntegrationDTO,
    CloudBackupLogDTO,
    CourtIntegrationDTO,
    NIAIntegrationDTO,
    PoliceIntegrationDTO,
    SynchronizationLogDTO,
)
from src.integrations.adapters import IntegrationOperation, IntegrationProviderNotConfigured, integration_adapter_registry
from src.integrations.security import (
    IntegrationSecurityError,
    assert_encryption_ready,
    assert_https_reference,
    assert_no_insecure_url,
    validate_provider_operation_security,
)
from src.models.external_integration import ExternalIntegrationRecord
from src.repositories.external_integration_repository import ExternalIntegrationRepository


class ExternalIntegrationNotFoundError(LookupError):
    pass


class ExternalIntegrationConflictError(ValueError):
    pass


class ExternalIntegrationForeignKeyError(ValueError):
    pass


class ExternalIntegrationWorkflowError(ValueError):
    pass


class ExternalIntegrationSecurityError(ValueError):
    pass


class ExternalIntegrationService:
    @staticmethod
    def record_court_integration(data: CourtIntegrationDTO) -> ExternalIntegrationRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                assert_encryption_ready()
                assert_no_insecure_url(data.court_api_source, field_name="court_api_source")
                record = ExternalIntegrationRepository.create(connection, "court_integrations", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def record_nia_integration(data: NIAIntegrationDTO) -> ExternalIntegrationRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                assert_encryption_ready()
                record = ExternalIntegrationRepository.create(connection, "nia_integrations", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def record_police_integration(data: PoliceIntegrationDTO) -> ExternalIntegrationRecord:
        with db_connection() as connection:
            try:
                _require_inmate(connection, data.inmate_id)
                assert_encryption_ready()
                record = ExternalIntegrationRepository.create(connection, "police_integrations", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def record_biometric_integration(data: BiometricIntegrationDTO) -> ExternalIntegrationRecord:
        with db_connection() as connection:
            try:
                if data.inmate_id is not None:
                    _require_inmate(connection, data.inmate_id)
                if data.visitor_id is not None:
                    _require_visitor(connection, data.visitor_id)
                if data.staff_id is not None:
                    _require_user(connection, data.staff_id, "Staff user does not exist")
                assert_encryption_ready()
                record = ExternalIntegrationRepository.create(connection, "biometric_integrations", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def register_api_integration(data: APIIntegrationDTO) -> ExternalIntegrationRecord:
        with db_connection() as connection:
            try:
                if ExternalIntegrationRepository.api_integration_name_exists(connection, data.integration_name):
                    raise ExternalIntegrationConflictError("Integration name already exists")
                if not data.encryption_enabled:
                    raise ExternalIntegrationWorkflowError("External integrations must have encrypted communication enabled")
                assert_encryption_ready()
                assert_https_reference(data.endpoint_reference, field_name="endpoint_reference")
                record = ExternalIntegrationRepository.create(connection, "api_integrations", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def record_synchronization(data: SynchronizationLogDTO) -> ExternalIntegrationRecord:
        with db_connection() as connection:
            try:
                if data.synchronization_status == "SYNCED" and data.completed_at is None:
                    raise ExternalIntegrationWorkflowError("Completed synchronization requires completed_at")
                if data.synchronization_status == "FAILED" and not data.error_message:
                    raise ExternalIntegrationWorkflowError("Failed synchronization requires error_message")
                assert_encryption_ready()
                assert_no_insecure_url(data.target_server, field_name="target_server")
                if ExternalIntegrationRepository.synchronization_duplicate_exists(
                    connection,
                    source_facility=data.source_facility,
                    target_server=data.target_server,
                    synchronization_type=data.synchronization_type,
                    last_attempt_at=data.last_attempt_at,
                ):
                    raise ExternalIntegrationConflictError("Duplicate synchronization attempt detected")
                record = ExternalIntegrationRepository.create(connection, "synchronization_logs", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def record_cloud_backup(data: CloudBackupLogDTO) -> ExternalIntegrationRecord:
        with db_connection() as connection:
            try:
                if ExternalIntegrationRepository.backup_reference_exists(connection, data.backup_reference):
                    raise ExternalIntegrationConflictError("Backup reference already exists")
                if data.backup_status == "COMPLETED" and data.backup_completed_at is None:
                    raise ExternalIntegrationWorkflowError("Completed backup requires backup_completed_at")
                if data.backup_status == "FAILED" and data.records_backed_up > 0:
                    raise ExternalIntegrationWorkflowError("Failed backup cannot report records backed up")
                assert_encryption_ready()
                assert_no_insecure_url(data.storage_location, field_name="storage_location")
                record = ExternalIntegrationRepository.create(connection, "cloud_backup_logs", asdict(data))
                connection.commit()
                return record
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def list_records(table: str, *, filters: dict[str, Any], limit: int, offset: int) -> list[ExternalIntegrationRecord]:
        with db_connection() as connection:
            return ExternalIntegrationRepository.list_records(connection, table, filters=filters, limit=limit, offset=offset)

    @staticmethod
    def get_reports() -> dict[str, Any]:
        with db_connection() as connection:
            return ExternalIntegrationRepository.reports(connection)

    @staticmethod
    def execute_provider_operation(*, provider: str, operation: str, reference: str) -> dict[str, Any]:
        validate_provider_operation_security(provider=provider, operation=operation, reference=reference)
        adapter = integration_adapter_registry.get(provider)
        integration_operation = IntegrationOperation(provider=provider, operation=operation, reference=reference)
        try:
            if operation == "warrant_verification":
                return adapter.verify_warrant(integration_operation)
            if operation == "nia_verification":
                return adapter.verify_national_id(integration_operation)
            if operation == "police_synchronization":
                return adapter.synchronize_police_record(integration_operation)
            if operation == "biometric_verification":
                return adapter.verify_biometric(integration_operation)
            if operation == "health_check":
                return adapter.run_health_check(integration_operation)
            if operation == "cloud_backup":
                return adapter.execute_backup(integration_operation)
        except IntegrationProviderNotConfigured:
            raise
        raise ExternalIntegrationWorkflowError("Unsupported external provider operation")


def _require_inmate(connection, inmate_id: int) -> None:
    if not ExternalIntegrationRepository.inmate_exists(connection, inmate_id):
        raise ExternalIntegrationForeignKeyError("Inmate does not exist")


def _require_visitor(connection, visitor_id: int) -> None:
    if not ExternalIntegrationRepository.visitor_exists(connection, visitor_id):
        raise ExternalIntegrationForeignKeyError("Visitor does not exist")


def _require_user(connection, user_id: int, message: str) -> None:
    if not ExternalIntegrationRepository.user_exists(connection, user_id):
        raise ExternalIntegrationForeignKeyError(message)


def is_duplicate_external_integration_error(exc: Exception) -> bool:
    return isinstance(exc, IntegrityError) and getattr(exc, "errno", None) == 1062


def is_mysql_error(exc: Exception) -> bool:
    return isinstance(exc, MySQLError)
