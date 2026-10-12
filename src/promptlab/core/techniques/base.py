"""Abstract Base Class for prompt engineering strategies.

This module defines the Strategy pattern interface for prompt techniques.
Prompt techniques transform raw user inputs and configurations into specialized
prompts (e.g. injecting demonstrations, chain-of-thought instructions, or JSON schemas)
without coupling the test runner to any particular formulation algorithm.
"""

from abc import ABC, abstractmethod
from typing import Any


# Design Pattern: Strategy pattern allowing interchangeable prompt formulation algorithms.
class PromptTechnique(ABC):
    """Abstract strategy for formatting prompt inputs and system instructions."""

    name: str

    @abstractmethod
    def apply(
        self, case_input: str, config: dict[str, Any]
    ) -> tuple[str | None, str]:
        """Transform test case input and configuration into prompt components.

        Args:
            case_input: The raw query or prompt for the test case.
            config: Technique-specific configuration dictionary.

        Returns:
            A tuple of (system_prompt_addition, user_prompt).
            If no system prompt addition is required, returns None as first element.
        """
        pass
