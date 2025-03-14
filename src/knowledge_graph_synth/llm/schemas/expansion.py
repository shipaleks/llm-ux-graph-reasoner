"""Response schemas for graph expansion."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# Pydantic models for research questions
class ResearchQuestion(BaseModel):
    """Research question for graph expansion."""
    question: str
    affected_nodes: List[str]
    expected_answer_type: str
    priority_reason: str


class ResearchQuestions(BaseModel):
    """A set of research questions for graph expansion."""
    questions: List[ResearchQuestion]


# Pydantic models for knowledge extraction
class NewEntity(BaseModel):
    """New entity to add to the graph."""
    name: str
    type: str
    attributes: Dict[str, str]
    source: str
    confidence: float = Field(ge=0.0, le=1.0)


class NewRelationship(BaseModel):
    """New relationship to add to the graph."""
    source_entity: str
    target_entity: str
    relationship_type: str
    direction: str
    source: str
    confidence: float = Field(ge=0.0, le=1.0)


class EntityClarification(BaseModel):
    """Clarification for an existing entity."""
    entity: str
    attribute: str
    new_value: str
    source: str
    confidence: float = Field(ge=0.0, le=1.0)


class RelationshipClarification(BaseModel):
    """Clarification for an existing relationship."""
    source_entity: str
    target_entity: str
    aspect: str
    new_value: str
    source: str
    confidence: float = Field(ge=0.0, le=1.0)


class MetaConcept(BaseModel):
    """Meta-concept or generalization."""
    name: str
    description: str
    related_entities: List[str]
    source: str
    confidence: float = Field(ge=0.0, le=1.0)


class ExtractedKnowledge(BaseModel):
    """Knowledge extracted from reasoning."""
    new_entities: List[NewEntity]
    new_relationships: List[NewRelationship]
    entity_clarifications: List[EntityClarification]
    relationship_clarifications: List[RelationshipClarification]
    meta_concepts: List[MetaConcept]


# Response schemas
class ResearchQuestionsResponse(BaseModel):
    """Response from research question generation."""
    research_questions: ResearchQuestions


class ExtractedKnowledgeResponse(BaseModel):
    """Response from knowledge extraction."""
    extracted_knowledge: ExtractedKnowledge


def get_research_questions_schema() -> Dict[str, Any]:
    """Get the schema for research questions.
    
    Returns:
        JSON Schema for research questions
    """
    return ResearchQuestionsResponse.schema()


def get_extracted_knowledge_schema() -> Dict[str, Any]:
    """Get the schema for extracted knowledge.
    
    Returns:
        JSON Schema for extracted knowledge
    """
    return ExtractedKnowledgeResponse.schema()