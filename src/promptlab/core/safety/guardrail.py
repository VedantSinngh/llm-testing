"""Safety Guardrail combining PII detection and risk assessment.

This module provides a unified guardrail filter suitable for scanning input queries
and output completions. It calculates a holistic risk level ('low', 'medium', 'high')
and can actively sanitize text payloads.
"""

from typing import Any, Literal

from promptlab.core.models import SafetyReport
from promptlab.core.safety.pii_detector import PIIDetector


class Guardrail:
    """Unified safety guardrail for detecting leaks and assessing payload risks."""

    def __init__(self, pii_detector: PIIDetector | None = None) -> None:
        """Initialize Guardrail with PII detector instance."""
        self._pii_detector = pii_detector or PIIDetector()

    def _determine_risk_level(
        self, pii_findings: list[dict[str, Any]]
    ) -> Literal["low", "medium", "high"]:
        """Determine aggregate risk level based on severity and volume of findings."""
        if not pii_findings:
            return "low"

        # Check for critical high-severity categories: API keys and Credit Cards
        has_critical = any(
            f.get("type") in {"api_key", "credit_card"} for f in pii_findings
        )
        if has_critical or len(pii_findings) >= 3:
            return "high"

        # Emails, phones, IPs are classified as medium risk
        return "medium"

    def check_text(self, text: str) -> SafetyReport:
        """Analyze text and generate a structured SafetyReport."""
        findings = self._pii_detector.scan(text)
        risk = self._determine_risk_level(findings)
        passed = risk == "low"

        return SafetyReport(
            injection_results=[],
            pii_findings=findings,
            risk_level=risk,
            passed=passed,
        )

    def filter_text(
        self, text: str, redact: bool = True
    ) -> tuple[bool, str, SafetyReport]:
        """Filter text and return whether it passed, the sanitized text, and the report.

        Args:
            text: Raw input or output string.
            redact: If True, replace identified PII with redacted snippets.

        Returns:
            Tuple of (passed_safety, sanitized_text, safety_report).
        """
        report = self.check_text(text)
        sanitized = self._pii_detector.redact(text) if redact else text
        is_safe = report.risk_level != "high"

        return (is_safe, sanitized, report)
