"""Abstract Base Class for LLM inference providers.

This module establishes the core contract that all LLM provider adapters must implement.
Adhering to the Interface Segregation and Dependency Inversion principles (SOLID),
the evaluation runner and API routes depend solely on this abstraction rather than
concrete vendor SDKs.
"""

from abc import ABC, abstractmethod

from promptlab.core.models import LLMRequest, LLMResponse


# Design Pattern: Abstract Base Class defining the contract for all LLM inference providers.
class LLMProvider(ABC):
    """Abstract interface defining required capabilities for any LLM provider adapter."""

    name: str

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Send a prompt request to the LLM and return a standardized response.

        Args:
            request: Prompt, system prompt, target model, and generation parameters.

        Returns:
            Standardized LLMResponse including generated text, latency, and token metrics.

        Raises:
            ProviderError: When the underlying inference API encounters a fatal failure.
            RateLimitError: When rate quotas are exhausted and retries have failed.
        """
        pass

    @abstractmethod
    async def list_models(self) -> list[str]:
        """Retrieve available model identifiers supported by this provider.

        Returns:
            List of model ID strings (e.g., ['llama-3.3-70b-versatile', 'qwen-2.5-72b']).

        Raises:
            ProviderError: If the models catalog cannot be fetched.
        """
        pass
