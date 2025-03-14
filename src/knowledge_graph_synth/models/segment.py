"""Text segment models for the knowledge graph synthesis system."""

from typing import Dict, List, Optional, Any, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class TextSegment(BaseModel):
    """A segment of text for processing.
    
    Text segments are the primary units of processing in the system. Each segment
    contains a portion of the original text, along with metadata about its position
    in the document and its place in the hierarchy of segments.
    """
    
    model_config = ConfigDict(frozen=False)
    
    id: UUID = Field(default_factory=uuid4)
    document_id: Optional[str] = None
    text: str
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    language: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parent_id: Optional[UUID] = None
    child_ids: List[UUID] = Field(default_factory=list)
    
    @property
    def length(self) -> int:
        """Get the length of the text segment.
        
        Returns:
            Number of characters in the segment
        """
        return len(self.text)
        
    @property
    def position_length(self) -> Optional[int]:
        """Get the length based on start and end positions.
        
        Returns:
            Number of characters between start and end positions, or None if positions are not set
        """
        if self.start_position is not None and self.end_position is not None:
            return self.end_position - self.start_position
        return None
    
    def add_child(self, child_id: UUID) -> None:
        """Add a child segment ID.
        
        Args:
            child_id: UUID of the child segment
        """
        if child_id not in self.child_ids:
            self.child_ids.append(child_id)
    
    def set_language(self, language_code: str) -> None:
        """Set the language of the segment.
        
        Args:
            language_code: ISO language code (e.g., 'en', 'ru')
        """
        self.language = language_code.lower()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the segment.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert segment to a dictionary representation.
        
        Returns:
            Dictionary representation of the segment
        """
        return {
            "id": str(self.id),
            "document_id": self.document_id,
            "text": self.text,
            "start_position": self.start_position,  # Может быть None
            "end_position": self.end_position,      # Может быть None
            "language": self.language,
            "metadata": self.metadata,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "child_ids": [str(cid) for cid in self.child_ids]
        }


class SegmentCollection(BaseModel):
    """A collection of text segments.
    
    This class manages a collection of text segments, providing methods for
    adding, retrieving, and navigating segments.
    """
    
    segments: Dict[UUID, TextSegment] = Field(default_factory=dict)
    document_id: Optional[str] = None
    
    def add_segment(self, segment: TextSegment) -> None:
        """Add a segment to the collection.
        
        Args:
            segment: Text segment to add
        """
        if not segment.document_id and self.document_id:
            segment.document_id = self.document_id
        
        self.segments[segment.id] = segment
        
        # Update parent-child relationships
        if segment.parent_id and segment.parent_id in self.segments:
            parent = self.segments[segment.parent_id]
            parent.add_child(segment.id)
    
    def get_segment(self, segment_id: UUID) -> Optional[TextSegment]:
        """Get a segment by ID.
        
        Args:
            segment_id: UUID of the segment to retrieve
            
        Returns:
            The segment if found, otherwise None
        """
        return self.segments.get(segment_id)
    
    def get_root_segments(self) -> List[TextSegment]:
        """Get all root segments (those without parents).
        
        Returns:
            List of root segments
        """
        return [seg for seg in self.segments.values() if seg.parent_id is None]
    
    def get_children(self, segment_id: UUID) -> List[TextSegment]:
        """Get all children of a segment.
        
        Args:
            segment_id: UUID of the parent segment
            
        Returns:
            List of child segments
        """
        segment = self.get_segment(segment_id)
        if not segment:
            return []
        
        return [self.segments[child_id] for child_id in segment.child_ids if child_id in self.segments]
    
    def get_descendants(self, segment_id: UUID) -> List[TextSegment]:
        """Get all descendants of a segment.
        
        Args:
            segment_id: UUID of the ancestor segment
            
        Returns:
            List of descendant segments
        """
        result = []
        to_process = self.get_children(segment_id)
        
        while to_process:
            current = to_process.pop(0)
            result.append(current)
            to_process.extend(self.get_children(current.id))
        
        return result
    
    def get_by_position(self, position: int, root_only: bool = False) -> List[TextSegment]:
        """Get segments that include a specific position.
        
        Args:
            position: Character position in the document
            root_only: If True, only consider root segments
            
        Returns:
            List of segments containing the position
        """
        segments = self.get_root_segments() if root_only else self.segments.values()
        result = []
        
        for seg in segments:
            # Проверяем, что позиции определены
            if seg.start_position is not None and seg.end_position is not None:
                if seg.start_position <= position and seg.end_position >= position:
                    result.append(seg)
        
        return result
    
    def __len__(self) -> int:
        """Get the number of segments in the collection.
        
        Returns:
            Segment count
        """
        return len(self.segments)