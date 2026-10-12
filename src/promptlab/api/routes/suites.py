"""Evaluation Suites CRUD routes.

This module exposes REST endpoints to manage test suite configurations:
- Creating suites with custom prompt engineering techniques and test cases.
- Retrieving and listing test suites with pagination.
- Deleting test suites.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status

from promptlab.api.dependencies import get_evaluation_service
from promptlab.api.schemas import (
    SuiteCreateRequest,
    SuiteListResponse,
    SuiteResponse,
)
from promptlab.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/suites", tags=["Suites"])


@router.post("", response_model=SuiteResponse, status_code=status.HTTP_201_CREATED)
async def create_suite(
    payload: SuiteCreateRequest,
    eval_service: EvaluationService = Depends(get_evaluation_service),
) -> SuiteResponse:
    """Register and persist a new evaluation test suite."""
    suite = payload.to_test_suite()
    suite_id = await eval_service.create_suite(suite)
    return SuiteResponse(id=suite_id, suite=suite)


@router.get("", response_model=SuiteListResponse)
async def list_suites(
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
    limit: int = Query(default=50, ge=1, le=100, description="Max items to retrieve."),
    eval_service: EvaluationService = Depends(get_evaluation_service),
) -> SuiteListResponse:
    """Retrieve paginated evaluation suites."""
    items, total = await eval_service.list_suites(offset=offset, limit=limit)
    response_items = [SuiteResponse(id=item[0], suite=item[1]) for item in items]
    return SuiteListResponse(
        items=response_items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{suite_id}", response_model=SuiteResponse)
async def get_suite(
    suite_id: str,
    eval_service: EvaluationService = Depends(get_evaluation_service),
) -> SuiteResponse:
    """Retrieve an evaluation suite by its unique identifier."""
    target_id, suite = await eval_service.get_suite(suite_id)
    return SuiteResponse(id=target_id, suite=suite)


@router.delete("/{suite_id}", response_model=dict[str, Any])
async def delete_suite(
    suite_id: str,
    eval_service: EvaluationService = Depends(get_evaluation_service),
) -> dict[str, Any]:
    """Delete a test suite by ID."""
    await eval_service.delete_suite(suite_id)
    return {"deleted": True, "id": suite_id}
