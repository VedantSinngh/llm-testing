"""Abstract Base Scorer defining the Template Method pattern.

This module provides the foundation for all evaluation scorers in PromptLab.
Using the Template Method pattern, `BaseScorer` guarantees that every evaluation
follows an invariant lifecycle: input preprocessing, subclass evaluation,
and post-evaluation finalization (score clamping, metric normalization).
"""

from abc import ABC, abstractmethod

from promptlab.core.models import ScoreResult, TestCase


# Design Pattern: Template Method pattern enforcing preprocessing -> evaluate -> finalize lifecycle.
class BaseScorer(ABC):
    """Abstract base scorer defining uniform evaluation lifecycle."""

    name: str

    def _preprocess(self, output: str) -> str:
        """Strip surrounding whitespace by default. Subclasses can override."""
        return output.strip()

    def _finalize(self, result: ScoreResult) -> ScoreResult:
        """Clamp score strictly between 0.0 and 1.0 and normalize metrics."""
        clamped = max(0.0, min(1.0, float(result.score)))
        return ScoreResult(
            score=round(clamped, 4),
            passed=result.passed,
            reason=result.reason,
            metadata=result.metadata,
        )

    def score(self, case: TestCase, output: str) -> ScoreResult:
        """Template Method: Preprocess -> Evaluate -> Finalize.

        Args:
            case: The test case being evaluated.
            output: Raw text output from the language model.

        Returns:
            Finalized ScoreResult with bounded score and justification.
        """
        normalized = self._preprocess(output)
        result = self._evaluate(case, normalized)
        return self._finalize(result)

    async def score_async(self, case: TestCase, output: str) -> ScoreResult:
        """Asynchronous execution hook for scorers requiring network I/O (e.g. LLM Judge).

        Args:
            case: The test case being evaluated.
            output: Raw text output from the language model.

        Returns:
            Finalized ScoreResult with bounded score and justification.
        """
        normalized = self._preprocess(output)
        result = await self._evaluate_async(case, normalized)
        return self._finalize(result)

    @abstractmethod
    def _evaluate(self, case: TestCase, output: str) -> ScoreResult:
        """Subclass implementation of scoring logic."""
        pass

    async def _evaluate_async(self, case: TestCase, output: str) -> ScoreResult:
        """Async evaluation fallback defaulting to synchronous _evaluate."""
        return self._evaluate(case, output)
