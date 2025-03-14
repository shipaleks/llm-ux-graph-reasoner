"""Response schemas for meta-graph creation."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# Pydantic models for cluster analysis
class ClusterEvaluation(BaseModel):
    """Evaluation of a cluster for meta-concept suitability."""
    cluster_id: str
    semantic_coherence: int = Field(ge=0, le=10)
    structural_integrity: int = Field(ge=0, le=10)
    abstraction_potential: int = Field(ge=0, le=10)
    total_score: int = Field(ge=0, le=30)
    proposed_name: Optional[str] = None
    definition: Optional[str] = None
    key_attributes: Optional[List[str]] = None


class ClusterAnalysis(BaseModel):
    """Analysis of cluster suitability for abstraction."""
    clusters: List[ClusterEvaluation]


# Pydantic models for meta-concept generation
class MetaConceptAttribute(BaseModel):
    """Attribute of a meta-concept."""
    name: str
    description: str
    source: str


class MetaConceptSubstructure(BaseModel):
    """Internal substructure of a meta-concept."""
    name: str
    members: List[str]
    relationship: str


class MetaConceptRelation(BaseModel):
    """Relationship between a meta-concept and other concepts."""
    target_concept: str
    relationship_type: str
    description: str


class MetaConcept(BaseModel):
    """A meta-concept that abstracts multiple entities."""
    name: str
    definition: str
    common_attributes: List[MetaConceptAttribute]
    new_attributes: List[MetaConceptAttribute]
    variable_attributes: List[MetaConceptAttribute]
    internal_structure: List[MetaConceptSubstructure]
    external_relations: List[MetaConceptRelation]


# Pydantic models for meta-relationship analysis
class MetaRelationshipAnalysis(BaseModel):
    """Analysis of a relationship between meta-concepts."""
    exists: bool
    strength: float = Field(ge=0.0, le=1.0)
    fundamental: bool
    confidence: float = Field(ge=0.0, le=1.0)
    relationship_type: Optional[str] = None
    direction: Optional[str] = None
    description: Optional[str] = None
    connected_aspects: Optional[List[str]] = None
    lost_information: Optional[List[str]] = None
    new_aspects: Optional[List[str]] = None
    formalization: Optional[Dict[str, Any]] = None


# Response schemas
class ClusterAnalysisResponse(BaseModel):
    """Response from cluster analysis."""
    analysis: ClusterAnalysis


class MetaConceptResponse(BaseModel):
    """Response from meta-concept generation."""
    meta_concept: MetaConcept


class MetaRelationshipResponse(BaseModel):
    """Response from meta-relationship analysis."""
    meta_relationship: MetaRelationshipAnalysis


def get_cluster_analysis_schema() -> Dict[str, Any]:
    """Get the schema for cluster analysis.
    
    Returns:
        JSON Schema for cluster analysis
    """
    return ClusterAnalysisResponse.schema()


def get_meta_concept_schema() -> Dict[str, Any]:
    """Get the schema for meta-concept generation.
    
    Returns:
        JSON Schema for meta-concept generation
    """
    return MetaConceptResponse.schema()


def get_meta_relationship_schema() -> Dict[str, Any]:
    """Get the schema for meta-relationship analysis.
    
    Returns:
        JSON Schema for meta-relationship analysis
    """
    return MetaRelationshipResponse.schema()