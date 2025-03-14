"""Response schemas for entity extraction."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# Pydantic models for entity extraction
class SourceSpan(BaseModel):
    """Source span indicating where an entity was found in text."""
    start: int = Field(description="Character position where the entity starts in the text")
    end: int = Field(description="Character position where the entity ends in the text")
    text: str = Field(description="The actual text span containing the entity")


class EntityAttribute(BaseModel):
    """An attribute of an entity with confidence."""
    key: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")


class Entity(BaseModel):
    """An entity extracted from text."""
    name: str = Field(description="The canonical name of the entity")
    type: str = Field(description="The type/category of the entity")
    source_span: SourceSpan = Field(
        description="The span of text where this entity was found"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, 
        description="Overall confidence score for the entity (0-1)"
    )
    attributes: List[EntityAttribute] = Field(
        description="List of entity attributes"
    )
    aliases: List[str] = Field(
        description="Alternative forms or mentions of the entity"
    )


class EntityExtractionResponse(BaseModel):
    """Response from entity extraction."""
    entities: List[Entity]


# Pydantic models for detailed entity analysis
class EntityAnalysisAttribute(BaseModel):
    """An attribute with evidence in entity analysis."""
    key: str
    value: str
    evidence: str = Field(description="Text from source that supports this attribute")
    confidence: float = Field(ge=0.0, le=1.0)


class EntityAnalysis(BaseModel):
    """Detailed analysis of a single entity."""
    name: str
    type: str
    description: str = Field(description="Detailed description of the entity based on text")
    attributes: List[EntityAnalysisAttribute]
    source_spans: List[SourceSpan] = Field(
        description="All mentions of this entity in the text"
    )
    aliases: Optional[List[str]] = None
    relevance: str = Field(
        description="Assessment of entity's importance in the text (high/medium/low)"
    )


class EntityAnalysisResponse(BaseModel):
    """Response from detailed entity analysis."""
    entity: EntityAnalysis


def get_entity_extraction_schema() -> Dict[str, Any]:
    """Get the schema for entity extraction.
    
    Returns:
        JSON Schema for entity extraction
    """
    return EntityExtractionResponse.schema()


def get_entity_analysis_schema() -> Dict[str, Any]:
    """Get the schema for detailed entity analysis.
    
    Returns:
        JSON Schema for entity analysis
    """
    return EntityAnalysisResponse.schema()