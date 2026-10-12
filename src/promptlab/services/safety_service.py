"""Safety Service orchestrating adversarial audits and PII scanning.

This module coordinates safety evaluations:
- Running prompt injection attack suites with canary tracking.
- Scanning text payloads for leaked PII and API credentials.
- Persisting safety audit logs into the database.
"""

from typing import Any

from promptlab.config import Settings, get_settings
from promptlab.core.models import SafetyReport
from promptlab.core.providers.base import LLMProvider
from promptlab.core.providers.factory import ProviderFactory
from promptlab.core.safety.guardrail import Guardrail
from promptlab.core.safety.injection_suite import InjectionSuite
from promptlab.db.repositories import SafetyRepository
from promptlab.exceptions import ResourceNotFoundError


class SafetyService:
    """Service for running injection vulnerability tests and PII scans."""

    def __init__(
        self,
        safety_repo: SafetyRepository,
        provider: LLMProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize SafetyService with repository and dependencies."""
        self._safety_repo = safety_repo
        self._provider = provider
        self._settings = settings or get_settings()
        self._guardrail = Guardrail()
        self._injection_suite = InjectionSuite()

    def _resolve_provider(self, provider_name: str | None = None) -> LLMProvider:
        """Resolve LLMProvider respecting demo mode settings."""
        if self._provider is not None:
            return self._provider
        if self._settings.demo_mode:
            return ProviderFactory.create("mock")
        target_name = provider_name or "groq"
        return ProviderFactory.create(target_name)

    async def run_injection_test(
        self,
        model: str,
        canary: str | None = None,
        provider_name: str | None = None,
    ) -> dict[str, Any]:
        """Execute adversarial injection attack suite and persist safety report."""
        provider = self._resolve_provider(provider_name)
        suite_report = await self._injection_suite.run_suite(
            provider=provider,
            model=model,
            canary=canary,
            max_concurrency=self._settings.max_concurrency,
        )

        breached = int(suite_report["breached_count"])
        risk_level = "high" if breached > 0 else "low"
        safety_report = SafetyReport(
            injection_results=suite_report["results"],
            pii_findings=[],
            risk_level=risk_level,
            passed=breached == 0,
        )

        report_id = await self._safety_repo.save(safety_report, model=model)
        suite_report["report_id"] = report_id
        suite_report["tested_count"] = int(
            suite_report.get("tested_count")
            or suite_report.get("total_attacks")
            or len(suite_report.get("results", []))
        )
        return suite_report

    def scan_text(self, text: str) -> SafetyReport:
        """Scan arbitrary text for PII entities, API credentials, and network addresses."""
        return self._guardrail.check_text(text)

    async def get_report(self, report_id: str) -> dict[str, Any]:
        """Retrieve stored safety report by ID."""
        report = await self._safety_repo.get_by_id(report_id)
        if not report:
            raise ResourceNotFoundError("SafetyReport", report_id)
        return report

    async def list_reports(
        self, offset: int = 0, limit: int = 50
    ) -> tuple[list[dict[str, Any]], int]:
        """List historical safety reports with pagination."""
        return await self._safety_repo.list(offset=offset, limit=limit)
