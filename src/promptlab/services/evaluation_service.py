"""Evaluation Service orchestrating test execution and persistence.

This module implements the Facade pattern. It coordinates provider factories,
the test runner, and repositories to deliver a unified interface for creating
suites, executing runs, and persisting outcomes.
"""

from promptlab.config import Settings, get_settings
from promptlab.core.models import GenerationParams, RunResult, TestSuite
from promptlab.core.providers.base import LLMProvider
from promptlab.core.providers.factory import ProviderFactory
from promptlab.core.runner import TestRunner
from promptlab.db.repositories import RunRepository, SuiteRepository
from promptlab.exceptions import ResourceNotFoundError


# Design Pattern: Facade pattern orchestrating test runner, repositories, providers, and persistence.
class EvaluationService:
    """Facade orchestrating evaluation suite execution, provider resolution, and storage."""

    def __init__(
        self,
        suite_repo: SuiteRepository,
        run_repo: RunRepository,
        provider: LLMProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize EvaluationService with required repositories and dependencies."""
        self._suite_repo = suite_repo
        self._run_repo = run_repo
        self._provider = provider
        self._settings = settings or get_settings()

    def _resolve_provider(self, provider_name: str | None = None) -> LLMProvider:
        """Resolve LLMProvider using injected instance, factory, or demo mode configuration."""
        if self._provider is not None:
            return self._provider

        if self._settings.demo_mode:
            return ProviderFactory.create("mock")

        target_provider = provider_name or "groq"
        return ProviderFactory.create(target_provider)

    async def create_suite(self, suite: TestSuite) -> str:
        """Persist a new test suite and return its generated ID."""
        return await self._suite_repo.save(suite)

    async def get_suite(self, suite_id: str) -> tuple[str, TestSuite]:
        """Retrieve test suite by ID or raise ResourceNotFoundError."""
        result = await self._suite_repo.get_by_id(suite_id)
        if not result:
            raise ResourceNotFoundError("TestSuite", suite_id)
        return result

    async def list_suites(
        self, offset: int = 0, limit: int = 50
    ) -> tuple[list[tuple[str, TestSuite]], int]:
        """List persisted suites with pagination."""
        return await self._suite_repo.list(offset=offset, limit=limit)

    async def delete_suite(self, suite_id: str) -> bool:
        """Delete test suite by ID."""
        deleted = await self._suite_repo.delete(suite_id)
        if not deleted:
            raise ResourceNotFoundError("TestSuite", suite_id)
        return True

    async def execute_run(
        self,
        suite_id_or_object: str | TestSuite,
        model: str,
        params: GenerationParams | None = None,
        provider_name: str | None = None,
    ) -> RunResult:
        """Execute a full test suite evaluation on a designated model and persist results."""
        if isinstance(suite_id_or_object, str):
            suite_id, suite = await self.get_suite(suite_id_or_object)
        else:
            suite = suite_id_or_object
            suite_id = None

        provider = self._resolve_provider(provider_name)
        runner = TestRunner(provider=provider, settings=self._settings)

        run_result = await runner.run_suite(suite, model=model, params=params)
        await self._run_repo.save(run_result, suite_id=suite_id)
        return run_result

    async def execute_matrix(
        self,
        suite_id_or_object: str | TestSuite,
        models: list[str],
        params_list: list[GenerationParams] | None = None,
        provider_name: str | None = None,
    ) -> list[RunResult]:
        """Execute multiple models and parameter sweep configurations."""
        if isinstance(suite_id_or_object, str):
            suite_id, suite = await self.get_suite(suite_id_or_object)
        else:
            suite = suite_id_or_object
            suite_id = None

        provider = self._resolve_provider(provider_name)
        runner = TestRunner(provider=provider, settings=self._settings)

        runs = await runner.run_matrix(suite, models=models, param_sets=params_list)
        for r in runs:
            await self._run_repo.save(r, suite_id=suite_id)
        return runs

    async def get_run(self, run_id: str) -> RunResult:
        """Retrieve evaluation run result by ID or raise ResourceNotFoundError."""
        run = await self._run_repo.get_by_id(run_id)
        if not run:
            raise ResourceNotFoundError("RunResult", run_id)
        return run

    async def list_runs(
        self,
        offset: int = 0,
        limit: int = 50,
        suite_name: str | None = None,
        model: str | None = None,
    ) -> tuple[list[RunResult], int]:
        """List historical evaluation runs with optional filtering."""
        return await self._run_repo.list(
            offset=offset, limit=limit, suite_name=suite_name, model=model
        )
