"""Scorer Registry for dynamic registration and lookup of evaluation scorers.

This module provides the central registry and factory for evaluation scorers.
Using the Registry pattern, custom scorers can be added via the `@register` decorator
without modifying existing runner or service logic.
"""

from collections.abc import Callable
from typing import Any

from promptlab.core.scorers.base import BaseScorer
from promptlab.core.scorers.contains import Contains
from promptlab.core.scorers.exact_match import ExactMatch
from promptlab.core.scorers.json_schema import JsonSchema
from promptlab.core.scorers.json_valid import JsonValid
from promptlab.core.scorers.llm_judge import LLMJudge
from promptlab.core.scorers.regex_match import RegexMatch
from promptlab.core.scorers.sql_result import SqlResult
from promptlab.exceptions import ScorerNotFoundError


# Design Pattern: Registry + Factory pattern enabling Open/Closed expansion of evaluation scorers.
class ScorerRegistry:
    """Central registry and lookup for all evaluation scorers."""

    _registry: dict[str, type[BaseScorer]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type[BaseScorer]], type[BaseScorer]]:
        """Decorator to register a BaseScorer subclass under a unique name."""

        def decorator(scorer_cls: type[BaseScorer]) -> type[BaseScorer]:
            cls.register_scorer(name, scorer_cls)
            return scorer_cls

        return decorator

    @classmethod
    def register_scorer(cls, name: str, scorer_cls: type[BaseScorer]) -> None:
        """Register a BaseScorer subclass directly."""
        cls._registry[name.lower()] = scorer_cls

    @classmethod
    def get(cls, name: str, **kwargs: Any) -> BaseScorer:
        """Instantiate and return requested scorer by identifier.

        Args:
            name: Scorer name (e.g., 'exact_match', 'sql_result').
            **kwargs: Configuration options passed to scorer constructor.

        Returns:
            Configured BaseScorer instance.

        Raises:
            ScorerNotFoundError: If scorer name is not registered.
        """
        lookup = name.lower()
        if lookup not in cls._registry:
            raise ScorerNotFoundError(name)
        return cls._registry[lookup](**kwargs)

    @classmethod
    def list_scorers(cls) -> list[str]:
        """Return sorted list of all registered scorer identifiers."""
        return sorted(list(cls._registry.keys()))


# Register standard built-in scorers
ScorerRegistry.register_scorer("exact_match", ExactMatch)
ScorerRegistry.register_scorer("contains", Contains)
ScorerRegistry.register_scorer("regex_match", RegexMatch)
ScorerRegistry.register_scorer("json_valid", JsonValid)
ScorerRegistry.register_scorer("json_schema", JsonSchema)
ScorerRegistry.register_scorer("sql_result", SqlResult)
ScorerRegistry.register_scorer("llm_judge", LLMJudge)
