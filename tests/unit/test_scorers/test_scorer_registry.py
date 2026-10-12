"""Unit tests for ScorerRegistry and scorer instantiation."""

import pytest

from promptlab.core.models import ScoreResult, TestCase
from promptlab.core.scorers.base import BaseScorer
from promptlab.core.scorers.contains import Contains
from promptlab.core.scorers.exact_match import ExactMatch
from promptlab.core.scorers.json_schema import JsonSchema
from promptlab.core.scorers.json_valid import JsonValid
from promptlab.core.scorers.llm_judge import LLMJudge
from promptlab.core.scorers.regex_match import RegexMatch
from promptlab.core.scorers.registry import ScorerRegistry
from promptlab.core.scorers.sql_result import SqlResult
from promptlab.exceptions import ScorerNotFoundError


def test_registry_get_built_in_scorers() -> None:
    """Verify built-in scorers are retrievable by name."""
    assert isinstance(ScorerRegistry.get("exact_match"), ExactMatch)
    assert isinstance(ScorerRegistry.get("contains"), Contains)
    assert isinstance(ScorerRegistry.get("regex_match"), RegexMatch)
    assert isinstance(ScorerRegistry.get("json_valid"), JsonValid)
    assert isinstance(ScorerRegistry.get("json_schema"), JsonSchema)
    assert isinstance(ScorerRegistry.get("sql_result"), SqlResult)
    assert isinstance(ScorerRegistry.get("llm_judge"), LLMJudge)


def test_registry_case_insensitivity() -> None:
    """Verify lookup is case-insensitive."""
    assert isinstance(ScorerRegistry.get("EXACT_MATCH"), ExactMatch)
    assert isinstance(ScorerRegistry.get("Sql_Result"), SqlResult)


def test_registry_unregistered_scorer_raises_error() -> None:
    """Verify ScorerNotFoundError is raised for unknown scorer identifier."""
    with pytest.raises(ScorerNotFoundError) as exc_info:
        ScorerRegistry.get("non_existent_scorer")
    assert exc_info.value.status_code == 404
    assert "non_existent_scorer" in str(exc_info.value)


def test_registry_decorator_custom_scorer() -> None:
    """Verify custom scorer can be registered via decorator without modifying core."""

    @ScorerRegistry.register("custom_metric")
    class CustomMetric(BaseScorer):
        name: str = "custom_metric"

        def _evaluate(self, case: TestCase, output: str) -> ScoreResult:
            return ScoreResult(score=0.88, passed=True, reason="Custom metric passed.")

    assert "custom_metric" in ScorerRegistry.list_scorers()
    scorer = ScorerRegistry.get("custom_metric")
    assert isinstance(scorer, CustomMetric)

    case = TestCase(id="custom-1", input="Input", scorer="custom_metric")
    res = scorer.score(case, "Some output")
    assert res.score == 0.88
    assert res.passed is True


def test_list_scorers() -> None:
    """Verify list_scorers returns complete list of registered scorers."""
    scorers = ScorerRegistry.list_scorers()
    assert "exact_match" in scorers
    assert "contains" in scorers
    assert "regex_match" in scorers
    assert "json_valid" in scorers
    assert "json_schema" in scorers
    assert "sql_result" in scorers
    assert "llm_judge" in scorers
