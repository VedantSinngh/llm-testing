"""Asynchronous Test Runner for LLM evaluation suites.

This module orchestrates concurrent evaluation runs across test cases, models,
and parameter configurations. Concurrency is strictly bounded by an asyncio Semaphore
to protect API rate limits and avoid socket exhaustion. Individual case errors are
captured gracefully, guaranteeing that a single case failure does not abort an entire run.
"""

import asyncio
from datetime import datetime, UTC
import logging

from promptlab.config import Settings, get_settings
from promptlab.core.models import (
    CaseResult,
    GenerationParams,
    LLMRequest,
    LLMResponse,
    RunResult,
    TestCase,
    TestSuite,
)
from promptlab.core.providers.base import LLMProvider
from promptlab.core.scorers.registry import ScorerRegistry
from promptlab.core.techniques.base import PromptTechnique
from promptlab.core.techniques.registry import TechniqueRegistry

logger = logging.getLogger(__name__)


class TestRunner:
    """Orchestrates concurrent execution and metric aggregation for evaluation suites."""

    def __init__(
        self,
        provider: LLMProvider,
        technique: PromptTechnique | str = "zero_shot",
        scorer_registry: ScorerRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize runner with inference provider, prompt strategy, and configuration."""
        self._provider = provider
        self._settings = settings or get_settings()
        self._scorer_registry = scorer_registry or ScorerRegistry()

        if isinstance(technique, str):
            self._technique = TechniqueRegistry.get(technique)
        else:
            self._technique = technique

    def _resolve_technique(self, technique_name: str) -> PromptTechnique:
        """Resolve technique instance dynamically."""
        return TechniqueRegistry.get(technique_name)

    def _combine_system_prompts(self, base_system: str | None, addition: str | None) -> str | None:
        """Merge suite system instructions with technique-specific guidance."""
        if base_system and addition:
            return f"{base_system}\n\n{addition}"
        return base_system or addition

    async def _evaluate_single_case(
        self,
        case: TestCase,
        suite: TestSuite,
        model: str,
        params: GenerationParams,
        semaphore: asyncio.Semaphore,
    ) -> CaseResult:
        """Execute and score an individual test case under semaphore concurrency control."""
        async with semaphore:
            technique = (
                self._resolve_technique(suite.technique)
                if suite.technique != self._technique.name
                else self._technique
            )

            sys_addition, user_prompt = technique.apply(case.input, suite.technique_config)
            combined_system = self._combine_system_prompts(suite.system_prompt, sys_addition)

            request = LLMRequest(
                model=model,
                prompt=user_prompt,
                system_prompt=combined_system,
                params=params,
            )

            try:
                response = await self._provider.generate(request)
                scorer = self._scorer_registry.get(case.scorer)
                score_res = await scorer.score_async(case, response.text)

                return CaseResult(
                    case_id=case.id,
                    response=response,
                    score=score_res.score,
                    passed=score_res.passed,
                    reason=score_res.reason,
                    error=None,
                )
            except Exception as exc:
                logger.error("Error evaluating test case '%s': %s", case.id, exc)
                fallback_response = LLMResponse(
                    text="",
                    model=model,
                    latency_ms=0.0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    raw_finish_reason="error",
                )
                return CaseResult(
                    case_id=case.id,
                    response=fallback_response,
                    score=0.0,
                    passed=False,
                    reason=f"Evaluation failed due to exception: {exc}",
                    error=str(exc),
                )

    async def run_suite(
        self,
        suite: TestSuite,
        model: str,
        params: GenerationParams | None = None,
    ) -> RunResult:
        """Execute all test cases in a suite concurrently and aggregate run metrics."""
        effective_params = params or GenerationParams()
        semaphore = asyncio.Semaphore(self._settings.max_concurrency)

        tasks = [
            self._evaluate_single_case(
                case=case,
                suite=suite,
                model=model,
                params=effective_params,
                semaphore=semaphore,
            )
            for case in suite.cases
        ]

        case_results: list[CaseResult] = await asyncio.gather(*tasks)

        total_cases = len(case_results)
        passed_count = sum(1 for cr in case_results if cr.passed)
        pass_rate = round(passed_count / total_cases, 4) if total_cases > 0 else 0.0

        total_latency = sum(cr.response.latency_ms for cr in case_results)
        avg_latency = round(total_latency / total_cases, 2) if total_cases > 0 else 0.0

        total_tokens = sum(
            cr.response.prompt_tokens + cr.response.completion_tokens for cr in case_results
        )

        return RunResult(
            suite_name=suite.name,
            model=model,
            params=effective_params,
            technique=suite.technique,
            case_results=case_results,
            pass_rate=pass_rate,
            avg_latency_ms=avg_latency,
            total_tokens=total_tokens,
            created_at=datetime.now(UTC),
        )

    async def run_matrix(
        self,
        suite: TestSuite,
        models: list[str],
        param_sets: list[GenerationParams] | None = None,
    ) -> list[RunResult]:
        """Execute a suite across multiple models and parameter configurations (sweeps)."""
        params_list = param_sets or [GenerationParams()]
        matrix_results: list[RunResult] = []

        for model in models:
            for params in params_list:
                result = await self.run_suite(suite, model, params)
                matrix_results.append(result)

        return matrix_results
