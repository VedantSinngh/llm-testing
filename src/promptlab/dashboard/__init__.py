"""Streamlit Multipage Dashboard for PromptLab.

This package provides the interactive user interface for:
- Playground: Interactive prompt engineering and single-shot evaluation.
- Test Suites: Suite management, test case authoring, and execution.
- Safety & Guardrails: Prompt injection testing and PII leakage scanning.
- History & Comparison: Multi-run side-by-side matrices and leaderboards.
"""

from promptlab.dashboard.api_client import PromptLabClient

__all__ = ["PromptLabClient"]
