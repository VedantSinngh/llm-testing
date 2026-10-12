"""Provider Factory and Registry for extensible LLM inference engines.

This module implements the Factory and Registry design patterns.
It allows instantiating providers dynamically by string identifier, decoupling
evaluations and runners from specific provider implementations. New providers
(e.g., Anthropic, Ollama, OpenAI) can be added without modifying existing code,
fulfilling the Open/Closed Principle (SOLID).
"""

from collections.abc import Callable
from typing import Any

from promptlab.core.providers.base import LLMProvider
from promptlab.core.providers.groq_provider import GroqProvider
from promptlab.core.providers.mock_provider import MockProvider
from promptlab.exceptions import ProviderNotFoundError


# Design Pattern: Factory / Registry pattern enabling Open/Closed addition of LLM providers.
class ProviderFactory:
    """Registry and factory for creating LLMProvider instances."""

    _registry: dict[str, type[LLMProvider]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type[LLMProvider]], type[LLMProvider]]:
        """Decorator to register a provider class under a specific identifier."""

        def decorator(provider_cls: type[LLMProvider]) -> type[LLMProvider]:
            cls.register_provider(name, provider_cls)
            return provider_cls

        return decorator

    @classmethod
    def register_provider(cls, name: str, provider_cls: type[LLMProvider]) -> None:
        """Register a provider class with the factory."""
        cls._registry[name.lower()] = provider_cls

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> LLMProvider:
        """Create and return an instance of the requested LLMProvider.

        Args:
            name: Case-insensitive name of provider (e.g., 'groq', 'mock').
            **kwargs: Keyword arguments passed to provider constructor.

        Returns:
            Configured LLMProvider instance.

        Raises:
            ProviderNotFoundError: If provider name has not been registered.
        """
        lookup = name.lower()
        if lookup not in cls._registry:
            raise ProviderNotFoundError(name)
        provider_cls = cls._registry[lookup]
        return provider_cls(**kwargs)

    @classmethod
    def list_providers(cls) -> list[str]:
        """Return list of all registered provider names."""
        return sorted(list(cls._registry.keys()))


# Register standard built-in providers
ProviderFactory.register_provider("mock", MockProvider)
ProviderFactory.register_provider("groq", GroqProvider)
