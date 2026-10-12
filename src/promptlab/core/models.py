"""Pydantic v2 domain models for PromptLab.

This module defines the core domain entities used across the evaluation engine.
These models represent the ubiquitous language of PromptLab: prompt configurations,
test cases, evaluation results, and safety findings. They are framework-agnostic
and enforce strict validation and type safety.
"""

from datetime import datetime, UTC
from typing import Any, Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field


class GenerationParams(BaseModel):
    """Hyperparameters controlling LLM text generation."""

    model_config = ConfigDict(frozen=True)

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature. Higher values yield more creative output.",
    )
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling probability threshold.",
    )
    max_tokens: int = Field(
        default=1024,
        ge=1,
        le=8192,
        description="Maximum tokens allowed in generation.",
    )
    seed: int | None = Field(
        default=None,
        description="Optional seed for deterministic sampling if supported by provider.",
    )


class LLMRequest(BaseModel):
    """Encapsulates a single prompt generation request to an LLM provider."""

    model_config = ConfigDict(frozen=True)

    model: str = Field(
        ...,
        min_length=1,
        description="Target model identifier (e.g., 'llama-3.3-70b-versatile').",
    )
    prompt: str = Field(
        ...,
        min_length=1,
        description="Primary user prompt string.",
    )
    system_prompt: str | None = Field(
        default=None,
        description="Optional system instruction providing behavior guidance.",
    )
    params: GenerationParams = Field(
        default_factory=GenerationParams,
        description="Generation hyperparameters.",
    )


class LLMResponse(BaseModel):
    """Standardized response returned by any LLM provider implementation."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(
        ...,
        description="Generated completion text.",
    )
    model: str = Field(
        ...,
        description="Identifier of model that produced the completion.",
    )
    latency_ms: float = Field(
        ...,
        ge=0.0,
        description="Round-trip inference latency in milliseconds.",
    )
    prompt_tokens: int = Field(
        default=0,
        ge=0,
        description="Number of tokens in prompt.",
    )
    completion_tokens: int = Field(
        default=0,
        ge=0,
        description="Number of tokens in generated completion.",
    )
    raw_finish_reason: str | None = Field(
        default=None,
        description="Provider-specific reason generation ended (e.g., 'stop', 'length').",
    )


class ScoreResult(BaseModel):
    """Result of scoring an LLM output against an evaluation rubric or ground truth."""

    model_config = ConfigDict(frozen=True)

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized evaluation score between 0.0 and 1.0.",
    )
    passed: bool = Field(
        ...,
        description="Indicates whether the score satisfied the success threshold.",
    )
    reason: str = Field(
        ...,
        description="Human-readable explanation or justification for the score.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Scorer-specific metrics or diagnostics (e.g. schema errors, row counts).",
    )


class TestCase(BaseModel):
    """Defines a single test scenario within an evaluation suite."""

    id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the test case (e.g., 'tc_001').",
    )
    input: str = Field(
        ...,
        min_length=1,
        description="User prompt or input query under test.",
    )
    expected: str | None = Field(
        default=None,
        description="Optional ground truth or reference output.",
    )
    scorer: str = Field(
        ...,
        min_length=1,
        description="Registered scorer name (e.g., 'exact_match', 'json_schema').",
    )
    scorer_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration parameters specific to chosen scorer.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization (e.g. ['regression', 'edge_case']).",
    )


class TestSuite(BaseModel):
    """Collection of test cases and shared prompt configuration."""

    name: str = Field(
        ...,
        min_length=1,
        description="Unique name of the evaluation test suite.",
    )
    description: str = Field(
        default="",
        description="Human-readable summary of suite objective.",
    )
    system_prompt: str | None = Field(
        default=None,
        description="System prompt applied to all cases in the suite.",
    )
    technique: str = Field(
        default="zero_shot",
        description="Prompt engineering technique name (e.g., 'chain_of_thought').",
    )
    technique_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration specific to prompt technique (e.g., few-shot examples).",
    )
    cases: list[TestCase] = Field(
        ...,
        min_length=1,
        description="List of test cases to evaluate.",
    )


class CaseResult(BaseModel):
    """Evaluation result for an individual test case."""

    case_id: str = Field(
        ...,
        description="Identifier of evaluated test case.",
    )
    response: LLMResponse = Field(
        ...,
        description="Raw output received from LLM provider.",
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized evaluation score between 0.0 and 1.0.",
    )
    passed: bool = Field(
        ...,
        description="Whether case passed evaluation threshold.",
    )
    reason: str = Field(
        ...,
        description="Explanation for the score or failure.",
    )
    error: str | None = Field(
        default=None,
        description="Error trace if execution failed during evaluation.",
    )


class RunResult(BaseModel):
    """Aggregated outcome of evaluating a TestSuite on a specific model and parameters."""

    run_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique execution run UUID.",
    )
    suite_name: str = Field(
        ...,
        description="Name of evaluated test suite.",
    )
    model: str = Field(
        ...,
        description="Model name that was evaluated.",
    )
    params: GenerationParams = Field(
        ...,
        description="Hyperparameters used during execution.",
    )
    technique: str = Field(
        ...,
        description="Prompt technique applied.",
    )
    case_results: list[CaseResult] = Field(
        default_factory=list,
        description="Per-case evaluation outcomes.",
    )
    pass_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Percentage of cases that passed (0.0 to 1.0).",
    )
    avg_latency_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Average latency across all cases in milliseconds.",
    )
    total_tokens: int = Field(
        default=0,
        ge=0,
        description="Total tokens consumed across all cases.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when run was executed.",
    )


class SafetyReport(BaseModel):
    """Comprehensive safety and vulnerability assessment report."""

    injection_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed results for prompt injection attack tests.",
    )
    pii_findings: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of detected PII entities and redacted previews.",
    )
    risk_level: Literal["low", "medium", "high"] = Field(
        default="low",
        description="Assessed risk classification based on safety findings.",
    )
    passed: bool = Field(
        default=True,
        description="True if risk level is low and no attack successfully breached.",
    )
