"""PromptLab Core Domain Package.

This package contains domain models, abstract base classes for providers,
prompt techniques, scorers, safety analyzers, and the test runner.
The core package is completely decoupled from FastAPI and can be used as a standalone library.
"""

from promptlab.core.models import (
    CaseResult,
    GenerationParams,
    LLMRequest,
    LLMResponse,
    RunResult,
    SafetyReport,
    ScoreResult,
    TestCase,
    TestSuite,
)
from promptlab.core.providers import (
    GroqProvider,
    LLMProvider,
    MockProvider,
    ProviderFactory,
)
from promptlab.core.scorers import (
    BaseScorer,
    Contains,
    ExactMatch,
    JsonSchema,
    JsonValid,
    LLMJudge,
    RegexMatch,
    ScorerRegistry,
    SqlResult,
)
from promptlab.core.runner import TestRunner
from promptlab.core.safety import Guardrail, InjectionSuite, PIIDetector
from promptlab.core.techniques import (
    ChainOfThought,
    FewShot,
    PromptTechnique,
    StructuredOutput,
    TechniqueRegistry,
    ZeroShot,
)

__all__ = [
    "GenerationParams",
    "LLMRequest",
    "LLMResponse",
    "ScoreResult",
    "TestCase",
    "TestSuite",
    "CaseResult",
    "RunResult",
    "SafetyReport",
    "LLMProvider",
    "GroqProvider",
    "MockProvider",
    "ProviderFactory",
    "PromptTechnique",
    "ZeroShot",
    "FewShot",
    "ChainOfThought",
    "StructuredOutput",
    "TechniqueRegistry",
    "BaseScorer",
    "ExactMatch",
    "Contains",
    "RegexMatch",
    "JsonValid",
    "JsonSchema",
    "SqlResult",
    "LLMJudge",
    "ScorerRegistry",
    "TestRunner",
    "Guardrail",
    "PIIDetector",
    "InjectionSuite",
]
