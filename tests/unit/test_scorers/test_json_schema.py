"""Unit tests for JsonSchema scorer."""

from promptlab.core.models import TestCase
from promptlab.core.scorers.json_schema import JsonSchema


def test_json_schema_valid() -> None:
    """Verify output conforming to JSON Schema passes with score 1.0."""
    scorer = JsonSchema()
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "stars": {"type": "integer", "minimum": 1, "maximum": 5},
        },
        "required": ["title", "stars"],
    }
    case = TestCase(
        id="js-1",
        input="Review a book",
        scorer="json_schema",
        scorer_config={"schema": schema},
    )
    result = scorer.score(case, '{"title": "Dune", "stars": 5}')
    assert result.score == 1.0
    assert result.passed is True


def test_json_schema_missing_required() -> None:
    """Verify missing required property fails with schema error path."""
    scorer = JsonSchema()
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "stars": {"type": "integer"},
        },
        "required": ["title", "stars"],
    }
    case = TestCase(
        id="js-2",
        input="Review a book",
        scorer="json_schema",
        scorer_config={"schema": schema},
    )
    result = scorer.score(case, '{"title": "Dune"}')
    assert result.score == 0.0
    assert result.passed is False
    assert "stars" in result.reason


def test_json_schema_type_mismatch() -> None:
    """Verify type mismatch fails schema validation."""
    scorer = JsonSchema()
    schema = {
        "type": "object",
        "properties": {
            "stars": {"type": "integer"},
        },
        "required": ["stars"],
    }
    case = TestCase(
        id="js-3",
        input="Score",
        scorer="json_schema",
        scorer_config={"schema": schema},
    )
    result = scorer.score(case, '{"stars": "five"}')
    assert result.score == 0.0
    assert result.passed is False
