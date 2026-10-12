"""Integration tests for EvaluationService facade."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from promptlab.config import Settings
from promptlab.core.models import GenerationParams, TestCase, TestSuite
from promptlab.core.providers.mock_provider import MockProvider
from promptlab.db.repositories import RunRepository, SuiteRepository
from promptlab.exceptions import ResourceNotFoundError
from promptlab.services.evaluation_service import EvaluationService


@pytest.mark.asyncio
async def test_evaluation_service_end_to_end_flow(
    async_db_session: AsyncSession,
) -> None:
    """Verify complete evaluation workflow: suite creation, execution, and persistence."""
    suite_repo = SuiteRepository(async_db_session)
    run_repo = RunRepository(async_db_session)

    mock_provider = MockProvider(simulated_latency_ms=0.0)
    mock_provider.set_canned_response("2+2", "4")
    mock_provider.set_canned_response("5+5", "10")

    service = EvaluationService(
        suite_repo=suite_repo,
        run_repo=run_repo,
        provider=mock_provider,
        settings=Settings(demo_mode=True),
    )

    # 1. Create suite
    suite = TestSuite(
        name="math_service_suite",
        description="Math tests",
        technique="zero_shot",
        cases=[
            TestCase(id="m1", input="2+2", expected="4", scorer="exact_match"),
            TestCase(id="m2", input="5+5", expected="10", scorer="exact_match"),
        ],
    )
    suite_id = await service.create_suite(suite)
    assert suite_id is not None

    # 2. Execute run using persisted suite ID
    run_result = await service.execute_run(
        suite_id_or_object=suite_id,
        model="mock-llama-3.3-70b",
        params=GenerationParams(temperature=0.0),
    )

    assert run_result.suite_name == "math_service_suite"
    assert run_result.model == "mock-llama-3.3-70b"
    assert run_result.pass_rate == 1.0
    assert len(run_result.case_results) == 2

    # 3. Retrieve run directly from database via service
    persisted_run = await service.get_run(run_result.run_id)
    assert persisted_run.run_id == run_result.run_id
    assert persisted_run.pass_rate == 1.0
    assert len(persisted_run.case_results) == 2


@pytest.mark.asyncio
async def test_evaluation_service_matrix_execution(
    async_db_session: AsyncSession,
) -> None:
    """Verify matrix execution across multiple models and parameter sets."""
    suite_repo = SuiteRepository(async_db_session)
    run_repo = RunRepository(async_db_session)
    mock_provider = MockProvider(simulated_latency_ms=0.0)
    mock_provider.set_canned_response("hello", "world")

    service = EvaluationService(
        suite_repo=suite_repo,
        run_repo=run_repo,
        provider=mock_provider,
    )

    suite = TestSuite(
        name="matrix_suite",
        cases=[TestCase(id="c1", input="hello", expected="world", scorer="exact_match")],
    )

    models = ["mock-model-a", "mock-model-b"]
    params_list = [GenerationParams(temperature=0.0), GenerationParams(temperature=1.0)]

    runs = await service.execute_matrix(
        suite_id_or_object=suite,
        models=models,
        params_list=params_list,
    )

    assert len(runs) == 4
    # Check that all 4 runs exist in DB
    for r in runs:
        saved = await service.get_run(r.run_id)
        assert saved is not None


@pytest.mark.asyncio
async def test_evaluation_service_not_found_handling(
    async_db_session: AsyncSession,
) -> None:
    """Verify ResourceNotFoundError is raised for non-existent suite or run IDs."""
    service = EvaluationService(
        suite_repo=SuiteRepository(async_db_session),
        run_repo=RunRepository(async_db_session),
    )

    with pytest.raises(ResourceNotFoundError):
        await service.get_suite("invalid-suite-id")

    with pytest.raises(ResourceNotFoundError):
        await service.get_run("invalid-run-id")
