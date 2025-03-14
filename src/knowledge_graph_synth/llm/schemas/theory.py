"""Response schemas for theory and hypothesis generation."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# Pydantic models for theory generation
class TheoryEntityRole(BaseModel):
    """Entity role in a theory."""
    name: str
    type: Optional[str] = None
    role: str = Field(description="Role the entity plays in the theory")


class TheoryRelationship(BaseModel):
    """Key relationship in a theory."""
    source: str
    target: str
    type: str
    description: Optional[str] = None


class TheoryEvidence(BaseModel):
    """Evidence supporting a theory."""
    text: str = Field(description="Text from source that supports this theory")
    relevance: str = Field(description="How this evidence supports the theory")


class TheoryAlternative(BaseModel):
    """Alternative explanation for the same evidence."""
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)


class TheoryPostulate(BaseModel):
    """A basic postulate of a theory."""
    statement: str = Field(description="The postulate statement")
    explanation: str = Field(description="Explanation or justification")


class TheoryMechanism(BaseModel):
    """Explanatory mechanism of a theory."""
    name: str = Field(description="Name of the mechanism")
    description: str = Field(description="Description of how the mechanism works")
    explained_patterns: List[str] = Field(description="Patterns explained by this mechanism")


class TheoryScope(BaseModel):
    """Scope of applicability of a theory."""
    applicable_areas: List[str] = Field(description="Areas where the theory applies fully")
    limitations: List[str] = Field(description="Limitations or exceptions")
    conditions: List[str] = Field(description="Conditions under which the theory operates")


class TheoryPrediction(BaseModel):
    """Prediction made by a theory."""
    description: str = Field(description="Description of the prediction")
    type: str = Field(description="Type of prediction (new node, new connection, change)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the prediction")


class Theory(BaseModel):
    """A comprehensive theory explaining observed patterns."""
    title: str = Field(description="A concise title for the theory")
    summary: str = Field(description="A brief summary of the theory (1-2 sentences)")
    postulates: List[TheoryPostulate] = Field(
        description="Basic postulates on which the theory is based"
    )
    mechanisms: List[TheoryMechanism] = Field(
        description="Explanatory mechanisms of the theory"
    )
    scope: TheoryScope = Field(
        description="Scope of applicability of the theory"
    )
    key_entities: List[TheoryEntityRole] = Field(
        description="Key entities involved in the theory"
    )
    key_relationships: Optional[List[TheoryRelationship]] = Field(
        default=None,
        description="Key relationships that form the basis of the theory"
    )
    predictions: List[TheoryPrediction] = Field(
        description="Predictions made by the theory"
    )
    evidence: List[TheoryEvidence] = Field(
        description="Evidence supporting the theory"
    )
    existing_theories_relation: Optional[str] = Field(
        default=None,
        description="How this theory relates to existing theories in the field"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Overall confidence in the theory (0-1)"
    )
    alternative_explanations: Optional[List[TheoryAlternative]] = Field(
        default=None,
        description="Alternative theories that could explain the same evidence"
    )
    gaps: Optional[List[str]] = Field(
        default=None,
        description="Knowledge gaps or questions that could strengthen/weaken the theory"
    )


class TheoryResponse(BaseModel):
    """Response from theory generation."""
    theory: Theory


# Pydantic models for hypothesis generation
class HypothesisEntityRole(BaseModel):
    """Entity role in a hypothesis."""
    name: str
    role: Optional[str] = None


class HypothesisEvidence(BaseModel):
    """Evidence supporting or contradicting a hypothesis."""
    text: str
    strength: str = Field(enum=["strong", "moderate", "weak"])


class HypothesisTestability(BaseModel):
    """Testability assessment for a hypothesis."""
    score: float = Field(
        ge=0.0, le=1.0,
        description="How testable is this hypothesis (0-1)"
    )
    method: Optional[str] = Field(
        default=None,
        description="How this hypothesis could be tested"
    )


class HypothesisConfirmation(BaseModel):
    """Data that could confirm a hypothesis."""
    description: str = Field(description="Description of confirming data")
    strength: str = Field(description="How strongly this would confirm the hypothesis")


class HypothesisRefutation(BaseModel):
    """Data that could refute a hypothesis."""
    description: str = Field(description="Description of refuting data")
    strength: str = Field(description="How strongly this would refute the hypothesis")


class HypothesisNovelty(BaseModel):
    """Assessment of hypothesis novelty."""
    score: float = Field(ge=0.0, le=1.0, description="Novelty score")
    justification: str = Field(description="Why this score was assigned")


class HypothesisSignificance(BaseModel):
    """Assessment of hypothesis significance."""
    score: float = Field(ge=0.0, le=1.0, description="Significance score")
    justification: str = Field(description="Why this score was assigned")


class Hypothesis(BaseModel):
    """A specific, testable hypothesis."""
    statement: str = Field(description="The hypothesis statement")
    if_then_form: str = Field(description="Hypothesis in 'if..., then...' format")
    type: str = Field(
        description="Type of hypothesis (e.g., predictive, explanatory, comparative, conditional)",
    )
    related_entities: List[HypothesisEntityRole]
    theory_connection: str = Field(description="Logical connection with the theory's postulates")
    confirmation: List[HypothesisConfirmation]
    refutation: List[HypothesisRefutation]
    supporting_evidence: List[HypothesisEvidence]
    confidence: float = Field(ge=0.0, le=1.0)
    testability: Optional[HypothesisTestability] = None
    novelty: Optional[HypothesisNovelty] = None
    significance: Optional[HypothesisSignificance] = None


class HypothesisResponse(BaseModel):
    """Response from hypothesis generation."""
    hypotheses: List[Hypothesis]


# Pydantic models for pattern identification
class PatternExample(BaseModel):
    """Example of a pattern in the text."""
    text: str
    explanation: str


class Pattern(BaseModel):
    """A pattern identified in the knowledge graph."""
    name: str = Field(description="Name or identifier for the pattern")
    description: str = Field(description="Description of the pattern")
    type: str = Field(
        description="Type of pattern (e.g., 'structural', 'causal', 'motif', 'anomaly')",
    )
    subtype: Optional[str] = Field(None, description="More specific type classification")
    examples: List[PatternExample] = Field(
        description="Examples of the pattern in the text"
    )
    locations: Optional[List[str]] = Field(
        None, description="Specific nodes or subgraphs where the pattern appears"
    )
    significance: str = Field(description="Why this pattern is significant")
    universality: Optional[str] = Field(None, description="Whether the pattern is local or global")
    confidence: float = Field(ge=0.0, le=1.0)


class PatternResponse(BaseModel):
    """Response from pattern identification."""
    patterns: List[Pattern]


def get_theory_generation_schema() -> Dict[str, Any]:
    """Get the schema for theory generation.
    
    Returns:
        JSON Schema for theory generation
    """
    return TheoryResponse.schema()


def get_hypothesis_generation_schema() -> Dict[str, Any]:
    """Get the schema for hypothesis generation.
    
    Returns:
        JSON Schema for hypothesis generation
    """
    return HypothesisResponse.schema()


def get_pattern_identification_schema() -> Dict[str, Any]:
    """Get the schema for pattern identification.
    
    Returns:
        JSON Schema for pattern identification
    """
    return PatternResponse.schema()