"""Zero-shot prompt engineering technique.

This module provides the baseline prompt strategy: the test case input is passed directly
to the language model without extra demonstration examples or reasoning scaffolds.
"""

from typing import Any

from promptlab.core.techniques.base import PromptTechnique


# Design Pattern: Strategy implementation for zero-shot prompt evaluation.
class ZeroShot(PromptTechnique):
    """Zero-shot prompting passing test input unmodified."""

    name: str = "zero_shot"

    def apply(
        self, case_input: str, config: dict[str, Any]
    ) -> tuple[str | None, str]:
        """Return the raw case input as the user prompt with no system addition."""
        return (None, case_input)
