"""Structured Output prompt engineering technique.

This module forces the language model to generate strict JSON complying with
a specified JSON Schema. It also provides a repair prompt formatter to guide
models in self-correcting malformed or schema-invalid JSON outputs.
"""

import json
from typing import Any

from promptlab.core.techniques.base import PromptTechnique


# Design Pattern: Strategy implementation for schema-constrained structured output.
class StructuredOutput(PromptTechnique):
    """Structured output technique constraining completions to valid JSON schemas."""

    name: str = "structured_output"

    def apply(
        self, case_input: str, config: dict[str, Any]
    ) -> tuple[str | None, str]:
        """Inject JSON schema constraints into the system and user prompts."""
        schema = config.get("schema")
        schema_repr = (
            json.dumps(schema, indent=2)
            if isinstance(schema, dict)
            else str(schema or "{}")
        )

        system_addition = (
            "You MUST output ONLY valid JSON adhering strictly to the JSON schema below.\n"
            "Do NOT include any explanatory text, markdown code blocks, or commentary.\n"
            f"Schema:\n{schema_repr}"
        )
        user_prompt = (
            f"{case_input}\n\n"
            "Respond strictly in valid JSON complying with the specified schema."
        )
        return (system_addition, user_prompt)

    @staticmethod
    def format_repair_prompt(malformed_output: str, error_msg: str) -> str:
        """Construct a targeted correction prompt to repair invalid JSON.

        Args:
            malformed_output: The previous generation that failed validation.
            error_msg: The syntax or schema validation error message.

        Returns:
            Repair prompt instructing the LLM to fix the invalid payload.
        """
        return (
            "Your previous JSON response was invalid.\n"
            f"Error details: {error_msg}\n"
            "Previous malformed response:\n"
            f"{malformed_output}\n\n"
            "Please fix the error and output ONLY the valid JSON:"
        )
