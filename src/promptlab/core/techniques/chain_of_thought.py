"""Chain-of-Thought (CoT) prompt technique and answer parser.

This module instructs the LLM to explain its reasoning step-by-step prior to
providing a concise final conclusion formatted strictly as 'Answer: <x>'.
It also includes an extraction parser to isolate the final answer for scoring.
"""

import re
from typing import Any

from promptlab.core.techniques.base import PromptTechnique


# Design Pattern: Strategy implementation for Chain-of-Thought reasoning.
class ChainOfThought(PromptTechnique):
    """Chain-of-Thought prompt technique requiring explicit intermediate reasoning."""

    name: str = "chain_of_thought"

    def apply(
        self, case_input: str, config: dict[str, Any]
    ) -> tuple[str | None, str]:
        """Apply step-by-step reasoning instructions and delimiter requirements."""
        system_addition = (
            "Think step-by-step before answering. Break down the problem logically. "
            "Conclude your response strictly on the final line with the format: "
            "'Answer: <your final answer>'."
        )
        user_prompt = (
            f"{case_input}\n\n"
            "Please reason step by step and present your final answer on the last line "
            "in the exact format: 'Answer: <final answer>'."
        )
        return (system_addition, user_prompt)

    @staticmethod
    def extract_answer(output: str) -> str:
        """Extract the final answer token following the 'Answer:' delimiter.

        Args:
            output: Full completion string produced by the model.

        Returns:
            The parsed answer substring, or the stripped last line if delimiter is missing.
        """
        match = re.search(r"(?:Answer|ANSWER):\s*(.+)$", output.strip(), re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Fallback to the last non-empty line
        lines = [line.strip() for line in output.strip().splitlines() if line.strip()]
        return lines[-1] if lines else output.strip()
