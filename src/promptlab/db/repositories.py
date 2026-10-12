"""Repository pattern implementations for database access.

This module encapsulates all persistence queries for test suites, runs, and safety reports.
Adhering to the Repository design pattern, higher-level services and API controllers
never write SQL queries or interact with raw database cursors directly.
"""

from typing import Any
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from promptlab.core.models import (
    CaseResult,
    GenerationParams,
    LLMResponse,
    RunResult,
    SafetyReport,
    TestCase,
    TestSuite,
)
from promptlab.db.orm_models import CaseResultModel, RunModel, SafetyReportModel, SuiteModel


# Design Pattern: Repository pattern abstracting database access behind dedicated domain interfaces.
class SuiteRepository:
    """Repository managing persistence and retrieval of TestSuite entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with active database session."""
        self._session = session

    async def save(self, suite: TestSuite, suite_id: str | None = None) -> str:
        """Persist a TestSuite entity. Updates existing record if ID matches."""
        target_id = suite_id or str(uuid.uuid4())
        existing = await self._session.get(SuiteModel, target_id)

        cases_dicts = [case.model_dump() for case in suite.cases]

        if existing:
            existing.name = suite.name
            existing.description = suite.description
            existing.system_prompt = suite.system_prompt
            existing.technique = suite.technique
            existing.technique_config = suite.technique_config
            existing.cases = cases_dicts
            return existing.id

        model = SuiteModel(
            id=target_id,
            name=suite.name,
            description=suite.description,
            system_prompt=suite.system_prompt,
            technique=suite.technique,
            technique_config=suite.technique_config,
            cases=cases_dicts,
        )
        self._session.add(model)
        await self._session.flush()
        return model.id

    async def get_by_id(self, suite_id: str) -> tuple[str, TestSuite] | None:
        """Retrieve a suite by its primary key ID."""
        model = await self._session.get(SuiteModel, suite_id)
        if not model:
            return None
        suite = TestSuite(
            name=model.name,
            description=model.description,
            system_prompt=model.system_prompt,
            technique=model.technique,
            technique_config=model.technique_config,
            cases=[TestCase(**c) for c in model.cases],
        )
        return (model.id, suite)

    async def get_by_name(self, name: str) -> tuple[str, TestSuite] | None:
        """Retrieve a suite by its unique name."""
        stmt = select(SuiteModel).where(SuiteModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        suite = TestSuite(
            name=model.name,
            description=model.description,
            system_prompt=model.system_prompt,
            technique=model.technique,
            technique_config=model.technique_config,
            cases=[TestCase(**c) for c in model.cases],
        )
        return (model.id, suite)

    async def list(
        self, offset: int = 0, limit: int = 50
    ) -> tuple[list[tuple[str, TestSuite]], int]:
        """List persisted suites with pagination and total count."""
        count_stmt = select(func.count(SuiteModel.id))
        total = (await self._session.execute(count_stmt)).scalar() or 0

        stmt = select(SuiteModel).order_by(SuiteModel.created_at.desc()).offset(offset).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()

        suites: list[tuple[str, TestSuite]] = []
        for m in models:
            suite = TestSuite(
                name=m.name,
                description=m.description,
                system_prompt=m.system_prompt,
                technique=m.technique,
                technique_config=m.technique_config,
                cases=[TestCase(**c) for c in m.cases],
            )
            suites.append((m.id, suite))
        return (suites, total)

    async def delete(self, suite_id: str) -> bool:
        """Delete a suite by its ID. Returns True if deleted."""
        model = await self._session.get(SuiteModel, suite_id)
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True


# Design Pattern: Repository pattern managing evaluation runs and granular case results.
class RunRepository:
    """Repository managing persistence and queries for evaluation RunResult entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with active database session."""
        self._session = session

    async def save(self, run: RunResult, suite_id: str | None = None) -> str:
        """Persist a RunResult along with all individual CaseResult child rows."""
        run_model = RunModel(
            id=run.run_id,
            suite_id=suite_id,
            suite_name=run.suite_name,
            model=run.model,
            params=run.params.model_dump(),
            technique=run.technique,
            pass_rate=run.pass_rate,
            avg_latency_ms=run.avg_latency_ms,
            total_tokens=run.total_tokens,
            created_at=run.created_at,
        )
        self._session.add(run_model)

        for cr in run.case_results:
            case_model = CaseResultModel(
                id=str(uuid.uuid4()),
                run_id=run.run_id,
                case_id=cr.case_id,
                output_text=cr.response.text,
                score=cr.score,
                passed=cr.passed,
                reason=cr.reason,
                error=cr.error,
                latency_ms=cr.response.latency_ms,
                prompt_tokens=cr.response.prompt_tokens,
                completion_tokens=cr.response.completion_tokens,
                finish_reason=cr.response.raw_finish_reason,
            )
            self._session.add(case_model)

        await self._session.flush()
        return run.run_id

    async def get_by_id(self, run_id: str) -> RunResult | None:
        """Retrieve a RunResult including all child case results."""
        stmt = (
            select(RunModel)
            .where(RunModel.id == run_id)
            .options(selectinload(RunModel.case_results))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None

        case_results: list[CaseResult] = []
        for cr in model.case_results:
            resp = LLMResponse(
                text=cr.output_text,
                model=model.model,
                latency_ms=cr.latency_ms,
                prompt_tokens=cr.prompt_tokens,
                completion_tokens=cr.completion_tokens,
                raw_finish_reason=cr.finish_reason,
            )
            case_results.append(
                CaseResult(
                    case_id=cr.case_id,
                    response=resp,
                    score=cr.score,
                    passed=cr.passed,
                    reason=cr.reason,
                    error=cr.error,
                )
            )

        return RunResult(
            run_id=model.id,
            suite_name=model.suite_name,
            model=model.model,
            params=GenerationParams(**model.params),
            technique=model.technique,
            case_results=case_results,
            pass_rate=model.pass_rate,
            avg_latency_ms=model.avg_latency_ms,
            total_tokens=model.total_tokens,
            created_at=model.created_at,
        )

    async def list(
        self,
        offset: int = 0,
        limit: int = 50,
        suite_name: str | None = None,
        model: str | None = None,
    ) -> tuple[list[RunResult], int]:
        """List runs with optional filtering and pagination."""
        query = select(RunModel).options(selectinload(RunModel.case_results))
        count_query = select(func.count(RunModel.id))

        if suite_name:
            query = query.where(RunModel.suite_name == suite_name)
            count_query = count_query.where(RunModel.suite_name == suite_name)
        if model:
            query = query.where(RunModel.model == model)
            count_query = count_query.where(RunModel.model == model)

        total = (await self._session.execute(count_query)).scalar() or 0

        stmt = query.order_by(RunModel.created_at.desc()).offset(offset).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()

        results: list[RunResult] = []
        for m in models:
            cases = [
                CaseResult(
                    case_id=c.case_id,
                    response=LLMResponse(
                        text=c.output_text,
                        model=m.model,
                        latency_ms=c.latency_ms,
                        prompt_tokens=c.prompt_tokens,
                        completion_tokens=c.completion_tokens,
                        raw_finish_reason=c.finish_reason,
                    ),
                    score=c.score,
                    passed=c.passed,
                    reason=c.reason,
                    error=c.error,
                )
                for c in m.case_results
            ]
            results.append(
                RunResult(
                    run_id=m.id,
                    suite_name=m.suite_name,
                    model=m.model,
                    params=GenerationParams(**m.params),
                    technique=m.technique,
                    case_results=cases,
                    pass_rate=m.pass_rate,
                    avg_latency_ms=m.avg_latency_ms,
                    total_tokens=m.total_tokens,
                    created_at=m.created_at,
                )
            )

        return (results, total)

    async def delete(self, run_id: str) -> bool:
        """Delete an execution run by ID."""
        model = await self._session.get(RunModel, run_id)
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True


# Design Pattern: Repository pattern managing safety assessments.
class SafetyRepository:
    """Repository managing storage of prompt injection audits and PII scans."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with active database session."""
        self._session = session

    async def save(self, report: SafetyReport, model: str) -> str:
        """Persist a SafetyReport entity."""
        report_id = str(uuid.uuid4())
        model_row = SafetyReportModel(
            id=report_id,
            model=model,
            risk_level=report.risk_level,
            passed=report.passed,
            injection_results=report.injection_results,
            pii_findings=report.pii_findings,
        )
        self._session.add(model_row)
        await self._session.flush()
        return report_id

    async def get_by_id(self, report_id: str) -> dict[str, Any] | None:
        """Retrieve a safety report by ID."""
        model = await self._session.get(SafetyReportModel, report_id)
        if not model:
            return None
        return {
            "id": model.id,
            "model": model.model,
            "risk_level": model.risk_level,
            "passed": model.passed,
            "injection_results": model.injection_results,
            "pii_findings": model.pii_findings,
            "created_at": model.created_at,
        }

    async def list(self, offset: int = 0, limit: int = 50) -> tuple[list[dict[str, Any]], int]:
        """List safety reports with pagination."""
        count_stmt = select(func.count(SafetyReportModel.id))
        total = (await self._session.execute(count_stmt)).scalar() or 0

        stmt = (
            select(SafetyReportModel)
            .order_by(SafetyReportModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        models = (await self._session.execute(stmt)).scalars().all()

        reports = [
            {
                "id": m.id,
                "model": m.model,
                "risk_level": m.risk_level,
                "passed": m.passed,
                "injection_results": m.injection_results,
                "pii_findings": m.pii_findings,
                "created_at": m.created_at,
            }
            for m in models
        ]
        return (reports, total)
