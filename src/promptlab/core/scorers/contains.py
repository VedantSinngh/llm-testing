"""Substring Contains evaluation scorer.

This module evaluates whether model output contains one or more required target
substrings, supporting both 'all' (conjunctive) and 'any' (disjunctive) modes.
"""

from typing import Literal

from promptlab.core.models import ScoreResult, TestCase
from promptlab.core.scorers.base import BaseScorer


# Design Pattern: Template Method concrete subclass for substring containment evaluation.
class Contains(BaseScorer):
    """Scorer checking presence of expected target substrings."""

    name: str = "contains"

    def _extract_targets(self, case: TestCase) -> list[str]:
        """Extract target strings from configuration or expected field."""
        targets = case.scorer_config.get("targets")
        if isinstance(targets, list):
            return [str(t) for t in targets if t]
        if case.expected:
            return [case.expected]
        return []

    def _evaluate(self, case: TestCase, output: str) -> ScoreResult:
        """Evaluate presence of target substrings in output."""
        targets = self._extract_targets(case)
        if not targets:
            return ScoreResult(
                score=1.0,
                passed=True,
                reason="No targets specified; trivial pass.",
            )

        config = case.scorer_config
        case_sensitive = config.get("case_sensitive", False)
        mode: Literal["all", "any"] = config.get("mode", "all")

        haystack = output if case_sensitive else output.lower()
        found: list[str] = []
        missing: list[str] = []

        for target in targets:
            needle = target if case_sensitive else target.lower()
            if needle in haystack:
                found.append(target)
            else:
                missing.append(target)

        if mode == "any":
            passed = len(found) > 0
            score = 1.0 if passed else 0.0
            reason = (
                f"Found {len(found)} matching target(s)."
                if passed
                else f"None of the required targets were found. Missing: {missing}"
            )
        else:  # mode == "all"
            score = len(found) / len(targets)
            passed = len(missing) == 0
            reason = (
                f"All {len(targets)} targets found."
                if passed
                else f"Missing {len(missing)} of {len(targets)} targets: {missing}"
            )

        return ScoreResult(
            score=score,
            passed=passed,
            reason=reason,
            metadata={"found": found, "missing": missing, "mode": mode},
        )
