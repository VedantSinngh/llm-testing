"""Integration tests for ComparisonService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from promptlab.core.models import (
    CaseResult,
    GenerationParams,
    LLMResponse,
    RunResult,
)
from promptlab.db.repositories import RunRepository
from promptlab.exceptions import ResourceNotFoundError, ValidationError
from promptlab.services.comparison_service import ComparisonService


@pytest.mark.asyncio
async def test_comparison_service_matrix(async_db_session: AsyncSession) -> None:
    """Verify side-by-side comparison matrix generation from persisted runs."""
    run_repo = RunRepository(async_db_session)
    comp_service = ComparisonService(run_repo)

    # Manufacturing Run 1 (Llama, pass_rate=1.0, latency=50ms)
    run1 = RunResult(
        run_id="run-1",
        suite_name="qa_suite",
        model="llama-3.3-70b",
        params=GenerationParams(temperature=0.0),
        technique="zero_shot",
        case_results=[
            CaseResult(
                case_id="tc_1",
                response=LLMResponse(text="Ans 1", model="llama-3.3-70b", latency_ms=50.0),
                score=1.0,
                passed=True,
                reason="Match",
            )
        ],
        pass_rate=1.0,
        avg_latency_ms=50.0,
        total_tokens=20,
    )

    # Manufacturing Run 2 (Qwen, pass_rate=0.0, latency=100ms)
    run2 = RunResult(
        run_id="run-2",
        suite_name="qa_suite",
        model="qwen-2.5-72b",
        params=GenerationParams(temperature=0.7),
        technique="zero_shot",
        case_results=[
            CaseResult(
                case_id="tc_1",
                response=LLMResponse(text="Wrong Ans", model="qwen-2.5-72b", latency_ms=100.0),
                score=0.0,
                passed=False,
                reason="Mismatch",
            )
        ],
        pass_rate=0.0,
        avg_latency_ms=100.0,
        total_tokens=30,
    )

    await run_repo.save(run1)
    await run_repo.save(run2)

    comparison = await comp_service.compare_runs_by_ids(["run-1", "run-2"])

    assert comparison["run_count"] == 2
    assert len(comparison["summaries"]) == 2
    assert comparison["best_performing_model"] == "llama-3.3-70b"
    assert comparison["fastest_model"] == "llama-3.3-70b"

    # Verify per-case breakdown
    matrix = comparison["case_matrix"]
    assert len(matrix) == 1
    assert matrix[0]["case_id"] == "tc_1"
    assert matrix[0]["runs"]["run-1"]["passed"] is True
    assert matrix[0]["runs"]["run-2"]["passed"] is False


@pytest.mark.asyncio
async def test_comparison_service_validations(async_db_session: AsyncSession) -> None:
    """Verify validation on count and missing IDs."""
    run_repo = RunRepository(async_db_session)
    comp_service = ComparisonService(run_repo)

    with pytest.raises(ValidationError):
        await comp_service.compare_runs_by_ids(["single-run-id"])

    with pytest.raises(ResourceNotFoundError):
        await comp_service.compare_runs_by_ids(["missing-1", "missing-2"])
