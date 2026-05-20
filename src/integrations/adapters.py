from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class IntegrationProviderNotConfigured(RuntimeError):
    pass


@dataclass(frozen=True)
class IntegrationOperation:
    provider: str
    operation: str
    reference: str


class ExternalIntegrationAdapter(Protocol):
    def verify_warrant(self, operation: IntegrationOperation) -> dict:
        ...

    def verify_national_id(self, operation: IntegrationOperation) -> dict:
        ...

    def synchronize_police_record(self, operation: IntegrationOperation) -> dict:
        ...

    def verify_biometric(self, operation: IntegrationOperation) -> dict:
        ...

    def run_health_check(self, operation: IntegrationOperation) -> dict:
        ...

    def execute_backup(self, operation: IntegrationOperation) -> dict:
        ...


class NoConfiguredProviderAdapter:
    def _raise(self, operation: IntegrationOperation) -> dict:
        raise IntegrationProviderNotConfigured(
            f"No configured external provider for {operation.provider}:{operation.operation}. "
            "Configure a real provider adapter before executing external communication."
        )

    def verify_warrant(self, operation: IntegrationOperation) -> dict:
        return self._raise(operation)

    def verify_national_id(self, operation: IntegrationOperation) -> dict:
        return self._raise(operation)

    def synchronize_police_record(self, operation: IntegrationOperation) -> dict:
        return self._raise(operation)

    def verify_biometric(self, operation: IntegrationOperation) -> dict:
        return self._raise(operation)

    def run_health_check(self, operation: IntegrationOperation) -> dict:
        return self._raise(operation)

    def execute_backup(self, operation: IntegrationOperation) -> dict:
        return self._raise(operation)


class IntegrationAdapterRegistry:
    def __init__(self) -> None:
        self._default_adapter = NoConfiguredProviderAdapter()
        self._adapters: dict[str, ExternalIntegrationAdapter] = {}

    def register(self, provider: str, adapter: ExternalIntegrationAdapter) -> None:
        self._adapters[provider.strip().lower()] = adapter

    def get(self, provider: str) -> ExternalIntegrationAdapter:
        return self._adapters.get(provider.strip().lower(), self._default_adapter)


integration_adapter_registry = IntegrationAdapterRegistry()
