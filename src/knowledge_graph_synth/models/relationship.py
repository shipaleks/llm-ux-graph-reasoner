"""Relationship models for the knowledge graph synthesis system."""

from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

from .provenance import SourceSpan
from .entity import EntityAttribute


class Relationship(BaseModel):
    """A relationship between two entities.
    
    Relationships are the edges in the knowledge graph. Each relationship
    connects two entities and has a type and attributes. It also includes
    provenance information tracking where it was found in the source text.
    """
    
    model_config = ConfigDict(frozen=False)
    
    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    target_id: UUID
    type: str
    directed: bool = True
    attributes: List[EntityAttribute] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    source_span: SourceSpan
    
    def add_attribute(self, key: str, value: Any, 
                      confidence: float = 1.0,
                      source_span: Optional[SourceSpan] = None) -> None:
        """Add an attribute to the relationship.
        
        Args:
            key: Attribute name
            value: Attribute value
            confidence: Confidence score for this attribute
            source_span: Source text span for this attribute
        """
        attr = EntityAttribute(
            key=key,
            value=value,
            confidence=confidence,
            source_span=source_span
        )
        self.attributes.append(attr)
    
    def get_attribute(self, key: str) -> List[EntityAttribute]:
        """Get all attributes with the given key.
        
        Args:
            key: Attribute name to search for
            
        Returns:
            List of matching attributes
        """
        return [attr for attr in self.attributes if attr.key == key]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to a dictionary representation.
        
        Returns:
            Dictionary representation of the relationship
        """
        return {
            "id": str(self.id),
            "source_id": str(self.source_id),
            "target_id": str(self.target_id),
            "type": self.type,
            "directed": self.directed,
            "attributes": [
                {
                    "key": attr.key,
                    "value": attr.value,
                    "confidence": attr.confidence,
                    "source_span": attr.source_span.to_dict() if attr.source_span else None
                }
                for attr in self.attributes
            ],
            "confidence": self.confidence,
            "source_span": self.source_span.to_dict()
        }