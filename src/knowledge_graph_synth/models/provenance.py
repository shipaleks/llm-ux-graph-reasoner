"""Provenance tracking models for the knowledge graph synthesis system.

This module provides data structures for tracking the source of information
extracted by the system, allowing for verification and citation.
"""

from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class SourceSpan(BaseModel):
    """A span of text in a source document.
    
    This class represents a specific location in a source document where
    an entity, relationship, or other information was found.
    """
    
    model_config = ConfigDict(frozen=False)
    
    document_id: Optional[str] = None
    segment_id: Optional[str] = None
    start: int
    end: int
    text: str
    
    def contains(self, other: 'SourceSpan') -> bool:
        """Check if this span contains another span.
        
        Args:
            other: Another source span to check
            
        Returns:
            True if this span contains the other span
        """
        if self.document_id != other.document_id:
            return False
        
        if self.segment_id != other.segment_id:
            return False
        
        return self.start <= other.start and self.end >= other.end
    
    def overlaps(self, other: 'SourceSpan') -> bool:
        """Check if this span overlaps with another span.
        
        Args:
            other: Another source span to check
            
        Returns:
            True if this span overlaps with the other span
        """
        if self.document_id != other.document_id:
            return False
        
        if self.segment_id != other.segment_id:
            return False
        
        return (self.start <= other.end and self.end >= other.start)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the source span
        """
        return {
            "document_id": self.document_id,
            "segment_id": self.segment_id,
            "start": self.start,
            "end": self.end,
            "text": self.text
        }
    
    def citation(self) -> str:
        """Generate a citation string for this source span.
        
        Returns:
            Formatted citation string
        """
        doc_part = f"document {self.document_id}" if self.document_id else "unknown document"
        seg_part = f", segment {self.segment_id}" if self.segment_id else ""
        pos_part = f", positions {self.start}-{self.end}"
        
        return f"[{doc_part}{seg_part}{pos_part}]"


class EvidenceCollection(BaseModel):
    """A collection of evidence supporting a claim.
    
    This class tracks multiple pieces of evidence that support a specific
    claim, theory, or inference made by the system.
    """
    
    source_spans: List[SourceSpan] = Field(default_factory=list)
    
    def add_evidence(self, span: SourceSpan) -> None:
        """Add a source span as evidence.
        
        Args:
            span: Source span to add as evidence
        """
        self.source_spans.append(span)
    
    def get_evidence_text(self) -> List[str]:
        """Get the text of all evidence spans.
        
        Returns:
            List of text from all evidence spans
        """
        return [span.text for span in self.source_spans]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the evidence collection
        """
        return {
            "source_spans": [span.to_dict() for span in self.source_spans]
        }
    
    @property
    def is_empty(self) -> bool:
        """Check if the evidence collection is empty.
        
        Returns:
            True if there are no source spans
        """
        return len(self.source_spans) == 0