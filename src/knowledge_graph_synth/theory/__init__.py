"""Theory generation module for the knowledge graph synthesis system.

This module provides functionality for identifying patterns, generating theories
and hypotheses, evaluating their quality, and tracking supporting evidence.
"""

from .pattern_finder import PatternFinder
from .theory_generator import TheoryGenerator
from .hypothesis import HypothesisGenerator
from .evaluator import TheoryEvaluator
from .evidence import EvidenceCollector

__all__ = [
    "PatternFinder",
    "TheoryGenerator",
    "HypothesisGenerator",
    "TheoryEvaluator",
    "EvidenceCollector"
]