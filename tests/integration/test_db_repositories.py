"""Integration tests for SuiteRepository, RunRepository, and SafetyRepository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from promptlab.core.models import (
    CaseResult,
    GenerationParams,
    LLMResponse,
    RunResult,
    SafetyReport,
    TestCase,
    TestSuite,
)
from promptlab.db.repositories import RunRepository, SafetyRepository, SuiteRepository


@pytest.mark.asyncio
async def test_suite_repository_crud(async_db_session: AsyncSession) -> None:
    """Verify SuiteRepository save, retrieve, update, list, and delete operations."""
    repo = SuiteRepository(async_db_session)
    test_case = TestCase(
        id="c1", input="Input 1", expected="Exp 1", scorer="exact_match"
    )
    suite = TestSuite(
        name="crud_suite",
        description="Testing CRUD",
        system_prompt="Be concise",
        technique="zero_shot",
        cases=[test_case],
    )

    # 1. Save
    suite_id = await repo.save(suite)
    assert suite_id is not None

    # 2. Get by ID
    fetched = await repo.get_by_id(suite_id)
    assert fetched is not None
    f_id, f_suite = fetched
    assert f_id == suite_id
    assert f_suite.name == "crud_suite"
    assert len(f_suite.cases) == 1
    assert f_suite.cases[0].id == "c1"

    # 3. Get by Name
    by_name = await repo.get_by_name("crud_suite")
    assert by_name is not None
    assert by_name[0] == suite_id

    # 4. Update
    updated_suite = TestSuite(
        name="crud_suite",
        description="Updated description",
        cases=[test_case],
    )
    await repo.save(updated_suite, suite_id=suite_id)
    _, re_fetched = (await repo.get_by_id(suite_id)) or ("", None)
    assert re_fetched is not None
    assert re_fetched.description == "Updated description"

    # 5. List
    suites, total = await repo.list(limit=10)
    assert total >= 1
    assert any(s[0] == suite_id for s in suites)

    # 6. Delete
    deleted = await repo.delete(suite_id)
    assert deleted is True
    assert await repo.get_by_id(suite_id) is None


@pytest.mark.asyncio
async def test_run_repository_crud(async_db_session: AsyncSession) -> None:
    """Verify RunRepository save, child case results loading, and list filtering."""
    repo = RunRepository(async_db_session)
    case_resp = LLMResponse(
        text="Sample output text",
        model="mock-model",
        latency_ms=120.5,
        prompt_tokens=15,
        completion_tokens=25,
        raw_finish_reason="stop",
    )
    case_result = CaseResult(
        case_id="tc_1",
        response=case_resp,
        score=1.0,
        passed=True,
        reason="Perfect match",
    )
    run_result = RunResult(
        run_id="run-uuid-abc-123",
        suite_name="qa_suite",
        model="mock-llama-3.3-70b",
        params=GenerationParams(temperature=0.0),
        technique="zero_shot",
        case_results=[case_result],
        pass_rate=1.0,
        avg_latency_ms=120.5,
        total_tokens=40,
    )

    # 1. Save
    saved_id = await repo.save(run_result)
    assert saved_id == "run-uuid-abc-123"

    # 2. Get by ID (eagerly loading child case results)
    fetched = await repo.get_by_id("run-uuid-abc-123")
    assert fetched is not None
    assert fetched.suite_name == "qa_suite"
    assert fetched.model == "mock-llama-3.3-70b"
    assert len(fetched.case_results) == 1
    assert fetched.case_results[0].case_id == "tc_1"
    assert fetched.case_results[0].response.text == "Sample output text"
    assert fetched.case_results[0].response.prompt_tokens == 15

    # 3. List with filters
    filtered_runs, count = await repo.list(suite_name="qa_suite", model="mock-llama-3.3-70b")
    assert count == 1
    assert len(filtered_runs) == 1

    # 4. Delete
    deleted = await repo.delete("run-uuid-abc-123")
    assert deleted is True
    assert await repo.get_by_id("run-uuid-abc-123") is None


@pytest.mark.asyncio
async def test_safety_repository_crud(async_db_session: AsyncSession) -> None:
    """Verify SafetyRepository save, fetch, and list."""
    repo = SafetyRepository(async_db_session)
    report = SafetyReport(
        injection_results=[{"attack_id": "inj_1", "breached": False}],
        pii_findings=[],
        risk_level="low",
        passed=True,
    )

    report_id = await repo.save(report, model="mock-model")
    assert report_id is not None

    fetched = await repo.get_by_id(report_id)
    assert fetched is not None
    assert fetched["model"] == "mock-model"
    assert fetched["risk_level"] == "low"
    assert fetched["passed"] is True

    reports, total = await repo.list()
    assert total >= 1
    assert any(r["id"] == report_id for r in reports)
