"""Unit tests for StructuredOutput prompt technique and repair formatting."""

from promptlab.core.techniques.structured_output import StructuredOutput


def test_structured_output_application() -> None:
    """Verify StructuredOutput embeds JSON schema into prompt instruction."""
    technique = StructuredOutput()
    schema = {
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
    }
    sys_add, user_prompt = technique.apply("Summarize this article", {"schema": schema})

    assert sys_add is not None
    assert "JSON schema" in sys_add
    assert '"summary"' in sys_add
    assert "complying with the specified schema" in user_prompt


def test_structured_output_format_repair_prompt() -> None:
    """Verify format_repair_prompt formats targeted correction message."""
    malformed = "{'name': 'invalid single quotes'}"
    error_msg = "Expecting property name enclosed in double quotes"
    repair_prompt = StructuredOutput.format_repair_prompt(malformed, error_msg)

    assert "Previous malformed response" in repair_prompt
    assert error_msg in repair_prompt
    assert malformed in repair_prompt
