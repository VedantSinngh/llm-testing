"""Evaluation Runs execution, querying, and comparison routes.

This module exposes endpoints for:
- Executing an evaluation run on a model and persisting the results.
- Querying historical runs with pagination and filtering.
- Running side-by-side comparative analysis across multiple runs.
"""

from fastapi import APIRouter, Depends, Query, status

from promptlab.api.dependencies import (
    get_comparison_service,
    get_evaluation_service,
)
from promptlab.api.schemas import (
    CompareRequest,
    CompareResponse,
    RunExecuteRequest,
    RunListResponse,
)
from promptlab.core.models import RunResult
from promptlab.services.comparison_service import ComparisonService
from promptlab.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.post("", response_model=RunResult, status_code=status.HTTP_201_CREATED)
async def execute_run(
    payload: RunExecuteRequest,
    eval_service: EvaluationService = Depends(get_evaluation_service),
) -> RunResult:
    """Execute an evaluation run against a model and persist metrics."""
    target_suite = payload.suite_id if payload.suite_id else payload.suite
    assert target_suite is not None  # Guaranteed by model validator

    return await eval_service.execute_run(
        suite_id_or_object=target_suite,
        model=payload.model,
        params=payload.params,
        provider_name=payload.provider,
    )


@router.get("", response_model=RunListResponse)
async def list_runs(
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
    limit: int = Query(default=50, ge=1, le=100, description="Max items to retrieve."),
    suite_name: str | None = Query(default=None, description="Optional suite name filter."),
    model: str | None = Query(default=None, description="Optional model filter."),
    eval_service: EvaluationService = Depends(get_evaluation_service),
) -> RunListResponse:
    """Retrieve historical evaluation runs with optional filters."""
    items, total = await eval_service.list_runs(
        offset=offset,
        limit=limit,
        suite_name=suite_name,
        model=model,
    )
    return RunListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{run_id}", response_model=RunResult)
async def get_run(
    run_id: str,
    eval_service: EvaluationService = Depends(get_evaluation_service),
) -> RunResult:
    """Retrieve detailed evaluation run by ID."""
    return await eval_service.get_run(run_id)


@router.post("/compare", response_model=CompareResponse)
async def compare_runs(
    payload: CompareRequest,
    comparison_service: ComparisonService = Depends(get_comparison_service),
) -> CompareResponse:
    """Generate side-by-side comparison analytics across multiple evaluation runs."""
    matrix = await comparison_service.compare_runs_by_ids(payload.run_ids)
    return CompareResponse(**matrix)
