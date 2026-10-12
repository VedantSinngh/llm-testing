"""JSON Schema evaluation scorer using jsonschema.

This module validates that model output is valid JSON and conforms strictly
to a specified JSON Schema specification (Draft 7 / 2020-12).
"""

import json
import re
from typing import Any

import jsonschema
from jsonschema.exceptions import SchemaError, ValidationError as JsonSchemaValidationError

from promptlab.core.models import ScoreResult, TestCase
from promptlab.core.scorers.base import BaseScorer


# Design Pattern: Template Method concrete subclass for structural JSON Schema validation.
class JsonSchema(BaseScorer):
    """Scorer validating output against a formal JSON Schema."""

    name: str = "json_schema"

    def _strip_markdown_fence(self, text: str) -> str:
        """Strip surrounding markdown code fences."""
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            return fence_match.group(1).strip()
        return text.strip()

    def _evaluate(self, case: TestCase, output: str) -> ScoreResult:
        """Parse JSON and validate compliance with target schema."""
        schema: dict[str, Any] | None = case.scorer_config.get("schema")
        if not schema or not isinstance(schema, dict):
            return ScoreResult(
                score=0.0,
                passed=False,
                reason="Configuration error: 'schema' dictionary is required in scorer_config.",
            )

        cleaned = self._strip_markdown_fence(output)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as err:
            return ScoreResult(
                score=0.0,
                passed=False,
                reason=f"Failed to parse JSON: {err.msg}.",
                metadata={"error": str(err)},
            )

        try:
            jsonschema.validate(instance=parsed, schema=schema)
            return ScoreResult(
                score=1.0,
                passed=True,
                reason="JSON strictly satisfies schema specification.",
            )
        except JsonSchemaValidationError as val_err:
            return ScoreResult(
                score=0.0,
                passed=False,
                reason=f"Schema validation error at '{val_err.json_path}': {val_err.message}",
                metadata={"path": val_err.json_path, "message": val_err.message},
            )
        except SchemaError as schema_err:
            return ScoreResult(
                score=0.0,
                passed=False,
                reason=f"Invalid JSON Schema definition provided: {schema_err.message}",
            )
