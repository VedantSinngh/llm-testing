"""Unit tests for Contains scorer."""

from promptlab.core.models import TestCase
from promptlab.core.scorers.contains import Contains


def test_contains_all_success() -> None:
    """Verify all targets found yields score 1.0 and passed True."""
    scorer = Contains()
    case = TestCase(
        id="c-1",
        input="List colors",
        scorer="contains",
        scorer_config={"targets": ["red", "blue", "green"], "mode": "all"},
    )
    result = scorer.score(case, "The colors chosen are red, blue, and green.")
    assert result.score == 1.0
    assert result.passed is True


def test_contains_all_partial() -> None:
    """Verify partial match under 'all' mode yields proportional score."""
    scorer = Contains()
    case = TestCase(
        id="c-2",
        input="List colors",
        scorer="contains",
        scorer_config={"targets": ["red", "blue", "green", "yellow"], "mode": "all"},
    )
    result = scorer.score(case, "I found red and blue.")
    assert result.score == 0.5
    assert result.passed is False
    assert "yellow" in result.metadata["missing"]


def test_contains_any_success() -> None:
    """Verify single target match under 'any' mode yields score 1.0."""
    scorer = Contains()
    case = TestCase(
        id="c-3",
        input="Identify status",
        scorer="contains",
        scorer_config={"targets": ["success", "completed", "ok"], "mode": "any"},
    )
    result = scorer.score(case, "Operation completed without errors.")
    assert result.score == 1.0
    assert result.passed is True


def test_contains_any_failure() -> None:
    """Verify zero target match under 'any' mode yields score 0.0."""
    scorer = Contains()
    case = TestCase(
        id="c-4",
        input="Identify status",
        scorer="contains",
        scorer_config={"targets": ["success", "completed"], "mode": "any"},
    )
    result = scorer.score(case, "An unexpected error occurred.")
    assert result.score == 0.0
    assert result.passed is False
