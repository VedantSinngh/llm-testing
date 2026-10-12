"""Domain exception hierarchy for PromptLab.

This module establishes a unified error handling taxonomy. All application-specific
exceptions derive from `PromptLabError`, carrying an explicit machine-readable error code,
an HTTP status code, and optional diagnostic context. This enables uniform API error
responses and decoupling from web frameworks.
"""

from typing import Any


class PromptLabError(Exception):
    """Base exception for all PromptLab domain and infrastructure errors.

    Attributes:
        message: Human-readable error description.
        error_code: Unique machine-readable error token (e.g., 'PROVIDER_ERROR').
        status_code: Suggested HTTP status code for API mapping.
        details: Optional supplementary contextual metadata.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception to a JSON-compatible dictionary."""
        payload: dict[str, Any] = {
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class ConfigurationError(PromptLabError):
    """Raised when environment variables or application settings are invalid."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=details,
        )


class ProviderError(PromptLabError):
    """Raised when an external LLM inference provider fails or returns an error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            error_code="PROVIDER_ERROR",
            status_code=502,
            details=details,
        )


class RateLimitError(PromptLabError):
    """Raised when an LLM provider rejects requests due to quota or concurrency limits."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        details = {"retry_after": retry_after} if retry_after is not None else None
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details=details,
        )


class ProviderNotFoundError(PromptLabError):
    """Raised when an unregistered LLM provider is requested."""

    def __init__(self, provider_name: str) -> None:
        super().__init__(
            message=f"Provider '{provider_name}' is not registered.",
            error_code="PROVIDER_NOT_FOUND",
            status_code=404,
            details={"provider": provider_name},
        )


class ScorerNotFoundError(PromptLabError):
    """Raised when an unregistered evaluation scorer is requested."""

    def __init__(self, scorer_name: str) -> None:
        super().__init__(
            message=f"Scorer '{scorer_name}' is not registered.",
            error_code="SCORER_NOT_FOUND",
            status_code=404,
            details={"scorer": scorer_name},
        )


class TechniqueNotFoundError(PromptLabError):
    """Raised when an unregistered prompt technique is requested."""

    def __init__(self, technique_name: str) -> None:
        super().__init__(
            message=f"Prompt technique '{technique_name}' is not registered.",
            error_code="TECHNIQUE_NOT_FOUND",
            status_code=404,
            details={"technique": technique_name},
        )


class ValidationError(PromptLabError):
    """Raised when domain constraints or input payloads fail validation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class ResourceNotFoundError(PromptLabError):
    """Raised when a requested resource (e.g., Suite or Run) cannot be found."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' was not found.",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class SecurityError(PromptLabError):
    """Raised when an execution violates safety policies (e.g., non-SELECT SQL execution)."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            error_code="SECURITY_ERROR",
            status_code=400,
            details=details,
        )


class AuthenticationError(PromptLabError):
    """Raised when request authorization fails or API key is invalid."""

    def __init__(self, message: str = "Invalid or missing API key.") -> None:
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
        )
