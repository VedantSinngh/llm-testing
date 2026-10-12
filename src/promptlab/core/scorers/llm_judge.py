"""LLM-as-a-Judge evaluation scorer.

This module uses an independent evaluator language model to assess candidate outputs
against a qualitative rubric.

BIASES AND LIMITATIONS DOCUMENTATION:
1. Positional Bias: LLM judges tend to favor options presented earlier in the context window.
2. Verbosity Bias: Models disproportionately award higher scores to wordier, formatting-heavy
   responses regardless of factual conciseness or accuracy.
3. Self-Enhancement Bias: When evaluating outputs, models frequently rate completions generated
   by their own family (e.g. Llama evaluating Llama) higher than rival model architectures.
4. Scale Compression: LLM judges exhibit central-tendency bias, clustering scores between
   0.7 and 0.9 while rarely utilizing the full 0.0 to 1.0 distribution.
5. Stochastic Drift: Variations in sampling temperature can alter grading rubrics.
   Always use temperature=0.0 or low temperatures for judge evaluations.
"""

import json
import re
from typing import Any

from promptlab.config import get_settings
from promptlab.core.models import GenerationParams, LLMRequest, ScoreResult, TestCase
from promptlab.core.providers.base import LLMProvider
from promptlab.core.providers.factory import ProviderFactory
from promptlab.core.scorers.base import BaseScorer


# Design Pattern: Template Method concrete subclass with asynchronous LLM evaluation.
class LLMJudge(BaseScorer):
    """Evaluates qualitative response criteria using an independent judge LLM."""

    name: str = "llm_judge"

    def __init__(
        self,
        judge_provider: LLMProvider | None = None,
        judge_model: str | None = None,
    ) -> None:
        """Initialize LLMJudge with designated provider and model."""
        self._provider = judge_provider
        self._judge_model = judge_model or get_settings().judge_model

    def _get_provider(self) -> LLMProvider:
        """Resolve judge provider instance lazily."""
        if self._provider is not None:
            return self._provider
        # Default to groq provider unless in demo mode
        settings = get_settings()
        provider_name = "mock" if settings.demo_mode else "groq"
        return ProviderFactory.create(provider_name)

    def _build_judge_prompt(self, case: TestCase, output: str) -> str:
        """Construct evaluation rubric prompt for the judge model."""
        rubric = case.scorer_config.get(
            "rubric",
            "Rate accuracy, completeness, and adherence to instructions on a 0.0 to 1.0 scale.",
        )
        expected = case.expected or "N/A"

        return (
            "You are an impartial, expert evaluation judge assessing an AI completion.\n\n"
            f"User Prompt:\n{case.input}\n\n"
            f"Expected Reference:\n{expected}\n\n"
            f"Candidate Output:\n{output}\n\n"
            f"Evaluation Rubric:\n{rubric}\n\n"
            "Evaluate strictly based on the rubric. Respond ONLY with valid JSON in this schema:\n"
            '{"score": <float between 0.0 and 1.0>, "reason": "<concise justification>"}'
        )

    def _parse_judge_response(self, text: str) -> ScoreResult:
        """Parse structured score and rationale from judge LLM response."""
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        clean_text = fence_match.group(1).strip() if fence_match else text.strip()

        try:
            data = json.loads(clean_text)
            raw_score = float(data.get("score", 0.0))
            reason = str(data.get("reason", "No reason provided."))
            clamped_score = max(0.0, min(1.0, raw_score))
            passed = clamped_score >= 0.7  # standard passing threshold for judge evaluations
            return ScoreResult(
                score=clamped_score,
                passed=passed,
                reason=reason,
                metadata={"judge_model": self._judge_model},
            )
        except (json.JSONDecodeError, ValueError) as err:
            return ScoreResult(
                score=0.0,
                passed=False,
                reason=f"Failed to parse LLM Judge output as JSON: {err}. Raw output: {text[:100]}",
                metadata={"raw_output": text},
            )

    async def _evaluate_async(self, case: TestCase, output: str) -> ScoreResult:
        """Asynchronously call judge LLM to evaluate the candidate output."""
        provider = self._get_provider()
        prompt = self._build_judge_prompt(case, output)

        request = LLMRequest(
            model=self._judge_model,
            prompt=prompt,
            system_prompt="You are a strict, objective evaluation judge. Output only JSON.",
            params=GenerationParams(temperature=0.0, max_tokens=500),
        )

        response = await provider.generate(request)
        return self._parse_judge_response(response.text)

    def _evaluate(self, case: TestCase, output: str) -> ScoreResult:
        """Synchronous placeholder: instructs callers to use async evaluation."""
        return ScoreResult(
            score=0.0,
            passed=False,
            reason="LLMJudge requires asynchronous execution via score_async().",
        )
