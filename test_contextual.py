#\!/usr/bin/env python3
"""
Test script for contextual analysis functionality.
"""

import asyncio
import json
import logging
import uuid
from pathlib import Path

from src.knowledge_graph_synth.text.context import ContextManager
from src.knowledge_graph_synth.models.segment import TextSegment, SegmentCollection
from src.knowledge_graph_synth.llm.factory import LLMProviderFactory

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_contextual_analysis():
    """Run a test of the contextual analysis functionality."""
    logger.info("Testing contextual analysis...")
    
    # Create test segments
    segment1 = TextSegment(
        id=uuid.uuid4(),
        text="This is the first test segment for contextual analysis. It contains information about topic A and topic B.",
        start_position=0,
        end_position=100,
        language="en"
    )
    
    segment2 = TextSegment(
        id=uuid.uuid4(),
        text="This is the second test segment that continues discussing topic B and introduces topic C.",
        start_position=101,
        end_position=200,
        language="en"
    )
    
    segment3 = TextSegment(
        id=uuid.uuid4(),
        text="This third segment explores topic C in more detail and relates it back to topic A.",
        start_position=201,
        end_position=300,
        language="en"
    )
    
    # Create a collection
    collection = SegmentCollection()
    collection.add_segment(segment1)
    collection.add_segment(segment2)
    collection.add_segment(segment3)
    
    # Get the provider name (use default if available)
    try:
        available_providers = LLMProviderFactory.list_configured_providers()
        provider_name = available_providers[0] if available_providers else "openai"  # default fallback
    except Exception as e:
        logger.error(f"Error getting provider: {str(e)}")
        provider_name = "openai"  # default fallback
    
    logger.info(f"Using provider: {provider_name}")
    
    # Create a context manager
    context_manager = ContextManager(provider_name=provider_name)
    
    # Test building context
    logger.info("Building context for segment...")
    context = context_manager.build_context(segment2, collection)
    logger.info(f"Context built: {json.dumps(context, indent=2)}")
    
    # Enrich the collection
    logger.info("Enriching segment collection...")
    enriched_collection = await context_manager.enrich_segment_collection(
        collection, 
        language="en",
        analyze_connections=True
    )
    
    # Check the results
    logger.info("Checking results...")
    
    # Print segment summaries
    for segment_id, segment in enriched_collection.segments.items():
        if hasattr(segment, 'metadata') and segment.metadata.get('summary'):
            logger.info(f"Segment {segment_id} summary: {json.dumps(segment.metadata['summary'], indent=2)}")
    
    # Print segment connections
    connections = []
    for segment_id, segment in enriched_collection.segments.items():
        if hasattr(segment, 'metadata') and segment.metadata.get('connections'):
            for conn in segment.metadata['connections']:
                connections.append({
                    'source_id': str(segment_id),
                    'target_id': conn['target_id'],
                    'type': conn['type'],
                    'strength': conn['strength'],
                    'direction': conn['direction']
                })
    
    logger.info(f"Found {len(connections)} connections between segments")
    if connections:
        logger.info(f"Connections: {json.dumps(connections, indent=2)}")
    
    logger.info("Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_contextual_analysis())
