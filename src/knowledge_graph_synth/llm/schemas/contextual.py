"""Response schemas for contextual text analysis."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Pydantic models for hierarchical segmentation
class TextSegmentBase(BaseModel):
    """Base model for text segments."""
    id: str
    text: str
    start: int
    end: int


class TextSegment(TextSegmentBase):
    """A text segment with optional subsegments."""
    subsegments: Optional[List['TextSegment']] = None


# Pydantic models for segment summarization
class SegmentSummary(BaseModel):
    """Summary of a text segment."""
    id: str
    title: str  # Short, descriptive title for the segment
    summary: str
    key_points: List[str]
    role: str
    parent_relation: Optional[str] = None


# Pydantic models for cross-segment analysis
class SegmentConnection(BaseModel):
    """Connection between two text segments."""
    segment1_id: str
    segment2_id: str
    has_connection: bool
    connection_type: Optional[str] = None
    strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    direction: Optional[str] = None
    key_indicators: Optional[List[str]] = None


# Response schemas
class HierarchicalSegmentationResponse(BaseModel):
    """Response from hierarchical segmentation."""
    segments: List[TextSegment]


class SegmentSummaryResponse(BaseModel):
    """Response from segment summarization."""
    summary: SegmentSummary


class CrossSegmentAnalysisResponse(BaseModel):
    """Response from cross-segment analysis."""
    connection: SegmentConnection


def get_hierarchical_segmentation_schema() -> Dict[str, Any]:
    """Get the schema for hierarchical segmentation.
    
    Returns:
        JSON Schema for hierarchical segmentation
    """
    return HierarchicalSegmentationResponse.schema()


def get_segment_summary_schema() -> Dict[str, Any]:
    """Get the schema for segment summarization.
    
    Returns:
        JSON Schema for segment summarization
    """
    return SegmentSummaryResponse.schema()


def get_cross_segment_analysis_schema() -> Dict[str, Any]:
    """Get the schema for cross-segment analysis.
    
    Returns:
        JSON Schema for cross-segment analysis
    """
    return CrossSegmentAnalysisResponse.schema()