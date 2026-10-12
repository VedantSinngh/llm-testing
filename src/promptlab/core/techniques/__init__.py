"""Techniques package exporting prompt strategies and the central registry."""

from promptlab.core.techniques.base import PromptTechnique
from promptlab.core.techniques.chain_of_thought import ChainOfThought
from promptlab.core.techniques.few_shot import FewShot
from promptlab.core.techniques.registry import TechniqueRegistry
from promptlab.core.techniques.structured_output import StructuredOutput
from promptlab.core.techniques.zero_shot import ZeroShot

__all__ = [
    "PromptTechnique",
    "ZeroShot",
    "FewShot",
    "ChainOfThought",
    "StructuredOutput",
    "TechniqueRegistry",
]
