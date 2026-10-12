"""Unit tests for the domain exception hierarchy."""

import pytest

from promptlab.exceptions import (
    AuthenticationError,
    ConfigurationError,
    PromptLabError,
    ProviderError,
    ProviderNotFoundError,
    RateLimitError,
    ResourceNotFoundError,
    ScorerNotFoundError,
    SecurityError,
    TechniqueNotFoundError,
    ValidationError,
)


def test_base_promptlab_error() -> None:
    """Verify base PromptLabError serialization and default attributes."""
    err = PromptLabError(
        message="A catastrophic failure occurred",
        error_code="INTERNAL_CRASH",
        status_code=500,
        details={"trace_id": "abc-123"},
    )
    assert err.message == "A catastrophic failure occurred"
    assert err.error_code == "INTERNAL_CRASH"
    assert err.status_code == 500
    assert err.details == {"trace_id": "abc-123"}

    serialized = err.to_dict()
    assert serialized == {
        "error_code": "INTERNAL_CRASH",
        "message": "A catastrophic failure occurred",
        "details": {"trace_id": "abc-123"},
    }


def test_base_promptlab_error_no_details() -> None:
    """Verify serialization omits details when none are supplied."""
    err = PromptLabError(message="Simple error")
    serialized = err.to_dict()
    assert serialized == {
        "error_code": "INTERNAL_ERROR",
        "message": "Simple error",
    }


def test_provider_error() -> None:
    """Verify ProviderError properties and status code."""
    err = ProviderError("Inference gateway unreachable", details={"provider": "groq"})
    assert err.status_code == 502
    assert err.error_code == "PROVIDER_ERROR"
    assert isinstance(err, PromptLabError)


def test_rate_limit_error() -> None:
    """Verify RateLimitError captures retry-after header details."""
    err = RateLimitError("Rate limit exceeded", retry_after=12.5)
    assert err.status_code == 429
    assert err.error_code == "RATE_LIMIT_ERROR"
    assert err.details == {"retry_after": 12.5}


def test_not_found_errors() -> None:
    """Verify NotFound error family generates informative messages."""
    p_err = ProviderNotFoundError("unknown_llm")
    assert p_err.status_code == 404
    assert p_err.error_code == "PROVIDER_NOT_FOUND"
    assert "unknown_llm" in p_err.message

    s_err = ScorerNotFoundError("bleu_score")
    assert s_err.status_code == 404
    assert s_err.error_code == "SCORER_NOT_FOUND"

    t_err = TechniqueNotFoundError("tree_of_thought")
    assert t_err.status_code == 404
    assert t_err.error_code == "TECHNIQUE_NOT_FOUND"

    r_err = ResourceNotFoundError("TestSuite", "suite-999")
    assert r_err.status_code == 404
    assert r_err.error_code == "RESOURCE_NOT_FOUND"
    assert "TestSuite with ID 'suite-999' was not found" in r_err.message


def test_validation_and_security_errors() -> None:
    """Verify ValidationError and SecurityError statuses."""
    v_err = ValidationError("Prompt cannot be empty")
    assert v_err.status_code == 422
    assert v_err.error_code == "VALIDATION_ERROR"

    sec_err = SecurityError("DROP TABLE detected in SQL test")
    assert sec_err.status_code == 400
    assert sec_err.error_code == "SECURITY_ERROR"

    auth_err = AuthenticationError()
    assert auth_err.status_code == 401
    assert auth_err.error_code == "AUTHENTICATION_ERROR"

    config_err = ConfigurationError("Missing GROQ_API_KEY")
    assert config_err.status_code == 500
    assert config_err.error_code == "CONFIGURATION_ERROR"


def test_exception_polymorphism() -> None:
    """Verify any specific error can be caught as PromptLabError."""
    with pytest.raises(PromptLabError) as exc_info:
        raise SecurityError("Unauthorized action")
    assert exc_info.value.status_code == 400
