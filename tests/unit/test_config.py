"""Unit tests for configuration loading and validation."""

import pytest
from pydantic import ValidationError

from promptlab.config import Settings, get_settings


def test_default_settings() -> None:
    """Verify default configuration attributes are appropriately set."""
    settings = Settings()
    assert settings.default_model == "llama-3.3-70b-versatile"
    assert settings.max_concurrency == 5
    assert settings.database_url == "sqlite+aiosqlite:///./promptlab.db"
    assert settings.log_level == "INFO"
    assert settings.demo_mode is False
    assert settings.max_prompt_length == 10000
    assert settings.max_cases_per_suite == 100
    assert settings.request_timeout_seconds == 60.0


def test_custom_settings_override() -> None:
    """Verify custom values override defaults."""
    settings = Settings(
        groq_api_key="gsk_custom_test_key_12345",
        default_model="qwen-2.5-72b",
        max_concurrency=10,
        demo_mode=True,
    )
    assert settings.groq_api_key == "gsk_custom_test_key_12345"
    assert settings.default_model == "qwen-2.5-72b"
    assert settings.max_concurrency == 10
    assert settings.demo_mode is True


def test_log_level_normalization() -> None:
    """Verify lower-case log levels are normalized to upper-case."""
    settings = Settings(log_level="debug")  # type: ignore[arg-type]
    assert settings.log_level == "DEBUG"


def test_max_concurrency_validation() -> None:
    """Verify invalid max_concurrency raises validation error."""
    with pytest.raises(ValidationError):
        Settings(max_concurrency=0)

    with pytest.raises(ValidationError):
        Settings(max_concurrency=100)


def test_max_prompt_length_validation() -> None:
    """Verify prompt length limits are enforced."""
    with pytest.raises(ValidationError):
        Settings(max_prompt_length=10)


def test_request_timeout_validation() -> None:
    """Verify timeout must be positive and within bounds."""
    with pytest.raises(ValidationError):
        Settings(request_timeout_seconds=0.0)

    with pytest.raises(ValidationError):
        Settings(request_timeout_seconds=500.0)


def test_get_settings_caching() -> None:
    """Verify get_settings returns the same cached instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
