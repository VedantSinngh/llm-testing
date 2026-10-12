"""Unit tests for structured JSON logging and security masking."""

import json
import logging

from promptlab.logging_config import (
    JSONLogFormatter,
    configure_logging,
    get_request_id,
    mask_sensitive_value,
    set_request_id,
)


def test_request_id_context() -> None:
    """Verify request ID is properly tracked across context calls."""
    assert get_request_id() == ""
    set_request_id("req-uuid-456")
    assert get_request_id() == "req-uuid-456"
    set_request_id("")
    assert get_request_id() == ""


def test_mask_sensitive_values() -> None:
    """Verify secrets are redacted from output strings."""
    # Test Groq key
    raw_groq = "Loaded key: gsk_abcdef1234567890xyz"
    assert "gsk_abcdef1234567890xyz" not in mask_sensitive_value(raw_groq)
    assert "[REDACTED]" in mask_sensitive_value(raw_groq)

    # Test OpenAI-style key
    raw_openai = "Call failed with sk-1234567890abcdef123456"
    assert "sk-1234567890abcdef123456" not in mask_sensitive_value(raw_openai)
    assert "[REDACTED]" in mask_sensitive_value(raw_openai)

    # Test AWS Key
    raw_aws = "Credentials AKIAIOSFODNN7EXAMPLE loaded"
    assert "AKIAIOSFODNN7EXAMPLE" not in mask_sensitive_value(raw_aws)
    assert "[REDACTED]" in mask_sensitive_value(raw_aws)

    # Non-sensitive message unchanged
    clean_msg = "Evaluation run completed in 120ms."
    assert mask_sensitive_value(clean_msg) == clean_msg


def test_json_log_formatter_structure() -> None:
    """Verify JSONLogFormatter outputs valid structured JSON."""
    formatter = JSONLogFormatter()
    record = logging.LogRecord(
        name="promptlab.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg="Execution started with prompt %s",
        args=("Hello LLM",),
        exc_info=None,
    )

    set_request_id("req-test-999")
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["level"] == "INFO"
    assert data["logger"] == "promptlab.test"
    assert data["message"] == "Execution started with prompt Hello LLM"
    assert data["request_id"] == "req-test-999"
    assert "timestamp" in data
    assert data["line"] == 42


def test_json_log_formatter_masks_secrets() -> None:
    """Verify JSONLogFormatter masks secrets inside log messages."""
    formatter = JSONLogFormatter()
    record = logging.LogRecord(
        name="promptlab.provider",
        level=logging.ERROR,
        pathname=__file__,
        lineno=100,
        msg="Authentication failed for key gsk_secret_1234567890123456",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert "gsk_secret_1234567890123456" not in data["message"]
    assert "[REDACTED]" in data["message"]


def test_configure_logging() -> None:
    """Verify root logger configuration applies cleanly."""
    configure_logging("DEBUG")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0].formatter, JSONLogFormatter)
