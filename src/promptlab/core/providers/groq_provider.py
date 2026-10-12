"""Groq hosted LLM provider adapter.

This module integrates the Groq high-speed hosted inference SDK for open-source models
(Llama 3, Qwen 2.5, Mistral, Gemma). It encapsulates asynchronous requests, tracks
real-time inference latency, translates vendor-specific errors into domain exceptions,
and implements exponential backoff with jitter for resilient retry handling.
"""

import asyncio
import logging
import random
import time
from typing import Any

from groq import (
    APIConnectionError,
    APIStatusError,
    AsyncGroq,
    RateLimitError as GroqRateLimitError,
)

from promptlab.config import get_settings
from promptlab.core.models import LLMRequest, LLMResponse
from promptlab.core.providers.base import LLMProvider
from promptlab.exceptions import ConfigurationError, ProviderError, RateLimitError

logger = logging.getLogger(__name__)


# Design Pattern: Adapter pattern wrapping the external Groq SDK into the unified LLMProvider interface.
class GroqProvider(LLMProvider):
    """Adapter for hosted open-source LLM inference via the Groq SDK."""

    name: str = "groq"

    def __init__(
        self,
        api_key: str | None = None,
        max_retries: int = 3,
        base_backoff_seconds: float = 0.5,
        timeout_seconds: float = 60.0,
        client: Any = None,
    ) -> None:
        """Initialize Groq provider with API credentials and retry configuration."""
        self._max_retries = max_retries
        self._base_backoff_seconds = base_backoff_seconds

        if client is not None:
            self._client = client
            return

        resolved_key = api_key or get_settings().groq_api_key
        if not resolved_key:
            raise ConfigurationError(
                "Groq API key is missing. Set GROQ_API_KEY or run in DEMO_MODE=true."
            )

        self._client = AsyncGroq(api_key=resolved_key, timeout=timeout_seconds)

    def _build_messages(self, request: LLMRequest) -> list[dict[str, str]]:
        """Construct chat messages payload according to OpenAI/Groq schema."""
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        return messages

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with full jitter to avoid thundering herds."""
        exponential = self._base_backoff_seconds * (2**attempt)
        jitter = random.uniform(0.05, 0.25)
        return float(round(exponential + jitter, 3))

    def _is_transient(self, exc: Exception) -> bool:
        """Check if an exception represents a transient failure eligible for retry."""
        if isinstance(exc, (GroqRateLimitError, APIConnectionError)):
            return True
        if isinstance(exc, APIStatusError) and exc.status_code in {429, 500, 502, 503, 504}:
            return True
        return False

    async def _execute_with_retry(self, request: LLMRequest, messages: list[dict[str, str]]) -> Any:
        """Execute chat completion with bounded exponential retry for transient errors."""
        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "temperature": request.params.temperature,
            "top_p": request.params.top_p,
            "max_tokens": request.params.max_tokens,
        }
        if request.params.seed is not None:
            kwargs["seed"] = request.params.seed

        for attempt in range(self._max_retries + 1):
            try:
                return await self._client.chat.completions.create(**kwargs)
            except Exception as exc:
                if attempt < self._max_retries and self._is_transient(exc):
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        "Groq transient error (%s). Retrying in %.2fs (attempt %d/%d)",
                        type(exc).__name__,
                        delay,
                        attempt + 1,
                        self._max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue

                if isinstance(exc, GroqRateLimitError) or (
                    isinstance(exc, APIStatusError) and exc.status_code == 429
                ):
                    raise RateLimitError(f"Groq rate limit exceeded: {exc}") from exc

                status_code = getattr(exc, "status_code", None)
                raise ProviderError(
                    f"Groq inference failed: {exc}",
                    details={"model": request.model, "status_code": status_code},
                ) from exc

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Execute inference request and return standardized LLMResponse with metrics."""
        messages = self._build_messages(request)
        start_time = time.perf_counter()

        completion = await self._execute_with_retry(request, messages)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        choice = completion.choices[0]
        usage = completion.usage

        return LLMResponse(
            text=choice.message.content or "",
            model=completion.model or request.model,
            latency_ms=round(latency_ms, 2),
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            raw_finish_reason=choice.finish_reason,
        )

    async def list_models(self) -> list[str]:
        """Fetch model identifiers available through Groq API."""
        try:
            response = await self._client.models.list()
            return sorted([m.id for m in response.data])
        except Exception as exc:
            raise ProviderError(f"Failed to list Groq models: {exc}") from exc
