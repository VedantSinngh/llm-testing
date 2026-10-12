"""Deterministic Mock LLM Provider for unit testing and offline demo execution.

This module provides a lightweight, deterministic implementation of `LLMProvider`.
It enables testing the entire evaluation lifecycle without external API keys,
network round-trips, or API usage costs. It also powers PromptLab's zero-credential
demo mode and allows injection of simulated faults to test retry logic.
"""

import asyncio
import time
from typing import Any

from promptlab.core.models import LLMRequest, LLMResponse
from promptlab.core.providers.base import LLMProvider
from promptlab.exceptions import ProviderError


# Design Pattern: Mock Object pattern for deterministic testing and zero-credential demo execution.
class MockProvider(LLMProvider):
    """Deterministic LLM Provider producing reproducible outputs without network calls."""

    name: str = "mock"

    def __init__(
        self,
        canned_responses: dict[str, str] | None = None,
        default_response: str | None = None,
        simulated_latency_ms: float = 5.0,
    ) -> None:
        """Initialize MockProvider with optional canned responses and latency simulation."""
        self._canned_responses = canned_responses or {}
        self._default_response = default_response
        self._simulated_latency_ms = simulated_latency_ms
        self._failure_count: int = 0
        self._failure_error: Exception | None = None

    def simulate_failure(self, count: int, error: Exception | None = None) -> None:
        """Configure mock to fail the next `count` calls with `error`."""
        self._failure_count = count
        self._failure_error = error or ProviderError("Simulated mock provider failure")

    def set_canned_response(self, keyword: str, response: str) -> None:
        """Register a specific canned response triggered when keyword appears in prompt."""
        self._canned_responses[keyword.lower()] = response

    def _determine_text(self, prompt: str, model: str) -> str:
        """Generate response text matching keyword heuristics or defaults."""
        lower_prompt = prompt.lower()
        for keyword, response in self._canned_responses.items():
            if keyword in lower_prompt:
                return response

        if "sentiment" in lower_prompt:
            return '{"sentiment": "positive", "confidence": 0.98}'
        if "sql" in lower_prompt or "select" in lower_prompt:
            return "SELECT id, name, email FROM users WHERE active = 1;"
        if "json" in lower_prompt:
            return '{"status": "ok", "items": ["mock_item_1", "mock_item_2"]}'

        if self._default_response is not None:
            return self._default_response

        preview = prompt[:30].strip()
        return f"Mock output from [{model}] responding to: {preview}"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Execute mock completion, enforcing simulated errors and latency."""
        if self._failure_count > 0:
            self._failure_count -= 1
            error = self._failure_error or ProviderError("Simulated mock failure")
            raise error

        start_time = time.perf_counter()
        if self._simulated_latency_ms > 0:
            await asyncio.sleep(self._simulated_latency_ms / 1000.0)

        text = self._determine_text(request.prompt, request.model)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        prompt_tokens = max(1, len(request.prompt.split()))
        completion_tokens = max(1, len(text.split()))

        return LLMResponse(
            text=text,
            model=request.model,
            latency_ms=round(latency_ms, 2),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            raw_finish_reason="stop",
        )

    async def list_models(self) -> list[str]:
        """Return available mock model identifiers."""
        return [
            "mock-llama-3.3-70b",
            "mock-qwen-2.5-72b",
            "mock-mistral-large",
            "mock-gemma-2-9b",
        ]
