"""Unit tests for ExactMatch scorer."""

from promptlab.core.models import TestCase
from promptlab.core.scorers.exact_match import ExactMatch


def test_exact_match_success() -> None:
    """Verify exact match yields score 1.0 and passed True."""
    scorer = ExactMatch()
    case = TestCase(
        id="case-1",
        input="Say Hello",
        expected="Hello World",
        scorer="exact_match",
    )
    result = scorer.score(case, "Hello World")
    assert result.score == 1.0
    assert result.passed is True


def test_exact_match_case_sensitive() -> None:
    """Verify case sensitive mismatch yields score 0.0."""
    scorer = ExactMatch()
    case = TestCase(
        id="case-2",
        input="Say Hello",
        expected="Hello World",
        scorer="exact_match",
        scorer_config={"case_sensitive": True},
    )
    result = scorer.score(case, "hello world")
    assert result.score == 0.0
    assert result.passed is False


def test_exact_match_case_insensitive() -> None:
    """Verify case insensitive match yields score 1.0."""
    scorer = ExactMatch()
    case = TestCase(
        id="case-3",
        input="Say Hello",
        expected="Hello World",
        scorer="exact_match",
        scorer_config={"case_sensitive": False},
    )
    result = scorer.score(case, "hello world")
    assert result.score == 1.0
    assert result.passed is True


def test_exact_match_ignore_whitespace() -> None:
    """Verify collapsing multiple whitespaces and newlines."""
    scorer = ExactMatch()
    case = TestCase(
        id="case-4",
        input="Say Hello",
        expected="Hello World",
        scorer="exact_match",
        scorer_config={"ignore_whitespace": True},
    )
    result = scorer.score(case, "  Hello \n\t  World  ")
    assert result.score == 1.0
    assert result.passed is True
