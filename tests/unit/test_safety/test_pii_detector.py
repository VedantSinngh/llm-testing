"""Unit tests for PIIDetector and Luhn algorithm validation."""

from promptlab.core.safety.pii_detector import PIIDetector, validate_luhn


def test_luhn_algorithm_validation() -> None:
    """Verify Luhn algorithm correctly accepts valid cards and rejects invalid ones."""
    # Standard valid test numbers
    valid_visa = "4532015112830366"
    valid_mc = "5424180123456789"
    valid_amex = "378282246310005"

    assert validate_luhn(valid_visa) is True
    assert validate_luhn(valid_mc) is True
    assert validate_luhn(valid_amex) is True

    # Invalid numbers (checksum altered)
    invalid_visa = "4532015112830367"
    short_num = "12345678"
    assert validate_luhn(invalid_visa) is False
    assert validate_luhn(short_num) is False


def test_detect_and_redact_credit_cards() -> None:
    """Verify credit card numbers are detected and masked."""
    detector = PIIDetector()
    text = "Please bill card 4532-0151-1283-0366 for the transaction."
    findings = detector.scan(text)

    assert len(findings) == 1
    assert findings[0]["type"] == "credit_card"
    assert findings[0]["snippet"] == "****-****-****-0366"

    redacted = detector.redact(text)
    assert "4532-0151-1283-0366" not in redacted
    assert "****-****-****-0366" in redacted


def test_detect_and_redact_emails() -> None:
    """Verify email addresses are detected and masked."""
    detector = PIIDetector()
    text = "Contact support at customer.service@example.com for help."
    findings = detector.scan(text)

    assert len(findings) == 1
    assert findings[0]["type"] == "email"
    assert findings[0]["snippet"] == "c***@example.com"

    redacted = detector.redact(text)
    assert "customer.service@example.com" not in redacted
    assert "c***@example.com" in redacted


def test_detect_and_redact_phones() -> None:
    """Verify Indian and international phone numbers are detected."""
    detector = PIIDetector()
    text = "Call me at +91 9876543210 or intl line +14155552671."
    findings = detector.scan(text)

    phone_types = [f["type"] for f in findings]
    assert phone_types.count("phone") == 2

    redacted = detector.redact(text)
    assert "9876543210" not in redacted
    assert "14155552671" not in redacted


def test_detect_and_redact_api_keys() -> None:
    """Verify Groq, OpenAI, and AWS keys are identified."""
    detector = PIIDetector()
    text = (
        "Groq: gsk_1234567890abcdef1234567890, "
        "OpenAI: sk-proj123456789012345678901234, "
        "AWS: AKIAIOSFODNN7EXAMPLE"
    )
    findings = detector.scan(text)

    assert len(findings) == 3
    detectors = {f["detector"] for f in findings}
    assert "pii_groq_api_key" in detectors
    assert "pii_openai_api_key" in detectors
    assert "pii_aws_key" in detectors

    redacted = detector.redact(text)
    assert "gsk_1234567890abcdef" not in redacted
    assert "sk-proj123456789" not in redacted
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted


def test_detect_and_redact_ipv4() -> None:
    """Verify IPv4 addresses are identified."""
    detector = PIIDetector()
    text = "Internal gateway located at 192.168.1.105 on eth0."
    findings = detector.scan(text)

    assert len(findings) == 1
    assert findings[0]["type"] == "ipv4"
    assert findings[0]["snippet"] == "192.168.***.***"

    redacted = detector.redact(text)
    assert "192.168.1.105" not in redacted
    assert "192.168.***.***" in redacted


def test_clean_text_has_no_pii() -> None:
    """Verify benign text produces no findings."""
    detector = PIIDetector()
    text = "The quick brown fox jumps over the lazy dog."
    assert detector.has_pii(text) is False
    assert detector.scan(text) == []
    assert detector.redact(text) == text
