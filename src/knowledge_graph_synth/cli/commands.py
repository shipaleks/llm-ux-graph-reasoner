"""Command-line interface commands for the knowledge graph synthesis system."""

import argparse
import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import List, Optional

from ..config import settings
from ..text import TextLoader, TextNormalizer, TextSegmenter
from ..llm import LLMProviderFactory
from ..graph import expansion, metagraph, GraphVisualizer

logger = logging.getLogger(__name__)


async def process_command(args: argparse.Namespace):
    """Process a command based on arguments.
    
    Args:
        args: Parsed command-line arguments
    """
    if hasattr(args, "func"):
        await args.func(args)
    else:
        logger.error("No command specified")


async def process_file(args: argparse.Namespace):
    """Process a text file.
    
    Args:
        args: Parsed command-line arguments
    """
    file_path = args.file
    logger.info(f"Processing file: {file_path}")
    
    # Prepare output directory with timestamp
    from .utils import create_timestamped_dir
    import os
    base_output_dir = args.output
    output_dir, timestamp = create_timestamped_dir(base_output_dir)
    logger.info(f"Using timestamped output directory: {output_dir}")
    
    # Store the timestamped directory for other functions to use
    args.output_dir = output_dir
    
    # Load the text
    loader = TextLoader()
    try:
        segments = loader.load(file_path)
        logger.info(f"Loaded {len(segments.segments)} segments from {file_path}")
    except Exception as e:
        logger.error(f"Error loading file: {str(e)}")
        return
    
    # Normalize the text
    normalizer = TextNormalizer()
    normalized_segments = []
    for segment in segments.segments.values():
        normalized_segment = normalizer.normalize(segment)
        normalized_segments.append(normalized_segment)
        segments.add_segment(normalized_segment)
    
    logger.info(f"Normalized {len(normalized_segments)} segments")
    
    # Set custom segmentation parameters if provided
    segment_length = getattr(args, 'segment_length', settings.MAX_SEGMENT_LENGTH)
    segment_overlap = getattr(args, 'segment_overlap', settings.MAX_SEGMENT_OVERLAP)
    
    # Update settings with command line parameters
    settings.LLM_BATCH_SIZE = getattr(args, 'batch_size', settings.LLM_BATCH_SIZE)
    settings.LLM_DELAY_BETWEEN_REQUESTS = getattr(args, 'delay', settings.LLM_DELAY_BETWEEN_REQUESTS)
    
    # Segment the text
    segmenter = TextSegmenter(max_segment_length=segment_length, max_segment_overlap=segment_overlap)
    segmented_collection = segmenter.segment(segments)
    
    # Limit segments if max_segments specified (for testing with large files)
    max_segments = getattr(args, 'max_segments', None)
    gradual_processing = getattr(args, 'gradual', False)
    
    # Get leaf segments
    leaf_segments = [s for s in segmented_collection.segments.values() if not s.child_ids]
    total_segments = len(leaf_segments)
    
    # Process file gradually if specified
    if gradual_processing and not max_segments:
        # Process the file in increasingly larger chunks
        chunk_sizes = [10, 30, 100, 300, 1000, 3000]
        current_segment = 0
        
        for chunk_size in chunk_sizes:
            if current_segment >= total_segments:
                break
                
            # Determine number of segments to process in this chunk
            segments_to_process = min(chunk_size, total_segments - current_segment)
            end_segment = current_segment + segments_to_process
            
            logger.info(f"Processing segments {current_segment} to {end_segment} (chunk size: {segments_to_process})")
            
            # Create a collection with this chunk of segments
            from ..models import SegmentCollection
            chunk_collection = SegmentCollection()
            
            for i, segment in enumerate(leaf_segments):
                if current_segment <= i < end_segment:
                    chunk_collection.add_segment(segment)
            
            # Process this chunk
            await process_segment_collection(args, chunk_collection)
            
            # Update current position
            current_segment = end_segment
            
            # Wait between chunks to avoid API rate limits
            if current_segment < total_segments:
                wait_time = 30  # 30 second wait between chunks
                logger.info(f"Waiting {wait_time} seconds before processing next chunk...")
                await asyncio.sleep(wait_time)
        
        logger.info("Completed gradual processing of all segments")
        return
    
    # Regular processing (with optional max_segments limit)
    elif max_segments and len(leaf_segments) > max_segments:
        logger.info(f"Limiting processing to first {max_segments} segments (out of {total_segments}) for testing")
        # Create a new collection with limited segments
        from ..models import SegmentCollection
        limited_collection = SegmentCollection()
        for i, segment in enumerate(leaf_segments):
            if i < max_segments:
                limited_collection.add_segment(segment)
        segmented_collection = limited_collection
    
    # Process the collection
    await process_segment_collection(args, segmented_collection)
    
    # Display summary of output files
    from .utils import display_output_summary
    display_output_summary(args.output_dir)
    
    logger.info("Processing complete")


async def process_segment_collection(args: argparse.Namespace, segmented_collection):
    """Process a segment collection with entity extraction, graph building, and theory generation.
    
    This function is the core processing pipeline that:
    1. Performs contextual analysis on text segments (if requested)
    2. Analyzes text segments for entities and relationships
    3. Constructs a knowledge graph
    4. Optionally expands the graph recursively
    5. Optionally creates a meta-graph for higher-level insights
    6. Generates theories and hypotheses
    7. Generates a comprehensive HTML research report
    
    Args:
        args: Command-line arguments containing processing options
        segmented_collection: Collection of text segments to process
    """
    # Ensure we have output directory from the caller
    if not hasattr(args, 'output_dir'):
        args.output_dir = args.output
    
    logger.info(f"Segmented into {len(segmented_collection.segments)} segments")
    
    # Test LLM provider if specified
    if args.test_llm:
        try:
            provider = LLMProviderFactory.get_provider(args.provider)
            logger.info(f"Using LLM provider: {provider.name()}")
            
            # Get the first leaf segment for testing
            leaf_segments = [s for s in segmented_collection.segments.values() if not s.child_ids]
            if leaf_segments:
                test_segment = leaf_segments[0]
                response = await provider.generate_text(
                    f"Summarize the following text in one sentence:\n\n{test_segment.text[:1000]}"
                )
                logger.info(f"Test LLM response: {response}")
                
                # Test structured output if available
                try:
                    schema = {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "language": {"type": "string"},
                            "topics": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                    
                    structured_response = await provider.generate_structured(
                        f"Analyze the following text and provide a summary, language detection, and main topics:\n\n{test_segment.text[:1000]}",
                        schema,
                        "reasoning"
                    )
                    
                    logger.info(f"Test structured output: {structured_response}")
                except Exception as struct_error:
                    logger.warning(f"Structured output test failed: {str(struct_error)}")
            
        except Exception as e:
            logger.error(f"Error with LLM provider: {str(e)}")
    
    # Perform contextual analysis if requested
    if getattr(args, 'contextual_analysis', False):
        from ..text.context import ContextManager
        
        logger.info("Performing contextual analysis on segments...")
        
        # Determine if cross-segment analysis should be performed
        analyze_connections = getattr(args, 'analyze_connections', True)
        
        # Create a context manager
        context_manager = ContextManager(provider_name=args.provider, analyze_connections=analyze_connections)
        
        # Get the language from the segments (default to English)
        language = "en"
        for segment in segmented_collection.segments.values():
            if hasattr(segment, 'language') and segment.language:
                language = segment.language
                break
        
        # Verify segments have valid positions, но не удаляем сегменты транскриптов
        for segment_id, segment in list(segmented_collection.segments.items()):
            # Пропускаем проверку позиций для транскриптов (WEBVTT)
            if segment.metadata.get('segment_type') in ('transcript_topic', 'llm_transcript_topic'):
                continue
                
            # Проверяем позиции только для обычных сегментов
            if not hasattr(segment, 'start_position') or segment.start_position is None or not hasattr(segment, 'end_position') or segment.end_position is None:
                logger.warning(f"Removing segment {segment_id} with invalid position information")
                del segmented_collection.segments[segment_id]
        
        # Enrich the segment collection with summaries and connections
        # Use a default max_segments of 5000 to prevent crashes with large texts
        max_segments = getattr(args, 'max_segments', 5000)
        
        try:
            enriched_collection = await context_manager.enrich_segment_collection(
                segmented_collection,
                language=language,
                analyze_connections=analyze_connections,
                max_segments=max_segments
            )
        except Exception as e:
            import traceback
            logger.error(f"Error during contextual analysis: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Continue with the original collection
            enriched_collection = segmented_collection
        
        # Update the collection for subsequent processing
        segmented_collection = enriched_collection
        
        # Save contextual analysis results if intermediate saving is enabled
        save_intermediate = getattr(args, 'save_intermediate', True)
        if save_intermediate:
            import json
            # Use the timestamped directory for saving contextual analysis
            from .utils import get_subdirectory_path
            context_dir = get_subdirectory_path(args.output_dir, "context")
            
            # Save segment summaries
            summaries = {}
            connections = []
            
            for segment_id, segment in segmented_collection.segments.items():
                if hasattr(segment, 'metadata') and segment.metadata.get('summary'):
                    summaries[str(segment_id)] = segment.metadata['summary']
                
                if hasattr(segment, 'metadata') and segment.metadata.get('connections'):
                    for conn in segment.metadata['connections']:
                        connections.append({
                            'source_id': str(segment_id),
                            'target_id': conn['target_id'],
                            'type': conn['type'],
                            'strength': conn['strength'],
                            'direction': conn['direction']
                        })
            
            # Save summaries
            import os
            summaries_path = os.path.join(context_dir, "segment_summaries.json")
            with open(summaries_path, "w", encoding="utf-8") as f:
                json.dump(summaries, f, ensure_ascii=False, indent=2)
            
            # Save connections
            connections_path = os.path.join(context_dir, "segment_connections.json")
            with open(connections_path, "w", encoding="utf-8") as f:
                json.dump(connections, f, ensure_ascii=False, indent=2)
            
            # Save original segment texts
            segment_texts = {}
            for segment_id, segment in segmented_collection.segments.items():
                segment_texts[str(segment_id)] = segment.text
            
            segments_path = os.path.join(context_dir, "segments.json")
            with open(segments_path, "w", encoding="utf-8") as f:
                json.dump(segment_texts, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved contextual analysis results to {context_dir}")
    
    # Extract entities and relationships if requested
    entities = []
    relationships = []
    
    if args.extract:
        from ..extraction import EntityExtractor, RelationshipExtractor, CoreferenceResolver, Grounder
        
        logger.info("Extracting entities and relationships...")
        
        # Set up output directories for intermediate results
        import os
        from .utils import get_subdirectory_path
        entities_dir = get_subdirectory_path(args.output_dir, "entities")
        relationships_dir = get_subdirectory_path(args.output_dir, "relationships")
        save_intermediate = getattr(args, 'save_intermediate', True)
        
        # Extract entities
        entity_extractor = EntityExtractor(provider_name=args.provider)
        entities = await entity_extractor.extract_from_collection(
            segmented_collection,
            save_intermediate=save_intermediate,
            output_dir=str(entities_dir)
        )
        logger.info(f"Extracted {len(entities)} entities")
        
        # Resolve coreferences
        resolver = CoreferenceResolver()
        resolved_entities = resolver.resolve_entities(entities)
        logger.info(f"Resolved {len(entities)} entities into {len(resolved_entities)} unique entities")
        
        # Save resolved entities if intermediate saving is enabled
        if save_intermediate:
            import json
            resolved_path = os.path.join(entities_dir, "resolved_entities.json")
            with open(resolved_path, "w", encoding="utf-8") as f:
                entities_json = [entity.to_dict() for entity in resolved_entities]
                json.dump(entities_json, f, ensure_ascii=False, indent=2)
        
        # Ground entities
        grounder = Grounder()
        grounded_entities = grounder.ground_entities(resolved_entities, segmented_collection)
        logger.info(f"Grounded {len(grounded_entities)} entities")
        
        # Extract relationships
        relationship_extractor = RelationshipExtractor(provider_name=args.provider)
        relationships = await relationship_extractor.extract_from_collection(
            segmented_collection, grounded_entities,
            save_intermediate=save_intermediate,
            output_dir=str(relationships_dir)
        )
        logger.info(f"Extracted {len(relationships)} relationships")
        
        # Ground relationships
        entity_map = {entity.id: entity for entity in grounded_entities}
        grounded_relationships = grounder.ground_relationships(
            relationships, entity_map, segmented_collection
        )
        logger.info(f"Grounded {len(grounded_relationships)} relationships")
        
        # Save grounded relationships if intermediate saving is enabled
        if save_intermediate:
            import json
            grounded_path = os.path.join(relationships_dir, "grounded_relationships.json")
            with open(grounded_path, "w", encoding="utf-8") as f:
                rels_json = [rel.to_dict() for rel in grounded_relationships]
                json.dump(rels_json, f, ensure_ascii=False, indent=2)
        
        # Update entities and relationships
        entities = grounded_entities
        relationships = grounded_relationships
    
    # Build knowledge graph if requested
    graph = None
    
    if args.build_graph and entities:
        from ..graph import GraphBuilder
        import os
        
        logger.info("Building knowledge graph...")
        
        # Build the graph
        builder = GraphBuilder()
        graph = builder.build(entities, relationships)
        logger.info(f"Built graph with {len(graph.entities)} entities and {len(graph.relationships)} relationships")
        
        # Visualize the graph
        from .utils import get_subdirectory_path
        graphs_dir = get_subdirectory_path(args.output_dir, "graphs")
        
        visualizer = GraphVisualizer(output_dir=str(graphs_dir))
        
        # Create HTML visualization with report
        html_path = visualizer.visualize_html(
            graph, 
            filename="knowledge_graph.html",
            title="Knowledge Graph",
            generate_report=True
        )
        
        # Create a filtered version with higher confidence threshold if there are many entities
        if len(graph.entities) > 50:
            visualizer.visualize_html(
                graph, 
                filename="knowledge_graph_filtered.html",
                title="Knowledge Graph (High Confidence)",
                filter_threshold=0.8,
                generate_report=True
            )
            logger.info("Created filtered graph with higher confidence threshold")
        
        logger.info(f"Graph visualization saved to {html_path}")
        logger.info(f"Graph report saved to {graphs_dir}/knowledge_graph_report.md")
    
    # Expand graph if requested
    if args.expand_graph and graph:
        logger.info("Recursively expanding the knowledge graph...")
        
        # Create a graph expander
        graph_expander = expansion.GraphExpander(provider_name=args.provider)
        
        try:
            # Expand the graph
            expanded_graph = await graph_expander.expand_graph(
                graph,
                segmented_collection,
                max_iterations=args.expansion_iterations,
                output_dir=args.output_dir
            )
            
            logger.info(f"Graph expanded successfully with {len(expanded_graph.entities)} entities and {len(expanded_graph.relationships)} relationships")
        except Exception as e:
            logger.error(f"Error expanding graph: {str(e)}")
            logger.warning("Using original graph without expansion")
            expanded_graph = graph
        
        # Update the graph with the expanded one
        graph = expanded_graph
        
        # Update entities and relationships for later use
        entities = list(graph.entities.values())
        relationships = list(graph.relationships.values())
        
        logger.info(f"Graph expanded to {len(graph.entities)} entities and {len(graph.relationships)} relationships")
        
        # Visualize the expanded graph
        from .utils import get_subdirectory_path
        graphs_dir = get_subdirectory_path(args.output_dir, "graphs")
        expanded_graphs_dir = get_subdirectory_path(graphs_dir, "expanded")
        
        visualizer = GraphVisualizer(output_dir=str(expanded_graphs_dir))
        
        # Create HTML visualization with report
        html_path = visualizer.visualize_html(
            graph, 
            filename="expanded_graph.html",
            title="Expanded Knowledge Graph",
            generate_report=True
        )
        
        logger.info(f"Expanded graph visualization saved to {html_path}")
    
    # Build meta-graph if requested
    if args.build_metagraph and graph:
        logger.info("Building meta-graph from knowledge graph...")
        
        # Create a meta-graph builder
        meta_builder = metagraph.MetaGraphBuilder(
            provider_name=args.provider,
            min_cluster_size=args.min_cluster_size
        )
        
        # Build the meta-graph
        meta_graph = await meta_builder.build_metagraph(graph)
        
        # Save the meta-graph
        if len(meta_graph.entities) > 0:
            logger.info(f"Created meta-graph with {len(meta_graph.entities)} meta-concepts and {len(meta_graph.relationships)} meta-relationships")
            
            # Visualize the meta-graph
            from .utils import get_subdirectory_path
            graphs_dir = get_subdirectory_path(args.output_dir, "graphs")
            meta_graphs_dir = get_subdirectory_path(graphs_dir, "meta")
            
            visualizer = GraphVisualizer(output_dir=str(meta_graphs_dir))
            
            # Create HTML visualization with report
            html_path = visualizer.visualize_html(
                meta_graph, 
                filename="meta_graph.html",
                title="Meta-Graph",
                generate_report=True
            )
            
            logger.info(f"Meta-graph visualization saved to {html_path}")
        else:
            logger.warning("No meta-concepts found. Unable to create meta-graph.")
    
    # Generate theories if requested
    if args.generate_theories and graph:
        from ..theory import TheoryGenerator, PatternFinder
        import json
        import os
        
        logger.info("Generating theories...")
        
        # Create theories directory
        from .utils import get_subdirectory_path
        theories_dir = get_subdirectory_path(args.output_dir, "theories")
        
        # Find patterns
        pattern_finder = PatternFinder(provider_name=args.provider)
        patterns = await pattern_finder.find_patterns(graph)
        logger.info(f"Found {len(patterns)} patterns")
        
        # Save patterns if found
        if patterns:
            patterns_path = os.path.join(theories_dir, "patterns.json")
            with open(patterns_path, "w", encoding="utf-8") as f:
                # Patterns are already dictionaries, no need to convert
                json.dump(patterns, f, ensure_ascii=False, indent=2)
            logger.info(f"Patterns saved to {patterns_path}")
        
        # Generate theories
        theory_generator = TheoryGenerator(provider_name=args.provider)
        theories = await theory_generator.generate_theories(
            graph, segmented_collection, max_theories=3
        )
        logger.info(f"Generated {len(theories)} theories")
        
        # Save theories to a file
        theories_json_path = os.path.join(theories_dir, "theories.json")
        with open(theories_json_path, "w", encoding="utf-8") as f:
            # Theories are already dictionaries, no need to convert
            json.dump(theories, f, indent=2, ensure_ascii=False)
        
        # Generate a markdown report for theories
        theories_md_path = os.path.join(theories_dir, "theories.md")
        with open(theories_md_path, "w", encoding="utf-8") as f:
            f.write("# Generated Theories\n\n")
            
            for i, theory in enumerate(theories):
                f.write(f"## Theory {i+1}: {theory.get('name', 'Unnamed Theory')}\n\n")
                f.write(f"**Confidence**: {theory.get('confidence', 0.0):.2f}\n\n")
                f.write(f"**Summary**: {theory.get('description', 'No description')}\n\n")
                
                if 'hypotheses' in theory and theory['hypotheses']:
                    f.write("### Hypotheses\n\n")
                    for j, hypothesis in enumerate(theory['hypotheses']):
                        f.write(f"#### Hypothesis {j+1}: {hypothesis.get('statement', 'No statement')}\n\n")
                        f.write(f"**Confidence**: {hypothesis.get('confidence', 0.0):.2f}\n\n")
                        f.write(f"**Evidence**:\n\n")
                        if 'evidence' in hypothesis and hypothesis['evidence']:
                            for evidence in hypothesis['evidence']:
                                f.write(f"- {evidence.get('description', 'No description')} (Strength: {evidence.get('strength', 0.0):.2f})\n")
                        f.write("\n")
                
                f.write("---\n\n")
        
        logger.info(f"Theories saved to {theories_json_path}")
        logger.info(f"Theories report saved to {theories_md_path}")
    
    # Generate comprehensive HTML research report
    if args.generate_report and graph:
        from ..output.report import ReportGenerator
        import os
        
        logger.info("Generating comprehensive research report...")
        
        # Create the report generator
        report_generator = ReportGenerator()
        
        # Generate the report to the timestamped directory
        from .utils import is_timestamped_dir
        # Always use the timestamped directory - consistency is key
        report_path = os.path.join(args.output_dir, "report.html")
        
        report_generator.generate_report(
            str(report_path),
            graph,
            source_file=args.file,
            output_dir=str(args.output_dir),
            title=f"Knowledge Graph Analysis: {os.path.basename(args.file)}"
        )
        
        # Ensure segment pages are created for the report
        from .fix_segment_links import ensure_segment_pages
        ensure_segment_pages(args.output_dir)
        
        logger.info(f"Comprehensive research report saved to {report_path}")


async def process_file(args: argparse.Namespace):
    """Process a text file with optional gradual processing.
    
    Args:
        args: Parsed command-line arguments
        
    This function has been updated to support:
    - Hierarchical segmentation with custom parameters
    - Contextual analysis for cross-segment understanding
    - Recursive graph expansion for deeper insights
    - Meta-graph creation for higher-level abstractions
    """
    file_path = args.file
    logger.info(f"Processing file: {file_path}")
    
    # Prepare output directory with timestamp
    from .utils import create_timestamped_dir
    import os
    base_output_dir = args.output
    output_dir, timestamp = create_timestamped_dir(base_output_dir)
    logger.info(f"Using timestamped output directory: {output_dir}")
    
    # Store the timestamped directory for other functions to use
    args.output_dir = output_dir
    
    # Load the text
    loader = TextLoader()
    try:
        segments = loader.load(file_path)
        logger.info(f"Loaded {len(segments.segments)} segments from {file_path}")
    except Exception as e:
        logger.error(f"Error loading file: {str(e)}")
        return
    
    # Normalize the text
    normalizer = TextNormalizer()
    normalized_segments = []
    for segment in segments.segments.values():
        normalized_segment = normalizer.normalize(segment)
        normalized_segments.append(normalized_segment)
        segments.add_segment(normalized_segment)
    
    logger.info(f"Normalized {len(normalized_segments)} segments")
    
    # Set custom segmentation parameters if provided
    segment_length = getattr(args, 'segment_length', settings.MAX_SEGMENT_LENGTH)
    segment_overlap = getattr(args, 'segment_overlap', settings.MAX_SEGMENT_OVERLAP)
    
    # Update settings with command line parameters
    settings.LLM_BATCH_SIZE = getattr(args, 'batch_size', settings.LLM_BATCH_SIZE)
    settings.LLM_DELAY_BETWEEN_REQUESTS = getattr(args, 'delay', settings.LLM_DELAY_BETWEEN_REQUESTS)
    
    # Segment the text
    segmenter = TextSegmenter(max_segment_length=segment_length, max_segment_overlap=segment_overlap)
    segmented_collection = segmenter.segment(segments)
    
    # Limit segments if max_segments specified (for testing with large files)
    max_segments = getattr(args, 'max_segments', None)
    gradual_processing = getattr(args, 'gradual', False)
    
    # Get leaf segments
    leaf_segments = [s for s in segmented_collection.segments.values() if not s.child_ids]
    total_segments = len(leaf_segments)
    
    # Process file gradually if specified
    if gradual_processing and not max_segments:
        # Process the file in increasingly larger chunks
        chunk_sizes = [10, 30, 100, 300, 1000, 3000]
        current_segment = 0
        
        for chunk_size in chunk_sizes:
            if current_segment >= total_segments:
                break
                
            # Determine number of segments to process in this chunk
            segments_to_process = min(chunk_size, total_segments - current_segment)
            end_segment = current_segment + segments_to_process
            
            logger.info(f"Processing segments {current_segment} to {end_segment} (chunk size: {segments_to_process})")
            
            # Create a collection with this chunk of segments
            from ..models import SegmentCollection
            chunk_collection = SegmentCollection()
            
            for i, segment in enumerate(leaf_segments):
                if current_segment <= i < end_segment:
                    chunk_collection.add_segment(segment)
            
            # Process this chunk
            await process_segment_collection(args, chunk_collection)
            
            # Update current position
            current_segment = end_segment
            
            # Wait between chunks to avoid API rate limits
            if current_segment < total_segments:
                wait_time = 30  # 30 second wait between chunks
                logger.info(f"Waiting {wait_time} seconds before processing next chunk...")
                await asyncio.sleep(wait_time)
        
        logger.info("Completed gradual processing of all segments")
    
    # Regular processing (with optional max_segments limit)
    elif max_segments and len(leaf_segments) > max_segments:
        logger.info(f"Limiting processing to first {max_segments} segments (out of {total_segments}) for testing")
        # Create a new collection with limited segments
        from ..models import SegmentCollection
        limited_collection = SegmentCollection()
        for i, segment in enumerate(leaf_segments):
            if i < max_segments:
                limited_collection.add_segment(segment)
        segmented_collection = limited_collection
        
        # Process the collection
        await process_segment_collection(args, segmented_collection)
    else:
        # Process the collection
        await process_segment_collection(args, segmented_collection)
    
    # Display summary of output files
    from .utils import display_output_summary
    display_output_summary(args.output_dir)
    
    logger.info("Processing complete")


async def list_providers(args: argparse.Namespace):
    """List available LLM providers.
    
    Args:
        args: Parsed command-line arguments
    """
    logger.info("Available LLM providers:")
    
    available_providers = LLMProviderFactory.list_available_providers()
    configured_providers = LLMProviderFactory.list_configured_providers()
    
    for provider in available_providers:
        status = "Configured" if provider in configured_providers else "Not configured"
        logger.info(f"  - {provider}: {status}")


async def fix_segment_links_cmd(args: argparse.Namespace):
    """Fix segment links in reports.
    
    Args:
        args: Command-line arguments containing the output directory
    """
    from .fix_segment_links import fix_report_segment_links, ensure_segment_pages
    
    logger.info(f"Fixing segment links in directory: {args.output}")
    
    if args.recursive:
        logger.info("Recursively searching for reports...")
        # Walk through all subdirectories
        for root, dirs, files in os.walk(args.output):
            if "report.html" in files:
                logger.info(f"Found report in: {root}")
                # Fix links in this report
                fix_report_segment_links(root)
                # Ensure segment pages exist
                ensure_segment_pages(root)
    else:
        # Fix links in specified directory
        fix_report_segment_links(args.output)
        ensure_segment_pages(args.output)
    
    logger.info("Link fixing completed")


def setup_parser() -> argparse.ArgumentParser:
    """Set up the command-line parser.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Knowledge Graph Synthesis")
    parser.add_argument(
        "--log-level", "-l",
        help=f"Logging level (default: {settings.LOG_LEVEL})",
        default=settings.LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    
    subparsers = parser.add_subparsers(title="commands", dest="command")
    
    # Process file command
    process_parser = subparsers.add_parser("process", help="Process a text file")
    process_parser.add_argument(
        "--file", "-f", 
        help="Path to the text file to process",
        required=True
    )
    process_parser.add_argument(
        "--provider", "-p",
        help=f"LLM provider to use (default: {settings.DEFAULT_LLM_PROVIDER})",
        default=settings.DEFAULT_LLM_PROVIDER
    )
    process_parser.add_argument(
        "--extract", "-e",
        help="Extract entities and relationships",
        action="store_true"
    )
    process_parser.add_argument(
        "--build-graph", "-b",
        help="Build a knowledge graph from extracted entities and relationships",
        action="store_true"
    )
    process_parser.add_argument(
        "--generate-theories", "-g",
        help="Generate theories from the knowledge graph",
        action="store_true"
    )
    process_parser.add_argument(
        "--output", "-o",
        help="Output directory for files (default: output)",
        default="output"
    )
    process_parser.add_argument(
        "--test-llm", "-t",
        help="Test the LLM provider with a sample prompt",
        action="store_true"
    )
    process_parser.add_argument(
        "--save-intermediate", "-s", 
        help="Save intermediate results",
        action="store_true",
        default=True
    )
    process_parser.add_argument(
        "--max-segments", "-m", 
        help="Maximum number of segments to process (for testing with large files)",
        type=int,
        default=None
    )
    process_parser.add_argument(
        "--segment-length",
        help=f"Maximum segment length (default: {settings.MAX_SEGMENT_LENGTH})",
        type=int,
        default=settings.MAX_SEGMENT_LENGTH
    )
    process_parser.add_argument(
        "--segment-overlap",
        help=f"Segment overlap (default: {settings.MAX_SEGMENT_OVERLAP})",
        type=int,
        default=settings.MAX_SEGMENT_OVERLAP
    )
    process_parser.add_argument(
        "--contextual-analysis",
        help="Perform contextual analysis on segments",
        action="store_true"
    )
    process_parser.add_argument(
        "--analyze-connections",
        help="Analyze connections between segments during contextual analysis",
        action="store_true",
        default=True
    )
    process_parser.add_argument(
        "--batch-size",
        help=f"Number of segments to process in a single batch (default: {settings.LLM_BATCH_SIZE})",
        type=int,
        default=settings.LLM_BATCH_SIZE
    )
    process_parser.add_argument(
        "--delay",
        help=f"Delay between API requests in seconds (default: {settings.LLM_DELAY_BETWEEN_REQUESTS})",
        type=float,
        default=settings.LLM_DELAY_BETWEEN_REQUESTS
    )
    process_parser.add_argument(
        "--gradual",
        help="Process file gradually, with increasingly larger chunks to manage API quotas",
        action="store_true"
    )
    process_parser.add_argument(
        "--expand-graph",
        help="Recursively expand the knowledge graph through questioning",
        action="store_true"
    )
    process_parser.add_argument(
        "--expansion-iterations",
        help="Number of expansion iterations to perform (default: 3)",
        type=int,
        default=3
    )
    process_parser.add_argument(
        "--build-metagraph",
        help="Build a meta-graph by abstracting the knowledge graph",
        action="store_true"
    )
    process_parser.add_argument(
        "--min-cluster-size",
        help="Minimum size of entity clusters for meta-graph creation (default: 3)",
        type=int,
        default=3
    )
    process_parser.add_argument(
        "--generate-report",
        help="Generate a comprehensive HTML research report",
        action="store_true"
    )
    process_parser.set_defaults(func=process_file)
    
    # List providers command
    providers_parser = subparsers.add_parser("providers", help="List available LLM providers")
    providers_parser.set_defaults(func=list_providers)
    
    # Fix segment links command
    fix_links_parser = subparsers.add_parser("fix-links", help="Fix segment links in reports")
    fix_links_parser.add_argument(
        "--output", "-o",
        help="Output directory containing reports (default: output)",
        default="output"
    )
    fix_links_parser.add_argument(
        "--recursive", "-r",
        help="Recursively search for reports in subdirectories",
        action="store_true"
    )
    fix_links_parser.set_defaults(func=fix_segment_links_cmd)
    
    return parser


def main(args: Optional[List[str]] = None):
    """Main CLI entry point.
    
    Args:
        args: Command-line arguments (defaults to sys.argv)
    """
    parser = setup_parser()
    parsed_args = parser.parse_args(args)
    
    # Configure logging based on args
    logging.basicConfig(
        level=getattr(logging, parsed_args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    
    # Process the command
    asyncio.run(process_command(parsed_args))