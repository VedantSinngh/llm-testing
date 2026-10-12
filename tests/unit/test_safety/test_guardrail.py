"""Unit tests for Guardrail risk classification and filtering."""

from promptlab.core.safety.guardrail import Guardrail


def test_guardrail_clean_text_low_risk() -> None:
    """Verify clean text produces low risk level and passes."""
    guardrail = Guardrail()
    text = "The forecast for tomorrow predicts sunshine and clear skies."
    report = guardrail.check_text(text)

    assert report.risk_level == "low"
    assert report.passed is True
    assert len(report.pii_findings) == 0


def test_guardrail_email_medium_risk() -> None:
    """Verify email finding results in medium risk."""
    guardrail = Guardrail()
    text = "Reach out to user.help@company.org for onboarding."
    report = guardrail.check_text(text)

    assert report.risk_level == "medium"
    assert report.passed is False
    assert len(report.pii_findings) == 1


def test_guardrail_api_key_high_risk() -> None:
    """Verify API key results in high risk classification."""
    guardrail = Guardrail()
    text = "Authorization token: gsk_1234567890abcdef1234567890"
    report = guardrail.check_text(text)

    assert report.risk_level == "high"
    assert report.passed is False


def test_guardrail_credit_card_high_risk() -> None:
    """Verify valid credit card results in high risk classification."""
    guardrail = Guardrail()
    text = "Payment card number: 4532015112830366"
    report = guardrail.check_text(text)

    assert report.risk_level == "high"
    assert report.passed is False


def test_guardrail_filter_text_redacts_and_blocks() -> None:
    """Verify filter_text provides safety boolean and sanitized payload."""
    guardrail = Guardrail()
    text = "Contact john@doe.com with secret gsk_1234567890abcdef1234567890."

    is_safe, sanitized, report = guardrail.filter_text(text, redact=True)

    # Contains high-risk API key -> is_safe should be False
    assert is_safe is False
    assert report.risk_level == "high"
    assert "john@doe.com" not in sanitized
    assert "gsk_1234567890" not in sanitized
    assert "j***@doe.com" in sanitized
    assert "gsk_***[REDACTED]" in sanitized
