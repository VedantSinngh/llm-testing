"""Unit tests for RegexMatch scorer."""

from promptlab.core.models import TestCase
from promptlab.core.scorers.regex_match import RegexMatch


def test_regex_match_success() -> None:
    """Verify matching regex pattern yields score 1.0."""
    scorer = RegexMatch()
    case = TestCase(
        id="r-1",
        input="Generate ticket ID",
        scorer="regex_match",
        scorer_config={"pattern": r"TICKET-\d{4}"},
    )
    result = scorer.score(case, "Your reference is TICKET-9821.")
    assert result.score == 1.0
    assert result.passed is True
    assert result.metadata["matched_text"] == "TICKET-9821"


def test_regex_match_failure() -> None:
    """Verify non-matching output yields score 0.0."""
    scorer = RegexMatch()
    case = TestCase(
        id="r-2",
        input="Generate ticket ID",
        scorer="regex_match",
        scorer_config={"pattern": r"^TICKET-\d{4}$"},
    )
    result = scorer.score(case, "TICKET-ABCD")
    assert result.score == 0.0
    assert result.passed is False


def test_regex_invalid_pattern_handling() -> None:
    """Verify invalid regex syntax returns 0.0 without unhandled exception."""
    scorer = RegexMatch()
    case = TestCase(
        id="r-3",
        input="Test",
        scorer="regex_match",
        scorer_config={"pattern": "[unclosed-bracket"},
    )
    result = scorer.score(case, "sample text")
    assert result.score == 0.0
    assert result.passed is False
    assert "Invalid regex" in result.reason
