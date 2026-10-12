"""Pytest configuration and shared fixtures for unit and integration testing.

This module provides deterministic fixture factories used across test suites,
avoiding repetitive setup code in individual tests.
"""

from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from promptlab.config import Settings
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
from promptlab.logging_config import set_request_id


@pytest.fixture(autouse=True)
def reset_logging_context() -> Generator[None, None, None]:
    """Ensure each test runs with a clean request_id context."""
    set_request_id("")
    yield
    set_request_id("")


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing non-production test settings."""
    return Settings(
        groq_api_key="test-dummy-groq-key",
        default_model="llama-3.3-70b-versatile",
        max_concurrency=2,
        database_url="sqlite+aiosqlite:///:memory:",
        log_level="DEBUG",
        judge_model="llama-3.3-70b-versatile",
        demo_mode=True,
    )


@pytest.fixture
def sample_params() -> GenerationParams:
    """Fixture providing standard generation parameters."""
    return GenerationParams(
        temperature=0.2,
        top_p=0.9,
        max_tokens=256,
        seed=42,
    )


@pytest.fixture
def sample_request(sample_params: GenerationParams) -> LLMRequest:
    """Fixture providing a valid LLM request."""
    return LLMRequest(
        model="llama-3.3-70b-versatile",
        prompt="Explain dependency injection in 2 sentences.",
        system_prompt="You are an expert software engineer.",
        params=sample_params,
    )


@pytest.fixture
def sample_response() -> LLMResponse:
    """Fixture providing a standard LLM response."""
    return LLMResponse(
        text="Dependency injection passes dependencies to objects rather than creating them internally.",
        model="llama-3.3-70b-versatile",
        latency_ms=145.2,
        prompt_tokens=25,
        completion_tokens=18,
        raw_finish_reason="stop",
    )


@pytest.fixture
def sample_score_result() -> ScoreResult:
    """Fixture providing a successful score result."""
    return ScoreResult(
        score=1.0,
        passed=True,
        reason="Output matches reference specification perfectly.",
        metadata={"similarity": 1.0},
    )


@pytest.fixture
def sample_test_case() -> TestCase:
    """Fixture providing a representative test case."""
    return TestCase(
        id="tc-001",
        input="What is 2 + 2?",
        expected="4",
        scorer="exact_match",
        scorer_config={"case_sensitive": False},
        tags=["math", "basic"],
    )


@pytest.fixture
def sample_test_suite(sample_test_case: TestCase) -> TestSuite:
    """Fixture providing a test suite containing test cases."""
    return TestSuite(
        name="arithmetic_suite",
        description="Basic arithmetic evaluation tests",
        system_prompt="Answer with only the calculated number.",
        technique="zero_shot",
        technique_config={},
        cases=[sample_test_case],
    )


@pytest.fixture
def sample_case_result(sample_response: LLMResponse) -> CaseResult:
    """Fixture providing an individual case evaluation result."""
    return CaseResult(
        case_id="tc-001",
        response=sample_response,
        score=1.0,
        passed=True,
        reason="Match verified.",
    )


@pytest.fixture
def sample_run_result(
    sample_params: GenerationParams, sample_case_result: CaseResult
) -> RunResult:
    """Fixture providing an aggregated run result."""
    return RunResult(
        run_id="run-test-uuid-1234",
        suite_name="arithmetic_suite",
        model="llama-3.3-70b-versatile",
        params=sample_params,
        technique="zero_shot",
        case_results=[sample_case_result],
        pass_rate=1.0,
        avg_latency_ms=145.2,
        total_tokens=43,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_safety_report() -> SafetyReport:
    """Fixture providing a benign safety report."""
    return SafetyReport(
        injection_results=[],
        pii_findings=[],
        risk_level="low",
        passed=True,
    )


@pytest.fixture
async def async_db_session() -> AsyncGenerator["AsyncSession", None]:
    """Provide an isolated, in-memory SQLite database session for integration tests."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from promptlab.db.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        yield session

    await engine.dispose()

