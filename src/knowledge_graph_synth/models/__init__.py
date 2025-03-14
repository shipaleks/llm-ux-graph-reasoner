"""Data models for the knowledge graph synthesis system.

This module provides Pydantic models for the core data structures used in the system,
including text segments, entities, relationships, and the knowledge graph itself.
"""

from .segment import TextSegment, SegmentCollection
from .entity import Entity, EntityAttribute
from .relationship import Relationship
from .graph import KnowledgeGraph
from .provenance import SourceSpan, EvidenceCollection

__all__ = [
    "TextSegment", "SegmentCollection",
    "Entity", "EntityAttribute",
    "Relationship",
    "KnowledgeGraph",
    "SourceSpan", "EvidenceCollection"
]