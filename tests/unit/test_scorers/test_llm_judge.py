"""Unit tests for LLMJudge scorer."""

import pytest

from promptlab.core.models import TestCase
from promptlab.core.providers.mock_provider import MockProvider
from promptlab.core.scorers.llm_judge import LLMJudge


@pytest.mark.asyncio
async def test_llm_judge_score_async_success() -> None:
    """Verify LLMJudge parses valid JSON evaluation from judge provider."""
    mock_provider = MockProvider()
    mock_provider.set_canned_response(
        "evaluation rubric",
        '{"score": 0.90, "reason": "Accurate, well-structured explanation."}',
    )

    judge = LLMJudge(judge_provider=mock_provider, judge_model="mock-llama-3.3-70b")
    case = TestCase(
        id="judge-1",
        input="Explain recursion",
        expected="A function that calls itself.",
        scorer="llm_judge",
        scorer_config={"rubric": "Clarity and technical accuracy"},
    )

    result = await judge.score_async(
        case, "Recursion is when a function calls itself until a base condition."
    )
    assert result.score == 0.9
    assert result.passed is True
    assert "Accurate, well-structured explanation" in result.reason
    assert result.metadata["judge_model"] == "mock-llama-3.3-70b"


@pytest.mark.asyncio
async def test_llm_judge_score_async_failing_grade() -> None:
    """Verify score below 0.7 threshold marks case as passed=False."""
    mock_provider = MockProvider()
    mock_provider.set_canned_response(
        "evaluation rubric",
        '{"score": 0.45, "reason": "Missed base case explanation."}',
    )

    judge = LLMJudge(judge_provider=mock_provider, judge_model="mock-llama-3.3-70b")
    case = TestCase(
        id="judge-2",
        input="Explain recursion",
        scorer="llm_judge",
    )

    result = await judge.score_async(case, "Just keep calling function.")
    assert result.score == 0.45
    assert result.passed is False
    assert "Missed base case" in result.reason


@pytest.mark.asyncio
async def test_llm_judge_malformed_json_fallback() -> None:
    """Verify non-JSON judge response is caught without unhandled crash."""
    mock_provider = MockProvider()
    mock_provider.set_canned_response("evaluation rubric", "I think this deserves an 8 out of 10.")

    judge = LLMJudge(judge_provider=mock_provider, judge_model="mock-llama-3.3-70b")
    case = TestCase(id="judge-3", input="Task", scorer="llm_judge")

    result = await judge.score_async(case, "Some output")
    assert result.score == 0.0
    assert result.passed is False
    assert "Failed to parse LLM Judge output as JSON" in result.reason


def test_llm_judge_sync_evaluation_warning() -> None:
    """Verify synchronous score() call guides user to score_async()."""
    judge = LLMJudge()
    case = TestCase(id="judge-4", input="Task", scorer="llm_judge")
    result = judge.score(case, "Output")
    assert result.score == 0.0
    assert result.passed is False
    assert "score_async" in result.reason
