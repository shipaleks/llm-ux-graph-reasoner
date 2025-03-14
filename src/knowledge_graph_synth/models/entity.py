"""Entity models for the knowledge graph synthesis system."""

from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict, field_validator

from .provenance import SourceSpan


class EntityAttribute(BaseModel):
    """A key-value attribute of an entity."""
    
    key: str
    value: Any
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    source_span: Optional[SourceSpan] = None


class Entity(BaseModel):
    """An entity extracted from text.
    
    Entities are the nodes in the knowledge graph. Each entity has a unique ID,
    a name, a type, and a set of attributes. It also includes provenance
    information tracking where it was found in the source text.
    """
    
    model_config = ConfigDict(frozen=False)
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: str
    attributes: List[EntityAttribute] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    source_span: SourceSpan
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validates and normalizes the entity type."""
        return v.strip().lower()
    
    def add_attribute(self, key: str, value: Any, 
                      confidence: float = 1.0,
                      source_span: Optional[SourceSpan] = None) -> None:
        """Add an attribute to the entity.
        
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
        """Convert entity to a dictionary representation.
        
        Returns:
            Dictionary representation of the entity
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.type,
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