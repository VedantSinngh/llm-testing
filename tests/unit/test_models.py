"""Unit tests for Pydantic domain models validation and behavior."""

import pytest
from pydantic import ValidationError

from promptlab.core.models import (
    CaseResult,
    GenerationParams,
    LLMRequest,
    LLMResponse,
    RunResult,
    SafetyReport,
    ScoreResult,
    TestCase,
    TestSuite,
)


def test_generation_params_defaults_and_validation() -> None:
    """Verify default values and constraint validation for GenerationParams."""
    params = GenerationParams()
    assert params.temperature == 0.7
    assert params.top_p == 1.0
    assert params.max_tokens == 1024
    assert params.seed is None

    # Test temperature bounds
    with pytest.raises(ValidationError):
        GenerationParams(temperature=-0.1)
    with pytest.raises(ValidationError):
        GenerationParams(temperature=2.1)

    # Test top_p bounds
    with pytest.raises(ValidationError):
        GenerationParams(top_p=-0.1)
    with pytest.raises(ValidationError):
        GenerationParams(top_p=1.1)

    # Test max_tokens bounds
    with pytest.raises(ValidationError):
        GenerationParams(max_tokens=0)
    with pytest.raises(ValidationError):
        GenerationParams(max_tokens=10000)


def test_generation_params_frozen() -> None:
    """Verify GenerationParams is immutable."""
    params = GenerationParams()
    with pytest.raises(ValidationError):
        params.temperature = 0.5  # type: ignore[misc]


def test_llm_request_validation(sample_params: GenerationParams) -> None:
    """Verify LLMRequest validates non-empty model and prompt strings."""
    req = LLMRequest(
        model="llama-3.3-70b-versatile",
        prompt="Test prompt",
        params=sample_params,
    )
    assert req.model == "llama-3.3-70b-versatile"
    assert req.prompt == "Test prompt"
    assert req.system_prompt is None

    with pytest.raises(ValidationError):
        LLMRequest(model="", prompt="Test prompt")

    with pytest.raises(ValidationError):
        LLMRequest(model="llama-3.3-70b-versatile", prompt="")


def test_llm_response_validation() -> None:
    """Verify LLMResponse requires non-negative latency and valid tokens."""
    res = LLMResponse(
        text="Sample output",
        model="llama-3.3-70b-versatile",
        latency_ms=85.5,
        prompt_tokens=10,
        completion_tokens=20,
    )
    assert res.latency_ms == 85.5
    assert res.prompt_tokens == 10
    assert res.completion_tokens == 20

    with pytest.raises(ValidationError):
        LLMResponse(
            text="Sample",
            model="llama-3.3-70b-versatile",
            latency_ms=-1.0,
        )


def test_score_result_clamping_and_validation() -> None:
    """Verify ScoreResult enforces 0.0 to 1.0 range."""
    sr = ScoreResult(score=0.85, passed=True, reason="High similarity")
    assert sr.score == 0.85
    assert sr.passed is True

    with pytest.raises(ValidationError):
        ScoreResult(score=-0.01, passed=False, reason="Negative score")

    with pytest.raises(ValidationError):
        ScoreResult(score=1.01, passed=True, reason="Above max score")


def test_test_case_validation() -> None:
    """Verify TestCase structure and defaults."""
    tc = TestCase(
        id="tc-101",
        input="Summarize this text",
        scorer="llm_judge",
    )
    assert tc.id == "tc-101"
    assert tc.expected is None
    assert tc.scorer_config == {}
    assert tc.tags == []

    with pytest.raises(ValidationError):
        TestCase(id="", input="Something", scorer="exact_match")


def test_test_suite_requires_cases() -> None:
    """Verify TestSuite requires at least one test case."""
    with pytest.raises(ValidationError):
        TestSuite(name="empty_suite", cases=[])


def test_run_result_generation(
    sample_params: GenerationParams, sample_case_result: CaseResult
) -> None:
    """Verify RunResult default UUID generation and fields."""
    run = RunResult(
        suite_name="test_suite",
        model="qwen-2.5-72b",
        params=sample_params,
        technique="few_shot",
        case_results=[sample_case_result],
        pass_rate=1.0,
        avg_latency_ms=120.0,
    )
    assert len(run.run_id) > 10
    assert run.pass_rate == 1.0
    assert run.avg_latency_ms == 120.0


def test_safety_report_risk_level() -> None:
    """Verify SafetyReport validates allowed risk levels."""
    report = SafetyReport(risk_level="high", passed=False)
    assert report.risk_level == "high"
    assert report.passed is False

    with pytest.raises(ValidationError):
        SafetyReport(risk_level="critical")  # type: ignore[arg-type]
