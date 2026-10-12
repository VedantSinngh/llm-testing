"""Unit tests for JsonValid scorer."""

from promptlab.core.models import TestCase
from promptlab.core.scorers.json_valid import JsonValid


def test_json_valid_plain() -> None:
    """Verify plain JSON string parses successfully."""
    scorer = JsonValid()
    case = TestCase(id="jv-1", input="Output json", scorer="json_valid")
    result = scorer.score(case, '{"name": "Alice", "age": 30}')
    assert result.score == 1.0
    assert result.passed is True


def test_json_valid_with_markdown_fences() -> None:
    """Verify markdown code fences are stripped before parsing."""
    scorer = JsonValid()
    case = TestCase(id="jv-2", input="Output json", scorer="json_valid")
    raw = '```json\n{\n  "items": [1, 2, 3]\n}\n```'
    result = scorer.score(case, raw)
    assert result.score == 1.0
    assert result.passed is True


def test_json_invalid_syntax() -> None:
    """Verify invalid JSON yields score 0.0 with syntax error explanation."""
    scorer = JsonValid()
    case = TestCase(id="jv-3", input="Output json", scorer="json_valid")
    result = scorer.score(case, '{"name": "Alice", "age": }')
    assert result.score == 0.0
    assert result.passed is False
    assert "JSON syntax error" in result.reason
