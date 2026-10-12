"""Structured JSON logging configuration for PromptLab.

This module provides production-grade structured logging with:
1. JSON output formatting for cloud observability platforms.
2. Context-bound request ID tracking across asynchronous tasks via ContextVar.
3. Automatic redaction of sensitive credentials (API keys, tokens) to prevent leaks.
"""

from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import re
from typing import Any

# Context variable to correlate log entries across asynchronous request lifecycles
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

# Regular expressions detecting common secret patterns for masking
SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(gsk_[A-Za-z0-9_]{16,})", re.IGNORECASE),
    re.compile(r"(sk-[A-Za-z0-9_-]{16,})", re.IGNORECASE),
    re.compile(r"(AKIA[0-9A-Z]{16})"),
    re.compile(r"(Bearer\s+)[A-Za-z0-9._\-]{16,}", re.IGNORECASE),
    re.compile(r"(api[_-]?key[\"'\s:=]+)([\w\-]{8,})", re.IGNORECASE),
]


def set_request_id(request_id: str) -> None:
    """Set the active request ID in the asynchronous context."""
    request_id_ctx.set(request_id)


def get_request_id() -> str:
    """Retrieve the active request ID from the asynchronous context."""
    return request_id_ctx.get()


def mask_sensitive_value(text: str) -> str:
    """Redact known credentials, tokens, and secret keys from text.

    Args:
        text: String content potentially containing sensitive keys.

    Returns:
        Sanitized string with identified secrets replaced by '[REDACTED]'.
    """
    sanitized = text
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(r"[REDACTED]", sanitized)
    return sanitized


class JSONLogFormatter(logging.Formatter):
    """Custom formatter rendering log records as serialized JSON dictionaries."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the specified record as a JSON string with redaction applied."""
        log_message = record.getMessage()
        masked_message = mask_sensitive_value(log_message)

        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": masked_message,
            "module": record.module,
            "line": record.lineno,
        }

        # Include request ID if bound to current async context
        active_req_id = get_request_id()
        if active_req_id:
            payload["request_id"] = active_req_id

        # Attach exception details if present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger with the structured JSON formatter.

    Args:
        level: Minimum log level string (e.g. 'DEBUG', 'INFO', 'WARNING').
    """
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Replace existing handlers to prevent duplicate formatting
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(JSONLogFormatter())
    root_logger.addHandler(handler)
