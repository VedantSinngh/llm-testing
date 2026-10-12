"""Regular expression evaluation scorer.

This module validates that model output conforms to a specified regular expression
pattern, useful for structured formats (e.g., dates, IDs, codes).
"""

import re

from promptlab.core.models import ScoreResult, TestCase
from promptlab.core.scorers.base import BaseScorer


# Design Pattern: Template Method concrete subclass for regex pattern validation.
class RegexMatch(BaseScorer):
    """Scorer evaluating pattern adherence using regular expressions."""

    name: str = "regex_match"

    def _evaluate(self, case: TestCase, output: str) -> ScoreResult:
        """Evaluate preprocessed output against configured regex pattern."""
        pattern_str = case.scorer_config.get("pattern") or case.expected
        if not pattern_str:
            return ScoreResult(
                score=1.0,
                passed=True,
                reason="No regex pattern specified; trivial pass.",
            )

        flags = 0
        if case.scorer_config.get("ignore_case", False):
            flags |= re.IGNORECASE
        if case.scorer_config.get("multiline", False):
            flags |= re.MULTILINE

        try:
            compiled = re.compile(pattern_str, flags)
        except re.error as err:
            return ScoreResult(
                score=0.0,
                passed=False,
                reason=f"Invalid regex pattern syntax: {err}",
                metadata={"pattern": pattern_str, "error": str(err)},
            )

        match = compiled.search(output)
        if match:
            return ScoreResult(
                score=1.0,
                passed=True,
                reason=f"Matched regex pattern '{pattern_str}'.",
                metadata={"matched_text": match.group(0)},
            )

        return ScoreResult(
            score=0.0,
            passed=False,
            reason=f"Output did not match pattern '{pattern_str}'.",
            metadata={"pattern": pattern_str},
        )
