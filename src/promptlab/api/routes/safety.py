"""Safety guardrail and prompt injection audit routes.

This module exposes endpoints for:
- Executing adversarial prompt injection vulnerability tests against models.
- Scanning arbitrary input or output text for PII entities, tokens, and credentials.
- Querying historical safety audits and risk classifications.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status

from promptlab.api.dependencies import get_safety_service
from promptlab.api.schemas import (
    InjectionTestRequest,
    SafetyReportListResponse,
    ScanTextRequest,
    ScanTextResponse,
)
from promptlab.services.safety_service import SafetyService

router = APIRouter(prefix="/safety", tags=["Safety"])


@router.post("/injection-test", response_model=dict[str, Any], status_code=status.HTTP_200_OK)
async def run_injection_test(
    payload: InjectionTestRequest,
    safety_service: SafetyService = Depends(get_safety_service),
) -> dict[str, Any]:
    """Execute adversarial prompt injection test suite against a model."""
    return await safety_service.run_injection_test(
        model=payload.model,
        canary=payload.canary,
        provider_name=payload.provider,
    )


@router.post("/scan", response_model=ScanTextResponse)
async def scan_text(
    payload: ScanTextRequest,
    safety_service: SafetyService = Depends(get_safety_service),
) -> ScanTextResponse:
    """Scan text payload for PII entities, leaked secrets, and risk scoring."""
    is_safe, sanitized, report = safety_service._guardrail.filter_text(payload.text)
    return ScanTextResponse(
        risk_level=report.risk_level,
        passed=is_safe,
        pii_findings=report.pii_findings,
        redacted_text=sanitized,
    )


@router.get("/reports", response_model=SafetyReportListResponse)
async def list_safety_reports(
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
    limit: int = Query(default=50, ge=1, le=100, description="Max items to retrieve."),
    safety_service: SafetyService = Depends(get_safety_service),
) -> SafetyReportListResponse:
    """Retrieve historical safety audit reports."""
    items, total = await safety_service.list_reports(offset=offset, limit=limit)
    return SafetyReportListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/reports/{report_id}", response_model=dict[str, Any])
async def get_safety_report(
    report_id: str,
    safety_service: SafetyService = Depends(get_safety_service),
) -> dict[str, Any]:
    """Retrieve single safety audit report by ID."""
    return await safety_service.get_report(report_id)
