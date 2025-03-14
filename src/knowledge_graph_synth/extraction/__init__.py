"""Extraction module for the knowledge graph synthesis system.

This module provides functionality for extracting entities and relationships
from text, resolving coreferences, and grounding extractions to source text.
"""

from .entity_extractor import EntityExtractor
from .relation_extractor import RelationshipExtractor
from .coreference import CoreferenceResolver
from .grounding import Grounder

__all__ = [
    "EntityExtractor",
    "RelationshipExtractor",
    "CoreferenceResolver",
    "Grounder"
]