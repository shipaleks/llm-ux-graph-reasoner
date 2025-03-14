"""Text processing module for the knowledge graph synthesis system.

This module provides functionality for loading, normalizing, segmenting, and
managing context for text documents.
"""

from .loader import TextLoader
from .normalizer import TextNormalizer
from .segmenter import TextSegmenter
from .context import ContextManager

__all__ = [
    "TextLoader",
    "TextNormalizer",
    "TextSegmenter",
    "ContextManager"
]