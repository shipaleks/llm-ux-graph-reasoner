"""Grounding for the knowledge graph synthesis system.

This module implements grounding of extracted entities and relationships
to their source text, ensuring that all information has a valid source
and can be traced back to the original document.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID

from ..models import Entity, Relationship, TextSegment, SegmentCollection, SourceSpan

logger = logging.getLogger(__name__)


class Grounder:
    """Grounds extracted information to source text.
    
    This class verifies that extracted entities and relationships are present
    in the source text, ensuring that all information has valid provenance.
    """
    
    def __init__(self, 
               exact_match: bool = False,
               fuzzy_match_threshold: float = 0.8):
        """Initialize the grounder.
        
        Args:
            exact_match: Whether to require exact text matches
            fuzzy_match_threshold: Threshold for fuzzy matching (0-1)
        """
        self.exact_match = exact_match
        self.fuzzy_match_threshold = fuzzy_match_threshold
    
    def ground_entity(self, entity: Entity, 
                    segment: TextSegment) -> Tuple[bool, Optional[SourceSpan]]:
        """Ground an entity to its source text.
        
        Args:
            entity: Entity to ground
            segment: Text segment to search in
            
        Returns:
            (is_grounded, updated_source_span) tuple
        """
        # If the entity already has a source span, verify it
        if entity.source_span:
            source_span = entity.source_span
            
            # Check if this source span is from a different segment
            if source_span.segment_id and source_span.segment_id != str(segment.id):
                return False, None
            
            # Check if the span text matches the entity name
            if self._verify_span(source_span, segment.text):
                return True, source_span
        
        # Try to find the entity in the text
        span = self._find_in_text(entity.name, segment.text)
        if span:
            # Create a new source span
            source_span = SourceSpan(
                document_id=segment.document_id,
                segment_id=str(segment.id),
                start=span[0],
                end=span[1],
                text=segment.text[span[0]:span[1]]
            )
            return True, source_span
        
        return False, None
    
    def ground_relationship(self, relationship: Relationship,
                         segment: TextSegment,
                         source_entity: Entity,
                         target_entity: Entity) -> Tuple[bool, Optional[SourceSpan]]:
        """Ground a relationship to its source text.
        
        Args:
            relationship: Relationship to ground
            segment: Text segment to search in
            source_entity: Source entity of the relationship
            target_entity: Target entity of the relationship
            
        Returns:
            (is_grounded, updated_source_span) tuple
        """
        # If the relationship already has a source span, verify it
        if relationship.source_span:
            source_span = relationship.source_span
            
            # Check if this source span is from a different segment
            if source_span.segment_id and source_span.segment_id != str(segment.id):
                return False, None
            
            # Check if the span contains both entities
            if self._verify_span(source_span, segment.text):
                # Check if the span contains both entities
                span_text = source_span.text.lower()
                source_name = source_entity.name.lower()
                target_name = target_entity.name.lower()
                
                if source_name in span_text and target_name in span_text:
                    return True, source_span
        
        # Try to find a span that contains both entities
        start_pos = 0
        found_spans = []
        
        while start_pos < len(segment.text):
            # Find the first occurrence of either entity after start_pos
            source_pos = segment.text.lower().find(source_entity.name.lower(), start_pos)
            target_pos = segment.text.lower().find(target_entity.name.lower(), start_pos)
            
            if source_pos == -1 and target_pos == -1:
                # Neither entity found
                break
            
            if source_pos == -1:
                first_entity_pos = target_pos
                second_entity_name = source_entity.name.lower()
            elif target_pos == -1:
                first_entity_pos = source_pos
                second_entity_name = target_entity.name.lower()
            else:
                # Both entities found, use the first one
                if source_pos < target_pos:
                    first_entity_pos = source_pos
                    second_entity_name = target_entity.name.lower()
                else:
                    first_entity_pos = target_pos
                    second_entity_name = source_entity.name.lower()
            
            # Look for the second entity in the next 200 characters
            context_end = min(first_entity_pos + 200, len(segment.text))
            context = segment.text[first_entity_pos:context_end].lower()
            
            if second_entity_name in context:
                # Found a span with both entities
                second_entity_pos = context.find(second_entity_name)
                span_start = first_entity_pos
                span_end = first_entity_pos + second_entity_pos + len(second_entity_name)
                
                # Expand the span to include a full sentence
                span_start = max(0, self._find_sentence_start(segment.text, span_start))
                span_end = min(len(segment.text), self._find_sentence_end(segment.text, span_end))
                
                found_spans.append((span_start, span_end))
            
            # Move past this occurrence
            start_pos = first_entity_pos + 1
        
        if found_spans:
            # Use the shortest span that contains both entities
            best_span = min(found_spans, key=lambda span: span[1] - span[0])
            
            # Create a new source span
            source_span = SourceSpan(
                document_id=segment.document_id,
                segment_id=str(segment.id),
                start=best_span[0],
                end=best_span[1],
                text=segment.text[best_span[0]:best_span[1]]
            )
            return True, source_span
        
        return False, None
    
    def ground_entities(self, entities: List[Entity], 
                      collection: SegmentCollection) -> List[Entity]:
        """Ground a list of entities to their source text.
        
        Args:
            entities: List of entities to ground
            collection: Segment collection to search in
            
        Returns:
            List of grounded entities
        """
        grounded_entities = []
        
        for entity in entities:
            if not entity.source_span or not entity.source_span.segment_id:
                # Entity has no source span, skip it
                logger.warning(f"Entity {entity.name} has no source span, skipping")
                continue
            
            # Get the segment containing this entity
            segment_id = UUID(entity.source_span.segment_id)
            segment = collection.get_segment(segment_id)
            
            if not segment:
                # Segment not found, skip this entity
                logger.warning(f"Segment {segment_id} not found for entity {entity.name}")
                continue
            
            # Ground the entity
            is_grounded, updated_span = self.ground_entity(entity, segment)
            
            if is_grounded:
                if updated_span and updated_span != entity.source_span:
                    # Update the source span
                    entity.source_span = updated_span
                
                grounded_entities.append(entity)
            else:
                logger.warning(f"Entity {entity.name} could not be grounded in segment {segment_id}")
        
        logger.info(f"Grounded {len(grounded_entities)}/{len(entities)} entities")
        return grounded_entities
    
    def ground_relationships(self, relationships: List[Relationship],
                          entities: Dict[UUID, Entity],
                          collection: SegmentCollection) -> List[Relationship]:
        """Ground a list of relationships to their source text.
        
        Args:
            relationships: List of relationships to ground
            entities: Dictionary of entities keyed by ID
            collection: Segment collection to search in
            
        Returns:
            List of grounded relationships
        """
        grounded_relationships = []
        
        for relationship in relationships:
            if not relationship.source_span or not relationship.source_span.segment_id:
                # Relationship has no source span, skip it
                logger.warning(f"Relationship {relationship.type} has no source span, skipping")
                continue
            
            # Get the source and target entities
            source_entity = entities.get(relationship.source_id)
            target_entity = entities.get(relationship.target_id)
            
            if not source_entity or not target_entity:
                # Entities not found, skip this relationship
                logger.warning(f"Entities not found for relationship {relationship.type}")
                continue
            
            # Get the segment containing this relationship
            segment_id = UUID(relationship.source_span.segment_id)
            segment = collection.get_segment(segment_id)
            
            if not segment:
                # Segment not found, skip this relationship
                logger.warning(f"Segment {segment_id} not found for relationship {relationship.type}")
                continue
            
            # Ground the relationship
            is_grounded, updated_span = self.ground_relationship(
                relationship, segment, source_entity, target_entity
            )
            
            if is_grounded:
                if updated_span and updated_span != relationship.source_span:
                    # Update the source span
                    relationship.source_span = updated_span
                
                grounded_relationships.append(relationship)
            else:
                logger.warning(f"Relationship {relationship.type} between {source_entity.name} and {target_entity.name} could not be grounded")
        
        logger.info(f"Grounded {len(grounded_relationships)}/{len(relationships)} relationships")
        return grounded_relationships
    
    def _verify_span(self, span: SourceSpan, text: str) -> bool:
        """Verify that a source span is valid in the given text.
        
        Args:
            span: Source span to verify
            text: Text to verify against
            
        Returns:
            True if the span is valid
        """
        # Check if the span is within the text bounds
        if span.start < 0 or span.end > len(text):
            return False
        
        # Check if the span text matches the text at the span location
        span_text = text[span.start:span.end]
        
        if self.exact_match:
            return span_text == span.text
        else:
            # Use a simple fuzzy match: check if the span text is
            # contained in the text at the span location, or vice versa
            span_text_lower = span_text.lower()
            span_original_lower = span.text.lower()
            
            return (span_text_lower in span_original_lower or
                   span_original_lower in span_text_lower)
    
    def _find_in_text(self, text_to_find: str, text: str) -> Optional[Tuple[int, int]]:
        """Find a piece of text within a larger text.
        
        Args:
            text_to_find: Text to find
            text: Text to search in
            
        Returns:
            (start, end) tuple or None if not found
        """
        # Case-insensitive search
        text_lower = text.lower()
        find_lower = text_to_find.lower()
        
        pos = text_lower.find(find_lower)
        if pos != -1:
            return (pos, pos + len(text_to_find))
        
        # If exact match not found and fuzzy matching is enabled,
        # implement more sophisticated matching here
        
        return None
    
    def _find_sentence_start(self, text: str, pos: int) -> int:
        """Find the start of the sentence containing the given position.
        
        Args:
            text: Text to search in
            pos: Position to start from
            
        Returns:
            Start position of the sentence
        """
        # Look backward for sentence-ending punctuation
        for i in range(pos, 0, -1):
            if text[i-1] in '.!?' and (i == 1 or text[i-2] != '.'):
                # Check if this is actually the end of a sentence
                # (e.g., not part of an ellipsis or abbreviation)
                return i
        
        # If no sentence boundary found, return the beginning of the text
        return 0
    
    def _find_sentence_end(self, text: str, pos: int) -> int:
        """Find the end of the sentence containing the given position.
        
        Args:
            text: Text to search in
            pos: Position to start from
            
        Returns:
            End position of the sentence
        """
        # Look forward for sentence-ending punctuation
        for i in range(pos, len(text)):
            if text[i] in '.!?' and (i == len(text) - 1 or text[i+1] != '.'):
                # Check if this is actually the end of a sentence
                # (e.g., not part of an ellipsis or abbreviation)
                return i + 1
        
        # If no sentence boundary found, return the end of the text
        return len(text)