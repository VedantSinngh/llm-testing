"""JSON Validity evaluation scorer.

This module verifies that the language model generated syntactically valid JSON,
automatically stripping markdown fences if present.
"""

import json
import re

from promptlab.core.models import ScoreResult, TestCase
from promptlab.core.scorers.base import BaseScorer


# Design Pattern: Template Method concrete subclass for syntax-level JSON validation.
class JsonValid(BaseScorer):
    """Scorer verifying that completion text parses as valid JSON."""

    name: str = "json_valid"

    def _strip_markdown_fence(self, text: str) -> str:
        """Strip surrounding markdown code fences (e.g. ```json ... ```)."""
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            return fence_match.group(1).strip()
        return text.strip()

    def _evaluate(self, case: TestCase, output: str) -> ScoreResult:
        """Attempt to parse preprocessed output as valid JSON."""
        cleaned = self._strip_markdown_fence(output)

        try:
            parsed = json.loads(cleaned)
            return ScoreResult(
                score=1.0,
                passed=True,
                reason="Successfully parsed valid JSON.",
                metadata={"parsed_type": type(parsed).__name__},
            )
        except json.JSONDecodeError as err:
            return ScoreResult(
                score=0.0,
                passed=False,
                reason=f"JSON syntax error: {err.msg} at line {err.lineno}, col {err.colno}.",
                metadata={"error": str(err), "position": err.pos},
            )
