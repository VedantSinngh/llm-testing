"""Application configuration using Pydantic Settings.

This module provides strongly-typed configuration loaded from environment variables
and `.env` files. Using Pydantic Settings ensures validation at startup, eliminating
silent misconfigurations, and exposes a clean singleton pattern for dependency injection.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global runtime configuration for PromptLab.

    Attributes:
        groq_api_key: API key for hosted Groq inference (free tier open-source models).
        default_model: Default LLM model identifier for evaluations.
        max_concurrency: Maximum concurrent requests executed by TestRunner.
        database_url: SQLAlchemy async connection string.
        log_level: Application logging level.
        judge_model: Model used for LLM-as-a-Judge evaluations.
        api_key: Optional backend authorization key for the X-API-Key header.
        demo_mode: When True, uses MockProvider to run without external API keys.
        max_prompt_length: Input limit to prevent payload abuse.
        max_cases_per_suite: Suite size limit for rate and memory safety.
        request_timeout_seconds: Timeout per provider request in seconds.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    groq_api_key: str | None = Field(
        default=None,
        description="Groq API key for hosted model inference",
    )
    default_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Default model for runs and playground",
    )
    max_concurrency: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Semaphore limit for concurrent evaluation calls",
    )
    database_url: str = Field(
        default="sqlite+aiosqlite:///./promptlab.db",
        description="SQLAlchemy async database connection URL",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Log verbosity level",
    )
    judge_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Model identifier for LLM-as-a-judge scoring",
    )
    api_key: str | None = Field(
        default=None,
        description="Optional backend secret key for endpoint authentication",
    )
    demo_mode: bool = Field(
        default=False,
        description="If True, runs with MockProvider without hitting external APIs",
    )
    max_prompt_length: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Maximum allowed prompt character length",
    )
    max_cases_per_suite: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum test cases per single evaluation suite",
    )
    request_timeout_seconds: float = Field(
        default=60.0,
        gt=0.0,
        le=300.0,
        description="Timeout per LLM request in seconds",
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        """Ensure log level strings are uppercase."""
        return value.upper() if isinstance(value, str) else value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings.

    Using LRU cache prevents reloading and re-validating environment variables
    on every dependency resolution.
    """
    return Settings()
