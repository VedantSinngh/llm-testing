"""SQLAlchemy 2.0 Typed ORM Models.

This module maps PromptLab domain entities to relational database tables:
- `SuiteModel` (`suites`): Test suite definitions and cases.
- `RunModel` (`runs`): Executed test runs with aggregated metrics.
- `CaseResultModel` (`case_results`): Granular per-case scoring outcomes.
- `SafetyReportModel` (`safety_reports`): Vulnerability and PII audit logs.
"""

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from promptlab.db.base import Base


class SuiteModel(Base):
    """Stores reusable test suites and their constituent test cases."""

    __tablename__ = "suites"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    technique: Mapped[str] = mapped_column(String(64), default="zero_shot", nullable=False)
    technique_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    cases: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    runs: Mapped[list["RunModel"]] = relationship(
        "RunModel", back_populates="suite", cascade="all, delete-orphan"
    )


class RunModel(Base):
    """Stores aggregated execution outcomes for a test suite run."""

    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    suite_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("suites.id", ondelete="SET NULL"), nullable=True
    )
    suite_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    technique: Mapped[str] = mapped_column(String(64), nullable=False)
    pass_rate: Mapped[float] = mapped_column(Float, nullable=False)
    avg_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )

    # Relationships
    suite: Mapped[SuiteModel | None] = relationship("SuiteModel", back_populates="runs")
    case_results: Mapped[list["CaseResultModel"]] = relationship(
        "CaseResultModel", back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_runs_suite_created", "suite_name", "created_at"),
    )


class CaseResultModel(Base):
    """Stores granular evaluation result for an individual test case in a run."""

    __tablename__ = "case_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    case_id: Mapped[str] = mapped_column(String(128), nullable=False)
    output_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    finish_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    run: Mapped[RunModel] = relationship("RunModel", back_populates="case_results")


class SafetyReportModel(Base):
    """Stores prompt injection vulnerability scans and PII audit reports."""

    __tablename__ = "safety_reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    injection_results: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    pii_findings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
