"""Response schemas for structured LLM output.

This module provides JSON Schema definitions for structured LLM responses,
helping to constrain model outputs and reduce hallucinations.
"""

from .entity import get_entity_extraction_schema, get_entity_analysis_schema
from .relationship import get_relationship_extraction_schema, get_relationship_analysis_schema
from .theory import (
    get_theory_generation_schema,
    get_hypothesis_generation_schema,
    get_pattern_identification_schema,
)

# Import new schemas
from .contextual import (
    get_hierarchical_segmentation_schema,
    get_segment_summary_schema,
    get_cross_segment_analysis_schema,
)
from .expansion import (
    get_research_questions_schema,
    get_extracted_knowledge_schema,
)
from .metagraph import (
    get_cluster_analysis_schema,
    get_meta_concept_schema,
    get_meta_relationship_schema,
)

__all__ = [
    # Original schemas
    "get_entity_extraction_schema",
    "get_entity_analysis_schema",
    "get_relationship_extraction_schema",
    "get_relationship_analysis_schema",
    "get_theory_generation_schema",
    "get_hypothesis_generation_schema",
    "get_pattern_identification_schema",
    
    # New contextual analysis schemas
    "get_hierarchical_segmentation_schema",
    "get_segment_summary_schema",
    "get_cross_segment_analysis_schema",
    
    # New expansion schemas
    "get_research_questions_schema",
    "get_extracted_knowledge_schema",
    
    # New metagraph schemas
    "get_cluster_analysis_schema",
    "get_meta_concept_schema",
    "get_meta_relationship_schema",
]