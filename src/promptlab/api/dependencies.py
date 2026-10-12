"""FastAPI Dependency Injection providers for database, repositories, and services.

This module implements the Dependency Injection pattern (IoC) using FastAPI's
`Depends` mechanism. It ensures that routes receive fully constructed repositories
and services while keeping database session lifecycles strictly managed.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from promptlab.config import Settings, get_settings
from promptlab.db.base import get_session_factory
from promptlab.db.repositories import (
    RunRepository,
    SafetyRepository,
    SuiteRepository,
)
from promptlab.services.comparison_service import ComparisonService
from promptlab.services.evaluation_service import EvaluationService
from promptlab.services.safety_service import SafetyService


# Design Pattern: Dependency Injection providing scoped AsyncSession per request.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session committed on success or rolled back on error."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_suite_repo(session: AsyncSession = Depends(get_db)) -> SuiteRepository:
    """Provide a SuiteRepository bound to the current request session."""
    return SuiteRepository(session)


def get_run_repo(session: AsyncSession = Depends(get_db)) -> RunRepository:
    """Provide a RunRepository bound to the current request session."""
    return RunRepository(session)


def get_safety_repo(session: AsyncSession = Depends(get_db)) -> SafetyRepository:
    """Provide a SafetyRepository bound to the current request session."""
    return SafetyRepository(session)


def get_evaluation_service(
    suite_repo: SuiteRepository = Depends(get_suite_repo),
    run_repo: RunRepository = Depends(get_run_repo),
    settings: Settings = Depends(get_settings),
) -> EvaluationService:
    """Provide configured EvaluationService facade instance."""
    return EvaluationService(
        suite_repo=suite_repo,
        run_repo=run_repo,
        settings=settings,
    )


def get_comparison_service(
    run_repo: RunRepository = Depends(get_run_repo),
) -> ComparisonService:
    """Provide ComparisonService instance."""
    return ComparisonService(run_repo=run_repo)


def get_safety_service(
    safety_repo: SafetyRepository = Depends(get_safety_repo),
    settings: Settings = Depends(get_settings),
) -> SafetyService:
    """Provide configured SafetyService instance."""
    return SafetyService(
        safety_repo=safety_repo,
        settings=settings,
    )
