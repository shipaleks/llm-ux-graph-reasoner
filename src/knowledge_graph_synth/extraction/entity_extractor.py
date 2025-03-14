"""Entity extraction for the knowledge graph synthesis system."""

import logging
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID, uuid4

import asyncio

from ..config import settings
from ..models import TextSegment, SegmentCollection, Entity, SourceSpan
from ..llm import LLMProviderFactory, prompt_manager, ResponseValidator
from ..llm.schemas import get_entity_extraction_schema, get_entity_analysis_schema

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extracts entities from text segments.
    
    This class implements entity extraction using LLMs, with support for
    verifying entities against source text and handling multiple languages.
    """
    
    def __init__(self, 
               provider_name: Optional[str] = None,
               confidence_threshold: float = settings.DEFAULT_CONFIDENCE_THRESHOLD):
        """Initialize the entity extractor.
        
        Args:
            provider_name: Name of the LLM provider to use
            confidence_threshold: Minimum confidence score for entities
        """
        self.provider_name = provider_name
        self.confidence_threshold = confidence_threshold
        self.validator = ResponseValidator()
    
    async def extract_from_segment(self, segment: TextSegment) -> List[Entity]:
        """Extract entities from a single text segment.
        
        Args:
            segment: Text segment to process
            
        Returns:
            List of extracted entities
        """
        # Get the LLM provider
        try:
            provider = LLMProviderFactory.get_provider(self.provider_name)
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
        
        # Get the appropriate prompt template for the segment's language
        language = segment.language or "en"
        schema = get_entity_extraction_schema()
        
        prompt = prompt_manager.format_prompt(
            "entity_extraction",
            language,
            text=segment.text,
            schema=schema
        )
        
        if not prompt:
            logger.error(f"Error getting prompt template for entity extraction ({language})")
            return []
        
        # Extract entities using the LLM
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
            
            valid_source, source_errors = self.validator.validate_entity_source_spans(
                response, segment.text
            )
            if not valid_source:
                for error in source_errors:
                    logger.warning(f"Source validation error: {error}")
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return []
        
        # Convert response to Entity objects
        entities = []
        
        for entity_data in response.get("entities", []):
            # Skip entities below confidence threshold
            confidence = entity_data.get("confidence", 0.0)
            if confidence < self.confidence_threshold:
                continue
            
            # Create source span
            source_span_data = entity_data.get("source_span", {})
            source_span = SourceSpan(
                document_id=segment.document_id,
                segment_id=str(segment.id),
                start=source_span_data.get("start", 0),
                end=source_span_data.get("end", 0),
                text=source_span_data.get("text", "")
            )
            
            # Create entity
            entity = Entity(
                name=entity_data.get("name", "Unknown"),
                type=entity_data.get("type", "unknown"),
                confidence=confidence,
                source_span=source_span
            )
            
            # Add attributes
            for attr in entity_data.get("attributes", []):
                entity.add_attribute(
                    attr.get("key", "unknown"),
                    attr.get("value", ""),
                    attr.get("confidence", 1.0)
                )
            
            entities.append(entity)
        
        return entities
    
    async def extract_from_mega_batch(self, segments: List[TextSegment]) -> List[Entity]:
        """Extract entities from a super large batch of segments using a single LLM call.
        
        This method leverages the massive context window of Gemini models (up to 1M tokens)
        to process hundreds of segments in a single call, dramatically reducing API calls
        and avoiding rate limits.
        
        Args:
            segments: List of text segments to process in a single mega batch
            
        Returns:
            List of extracted entities
        """
        if not segments:
            return []
            
        # Create a schema for the mega batch extraction
        batch_schema = {
            "type": "object",
            "properties": {
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "segment_id": {"type": "string"},
                            "entities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "type": {"type": "string"},
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
                                    "required": ["name", "type", "confidence", "source_span"]
                                }
                            }
                        },
                        "required": ["segment_id", "entities"]
                    }
                }
            },
            "required": ["segments"]
        }
        
        # Get language (assuming all segments in a batch have the same language)
        language = segments[0].language or "en"
        
        # Build the instruction part of the prompt
        system_instruction = """
You are an entity extraction expert with the ability to process large amounts of text efficiently.
Your task is to extract all named entities, concepts, and other important elements from multiple text segments.

If the text appears to be a transcript of a conversation (contains signs of dialogue, speech, interview), pay special attention to:
- Names of people and organizations mentioned
- Products and services (e.g., "Yandex search", "application", "service")
- Technologies and product features
- Key concepts from the topics being discussed
- Questions and issues discussed by the conversation participants

For EACH segment, identify ALL entities and categorize them appropriately.
Provide the following information for each entity:
1. Name - use the normalized/canonical form
2. Type - person, organization, location, date, time, concept, technology, product, service, feature, etc.
3. Confidence score - between 0.0-1.0
4. Source span - exact start/end position in the text and the exact text that matches
5. Relevant attributes - when applicable

VERY IMPORTANT:
- Process each segment independently
- Be precise with position indexes - they must exactly match the source text
- Maintain all entity mentions in their original language (don't translate)
- Return complete results for all segments
- Use the segment_id as provided for each segment to maintain traceability
- Focus particularly on organizations, people, products, services, technologies, and key concepts
- For transcript segments, extract entities that relate to the topics being discussed
"""
        
        # Get the LLM provider
        try:
            provider = LLMProviderFactory.get_provider(self.provider_name)
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
        
        # Create segment data - format as efficiently as possible
        segments_text = "# SEGMENTS TO PROCESS\n\n"
        
        # Create a compact representation of the segments to maximize context usage
        for i, segment in enumerate(segments):
            segments_text += f"SEGMENT {i+1} [ID: {segment.id}]\n{segment.text}\n\n"
            
        # Split the mega batch if it grows too large
        # This is a safety measure in case the text is still too large
        if len(segments_text) > settings.LLM_CONTEXT_WINDOW_SIZE / 2:  # Use half of the context window for safety
            logger.warning(f"Mega batch too large ({len(segments_text)} chars), splitting")
            mid = len(segments) // 2
            first_half = await self.extract_from_mega_batch(segments[:mid])
            second_half = await self.extract_from_mega_batch(segments[mid:])
            return first_half + second_half
        
        # Create the full prompt
        prompt = f"{system_instruction}\n\n{segments_text}"
        
        # Log the size of the request
        logger.info(f"Processing mega batch with {len(segments)} segments ({len(prompt)} chars)")
        
        # Extract entities using the LLM
        try:
            # Use the model with the largest context window and best reasoning
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
            all_entities = []
            
            # Map segment IDs to segments
            segment_map = {str(segment.id): segment for segment in segments}
            
            # Process each segment's results
            if "segments" in response:
                for segment_data in response["segments"]:
                    segment_id = segment_data.get("segment_id")
                    if segment_id in segment_map:
                        segment = segment_map[segment_id]
                        
                        # Process entities
                        for entity_data in segment_data.get("entities", []):
                            # Skip entities below confidence threshold
                            confidence = entity_data.get("confidence", 0.0)
                            if confidence < self.confidence_threshold:
                                continue
                                
                            # Create source span
                            source_span_data = entity_data.get("source_span", {})
                            source_span = SourceSpan(
                                document_id=segment.document_id,
                                segment_id=str(segment.id),
                                start=source_span_data.get("start", 0),
                                end=source_span_data.get("end", 0),
                                text=source_span_data.get("text", "")
                            )
                            
                            # Create entity
                            entity = Entity(
                                name=entity_data.get("name", "Unknown"),
                                type=entity_data.get("type", "unknown"),
                                confidence=confidence,
                                source_span=source_span
                            )
                            
                            # Add attributes
                            for attr in entity_data.get("attributes", []):
                                entity.add_attribute(
                                    attr.get("key", "unknown"),
                                    attr.get("value", ""),
                                    attr.get("confidence", 1.0)
                                )
                                
                            all_entities.append(entity)
            
            logger.info(f"Extracted {len(all_entities)} entities from mega batch")
            return all_entities
            
        except Exception as e:
            logger.error(f"Error extracting entities from mega batch: {str(e)}")
            
            # If mega batch fails, split it and try again
            if len(segments) > 1:
                logger.info(f"Splitting mega batch into smaller batches")
                mid = len(segments) // 2
                first_half = await self.extract_from_mega_batch(segments[:mid])
                
                # Add extra delay before processing second half
                await asyncio.sleep(settings.LLM_DELAY_BETWEEN_REQUESTS * 2)
                
                second_half = await self.extract_from_mega_batch(segments[mid:])
                return first_half + second_half
            else:
                # For single segments, try the regular extraction
                logger.info(f"Falling back to individual segment extraction")
                return await self.extract_from_batch(segments)
    
    async def extract_from_batch(self, segments: List[TextSegment]) -> List[Entity]:
        """Extract entities from a batch of segments using a single LLM call.
        
        Args:
            segments: List of text segments to process in a single batch
            
        Returns:
            List of extracted entities
        """
        if not segments:
            return []
            
        # Create a schema for batch extraction with multiple segments
        batch_schema = {
            "type": "object",
            "properties": {
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "segment_id": {"type": "string"},
                            "entities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "type": {"type": "string"},
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
                                    "required": ["name", "type", "confidence", "source_span"]
                                }
                            }
                        },
                        "required": ["segment_id", "entities"]
                    }
                }
            },
            "required": ["segments"]
        }
        
        # Get language (assuming all segments in a batch have the same language)
        language = segments[0].language or "en"
        
        # Build a batch prompt that includes all segments
        segments_text = ""
        for i, segment in enumerate(segments):
            segments_text += f"SEGMENT {i+1} [ID: {segment.id}]:\n{segment.text}\n\n"
            
        # Get the LLM provider
        try:
            provider = LLMProviderFactory.get_provider(self.provider_name)
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
        
        # Create a prompt for batch extraction
        prompt = f"""
You are an expert entity extractor. Extract all entities from the following text segments.
For each segment, identify all named entities and concepts, classifying them appropriately.

If any segment appears to be a transcript of a conversation (contains signs of dialogue, speech, interview), pay special attention to:
- Names of people and organizations mentioned
- Products and services (e.g., "Yandex search", "application", "service")
- Technologies and product features
- Key concepts from the topics being discussed
- Questions and issues discussed by the conversation participants

For each entity found, include:
1. The entity name (normalized form)
2. The entity type (person, organization, location, date, time, concept, product, service, technology, feature, etc.)
3. A confidence score (0.0-1.0)
4. The source span (start and end positions in the text, and the exact text)
5. Any relevant attributes of the entity

The segments are delimited clearly. Process each segment independently, but return all results in a single structured response.

{segments_text}

Return the results as a structured JSON object with a "segments" array containing the entities for each segment.
Be precise about the source spans - they must match the exact text positions.
"""
        
        # Extract entities using the LLM
        try:
            # Use reasoning model for better extraction
            model_name = "reasoning"
            
            # Extract entities
            response = await provider.generate_structured(
                prompt,
                batch_schema,
                model_name
            )
            
            # Process the response
            all_entities = []
            
            # Map segment IDs to segments
            segment_map = {str(segment.id): segment for segment in segments}
            
            # Process each segment's results
            if "segments" in response:
                for segment_data in response["segments"]:
                    segment_id = segment_data.get("segment_id")
                    if segment_id in segment_map:
                        segment = segment_map[segment_id]
                        
                        # Process entities
                        for entity_data in segment_data.get("entities", []):
                            # Skip entities below confidence threshold
                            confidence = entity_data.get("confidence", 0.0)
                            if confidence < self.confidence_threshold:
                                continue
                                
                            # Create source span
                            source_span_data = entity_data.get("source_span", {})
                            source_span = SourceSpan(
                                document_id=segment.document_id,
                                segment_id=str(segment.id),
                                start=source_span_data.get("start", 0),
                                end=source_span_data.get("end", 0),
                                text=source_span_data.get("text", "")
                            )
                            
                            # Create entity
                            entity = Entity(
                                name=entity_data.get("name", "Unknown"),
                                type=entity_data.get("type", "unknown"),
                                confidence=confidence,
                                source_span=source_span
                            )
                            
                            # Add attributes
                            for attr in entity_data.get("attributes", []):
                                entity.add_attribute(
                                    attr.get("key", "unknown"),
                                    attr.get("value", ""),
                                    attr.get("confidence", 1.0)
                                )
                                
                            all_entities.append(entity)
            
            return all_entities
            
        except Exception as e:
            logger.error(f"Error extracting entities from batch: {str(e)}")
            # If batch extraction fails, fall back to individual segment extraction
            logger.info("Falling back to individual segment extraction")
            
            # Process each segment individually with a delay
            all_entities = []
            for segment in segments:
                try:
                    await asyncio.sleep(settings.LLM_DELAY_BETWEEN_REQUESTS)
                    entities = await self.extract_from_segment(segment)
                    all_entities.extend(entities)
                except Exception as seg_error:
                    logger.error(f"Error extracting entities from segment {segment.id}: {str(seg_error)}")
            
            return all_entities
    
    async def extract_from_collection(self, collection: SegmentCollection, 
                               save_intermediate: bool = True,
                               output_dir: str = "output/entities") -> List[Entity]:
        """Extract entities from a collection of text segments.
        
        Args:
            collection: Segment collection to process
            save_intermediate: Whether to save intermediate results
            output_dir: Directory to save intermediate results
            
        Returns:
            List of extracted entities
        """
        import os
        import json
        from pathlib import Path
        
        all_entities = []
        
        # Create intermediate results directory
        if save_intermediate:
            os.makedirs(output_dir, exist_ok=True)
        
        # Get leaf segments (those without children)
        leaf_segments = [
            segment for segment in collection.segments.values()
            if not segment.child_ids
        ]
        
        # Try mega batch processing first (maximum efficiency with massive context window)
        try:
            logger.info(f"Attempting mega batch processing of {len(leaf_segments)} segments")
            
            # Process in mega batches to maximize context window usage
            mega_batch_size = settings.LLM_MEGA_BATCH_SIZE
            
            # Create a list of mega batches
            mega_batches = []
            for i in range(0, len(leaf_segments), mega_batch_size):
                batch = leaf_segments[i:i+mega_batch_size]
                mega_batches.append(batch)
            
            logger.info(f"Created {len(mega_batches)} mega batches with up to {mega_batch_size} segments each")
            
            # Process each mega batch sequentially (to avoid API rate limits)
            for batch_idx, batch in enumerate(mega_batches):
                logger.info(f"Processing mega batch {batch_idx+1}/{len(mega_batches)} with {len(batch)} segments")
                
                # Add delay between mega batches to avoid rate limiting
                if batch_idx > 0:
                    wait_time = settings.LLM_DELAY_BETWEEN_REQUESTS * 2
                    logger.info(f"Waiting {wait_time} seconds before processing next mega batch...")
                    await asyncio.sleep(wait_time)
                
                # Process the mega batch
                mega_batch_entities = await self.extract_from_mega_batch(batch)
                all_entities.extend(mega_batch_entities)
                
                # Save mega batch results
                if save_intermediate and mega_batch_entities:
                    batch_start = batch_idx * mega_batch_size
                    batch_end = min(batch_start + mega_batch_size, len(leaf_segments))
                    batch_file = Path(output_dir) / f"mega_batch_{batch_start}_{batch_end}.json"
                    
                    with open(batch_file, "w", encoding="utf-8") as f:
                        entities_json = [entity.to_dict() for entity in mega_batch_entities]
                        json.dump(entities_json, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Processed {batch_end}/{len(leaf_segments)} segments total")
                
            logger.info(f"Mega batch processing complete. Extracted {len(all_entities)} entities.")
            
        except Exception as mega_error:
            logger.error(f"Mega batch processing failed: {str(mega_error)}")
            logger.info("Falling back to standard batch processing")
            
            # Fall back to standard batch processing
            parallel_batch_size = 3  # Lower concurrent tasks 
            batch_size = settings.LLM_BATCH_SIZE
            
            # Group segments into batches for efficient processing
            segment_batches = []
            for i in range(0, len(leaf_segments), batch_size):
                batch = leaf_segments[i:i+batch_size]
                segment_batches.append(batch)
            
            # Process batches with limited parallelism
            for i in range(0, len(segment_batches), parallel_batch_size):
                current_batches = segment_batches[i:i+parallel_batch_size]
                
                # Process batches in parallel
                tasks = []
                for batch in current_batches:
                    # Add delay between tasks to avoid rate limiting
                    await asyncio.sleep(settings.LLM_DELAY_BETWEEN_REQUESTS)
                    tasks.append(self.extract_from_batch(batch))
                
                batch_results = await asyncio.gather(*tasks)
                
                # Process results from each batch
                batch_entities = []
                for batch_idx, entities in enumerate(batch_results):
                    batch_entities.extend(entities)
                    
                    # Save batch results
                    if save_intermediate and entities:
                        batch_num = i + batch_idx
                        batch_start = batch_num * batch_size
                        batch_end = min(batch_start + batch_size, len(leaf_segments))
                        import os
                        batch_file = os.path.join(output_dir, f"batch_{batch_start}_{batch_end}.json")
                        
                        with open(batch_file, "w", encoding="utf-8") as f:
                            entities_json = [entity.to_dict() for entity in entities]
                            json.dump(entities_json, f, ensure_ascii=False, indent=2)
                
                all_entities.extend(batch_entities)
                processed_count = min((i + parallel_batch_size) * batch_size, len(leaf_segments))
                logger.info(f"Processed {processed_count}/{len(leaf_segments)} segments")
        
        # Save complete results
        if save_intermediate:
            all_file = os.path.join(output_dir, "all_entities.json")
            with open(all_file, "w", encoding="utf-8") as f:
                entities_json = [entity.to_dict() for entity in all_entities]
                json.dump(entities_json, f, ensure_ascii=False, indent=2)
        
        return all_entities
    
    async def analyze_entity(self, entity: Entity, 
                          segment: TextSegment) -> Dict[str, Any]:
        """Perform detailed analysis of an entity.
        
        Args:
            entity: Entity to analyze
            segment: Text segment containing the entity
            
        Returns:
            Detailed analysis of the entity
        """
        # Get the LLM provider
        try:
            # Use reasoning provider for detailed analysis
            provider = LLMProviderFactory.get_reasoning_provider()
        except Exception:
            provider = LLMProviderFactory.get_provider(self.provider_name)
        
        if not provider:
            logger.error("No LLM provider available for entity analysis")
            return {}
        
        # Get the analysis schema
        schema = get_entity_analysis_schema()
        
        # Prepare the prompt
        language = segment.language or "en"
        prompt = f"""
Analyze the following entity found in the text:

Entity: {entity.name}
Type: {entity.type}
Context: {entity.source_span.text}

Full text context:
{segment.text}

Provide a detailed analysis of this entity, including:
1. Comprehensive description based on all mentions in the text
2. All attributes and properties with supporting evidence
3. All locations in the text where it's mentioned (source spans)
4. Any alternative names or aliases
5. Assessment of its relevance in the text

Ensure all information is strictly derived from the text and properly evidenced.
"""
        
        # Generate the analysis
        try:
            response = await provider.generate_structured(
                prompt,
                schema,
                "reasoning" if hasattr(provider, "get_model") and "reasoning" in provider.models else "default"
            )
            
            return response.get("entity", {})
        except Exception as e:
            logger.error(f"Error analyzing entity: {str(e)}")
            return {}