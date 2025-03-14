"""Context preservation for the knowledge graph synthesis system."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from uuid import UUID

from ..models.segment import TextSegment, SegmentCollection
from ..llm import LLMProviderFactory, prompt_manager
from ..llm.schemas.contextual import (
    get_segment_summary_schema,
    get_cross_segment_analysis_schema
)


logger = logging.getLogger(__name__)


class ContextManager:
    """Manages context for text segments.
    
    This class helps maintain context between related text segments, enabling
    better entity resolution and relationship extraction across segment boundaries.
    """
    
    def __init__(self, provider_name: Optional[str] = None, analyze_connections: bool = False):
        """Initialize the context manager.
        
        Args:
            provider_name: Name of the LLM provider to use
            analyze_connections: Whether to analyze connections between segments
        """
        self.provider_name = provider_name
        self.analyze_connections = analyze_connections
        self.segment_summaries = {}
        self.segment_connections = []
        self.segment_texts = {}
    
    def build_context(self, segment: TextSegment, 
                     collection: SegmentCollection,
                     context_size: int = 3) -> Dict[str, Any]:
        """Build context information for a segment.
        
        Args:
            segment: The segment to build context for
            collection: The segment collection
            context_size: Number of surrounding segments to include
            
        Returns:
            Dictionary with context information
        """
        context = {
            "segment_id": str(segment.id),
            "parent": None,
            "siblings": [],
            "previous": [],
            "next": [],
            "children": [],
            "summary": None,
            "connections": []
        }
        
        # Add parent context
        if segment.parent_id:
            parent = collection.get_segment(segment.parent_id)
            if parent:
                context["parent"] = {
                    "id": str(parent.id),
                    "text": parent.text[:200] + "..." if len(parent.text) > 200 else parent.text,
                    "segment_type": parent.metadata.get("segment_type", "unknown")
                }
        
        # Add sibling context
        if segment.parent_id:
            siblings = collection.get_children(segment.parent_id)
            siblings_info = []
            
            for sib in siblings:
                if sib.id == segment.id:
                    continue
                
                # Safely determine position - default to "unknown" if positions are None
                position = "unknown"
                if hasattr(sib, 'start_position') and sib.start_position is not None and hasattr(segment, 'start_position') and segment.start_position is not None:
                    position = "before" if sib.start_position < segment.start_position else "after"
                    
                siblings_info.append({
                    "id": str(sib.id),
                    "text": sib.text[:100] + "..." if len(sib.text) > 100 else sib.text,
                    "position": position
                })
            
            context["siblings"] = siblings_info
        
        # Add previous and next segments
        all_segments = list(collection.segments.values())
        # Safely sort segments, handling None values
        def safe_position_key(s):
            if hasattr(s, 'start_position') and s.start_position is not None:
                return s.start_position
            return -1  # Default value for segments with None position
            
        all_segments.sort(key=safe_position_key)
        
        # Find index of current segment
        current_idx = -1
        for i, seg in enumerate(all_segments):
            if seg.id == segment.id:
                current_idx = i
                break
        
        if current_idx >= 0:
            # Add previous segments
            prev_start = max(0, current_idx - context_size)
            for i in range(prev_start, current_idx):
                prev_seg = all_segments[i]
                context["previous"].append({
                    "id": str(prev_seg.id),
                    "text": prev_seg.text[:100] + "..." if len(prev_seg.text) > 100 else prev_seg.text,
                    "segment_type": prev_seg.metadata.get("segment_type", "unknown")
                })
            
            # Add next segments
            next_end = min(len(all_segments), current_idx + context_size + 1)
            for i in range(current_idx + 1, next_end):
                next_seg = all_segments[i]
                context["next"].append({
                    "id": str(next_seg.id),
                    "text": next_seg.text[:100] + "..." if len(next_seg.text) > 100 else next_seg.text,
                    "segment_type": next_seg.metadata.get("segment_type", "unknown")
                })
        
        # Add children context
        children = collection.get_children(segment.id)
        children_info = []
        
        for child in children:
            children_info.append({
                "id": str(child.id),
                "text": child.text[:100] + "..." if len(child.text) > 100 else child.text,
                "segment_type": child.metadata.get("segment_type", "unknown")
            })
        
        context["children"] = children_info
        
        return context
    
    def generate_summary(self, segment: TextSegment, 
                        collection: SegmentCollection) -> str:
        """Generate a summary of the segment context.
        
        Args:
            segment: The segment to summarize context for
            collection: The segment collection
            
        Returns:
            Text summary of the context
        """
        context = self.build_context(segment, collection)
        
        summary_parts = [
            f"SEGMENT ID: {context['segment_id']}",
            f"SEGMENT TYPE: {segment.metadata.get('segment_type', 'unknown')}",
            f"LANGUAGE: {segment.language}"
        ]
        
        # Add parent information
        if context["parent"]:
            summary_parts.append(f"PARENT: {context['parent']['text']}")
        
        # Add previous segments
        if context["previous"]:
            prev_text = "\n".join([f"- {p['text']}" for p in context["previous"]])
            summary_parts.append(f"PREVIOUS SEGMENTS:\n{prev_text}")
        
        # Add next segments
        if context["next"]:
            next_text = "\n".join([f"- {n['text']}" for n in context["next"]])
            summary_parts.append(f"NEXT SEGMENTS:\n{next_text}")
        
        return "\n\n".join(summary_parts)
    
    def is_continuation(self, segment1: TextSegment, segment2: TextSegment) -> bool:
        """Check if one segment is a continuation of another.
        
        Args:
            segment1: First segment
            segment2: Second segment
            
        Returns:
            True if segment2 continues from segment1
        """
        # Check if they have the same parent
        if segment1.parent_id and segment1.parent_id == segment2.parent_id:
            # Safely check if they are adjacent
            if (hasattr(segment1, 'end_position') and segment1.end_position is not None and 
                hasattr(segment2, 'start_position') and segment2.start_position is not None):
                return segment1.end_position == segment2.start_position
        
        return False
    
    async def generate_segment_summary(self, 
                                    segment: TextSegment, 
                                    collection: SegmentCollection,
                                    language: str = "en") -> Dict[str, Any]:
        """Generate a detailed summary for a segment.
        
        Args:
            segment: The segment to summarize
            collection: The segment collection for context
            language: The language to use for the summary
            
        Returns:
            Summary information
        """
        # Get context for the segment
        context = self.build_context(segment, collection)
        
        # Prepare parent context
        parent_context = ""
        if context["parent"]:
            parent_context = context["parent"]["text"]
        
        # Get the LLM providers - one for structured output, one for thinking
        try:
            # Default provider for structured JSON outputs
            provider = LLMProviderFactory.get_provider(self.provider_name)
            if not provider:
                logger.error("No LLM provider available for segment summarization")
                return {}
                
            # Try to get thinking provider for deeper analysis
            thinking_provider = LLMProviderFactory.get_thinking_provider()
            
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return {}
        
        # Get the schema
        schema = get_segment_summary_schema()
        
        # Use thinking model for preliminary analysis if available
        preliminary_insights = ""
        if thinking_provider:
            try:
                # Create a simpler prompt for free-form thinking
                thinking_prompt = f"""
                Проанализируйте этот текстовый сегмент глубоко и выделите ключевые идеи и концепции.
                Не используйте специальный формат. Дайте глубокий, содержательный анализ.
                
                СЕГМЕНТ ID: {str(segment.id)}
                ТЕКСТ:
                {segment.text}
                
                {parent_context}
                
                Обратите внимание на следующие аспекты:
                1. Главные темы и концепции
                2. Тон и стиль текста
                3. Характеристики контекста и их значение
                4. Отношения между упомянутыми концепциями/идеями
                5. Любые скрытые смыслы или намеки
                """
                
                # Get free-form analysis
                preliminary_insights = await thinking_provider.generate_text(thinking_prompt)
                logger.info(f"Generated preliminary insights for segment {segment.id} using thinking model")
            except Exception as e:
                logger.warning(f"Error generating preliminary analysis: {str(e)}")
        
        # Format the main prompt for structured output
        prompt = prompt_manager.format_prompt(
            "contextual/segment_summarization",
            language,
            segment_text=segment.text,
            segment_id=str(segment.id),
            parent_context=parent_context,
            preliminary_insights=preliminary_insights,
            schema=schema
        )
        
        if not prompt:
            logger.error("Failed to format summarization prompt")
            return {}
        
        # Generate the summary
        try:
            response = await provider.generate_structured(prompt, schema)
            return response.get("summary", {})
        except Exception as e:
            logger.error(f"Error generating segment summary: {str(e)}")
            return {}
    
    async def analyze_segment_connection(self,
                                      segment1: TextSegment,
                                      segment2: TextSegment,
                                      language: str = "en") -> Dict[str, Any]:
        """Analyze the connection between two segments.
        
        Args:
            segment1: First segment
            segment2: Second segment
            language: The language to use for the analysis
            
        Returns:
            Connection information
        """
        # Get the LLM provider
        try:
            provider = LLMProviderFactory.get_provider(self.provider_name)
            if not provider:
                logger.error("No LLM provider available for segment connection analysis")
                return {}
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return {}
        
        # Get the schema
        schema = get_cross_segment_analysis_schema()
        
        # Format the prompt
        prompt = prompt_manager.format_prompt(
            "contextual/cross_segment_analysis",
            language,
            segment1_text=segment1.text,
            segment1_id=str(segment1.id),
            segment2_text=segment2.text,
            segment2_id=str(segment2.id),
            schema=schema
        )
        
        if not prompt:
            logger.error("Failed to format cross-segment analysis prompt")
            return {}
        
        # Generate the analysis
        try:
            response = await provider.generate_structured(prompt, schema)
            return response.get("connection", {})
        except Exception as e:
            logger.error(f"Error analyzing segment connection: {str(e)}")
            return {}
            
    async def enrich_segment_collection(self,
                                     collection: SegmentCollection,
                                     language: str = "en",
                                     analyze_connections: bool = True,
                                     max_segments: int = 5000) -> SegmentCollection:
        # Добавляем отладочную информацию для отслеживания ошибок
        import traceback
        """Enrich a segment collection with summaries and connections.
        
        Args:
            collection: The segment collection to enrich
            language: The language to use
            analyze_connections: Whether to analyze connections between segments
            max_segments: Maximum number of segments to process (to prevent crashes with very large texts)
            
        Returns:
            Enriched segment collection
        """
        try:
            # Generate summaries for all segments
            segment_count = len(collection.segments)
            logger.info(f"Generating summaries for {segment_count} segments")
            
            # Debug output to check segments
            logger.info("Checking segment positions:")
            for seg_id, segment in collection.segments.items():
                logger.debug(f"Segment {seg_id}: start_position={getattr(segment, 'start_position', 'missing')}, end_position={getattr(segment, 'end_position', 'missing')}")
                if not hasattr(segment, 'start_position') or segment.start_position is None or not hasattr(segment, 'end_position') or segment.end_position is None:
                    logger.warning(f"Segment {seg_id} has invalid position information: start_position={getattr(segment, 'start_position', 'missing')}, end_position={getattr(segment, 'end_position', 'missing')}")
            
            # Убеждаемся, что max_segments не None
            max_segments = max_segments or 5000  # Значение по умолчанию, если max_segments is None
            
            # Limit the number of segments to process if there are too many
            if segment_count > max_segments:
                logger.warning(f"Limiting processing to {max_segments} segments (out of {segment_count})")
            
            # Return early if no segments to process
            if segment_count == 0:
                logger.warning("No segments to process")
                return collection
                
            # Process segments in batches to avoid overloading the API
            batch_size = 5
            segment_ids = list(collection.segments.keys())
            
            # Limit the number of segments to process
            segment_ids = segment_ids[:max_segments]
        except Exception as e:
            logger.error(f"Error initializing segment processing: {str(e)}")
            logger.error(traceback.format_exc())
            # Return the original collection
            return collection
        
        for i in range(0, len(segment_ids), batch_size):
            batch_ids = segment_ids[i:i+batch_size]
            tasks = []
            
            # Create tasks for segment summarization
            for segment_id in batch_ids:
                segment = collection.get_segment(segment_id)
                if segment:
                    task = self.generate_segment_summary(segment, collection, language)
                    tasks.append(task)
            
            # Run the tasks concurrently
            batch_summaries = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process the results
            for j, segment_id in enumerate(batch_ids):
                if j < len(batch_summaries):
                    result = batch_summaries[j]
                    if isinstance(result, Exception):
                        logger.error(f"Error generating summary for segment {segment_id}: {str(result)}")
                    else:
                        # Store the summary in the segment's metadata
                        segment = collection.get_segment(segment_id)
                        if segment and result:
                            if "metadata" not in segment.__dict__:
                                segment.metadata = {}
                            segment.metadata["summary"] = result
                            
                            # Store the summary and original text for report generation
                            self.segment_summaries[str(segment_id)] = result
                            self.segment_texts[str(segment_id)] = segment.text
            
            # Log progress
            logger.info(f"Processed {min(i + batch_size, len(segment_ids))}/{len(segment_ids)} segments")
        
        # Analyze connections between segments if requested
        if analyze_connections:
            logger.info("Analyzing connections between segments")
            
            # Find pairs of segments to analyze
            pairs = []
            for i, segment1_id in enumerate(segment_ids):
                segment1 = collection.get_segment(segment1_id)
                if not segment1:
                    continue
                
                # Ensure segment1 has valid positions
                if not hasattr(segment1, 'start_position') or segment1.start_position is None or not hasattr(segment1, 'end_position') or segment1.end_position is None:
                    logger.warning(f"Segment {segment1.id} has invalid position information, skipping")
                    continue
                
                # Look at adjacent segments and siblings
                for j in range(i+1, min(i+3, len(segment_ids))):
                    segment2_id = segment_ids[j]
                    segment2 = collection.get_segment(segment2_id)
                    if not segment2:
                        continue
                    
                    # Ensure segment2 has valid positions
                    if not hasattr(segment2, 'start_position') or segment2.start_position is None or not hasattr(segment2, 'end_position') or segment2.end_position is None:
                        logger.warning(f"Segment {segment2.id} has invalid position information, skipping")
                        continue
                    
                    # Check if they have the same parent or are adjacent
                    if (segment1.parent_id and segment1.parent_id == segment2.parent_id):
                        pairs.append((segment1, segment2))
                    # Safely check positions - double check that they're not None before arithmetic operation
                    elif (segment1.end_position is not None and 
                          segment2.start_position is not None and 
                          abs(segment1.end_position - segment2.start_position) < 100):
                        pairs.append((segment1, segment2))
            
            logger.info(f"Found {len(pairs)} segment pairs to analyze")
            
            # Process pairs in batches
            batch_size = 3
            for i in range(0, len(pairs), batch_size):
                batch_pairs = pairs[i:i+batch_size]
                tasks = []
                
                # Create tasks for connection analysis
                for segment1, segment2 in batch_pairs:
                    task = self.analyze_segment_connection(segment1, segment2, language)
                    tasks.append(task)
                
                # Run the tasks concurrently
                batch_connections = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process the results
                for j, (segment1, segment2) in enumerate(batch_pairs):
                    if j < len(batch_connections):
                        result = batch_connections[j]
                        if isinstance(result, Exception):
                            logger.error(f"Error analyzing connection between segments {segment1.id} and {segment2.id}: {str(result)}")
                        else:
                            # Store the connection in the segments' metadata
                            if result and result.get("has_connection", False):
                                # Store connection in segment1
                                if "metadata" not in segment1.__dict__:
                                    segment1.metadata = {}
                                if "connections" not in segment1.metadata:
                                    segment1.metadata["connections"] = []
                                
                                connection = {
                                    "source_id": str(segment1.id),
                                    "target_id": str(segment2.id),
                                    "type": result.get("connection_type", "unknown"),
                                    "strength": result.get("strength", 0.5),
                                    "direction": result.get("direction", "one-way")
                                }
                                segment1.metadata["connections"].append(connection)
                                
                                # Save connection for report generation
                                self.segment_connections.append(connection)
                                
                                # Store connection in segment2 if bidirectional
                                if result.get("direction", "") == "bidirectional":
                                    if "metadata" not in segment2.__dict__:
                                        segment2.metadata = {}
                                    if "connections" not in segment2.metadata:
                                        segment2.metadata["connections"] = []
                                    
                                    bidirectional_connection = {
                                        "source_id": str(segment2.id),
                                        "target_id": str(segment1.id),
                                        "type": result.get("connection_type", "unknown"),
                                        "strength": result.get("strength", 0.5),
                                        "direction": result.get("direction", "one-way")
                                    }
                                    segment2.metadata["connections"].append(bidirectional_connection)
                                    
                                    # Save bidirectional connection for report generation
                                    self.segment_connections.append(bidirectional_connection)
                
                # Log progress
                logger.info(f"Processed {min(i + batch_size, len(pairs))}/{len(pairs)} segment pairs")
        
        return collection