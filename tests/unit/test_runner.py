"""Unit tests for TestRunner execution, concurrency, and error handling."""

import pytest

from promptlab.core.models import GenerationParams, TestCase, TestSuite
from promptlab.core.providers.mock_provider import MockProvider
from promptlab.core.runner import TestRunner


@pytest.mark.asyncio
async def test_runner_basic_suite_execution() -> None:
    """Verify TestRunner evaluates all cases in suite and aggregates metrics."""
    provider = MockProvider(simulated_latency_ms=2.0)
    cases = [
        TestCase(id="c1", input="What is 2+2?", expected="4", scorer="exact_match"),
        TestCase(id="c2", input="Say hello", expected="hello", scorer="contains"),
    ]
    suite = TestSuite(name="basic_math", technique="zero_shot", cases=cases)

    provider.set_canned_response("2+2", "4")
    provider.set_canned_response("hello", "Well hello there!")

    runner = TestRunner(provider=provider)
    result = await runner.run_suite(suite, model="mock-llama-3.3-70b")

    assert result.suite_name == "basic_math"
    assert result.model == "mock-llama-3.3-70b"
    assert len(result.case_results) == 2
    assert result.pass_rate == 1.0
    assert result.avg_latency_ms >= 1.0
    assert result.total_tokens > 0


@pytest.mark.asyncio
async def test_runner_fault_tolerance_per_case() -> None:
    """Verify that a failure in one test case does not abort the entire run."""
    provider = MockProvider(simulated_latency_ms=0.0)
    cases = [
        TestCase(id="good_1", input="Ping", expected="Pong", scorer="exact_match"),
        TestCase(id="bad_scorer", input="Test", expected="X", scorer="non_existent_scorer"),
        TestCase(id="good_2", input="Ping", expected="Pong", scorer="exact_match"),
    ]
    suite = TestSuite(name="fault_tolerance_suite", cases=cases)
    provider.set_canned_response("ping", "Pong")

    runner = TestRunner(provider=provider)
    result = await runner.run_suite(suite, model="mock-model")

    assert len(result.case_results) == 3
    # Case with missing scorer should fail gracefully
    bad_case = next(cr for cr in result.case_results if cr.case_id == "bad_scorer")
    assert bad_case.passed is False
    assert bad_case.score == 0.0
    assert bad_case.error is not None
    assert "SCORER_NOT_FOUND" in str(bad_case.error) or "not registered" in str(bad_case.error)

    # Other cases must pass
    good_cases = [cr for cr in result.case_results if cr.case_id.startswith("good")]
    assert len(good_cases) == 2
    assert all(cr.passed for cr in good_cases)
    assert result.pass_rate == round(2 / 3, 4)


@pytest.mark.asyncio
async def test_runner_technique_application() -> None:
    """Verify that suite-level prompt technique is applied to inputs."""
    provider = MockProvider(simulated_latency_ms=0.0)
    provider.set_canned_response("answer: 4", "Correct! Answer: 4")

    cases = [
        TestCase(id="cot_1", input="Calculate 2*2", expected="Answer: 4", scorer="contains"),
    ]
    suite = TestSuite(
        name="cot_suite",
        technique="chain_of_thought",
        cases=cases,
    )

    runner = TestRunner(provider=provider)
    result = await runner.run_suite(suite, model="mock-model")
    assert result.technique == "chain_of_thought"
    assert result.pass_rate == 1.0


@pytest.mark.asyncio
async def test_runner_matrix_sweep() -> None:
    """Verify run_matrix evaluates all model and parameter combinations."""
    provider = MockProvider(simulated_latency_ms=0.0)
    provider.set_canned_response("2+2", "4")

    suite = TestSuite(
        name="sweep_suite",
        cases=[TestCase(id="s1", input="2+2", expected="4", scorer="exact_match")],
    )

    runner = TestRunner(provider=provider)
    models = ["mock-llama-3.3-70b", "mock-qwen-2.5-72b"]
    param_sets = [
        GenerationParams(temperature=0.0),
        GenerationParams(temperature=0.7),
    ]

    matrix_results = await runner.run_matrix(suite, models=models, param_sets=param_sets)
    # 2 models * 2 parameter sets = 4 runs
    assert len(matrix_results) == 4
    model_names = {r.model for r in matrix_results}
    assert model_names == {"mock-llama-3.3-70b", "mock-qwen-2.5-72b"}
    temperatures = {r.params.temperature for r in matrix_results}
    assert temperatures == {0.0, 0.7}
