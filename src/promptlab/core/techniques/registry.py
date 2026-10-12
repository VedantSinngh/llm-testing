"""Registry for dynamic registration and lookup of prompt techniques.

This module provides the central registry for prompt strategies.
Using the Registry pattern with a `@register` decorator, new prompt techniques
can be introduced without altering existing execution pipelines.
"""

from collections.abc import Callable
from typing import Any

from promptlab.core.techniques.base import PromptTechnique
from promptlab.core.techniques.chain_of_thought import ChainOfThought
from promptlab.core.techniques.few_shot import FewShot
from promptlab.core.techniques.structured_output import StructuredOutput
from promptlab.core.techniques.zero_shot import ZeroShot
from promptlab.exceptions import TechniqueNotFoundError


# Design Pattern: Registry pattern enabling Open/Closed expansion of prompt engineering strategies.
class TechniqueRegistry:
    """Central registry and lookup for prompt engineering techniques."""

    _registry: dict[str, type[PromptTechnique]] = {}

    @classmethod
    def register(
        cls, name: str
    ) -> Callable[[type[PromptTechnique]], type[PromptTechnique]]:
        """Decorator to register a PromptTechnique subclass under a unique name."""

        def decorator(technique_cls: type[PromptTechnique]) -> type[PromptTechnique]:
            cls.register_technique(name, technique_cls)
            return technique_cls

        return decorator

    @classmethod
    def register_technique(
        cls, name: str, technique_cls: type[PromptTechnique]
    ) -> None:
        """Register a PromptTechnique subclass directly."""
        cls._registry[name.lower()] = technique_cls

    @classmethod
    def get(cls, name: str) -> PromptTechnique:
        """Retrieve an instance of the requested PromptTechnique by name.

        Args:
            name: Identifier of prompt technique (e.g. 'zero_shot', 'chain_of_thought').

        Returns:
            Instantiated PromptTechnique strategy.

        Raises:
            TechniqueNotFoundError: If technique is not registered.
        """
        lookup = name.lower()
        if lookup not in cls._registry:
            raise TechniqueNotFoundError(name)
        return cls._registry[lookup]()

    @classmethod
    def list_techniques(cls) -> list[str]:
        """Return sorted list of all registered technique names."""
        return sorted(list(cls._registry.keys()))


# Register built-in standard prompt techniques
TechniqueRegistry.register_technique("zero_shot", ZeroShot)
TechniqueRegistry.register_technique("few_shot", FewShot)
TechniqueRegistry.register_technique("chain_of_thought", ChainOfThought)
TechniqueRegistry.register_technique("structured_output", StructuredOutput)
