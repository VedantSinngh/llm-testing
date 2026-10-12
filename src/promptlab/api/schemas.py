"""Data Transfer Objects (DTOs) and API request/response schemas.

This module defines Pydantic schemas for the FastAPI layer, isolating external
HTTP payloads from internal domain entities.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from promptlab.core.models import (
    GenerationParams,
    RunResult,
    TestCase,
    TestSuite,
)


class HealthResponse(BaseModel):
    """Health status and active environment configuration."""

    status: str = Field(default="ok", description="Application operational status.")
    demo_mode: bool = Field(
        ..., description="Whether system is running in zero-credential demo mode."
    )
    active_provider: str = Field(..., description="Configured inference provider.")
    timestamp: datetime = Field(..., description="Server timestamp.")


class ModelsResponse(BaseModel):
    """Catalog of supported model IDs for a provider."""

    provider: str = Field(..., description="Provider identifier.")
    models: list[str] = Field(..., description="List of available model IDs.")


class SuiteCreateRequest(BaseModel):
    """Payload for registering a new evaluation suite."""

    name: str = Field(..., min_length=1, description="Unique test suite name.")
    description: str = Field(default="", description="Suite purpose description.")
    system_prompt: str | None = Field(default=None, description="Shared system instruction.")
    technique: str = Field(default="zero_shot", description="Prompting strategy.")
    technique_config: dict[str, Any] = Field(
        default_factory=dict, description="Technique configuration."
    )
    cases: list[TestCase] = Field(..., min_length=1, description="Test cases to evaluate.")

    def to_test_suite(self) -> TestSuite:
        """Convert DTO to core domain TestSuite entity."""
        return TestSuite(
            name=self.name,
            description=self.description,
            system_prompt=self.system_prompt,
            technique=self.technique,
            technique_config=self.technique_config,
            cases=self.cases,
        )


class SuiteResponse(BaseModel):
    """Returned response containing registered suite details."""

    id: str = Field(..., description="Unique suite UUID.")
    suite: TestSuite = Field(..., description="Persisted suite structure.")


class SuiteListResponse(BaseModel):
    """Paginated list of evaluation suites."""

    items: list[SuiteResponse] = Field(..., description="Returned suite objects.")
    total: int = Field(..., ge=0, description="Total matching suite count.")
    offset: int = Field(..., ge=0, description="Query offset applied.")
    limit: int = Field(..., ge=1, description="Query limit applied.")


class RunExecuteRequest(BaseModel):
    """Payload to trigger evaluation on a suite or inline definition."""

    suite_id: str | None = Field(default=None, description="UUID of existing suite.")
    suite: TestSuite | None = Field(default=None, description="Inline suite definition.")
    model: str = Field(..., min_length=1, description="Target model identifier.")
    params: GenerationParams | None = Field(default=None, description="Optional hyperparameters.")
    provider: str | None = Field(default=None, description="Optional provider override.")

    @model_validator(mode="after")
    def validate_suite_source(self) -> "RunExecuteRequest":
        """Ensure either suite_id or inline suite is provided."""
        if not self.suite_id and not self.suite:
            raise ValueError("Either suite_id or inline suite must be provided.")
        return self


class RunListResponse(BaseModel):
    """Paginated list of historical evaluation runs."""

    items: list[RunResult] = Field(..., description="Returned run results.")
    total: int = Field(..., ge=0, description="Total matching run count.")
    offset: int = Field(..., ge=0, description="Query offset applied.")
    limit: int = Field(..., ge=1, description="Query limit applied.")


class CompareRequest(BaseModel):
    """Payload requesting side-by-side run comparisons."""

    run_ids: list[str] = Field(..., min_length=2, description="At least two run UUIDs to compare.")


class CompareResponse(BaseModel):
    """Side-by-side comparison matrix and leaderboard."""

    run_count: int = Field(..., ge=2, description="Number of evaluated runs compared.")
    summaries: list[dict[str, Any]] = Field(..., description="Metric summary per run.")
    case_matrix: list[dict[str, Any]] = Field(..., description="Per-case side-by-side matrix.")
    best_performing_model: str = Field(..., description="Highest pass-rate model.")
    fastest_model: str = Field(..., description="Lowest average-latency model.")


class InjectionTestRequest(BaseModel):
    """Payload for running adversarial injection attack vectors."""

    model: str = Field(..., min_length=1, description="Target model to audit.")
    canary: str | None = Field(default=None, description="Custom canary token string.")
    provider: str | None = Field(default=None, description="Optional provider override.")


class ScanTextRequest(BaseModel):
    """Payload for scanning text for PII and secrets."""

    text: str = Field(..., min_length=1, description="Payload string to inspect.")


class ScanTextResponse(BaseModel):
    """Outcome of safety scanning and PII sanitization."""

    risk_level: str = Field(..., description="Risk assessment: low, medium, or high.")
    passed: bool = Field(..., description="Whether content is deemed safe to process.")
    pii_findings: list[dict[str, Any]] = Field(..., description="Detected PII entity occurrences.")
    redacted_text: str = Field(..., description="Sanitized payload with secrets masked.")


class SafetyReportListResponse(BaseModel):
    """Paginated list of historical safety audits."""

    items: list[dict[str, Any]] = Field(..., description="List of safety audit reports.")
    total: int = Field(..., ge=0, description="Total safety reports count.")
    offset: int = Field(..., ge=0, description="Query offset applied.")
    limit: int = Field(..., ge=1, description="Query limit applied.")


class ErrorResponse(BaseModel):
    """Standardized error response payload."""

    error_code: str = Field(..., description="Machine-readable error identifier.")
    message: str = Field(..., description="Human-readable error explanation.")
    request_id: str = Field(default="", description="Correlated trace request ID.")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Supplementary contextual details."
    )
