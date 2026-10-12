"""Unit tests for GroqProvider adapter, error handling, and retry mechanics."""

from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest
from groq import (
    APIConnectionError,
    APIStatusError,
    RateLimitError as GroqRateLimitError,
)

from promptlab.core.models import GenerationParams, LLMRequest
from promptlab.core.providers.groq_provider import GroqProvider
from promptlab.exceptions import ConfigurationError, ProviderError, RateLimitError


def create_fake_completion(
    content: str = "Test output",
    model: str = "llama-3.3-70b-versatile",
    prompt_tokens: int = 12,
    completion_tokens: int = 20,
    finish_reason: str = "stop",
) -> MagicMock:
    """Helper to manufacture a mock Groq ChatCompletion structure."""
    choice = MagicMock()
    choice.message.content = content
    choice.finish_reason = finish_reason

    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens

    completion = MagicMock()
    completion.choices = [choice]
    completion.usage = usage
    completion.model = model
    return completion


def create_api_error(status_code: int, message: str) -> APIStatusError:
    """Helper to manufacture an APIStatusError with dummy HTTP response."""
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(status_code=status_code, request=request)
    if status_code == 429:
        return GroqRateLimitError(message, response=response, body=None)
    return APIStatusError(message, response=response, body=None)


def test_missing_api_key_raises_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify GroqProvider raises ConfigurationError if no API key is available."""
    monkeypatch.setenv("GROQ_API_KEY", "")
    with pytest.raises(ConfigurationError):
        GroqProvider(api_key=None, client=None)


@pytest.mark.asyncio
async def test_groq_generate_success() -> None:
    """Verify standard successful generation parsing and latency measurement."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=create_fake_completion(content="Explainable AI is vital.")
    )

    provider = GroqProvider(client=mock_client, base_backoff_seconds=0.01)
    request = LLMRequest(
        model="llama-3.3-70b-versatile",
        prompt="Explain XAI",
        system_prompt="You are a helpful assistant.",
        params=GenerationParams(temperature=0.5, max_tokens=150, seed=123),
    )

    response = await provider.generate(request)

    assert response.text == "Explainable AI is vital."
    assert response.model == "llama-3.3-70b-versatile"
    assert response.prompt_tokens == 12
    assert response.completion_tokens == 20
    assert response.raw_finish_reason == "stop"
    assert response.latency_ms >= 0.0

    # Validate client call arguments
    mock_client.chat.completions.create.assert_awaited_once()
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["model"] == "llama-3.3-70b-versatile"
    assert kwargs["messages"] == [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain XAI"},
    ]
    assert kwargs["temperature"] == 0.5
    assert kwargs["max_tokens"] == 150
    assert kwargs["seed"] == 123


@pytest.mark.asyncio
async def test_groq_retry_on_transient_rate_limit() -> None:
    """Verify that a transient 429 RateLimitError triggers backoff and retry succeeds."""
    mock_client = MagicMock()
    rate_limit_err = create_api_error(429, "Rate limit reached")
    success_completion = create_fake_completion(content="Recovered after retry.")

    mock_client.chat.completions.create = AsyncMock(
        side_effect=[rate_limit_err, success_completion]
    )

    provider = GroqProvider(
        client=mock_client,
        max_retries=2,
        base_backoff_seconds=0.01,
    )
    request = LLMRequest(model="llama-3.3-70b-versatile", prompt="Retry test")

    response = await provider.generate(request)
    assert response.text == "Recovered after retry."
    assert mock_client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_groq_rate_limit_exhausted() -> None:
    """Verify that exhausting retries on 429 raises domain RateLimitError."""
    mock_client = MagicMock()
    rate_limit_err = create_api_error(429, "Rate limit reached continuously")
    mock_client.chat.completions.create = AsyncMock(side_effect=rate_limit_err)

    provider = GroqProvider(
        client=mock_client,
        max_retries=2,
        base_backoff_seconds=0.01,
    )
    request = LLMRequest(model="llama-3.3-70b-versatile", prompt="Failing test")

    with pytest.raises(RateLimitError):
        await provider.generate(request)

    assert mock_client.chat.completions.create.await_count == 3  # initial + 2 retries


@pytest.mark.asyncio
async def test_groq_non_transient_error_fails_immediately() -> None:
    """Verify 400 Bad Request is not retried and raises ProviderError immediately."""
    mock_client = MagicMock()
    bad_request_err = create_api_error(400, "Invalid parameter combination")
    mock_client.chat.completions.create = AsyncMock(side_effect=bad_request_err)

    provider = GroqProvider(
        client=mock_client,
        max_retries=3,
        base_backoff_seconds=0.01,
    )
    request = LLMRequest(model="llama-3.3-70b-versatile", prompt="Invalid test")

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate(request)

    assert exc_info.value.status_code == 502
    assert exc_info.value.details.get("status_code") == 400
    assert mock_client.chat.completions.create.await_count == 1


@pytest.mark.asyncio
async def test_groq_list_models() -> None:
    """Verify list_models extracts and sorts IDs from client models list."""
    mock_client = MagicMock()
    m1 = MagicMock(id="llama-3.3-70b-versatile")
    m2 = MagicMock(id="gemma2-9b-it")
    mock_client.models.list = AsyncMock(return_value=MagicMock(data=[m1, m2]))

    provider = GroqProvider(client=mock_client)
    models = await provider.list_models()

    assert models == ["gemma2-9b-it", "llama-3.3-70b-versatile"]


@pytest.mark.asyncio
async def test_groq_list_models_failure() -> None:
    """Verify list_models maps API exceptions to ProviderError."""
    mock_client = MagicMock()
    req = httpx.Request("GET", "https://api.groq.com/openai/v1/models")
    mock_client.models.list = AsyncMock(
        side_effect=APIConnectionError(message="Network down", request=req)
    )

    provider = GroqProvider(client=mock_client)
    with pytest.raises(ProviderError):
        await provider.list_models()
