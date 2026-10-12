"""Personally Identifiable Information (PII) and Secret Leakage Detector.

This module detects sensitive information in text prompts and completions:
- Email addresses
- Phone numbers (Indian national and international E.164 formats)
- Credit card numbers verified via the Luhn algorithm
- Cloud and LLM API keys (Groq, OpenAI, AWS)
- IPv4 network addresses
All detected findings are masked into redacted previews to prevent secondary leakage.
"""

import re
from typing import Any


def validate_luhn(card_number_str: str) -> bool:
    """Validate credit card number using the Luhn algorithm (Mod 10 checksum)."""
    digits = [int(char) for char in card_number_str if char.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False

    checksum = 0
    reverse_digits = digits[::-1]
    for idx, digit in enumerate(reverse_digits):
        if idx % 2 == 1:
            doubled = digit * 2
            checksum += (doubled - 9) if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0


class PIIDetector:
    """Detects and redacts sensitive entities (PII, credentials, addresses)."""

    # Detection regex patterns
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    INDIAN_PHONE_PATTERN = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b")
    INTL_PHONE_PATTERN = re.compile(r"\+[1-9]\d{1,3}[\-\s]?\d{6,12}\b")
    CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{13,19}\b")
    GROQ_KEY_PATTERN = re.compile(r"\bgsk_[A-Za-z0-9_]{16,}\b")
    OPENAI_KEY_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")
    AWS_KEY_PATTERN = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
    IPV4_PATTERN = re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b"
    )

    @staticmethod
    def _mask_email(email: str) -> str:
        """Mask email preserving first char and domain."""
        parts = email.split("@", 1)
        if len(parts) != 2 or not parts[0]:
            return "[REDACTED_EMAIL]"
        user, domain = parts
        return f"{user[0]}***@{domain}"

    @staticmethod
    def _mask_card(card: str) -> str:
        """Mask credit card preserving last 4 digits."""
        digits = [c for c in card if c.isdigit()]
        last4 = "".join(digits[-4:])
        return f"****-****-****-{last4}"

    @staticmethod
    def _mask_phone(phone: str) -> str:
        """Mask phone number preserving prefix and last 2 digits."""
        cleaned = re.sub(r"[^\d+]", "", phone)
        if len(cleaned) <= 4:
            return "[REDACTED_PHONE]"
        return f"{cleaned[:3]}-***-***{cleaned[-2:]}"

    @staticmethod
    def _mask_ipv4(ip: str) -> str:
        """Mask last two octets of IPv4."""
        octets = ip.split(".")
        return f"{octets[0]}.{octets[1]}.***.***"

    def scan(self, text: str) -> list[dict[str, Any]]:
        """Scan text and return findings with redacted snippets and positions."""
        findings: list[dict[str, Any]] = []

        # 1. API Keys
        for match in self.GROQ_KEY_PATTERN.finditer(text):
            findings.append(
                {
                    "type": "api_key",
                    "category": "SECRET",
                    "detector": "pii_groq_api_key",
                    "snippet": "gsk_***[REDACTED]",
                    "start": match.start(),
                    "end": match.end(),
                }
            )
        for match in self.OPENAI_KEY_PATTERN.finditer(text):
            findings.append(
                {
                    "type": "api_key",
                    "category": "SECRET",
                    "detector": "pii_openai_api_key",
                    "snippet": "sk-***[REDACTED]",
                    "start": match.start(),
                    "end": match.end(),
                }
            )
        for match in self.AWS_KEY_PATTERN.finditer(text):
            findings.append(
                {
                    "type": "api_key",
                    "category": "SECRET",
                    "detector": "pii_aws_key",
                    "snippet": "AKIA***[REDACTED]",
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # 2. Credit Cards with Luhn check
        for match in self.CREDIT_CARD_PATTERN.finditer(text):
            raw = match.group(0)
            if validate_luhn(raw):
                findings.append(
                    {
                        "type": "credit_card",
                        "category": "FINANCIAL",
                        "detector": "pii_credit_card",
                        "snippet": self._mask_card(raw),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        # 3. Emails
        for match in self.EMAIL_PATTERN.finditer(text):
            raw = match.group(0)
            findings.append(
                {
                    "type": "email",
                    "category": "PII",
                    "detector": "pii_email",
                    "snippet": self._mask_email(raw),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # 4. Phone Numbers (Indian and International)
        for pattern, detector_name in [
            (self.INDIAN_PHONE_PATTERN, "pii_phone_indian"),
            (self.INTL_PHONE_PATTERN, "pii_phone_international"),
        ]:
            for match in pattern.finditer(text):
                raw = match.group(0)
                findings.append(
                    {
                        "type": "phone",
                        "category": "PII",
                        "detector": detector_name,
                        "snippet": self._mask_phone(raw),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        # 5. IPv4
        for match in self.IPV4_PATTERN.finditer(text):
            raw = match.group(0)
            findings.append(
                {
                    "type": "ipv4",
                    "category": "NETWORK",
                    "detector": "pii_ipv4",
                    "snippet": self._mask_ipv4(raw),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        return findings

    def redact(self, text: str) -> str:
        """Return a fully redacted copy of text replacing all detected secrets."""
        findings = self.scan(text)
        if not findings:
            return text

        # Sort findings descending by start index to substitute from end to start
        sorted_findings = sorted(findings, key=lambda f: int(f["start"]), reverse=True)
        result = text
        for finding in sorted_findings:
            start = int(finding["start"])
            end = int(finding["end"])
            snippet = str(finding["snippet"])
            result = result[:start] + snippet + result[end:]
        return result

    def has_pii(self, text: str) -> bool:
        """Return True if any PII or secret is detected."""
        return len(self.scan(text)) > 0
