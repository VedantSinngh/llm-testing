"""Integration tests for SafetyService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from promptlab.core.providers.mock_provider import MockProvider
from promptlab.db.repositories import SafetyRepository
from promptlab.exceptions import ResourceNotFoundError
from promptlab.services.safety_service import SafetyService


@pytest.mark.asyncio
async def test_safety_service_run_injection_and_persist(
    async_db_session: AsyncSession,
) -> None:
    """Verify executing injection vulnerability audit and retrieving persisted report."""
    safety_repo = SafetyRepository(async_db_session)
    mock_provider = MockProvider(simulated_latency_ms=0.0)

    service = SafetyService(
        safety_repo=safety_repo,
        provider=mock_provider,
    )

    result = await service.run_injection_test(
        model="mock-llama-3.3-70b",
        canary="CANARY-SEC99",
    )

    assert result["model"] == "mock-llama-3.3-70b"
    assert "report_id" in result
    report_id = result["report_id"]

    # Verify retrieval from database
    persisted = await service.get_report(report_id)
    assert persisted["id"] == report_id
    assert persisted["model"] == "mock-llama-3.3-70b"
    assert isinstance(persisted["injection_results"], list)


def test_safety_service_scan_text(async_db_session: AsyncSession) -> None:
    """Verify scanning text for PII returns structured SafetyReport."""
    service = SafetyService(safety_repo=SafetyRepository(async_db_session))
    text = "Send credentials to admin@corp.io and bill 4532-0151-1283-0366."

    report = service.scan_text(text)
    assert report.risk_level == "high"
    assert report.passed is False
    assert len(report.pii_findings) == 2


@pytest.mark.asyncio
async def test_safety_service_missing_report_error(
    async_db_session: AsyncSession,
) -> None:
    """Verify ResourceNotFoundError when report does not exist."""
    service = SafetyService(safety_repo=SafetyRepository(async_db_session))
    with pytest.raises(ResourceNotFoundError):
        await service.get_report("non-existent-report-uuid")
