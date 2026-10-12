"""Unit tests for ProviderFactory and provider registry."""

from unittest.mock import MagicMock
import pytest

from promptlab.core.models import LLMRequest, LLMResponse
from promptlab.core.providers.base import LLMProvider
from promptlab.core.providers.factory import ProviderFactory
from promptlab.core.providers.groq_provider import GroqProvider
from promptlab.core.providers.mock_provider import MockProvider
from promptlab.exceptions import ProviderNotFoundError


def test_create_built_in_mock_provider() -> None:
    """Verify factory instantiates MockProvider with default settings."""
    provider = ProviderFactory.create("mock")
    assert isinstance(provider, MockProvider)
    assert provider.name == "mock"


def test_create_case_insensitive() -> None:
    """Verify factory handles uppercase/mixed-case provider identifiers."""
    provider = ProviderFactory.create("MOCK")
    assert isinstance(provider, MockProvider)


def test_create_groq_provider() -> None:
    """Verify factory instantiates GroqProvider passing kwargs."""
    mock_client = MagicMock()
    provider = ProviderFactory.create("groq", client=mock_client)
    assert isinstance(provider, GroqProvider)
    assert provider.name == "groq"


def test_create_unregistered_provider_raises_error() -> None:
    """Verify factory raises ProviderNotFoundError for unknown provider string."""
    with pytest.raises(ProviderNotFoundError) as exc_info:
        ProviderFactory.create("non_existent_engine")
    assert exc_info.value.status_code == 404
    assert "non_existent_engine" in str(exc_info.value)


def test_register_custom_provider_open_closed() -> None:
    """Verify custom provider can be registered dynamically via decorator."""

    @ProviderFactory.register("custom_dummy")
    class DummyProvider(LLMProvider):
        name: str = "custom_dummy"

        async def generate(self, request: LLMRequest) -> LLMResponse:
            return LLMResponse(
                text="dummy",
                model=request.model,
                latency_ms=1.0,
            )

        async def list_models(self) -> list[str]:
            return ["dummy-v1"]

    # Verify provider is now listed and instantiable
    assert "custom_dummy" in ProviderFactory.list_providers()
    instance = ProviderFactory.create("custom_dummy")
    assert isinstance(instance, DummyProvider)
    assert instance.name == "custom_dummy"


def test_list_providers() -> None:
    """Verify list_providers includes built-in providers."""
    providers = ProviderFactory.list_providers()
    assert "mock" in providers
    assert "groq" in providers
