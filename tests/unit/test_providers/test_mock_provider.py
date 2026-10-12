"""Unit tests for MockProvider implementation."""

import pytest

from promptlab.core.models import GenerationParams, LLMRequest
from promptlab.core.providers.mock_provider import MockProvider
from promptlab.exceptions import ProviderError


@pytest.mark.asyncio
async def test_mock_provider_basic_generation() -> None:
    """Verify MockProvider generates expected response structure."""
    provider = MockProvider(simulated_latency_ms=1.0)
    request = LLMRequest(
        model="mock-llama-3.3-70b",
        prompt="Tell me a joke about Python.",
        params=GenerationParams(),
    )

    response = await provider.generate(request)
    assert response.model == "mock-llama-3.3-70b"
    assert "mock-llama-3.3-70b" in response.text
    assert response.latency_ms >= 1.0
    assert response.prompt_tokens > 0
    assert response.completion_tokens > 0
    assert response.raw_finish_reason == "stop"


@pytest.mark.asyncio
async def test_mock_provider_canned_heuristics() -> None:
    """Verify MockProvider responds with specific outputs for prompt keywords."""
    provider = MockProvider(simulated_latency_ms=0.0)

    # Sentiment heuristic
    req_sentiment = LLMRequest(
        model="mock-model",
        prompt="Analyze sentiment of this review",
        params=GenerationParams(),
    )
    res_sentiment = await provider.generate(req_sentiment)
    assert "sentiment" in res_sentiment.text

    # SQL heuristic
    req_sql = LLMRequest(
        model="mock-model",
        prompt="Write a SQL query for users",
        params=GenerationParams(),
    )
    res_sql = await provider.generate(req_sql)
    assert "SELECT" in res_sql.text

    # JSON heuristic
    req_json = LLMRequest(
        model="mock-model",
        prompt="Output valid JSON with items",
        params=GenerationParams(),
    )
    res_json = await provider.generate(req_json)
    assert '{"status":' in res_json.text


@pytest.mark.asyncio
async def test_mock_provider_custom_canned_response() -> None:
    """Verify registration and lookup of custom canned responses."""
    provider = MockProvider(simulated_latency_ms=0.0)
    provider.set_canned_response("weather", "The weather is 22 degrees and sunny.")

    req = LLMRequest(
        model="mock-model",
        prompt="What is the weather today in Seattle?",
        params=GenerationParams(),
    )
    res = await provider.generate(req)
    assert res.text == "The weather is 22 degrees and sunny."


@pytest.mark.asyncio
async def test_mock_provider_failure_simulation() -> None:
    """Verify simulated failure injection and recovery on subsequent call."""
    provider = MockProvider(simulated_latency_ms=0.0)
    custom_err = ProviderError("Temporary cluster overload")
    provider.simulate_failure(count=1, error=custom_err)

    req = LLMRequest(
        model="mock-model",
        prompt="Test query",
        params=GenerationParams(),
    )

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate(req)
    assert "Temporary cluster overload" in str(exc_info.value)

    # Subsequent call should succeed normally
    second_res = await provider.generate(req)
    assert second_res.text is not None


@pytest.mark.asyncio
async def test_mock_provider_list_models() -> None:
    """Verify MockProvider returns list of supported mock models."""
    provider = MockProvider()
    models = await provider.list_models()
    assert isinstance(models, list)
    assert len(models) >= 4
    assert "mock-llama-3.3-70b" in models
