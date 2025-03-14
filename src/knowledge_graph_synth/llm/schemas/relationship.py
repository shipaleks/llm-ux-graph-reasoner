"""Response schemas for relationship extraction."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .entity import SourceSpan


# Pydantic models for relationship extraction
class RelationshipEntity(BaseModel):
    """Entity reference in a relationship."""
    name: str
    type: str = Field(description="Type of the entity")


class RelationshipAttribute(BaseModel):
    """An attribute of a relationship with confidence."""
    key: str
    value: str
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score (0-1)"
    )


class RelationshipTemporality(BaseModel):
    """Temporal information about a relationship."""
    type: str = Field(
        description="Temporal classification of the relationship"
    )
    specific_time: str = Field(
        description="Specific time or date information if available"
    )


class Relationship(BaseModel):
    """A relationship between two entities."""
    source: RelationshipEntity = Field(
        description="The source/subject entity of the relationship"
    )
    target: RelationshipEntity = Field(
        description="The target/object entity of the relationship"
    )
    type: str = Field(
        description="The type/predicate of the relationship"
    )
    source_span: SourceSpan = Field(
        description="The span of text where this relationship was found"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Overall confidence score for the relationship (0-1)"
    )
    attributes: List[RelationshipAttribute] = Field(
        description="List of relationship attributes"
    )
    bidirectional: bool = Field(
        description="Whether the relationship applies in both directions"
    )
    temporality: RelationshipTemporality = Field(
        description="Temporal information about the relationship"
    )


class RelationshipExtractionResponse(BaseModel):
    """Response from relationship extraction."""
    relationships: List[Relationship]


# Pydantic models for detailed relationship analysis
class RelationshipAnalysisEntity(BaseModel):
    """Entity with description in relationship analysis."""
    name: str
    type: Optional[str] = None
    description: Optional[str] = None


class RelationshipAnalysisAttribute(BaseModel):
    """An attribute with evidence in relationship analysis."""
    key: str
    value: str
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)


class AlternativeInterpretation(BaseModel):
    """Alternative interpretation of a relationship."""
    description: str
    confidence: float = Field(ge=0.0, le=1.0)


class RelationshipAnalysisTemporality(BaseModel):
    """Temporal information with evidence in relationship analysis."""
    type: str
    evidence: Optional[str] = None
    specific_time: Optional[str] = None


class RelationshipAnalysis(BaseModel):
    """Detailed analysis of a single relationship."""
    source: RelationshipAnalysisEntity
    target: RelationshipAnalysisEntity
    type: str
    description: str = Field(
        description="Detailed description of the relationship based on text"
    )
    attributes: List[RelationshipAnalysisAttribute]
    source_spans: List[SourceSpan]
    bidirectional: Optional[bool] = None
    temporality: Optional[RelationshipAnalysisTemporality] = None
    strength: str = Field(
        description="Assessment of relationship strength or intensity",
    )
    alternative_interpretations: Optional[List[AlternativeInterpretation]] = None


class RelationshipAnalysisResponse(BaseModel):
    """Response from detailed relationship analysis."""
    relationship: RelationshipAnalysis


def get_relationship_extraction_schema() -> Dict[str, Any]:
    """Get the schema for relationship extraction.
    
    Returns:
        JSON Schema for relationship extraction
    """
    return RelationshipExtractionResponse.schema()


def get_relationship_analysis_schema() -> Dict[str, Any]:
    """Get the schema for detailed relationship analysis.
    
    Returns:
        JSON Schema for relationship analysis
    """
    return RelationshipAnalysisResponse.schema()