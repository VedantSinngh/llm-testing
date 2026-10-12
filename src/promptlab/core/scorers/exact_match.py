"""Exact Match evaluation scorer.

This module evaluates whether model output exactly matches expected reference text,
with configurable sensitivity to letter casing and whitespace variations.
"""

import re

from promptlab.core.models import ScoreResult, TestCase
from promptlab.core.scorers.base import BaseScorer


# Design Pattern: Template Method concrete subclass for exact string matching.
class ExactMatch(BaseScorer):
    """Scorer evaluating exact equality against ground-truth expected string."""

    name: str = "exact_match"

    def _evaluate(self, case: TestCase, output: str) -> ScoreResult:
        """Compare preprocessed output with case expected string."""
        expected = case.expected or ""
        config = case.scorer_config

        case_sensitive = config.get("case_sensitive", True)
        ignore_whitespace = config.get("ignore_whitespace", True)

        actual_cmp = output
        expected_cmp = expected

        if not case_sensitive:
            actual_cmp = actual_cmp.lower()
            expected_cmp = expected_cmp.lower()

        if ignore_whitespace:
            actual_cmp = re.sub(r"\s+", " ", actual_cmp).strip()
            expected_cmp = re.sub(r"\s+", " ", expected_cmp).strip()

        matched = actual_cmp == expected_cmp
        if matched:
            return ScoreResult(
                score=1.0,
                passed=True,
                reason="Output exactly matches expected ground truth.",
            )

        return ScoreResult(
            score=0.0,
            passed=False,
            reason=f"Mismatch: expected '{expected_cmp}', received '{actual_cmp}'.",
            metadata={"expected": expected_cmp, "actual": actual_cmp},
        )
