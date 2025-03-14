"""Relationship extraction for the knowledge graph synthesis system."""

import logging
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID, uuid4

import asyncio

from ..config import settings
from ..models import TextSegment, SegmentCollection, Entity, Relationship, SourceSpan
from ..llm import LLMProviderFactory, prompt_manager, ResponseValidator
from ..llm.schemas import get_relationship_extraction_schema, get_relationship_analysis_schema

logger = logging.getLogger(__name__)


class RelationshipExtractor:
    """Extracts relationships between entities from text segments.
    
    This class implements relationship extraction using LLMs, with support for
    verifying relationships against source text and handling multiple languages.
    """
    
    def __init__(self, 
               provider_name: Optional[str] = None,
               confidence_threshold: float = settings.DEFAULT_CONFIDENCE_THRESHOLD):
        """Initialize the relationship extractor.
        
        Args:
            provider_name: Name of the LLM provider to use
            confidence_threshold: Minimum confidence score for relationships
        """
        self.provider_name = provider_name
        self.confidence_threshold = confidence_threshold
        self.validator = ResponseValidator()
    
    async def extract_from_segment(self, 
                                segment: TextSegment, 
                                entities: List[Entity]) -> List[Relationship]:
        """Extract relationships from a single text segment.
        
        Args:
            segment: Text segment to process
            entities: List of entities to consider for relationships
            
        Returns:
            List of extracted relationships
        """
        if not entities:
            return []
        
        # Get the LLM provider
        try:
            provider = LLMProviderFactory.get_provider(self.provider_name)
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
        
        # Get the appropriate prompt template for the segment's language
        language = segment.language or "en"
        schema = get_relationship_extraction_schema()
        
        # Create a context with entities to help the LLM
        entity_context = "\nEntities found in this text:\n"
        for entity in entities:
            entity_context += f"- {entity.name} (Type: {entity.type})\n"
        
        prompt = prompt_manager.format_prompt(
            "relationship_extraction",
            language,
            text=segment.text + entity_context,
            schema=schema
        )
        
        if not prompt:
            logger.error(f"Error getting prompt template for relationship extraction ({language})")
            return []
        
        # Extract relationships using the LLM
        try:
            response = await provider.generate_structured(
                prompt,
                schema,
                "default"  # Use default model
            )
            
            # Validate the response
            valid_schema, schema_errors = self.validator.validate_schema(response, schema)
            if not valid_schema:
                for error in schema_errors:
                    logger.warning(f"Schema validation error: {error}")
            
            valid_source, source_errors = self.validator.validate_relationship_source_spans(
                response, segment.text
            )
            if not valid_source:
                for error in source_errors:
                    logger.warning(f"Source validation error: {error}")
            
        except Exception as e:
            logger.error(f"Error extracting relationships: {str(e)}")
            return []
        
        # Get entity map for looking up IDs
        entity_map = {(entity.name.lower(), entity.type.lower()): entity.id for entity in entities}
        
        # Convert response to Relationship objects
        relationships = []
        
        for rel_data in response.get("relationships", []):
            # Skip relationships below confidence threshold
            confidence = rel_data.get("confidence", 0.0)
            if confidence < self.confidence_threshold:
                continue
            
            # Get source and target entities
            source_entity = rel_data.get("source", {})
            target_entity = rel_data.get("target", {})
            
            source_name = source_entity.get("name", "").lower()
            source_type = source_entity.get("type", "").lower()
            target_name = target_entity.get("name", "").lower()
            target_type = target_entity.get("type", "").lower()
            
            # Look up entity IDs
            source_id = None
            target_id = None
            
            # Try exact match first
            if (source_name, source_type) in entity_map:
                source_id = entity_map[(source_name, source_type)]
            else:
                # Try name-only match
                for (name, type_), id_ in entity_map.items():
                    if name == source_name:
                        source_id = id_
                        break
            
            if (target_name, target_type) in entity_map:
                target_id = entity_map[(target_name, target_type)]
            else:
                # Try name-only match
                for (name, type_), id_ in entity_map.items():
                    if name == target_name:
                        target_id = id_
                        break
            
            # Skip if we can't find source or target entity
            if not source_id or not target_id:
                logger.warning(f"Skipping relationship: could not find entities {source_name} -> {target_name}")
                continue
            
            # Create source span
            source_span_data = rel_data.get("source_span", {})
            source_span = SourceSpan(
                document_id=segment.document_id,
                segment_id=str(segment.id),
                start=source_span_data.get("start", 0),
                end=source_span_data.get("end", 0),
                text=source_span_data.get("text", "")
            )
            
            # Create relationship
            relationship = Relationship(
                source_id=source_id,
                target_id=target_id,
                type=rel_data.get("type", "unknown"),
                directed=not rel_data.get("bidirectional", False),
                confidence=confidence,
                source_span=source_span
            )
            
            # Add attributes
            for attr in rel_data.get("attributes", []):
                relationship.add_attribute(
                    attr.get("key", "unknown"),
                    attr.get("value", ""),
                    attr.get("confidence", 1.0)
                )
            
            relationships.append(relationship)
        
        return relationships
    
    async def extract_from_batch(self, 
                               segments: List[TextSegment],
                               entities_by_segment: Dict[UUID, List[Entity]]) -> List[Relationship]:
        """Extract relationships from a batch of segments using a single LLM call.
        
        Args:
            segments: List of text segments to process
            entities_by_segment: Dictionary mapping segment IDs to lists of entities
            
        Returns:
            List of extracted relationships
        """
        if not segments:
            return []
        
        # Create a schema for batch relationship extraction
        batch_schema = {
            "type": "object",
            "properties": {
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "segment_id": {"type": "string"},
                            "relationships": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "source": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "type": {"type": "string"}
                                            }
                                        },
                                        "target": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "type": {"type": "string"}
                                            }
                                        },
                                        "bidirectional": {"type": "boolean"},
                                        "confidence": {"type": "number"},
                                        "source_span": {
                                            "type": "object",
                                            "properties": {
                                                "start": {"type": "integer"},
                                                "end": {"type": "integer"},
                                                "text": {"type": "string"}
                                            }
                                        },
                                        "attributes": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "key": {"type": "string"},
                                                    "value": {"type": "string"},
                                                    "confidence": {"type": "number"}
                                                }
                                            }
                                        }
                                    },
                                    "required": ["type", "source", "target", "confidence", "source_span"]
                                }
                            }
                        },
                        "required": ["segment_id", "relationships"]
                    }
                }
            },
            "required": ["segments"]
        }
        
        # Build segments text and entity context
        segments_text = ""
        for i, segment in enumerate(segments):
            # Skip segments without entities or with only one entity
            if segment.id not in entities_by_segment or len(entities_by_segment[segment.id]) < 2:
                continue
                
            segment_entities = entities_by_segment[segment.id]
            
            # Add segment text
            segments_text += f"SEGMENT {i+1} [ID: {segment.id}]:\n{segment.text}\n\n"
            
            # Add entity information
            segments_text += f"Entities in Segment {i+1}:\n"
            for j, entity in enumerate(segment_entities):
                segments_text += f"- Entity {j+1}: {entity.name} (Type: {entity.type})\n"
            
            segments_text += "\n"
        
        # Get language (assuming all segments in a batch have the same language)
        language = segments[0].language or "en"
        
        # Get the LLM provider
        try:
            provider = LLMProviderFactory.get_provider(self.provider_name)
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
        
        # Create batch prompt
        prompt = f"""
You are an expert relationship extractor. Extract all relationships between entities from the following text segments.
For each segment, identify relationships between the listed entities, classifying them appropriately.

For each relationship found, include:
1. The relationship type (a concise label like WORKS_FOR, LOCATED_IN, PART_OF, etc.)
2. The source entity (name and type)
3. The target entity (name and type)
4. Whether the relationship is bidirectional
5. A confidence score (0.0-1.0)
6. The source span (start and end positions in the text, and the exact text that expresses the relationship)
7. Any relevant attributes of the relationship

The segments are delimited clearly. Process each segment independently, but return all results in a single structured response.

{segments_text}

Return the results as a structured JSON object with a "segments" array containing the relationships for each segment.
Be precise about the source spans - they must match the exact text positions.
Only identify relationships that are explicitly stated in the text.
"""
        
        # Extract relationships using the LLM
        try:
            # Use reasoning model for better extraction
            model_name = "reasoning"
            
            # Extract relationships
            response = await provider.generate_structured(
                prompt,
                batch_schema,
                model_name
            )
            
            # Process the response
            all_relationships = []
            
            # Map segment IDs to segments
            segment_map = {str(segment.id): segment for segment in segments}
            
            # Get entity map for looking up IDs
            entity_map = {}
            for segment_id, segment_entities in entities_by_segment.items():
                for entity in segment_entities:
                    key = (entity.name.lower(), entity.type.lower())
                    entity_map[key] = entity.id
            
            # Process each segment's results
            if "segments" in response:
                for segment_data in response["segments"]:
                    segment_id = segment_data.get("segment_id")
                    if segment_id in segment_map:
                        segment = segment_map[segment_id]
                        
                        # Process relationships
                        for rel_data in segment_data.get("relationships", []):
                            # Skip relationships below confidence threshold
                            confidence = rel_data.get("confidence", 0.0)
                            if confidence < self.confidence_threshold:
                                continue
                            
                            # Get source and target entities
                            source_entity = rel_data.get("source", {})
                            target_entity = rel_data.get("target", {})
                            
                            source_name = source_entity.get("name", "").lower()
                            source_type = source_entity.get("type", "").lower()
                            target_name = target_entity.get("name", "").lower()
                            target_type = target_entity.get("type", "").lower()
                            
                            # Look up entity IDs
                            source_id = None
                            target_id = None
                            
                            # Try exact match first
                            if (source_name, source_type) in entity_map:
                                source_id = entity_map[(source_name, source_type)]
                            else:
                                # Try name-only match
                                for (name, type_), id_ in entity_map.items():
                                    if name == source_name:
                                        source_id = id_
                                        break
                            
                            if (target_name, target_type) in entity_map:
                                target_id = entity_map[(target_name, target_type)]
                            else:
                                # Try name-only match
                                for (name, type_), id_ in entity_map.items():
                                    if name == target_name:
                                        target_id = id_
                                        break
                            
                            # Skip if we can't find source or target entity
                            if not source_id or not target_id:
                                logger.warning(f"Skipping relationship: could not find entities {source_name} -> {target_name}")
                                continue
                            
                            # Create source span
                            source_span_data = rel_data.get("source_span", {})
                            source_span = SourceSpan(
                                document_id=segment.document_id,
                                segment_id=str(segment.id),
                                start=source_span_data.get("start", 0),
                                end=source_span_data.get("end", 0),
                                text=source_span_data.get("text", "")
                            )
                            
                            # Create relationship
                            relationship = Relationship(
                                source_id=source_id,
                                target_id=target_id,
                                type=rel_data.get("type", "unknown"),
                                directed=not rel_data.get("bidirectional", False),
                                confidence=confidence,
                                source_span=source_span
                            )
                            
                            # Add attributes
                            for attr in rel_data.get("attributes", []):
                                relationship.add_attribute(
                                    attr.get("key", "unknown"),
                                    attr.get("value", ""),
                                    attr.get("confidence", 1.0)
                                )
                            
                            all_relationships.append(relationship)
            
            return all_relationships
            
        except Exception as e:
            logger.error(f"Error extracting relationships from batch: {str(e)}")
            # If batch extraction fails, fall back to individual segment extraction
            logger.info("Falling back to individual segment extraction")
            
            # Process each segment individually with a delay
            all_relationships = []
            for segment in segments:
                if segment.id in entities_by_segment and len(entities_by_segment[segment.id]) > 1:
                    try:
                        await asyncio.sleep(settings.LLM_DELAY_BETWEEN_REQUESTS)
                        relationships = await self.extract_from_segment(
                            segment, 
                            entities_by_segment[segment.id]
                        )
                        all_relationships.extend(relationships)
                    except Exception as seg_error:
                        logger.error(f"Error extracting relationships from segment {segment.id}: {str(seg_error)}")
            
            return all_relationships
    
    async def extract_from_mega_batch(self,
                                    segments: List[TextSegment],
                                    entities_by_segment: Dict[UUID, List[Entity]]) -> List[Relationship]:
        """Extract relationships from a mega batch of segments using a single LLM call.
        
        This method leverages the massive context window of Gemini models to process
        many segments in one call, dramatically reducing API calls.
        
        Args:
            segments: List of text segments to process
            entities_by_segment: Dictionary mapping segment IDs to lists of entities
            
        Returns:
            List of extracted relationships
        """
        if not segments:
            return []
            
        # Create a schema for mega batch extraction
        batch_schema = {
            "type": "object",
            "properties": {
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "segment_id": {"type": "string"},
                            "relationships": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "source": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "type": {"type": "string"}
                                            }
                                        },
                                        "target": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "type": {"type": "string"}
                                            }
                                        },
                                        "bidirectional": {"type": "boolean"},
                                        "confidence": {"type": "number"},
                                        "source_span": {
                                            "type": "object",
                                            "properties": {
                                                "start": {"type": "integer"},
                                                "end": {"type": "integer"},
                                                "text": {"type": "string"}
                                            }
                                        },
                                        "attributes": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "key": {"type": "string"},
                                                    "value": {"type": "string"},
                                                    "confidence": {"type": "number"}
                                                }
                                            }
                                        }
                                    },
                                    "required": ["type", "source", "target", "confidence", "source_span"]
                                }
                            }
                        },
                        "required": ["segment_id", "relationships"]
                    }
                }
            },
            "required": ["segments"]
        }
        
        # Build system instruction
        system_instruction = """
You are a relationship extraction expert with the ability to process large amounts of text efficiently.
Your task is to identify all relationships between entities in multiple text segments.

For EACH segment, identify ALL relationships between the entities that are listed with each segment.
Provide the following information for each relationship:
1. Type - a concise, descriptive label (e.g., WORKS_FOR, LOCATED_IN, PART_OF, USES, etc.)
2. Source entity - the entity that is the subject of the relationship
3. Target entity - the entity that is the object of the relationship
4. Whether the relationship is bidirectional
5. Confidence score - between 0.0-1.0
6. Source span - exact start/end position in the text and the exact text that expresses the relationship
7. Relevant attributes - when applicable

VERY IMPORTANT:
- Process each segment independently
- Only identify relationships between entities that are explicitly listed for each segment
- Be precise with position indexes - they must exactly match the source text
- Return complete results for all segments
- Use the segment_id as provided for each segment to maintain traceability
"""
        
        # Create segment data - optimized for maximum content in context window
        segments_text = "# SEGMENTS TO PROCESS\n\n"
        
        # Filter segments to only include those with multiple entities
        segments_with_entities = []
        for segment in segments:
            if segment.id in entities_by_segment and len(entities_by_segment[segment.id]) > 1:
                segments_with_entities.append(segment)
        
        # If no segments have multiple entities, return empty list
        if not segments_with_entities:
            return []
        
        # Build compact representation of segments and their entities
        for i, segment in enumerate(segments_with_entities):
            segment_entities = entities_by_segment[segment.id]
            
            segments_text += f"SEGMENT {i+1} [ID: {segment.id}]\n{segment.text}\n\n"
            segments_text += f"Entities in Segment {i+1}:\n"
            
            for j, entity in enumerate(segment_entities):
                segments_text += f"- Entity {j+1}: {entity.name} (Type: {entity.type})\n"
            
            segments_text += "\n"
        
        # Check if mega batch is too large
        if len(segments_text) > settings.LLM_CONTEXT_WINDOW_SIZE / 2:
            logger.warning(f"Mega batch too large ({len(segments_text)} chars), splitting")
            mid = len(segments_with_entities) // 2
            first_half = await self.extract_from_mega_batch(segments_with_entities[:mid], entities_by_segment)
            second_half = await self.extract_from_mega_batch(segments_with_entities[mid:], entities_by_segment)
            return first_half + second_half
        
        # Create full prompt
        prompt = f"{system_instruction}\n\n{segments_text}"
        
        # Log mega batch info
        logger.info(f"Processing mega batch with {len(segments_with_entities)} segments ({len(prompt)} chars)")
        
        # Get the LLM provider
        try:
            provider = LLMProviderFactory.get_provider(self.provider_name)
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
            
        # Extract relationships using the LLM
        try:
            # Use the model with the best reasoning capabilities
            model_name = "reasoning"
            
            # Make the API call
            logger.info(f"Submitting mega batch request to {model_name} model")
            start_time = time.time()
            
            response = await provider.generate_structured(
                prompt,
                batch_schema,
                model_name
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Mega batch processed in {processing_time:.2f} seconds")
            
            # Process the response
            all_relationships = []
            
            # Map segment IDs to segments
            segment_map = {str(segment.id): segment for segment in segments}
            
            # Get entity map for looking up IDs
            entity_map = {}
            for segment_id, segment_entities in entities_by_segment.items():
                for entity in segment_entities:
                    key = (entity.name.lower(), entity.type.lower())
                    entity_map[key] = entity.id
            
            # Process each segment's results
            if "segments" in response:
                for segment_data in response["segments"]:
                    segment_id = segment_data.get("segment_id")
                    if segment_id in segment_map:
                        segment = segment_map[segment_id]
                        
                        # Process relationships
                        for rel_data in segment_data.get("relationships", []):
                            # Skip relationships below confidence threshold
                            confidence = rel_data.get("confidence", 0.0)
                            if confidence < self.confidence_threshold:
                                continue
                            
                            # Get source and target entities
                            source_entity = rel_data.get("source", {})
                            target_entity = rel_data.get("target", {})
                            
                            source_name = source_entity.get("name", "").lower()
                            source_type = source_entity.get("type", "").lower()
                            target_name = target_entity.get("name", "").lower()
                            target_type = target_entity.get("type", "").lower()
                            
                            # Look up entity IDs
                            source_id = None
                            target_id = None
                            
                            # Try exact match first
                            if (source_name, source_type) in entity_map:
                                source_id = entity_map[(source_name, source_type)]
                            else:
                                # Try name-only match
                                for (name, type_), id_ in entity_map.items():
                                    if name == source_name:
                                        source_id = id_
                                        break
                            
                            if (target_name, target_type) in entity_map:
                                target_id = entity_map[(target_name, target_type)]
                            else:
                                # Try name-only match
                                for (name, type_), id_ in entity_map.items():
                                    if name == target_name:
                                        target_id = id_
                                        break
                            
                            # Skip if we can't find source or target entity
                            if not source_id or not target_id:
                                logger.warning(f"Skipping relationship: could not find entities {source_name} -> {target_name}")
                                continue
                            
                            # Create source span
                            source_span_data = rel_data.get("source_span", {})
                            source_span = SourceSpan(
                                document_id=segment.document_id,
                                segment_id=str(segment.id),
                                start=source_span_data.get("start", 0),
                                end=source_span_data.get("end", 0),
                                text=source_span_data.get("text", "")
                            )
                            
                            # Create relationship
                            relationship = Relationship(
                                source_id=source_id,
                                target_id=target_id,
                                type=rel_data.get("type", "unknown"),
                                directed=not rel_data.get("bidirectional", False),
                                confidence=confidence,
                                source_span=source_span
                            )
                            
                            # Add attributes
                            for attr in rel_data.get("attributes", []):
                                relationship.add_attribute(
                                    attr.get("key", "unknown"),
                                    attr.get("value", ""),
                                    attr.get("confidence", 1.0)
                                )
                            
                            all_relationships.append(relationship)
            
            logger.info(f"Extracted {len(all_relationships)} relationships from mega batch")
            return all_relationships
            
        except Exception as e:
            logger.error(f"Error extracting relationships from mega batch: {str(e)}")
            
            # If mega batch fails and we have multiple segments, try splitting the batch
            if len(segments_with_entities) > 1:
                logger.info(f"Splitting mega batch into smaller batches")
                mid = len(segments_with_entities) // 2
                first_half = await self.extract_from_mega_batch(segments_with_entities[:mid], entities_by_segment)
                
                # Add extra delay before processing second half
                await asyncio.sleep(settings.LLM_DELAY_BETWEEN_REQUESTS * 2)
                
                second_half = await self.extract_from_mega_batch(segments_with_entities[mid:], entities_by_segment)
                return first_half + second_half
            
            # Fall back to standard batch processing for individual segments
            logger.info(f"Falling back to standard batch processing")
            relationships = []
            for segment in segments_with_entities:
                await asyncio.sleep(settings.LLM_DELAY_BETWEEN_REQUESTS)
                segment_rels = await self.extract_from_segment(segment, entities_by_segment[segment.id])
                relationships.extend(segment_rels)
            
            return relationships
            
    async def extract_from_collection(self, 
                                    collection: SegmentCollection,
                                    entities: List[Entity],
                                    save_intermediate: bool = True,
                                    output_dir: str = "output/relationships") -> List[Relationship]:
        """Extract relationships from a collection of text segments.
        
        Args:
            collection: Segment collection to process
            entities: List of entities to consider for relationships
            save_intermediate: Whether to save intermediate results
            output_dir: Directory to save intermediate results
            
        Returns:
            List of extracted relationships
        """
        import os
        import json
        from pathlib import Path
        import time
        
        all_relationships = []
        
        # Create intermediate results directory
        if save_intermediate:
            os.makedirs(output_dir, exist_ok=True)
        
        # Get leaf segments (those without children)
        leaf_segments = [
            segment for segment in collection.segments.values()
            if not segment.child_ids
        ]
        
        # Group entities by segment
        entities_by_segment = {}
        for entity in entities:
            if entity.source_span.segment_id:
                segment_id = UUID(entity.source_span.segment_id)
                if segment_id not in entities_by_segment:
                    entities_by_segment[segment_id] = []
                entities_by_segment[segment_id].append(entity)
        
        # Filter segments to only those with multiple entities
        segments_to_process = [
            segment for segment in leaf_segments
            if segment.id in entities_by_segment and len(entities_by_segment[segment.id]) > 1
        ]
        
        logger.info(f"Found {len(segments_to_process)} segments with multiple entities")
        
        # Try mega batch processing first
        try:
            logger.info(f"Attempting mega batch processing for relationships")
            
            # Process in mega batches to maximize context window usage
            mega_batch_size = settings.LLM_MEGA_BATCH_SIZE // 2  # Use smaller batches for relationships
            
            # Create a list of mega batches
            mega_batches = []
            for i in range(0, len(segments_to_process), mega_batch_size):
                batch = segments_to_process[i:i+mega_batch_size]
                mega_batches.append(batch)
            
            logger.info(f"Created {len(mega_batches)} mega batches with up to {mega_batch_size} segments each")
            
            # Process each mega batch sequentially
            for batch_idx, batch in enumerate(mega_batches):
                logger.info(f"Processing relationship mega batch {batch_idx+1}/{len(mega_batches)} with {len(batch)} segments")
                
                # Add delay between mega batches
                if batch_idx > 0:
                    wait_time = settings.LLM_DELAY_BETWEEN_REQUESTS * 3  # Longer delay for relationships
                    logger.info(f"Waiting {wait_time} seconds before processing next mega batch...")
                    await asyncio.sleep(wait_time)
                
                # Process the mega batch
                batch_start_time = time.time()
                mega_batch_rels = await self.extract_from_mega_batch(batch, entities_by_segment)
                all_relationships.extend(mega_batch_rels)
                
                batch_duration = time.time() - batch_start_time
                logger.info(f"Mega batch processing took {batch_duration:.2f} seconds")
                
                # Save mega batch results
                if save_intermediate and mega_batch_rels:
                    batch_start = batch_idx * mega_batch_size
                    batch_end = min(batch_start + mega_batch_size, len(segments_to_process))
                    import os
                    batch_file = os.path.join(output_dir, f"mega_batch_{batch_start}_{batch_end}.json")
                    
                    with open(batch_file, "w", encoding="utf-8") as f:
                        rels_json = [rel.to_dict() for rel in mega_batch_rels]
                        json.dump(rels_json, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Processed {batch_end}/{len(segments_to_process)} segments")
                
            logger.info(f"Mega batch processing complete. Extracted {len(all_relationships)} relationships.")
            
        except Exception as mega_error:
            logger.error(f"Mega batch processing for relationships failed: {str(mega_error)}")
            logger.info("Falling back to standard batch processing")
            
            # Fall back to standard batch processing
            parallel_batch_size = 2  # Fewer concurrent tasks for relationships
            batch_size = settings.LLM_BATCH_SIZE // 2  # Smaller batches
            
            # Group segments into batches
            segment_batches = []
            for i in range(0, len(segments_to_process), batch_size):
                batch = segments_to_process[i:i+batch_size]
                segment_batches.append(batch)
            
            # Process batches with limited parallelism
            for i in range(0, len(segment_batches), parallel_batch_size):
                current_batches = segment_batches[i:i+parallel_batch_size]
                
                # Process batches in parallel
                tasks = []
                for batch in current_batches:
                    # Add delay between tasks
                    await asyncio.sleep(settings.LLM_DELAY_BETWEEN_REQUESTS * 2)
                    tasks.append(self.extract_from_batch(batch, entities_by_segment))
                
                batch_results = await asyncio.gather(*tasks)
                
                # Process results from each batch
                batch_relationships = []
                for batch_idx, relationships in enumerate(batch_results):
                    batch_relationships.extend(relationships)
                    
                    # Save batch results
                    if save_intermediate and relationships:
                        batch_num = i + batch_idx
                        batch_start = batch_num * batch_size
                        batch_end = min(batch_start + batch_size, len(segments_to_process))
                        batch_file = Path(output_dir) / f"batch_{batch_start}_{batch_end}.json"
                        
                        with open(batch_file, "w", encoding="utf-8") as f:
                            rels_json = [rel.to_dict() for rel in relationships]
                            json.dump(rels_json, f, ensure_ascii=False, indent=2)
                
                all_relationships.extend(batch_relationships)
                processed_count = min((i + parallel_batch_size) * batch_size, len(segments_to_process))
                logger.info(f"Processed {processed_count}/{len(segments_to_process)} segments")
        
        # Save complete results
        if save_intermediate:
            import os
            all_file = os.path.join(output_dir, "all_relationships.json")
            with open(all_file, "w", encoding="utf-8") as f:
                rels_json = [rel.to_dict() for rel in all_relationships]
                json.dump(rels_json, f, ensure_ascii=False, indent=2)
        
        return all_relationships
    
    async def analyze_relationship(self, 
                                relationship: Relationship,
                                segment: TextSegment,
                                source_entity: Entity,
                                target_entity: Entity) -> Dict[str, Any]:
        """Perform detailed analysis of a relationship.
        
        Args:
            relationship: Relationship to analyze
            segment: Text segment containing the relationship
            source_entity: Source entity of the relationship
            target_entity: Target entity of the relationship
            
        Returns:
            Detailed analysis of the relationship
        """
        # Get the LLM provider
        try:
            # Use reasoning provider for detailed analysis
            provider = LLMProviderFactory.get_reasoning_provider()
        except Exception:
            provider = LLMProviderFactory.get_provider(self.provider_name)
        
        if not provider:
            logger.error("No LLM provider available for relationship analysis")
            return {}
        
        # Get the analysis schema
        schema = get_relationship_analysis_schema()
        
        # Prepare the prompt
        language = segment.language or "en"
        prompt = f"""
Analyze the following relationship found in the text:

Relationship type: {relationship.type}
Source entity: {source_entity.name} (Type: {source_entity.type})
Target entity: {target_entity.name} (Type: {target_entity.type})
Context: {relationship.source_span.text}

Full text context:
{segment.text}

Provide a detailed analysis of this relationship, including:
1. Comprehensive description based on all mentions in the text
2. All attributes and properties with supporting evidence
3. All locations in the text where it's mentioned (source spans)
4. Temporal aspects (when the relationship occurred, duration, etc.)
5. Assessment of relationship strength or significance
6. Alternative interpretations, if any

Ensure all information is strictly derived from the text and properly evidenced.
"""
        
        # Generate the analysis
        try:
            response = await provider.generate_structured(
                prompt,
                schema,
                "reasoning" if hasattr(provider, "get_model") and "reasoning" in provider.models else "default"
            )
            
            return response.get("relationship", {})
        except Exception as e:
            logger.error(f"Error analyzing relationship: {str(e)}")
            return {}