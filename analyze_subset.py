#!/usr/bin/env python3
"""
analyze_subset.py - Analyze a subset of lines from a text file using knowledge_graph_synth.

This script:
1. Extracts the first 500 lines from a file
2. Saves them to a temporary file
3. Runs a complete knowledge graph analysis
4. Tracks API calls and token usage
"""

import os
import tempfile
import asyncio
import logging
import argparse
from pathlib import Path
import time
import functools
from typing import Dict, Any, Callable, List

# Import knowledge_graph_synth components
from knowledge_graph_synth.text import TextLoader, TextNormalizer, TextSegmenter
from knowledge_graph_synth.llm import LLMProviderFactory
from knowledge_graph_synth.extraction import EntityExtractor, RelationshipExtractor, CoreferenceResolver, Grounder
from knowledge_graph_synth.graph import GraphBuilder, expansion, metagraph, GraphVisualizer
from knowledge_graph_synth.theory import TheoryGenerator, PatternFinder
from knowledge_graph_synth.models import SegmentCollection
from knowledge_graph_synth.config import settings
from knowledge_graph_synth.cli.utils import create_timestamped_dir, get_subdirectory_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("analyze_subset")

# Token and API call tracking
class APITracker:
    """Tracks API calls and token usage."""
    
    def __init__(self):
        self.api_calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.start_time = time.time()
    
    def increment_call(self, input_tokens=0, output_tokens=0):
        """Increment API call count and token usage."""
        self.api_calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
    
    def report(self):
        """Generate a report of API usage."""
        elapsed_time = time.time() - self.start_time
        return {
            "api_calls": self.api_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "elapsed_time": elapsed_time,
            "tokens_per_second": (self.input_tokens + self.output_tokens) / max(elapsed_time, 1)
        }
    
    def print_report(self):
        """Print API usage report to console."""
        report = self.report()
        print("\n" + "="*60)
        print("API USAGE REPORT")
        print("="*60)
        print(f"Total API calls:     {report['api_calls']}")
        print(f"Input tokens:        {report['input_tokens']}")
        print(f"Output tokens:       {report['output_tokens']}")
        print(f"Total tokens:        {report['total_tokens']}")
        print(f"Elapsed time:        {report['elapsed_time']:.2f} seconds")
        print(f"Tokens per second:   {report['tokens_per_second']:.2f}")
        print("="*60)

# Global tracker instance
api_tracker = APITracker()

# Function to monkey patch API methods to track calls
def patch_llm_provider(provider):
    """Patch LLM provider methods to track API calls."""
    original_generate_text = provider.generate_text
    original_generate_structured = provider.generate_structured
    
    @functools.wraps(original_generate_text)
    async def tracked_generate_text(prompt: str, *args, **kwargs):
        # Estimate token count from prompt length (rough estimate)
        input_tokens = len(prompt.split())
        result = await original_generate_text(prompt, *args, **kwargs)
        output_tokens = len(result.split())
        api_tracker.increment_call(input_tokens, output_tokens)
        return result
    
    @functools.wraps(original_generate_structured)
    async def tracked_generate_structured(prompt: str, response_schema, *args, **kwargs):
        # Estimate token count from prompt length (rough estimate)
        input_tokens = len(prompt.split())
        result = await original_generate_structured(prompt, response_schema, *args, **kwargs)
        # Estimate output tokens from JSON length
        import json
        output_tokens = len(json.dumps(result).split())
        api_tracker.increment_call(input_tokens, output_tokens)
        return result
    
    # Apply the patched methods
    provider.generate_text = tracked_generate_text
    provider.generate_structured = tracked_generate_structured
    
    return provider

def extract_first_n_lines(file_path: str, n: int = 500) -> str:
    """Extract the first n lines from a file."""
    lines = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            lines.append(line)
    return ''.join(lines)

async def process_segment_collection(output_dir: str, segmented_collection: SegmentCollection, provider_name: str = "gemini"):
    """Process a segment collection with entity extraction, graph building, and theory generation."""
    logger.info(f"Processing {len(segmented_collection.segments)} segments")
    
    # Extract entities and relationships
    entities_dir = get_subdirectory_path(output_dir, "entities")
    relationships_dir = get_subdirectory_path(output_dir, "relationships")
    
    # Get provider and patch for tracking
    provider = LLMProviderFactory.get_provider(provider_name)
    patched_provider = patch_llm_provider(provider)
    
    # Save the original get_provider function to restore later
    original_get_provider = LLMProviderFactory.get_provider
    
    # Monkey patch the LLMProviderFactory to always return our patched provider
    LLMProviderFactory.get_provider = lambda name=None: patched_provider
    
    # Extract entities
    logger.info("Extracting entities...")
    entity_extractor = EntityExtractor(provider_name=provider_name)
    entities = await entity_extractor.extract_from_collection(
        segmented_collection,
        save_intermediate=True,
        output_dir=str(entities_dir)
    )
    
    # Restore the original get_provider function
    LLMProviderFactory.get_provider = original_get_provider
    logger.info(f"Extracted {len(entities)} entities")
    
    # Resolve coreferences
    resolver = CoreferenceResolver()
    resolved_entities = resolver.resolve_entities(entities)
    logger.info(f"Resolved {len(entities)} entities into {len(resolved_entities)} unique entities")
    
    # Ground entities
    grounder = Grounder()
    grounded_entities = grounder.ground_entities(resolved_entities, segmented_collection)
    logger.info(f"Grounded {len(grounded_entities)} entities")
    
    # Extract relationships
    logger.info("Extracting relationships...")
    
    # Monkey patch the LLMProviderFactory again
    LLMProviderFactory.get_provider = lambda name=None: patched_provider
    
    relationship_extractor = RelationshipExtractor(provider_name=provider_name)
    relationships = await relationship_extractor.extract_from_collection(
        segmented_collection, grounded_entities,
        save_intermediate=True,
        output_dir=str(relationships_dir)
    )
    
    # Restore the original get_provider function
    LLMProviderFactory.get_provider = original_get_provider
    logger.info(f"Extracted {len(relationships)} relationships")
    
    # Ground relationships
    entity_map = {entity.id: entity for entity in grounded_entities}
    grounded_relationships = grounder.ground_relationships(
        relationships, entity_map, segmented_collection
    )
    logger.info(f"Grounded {len(grounded_relationships)} relationships")
    
    # Build knowledge graph
    logger.info("Building knowledge graph...")
    builder = GraphBuilder()
    graph = builder.build(grounded_entities, grounded_relationships)
    logger.info(f"Built graph with {len(graph.entities)} entities and {len(graph.relationships)} relationships")
    
    # Visualize the graph
    graphs_dir = get_subdirectory_path(output_dir, "graphs")
    visualizer = GraphVisualizer(output_dir=str(graphs_dir))
    html_path = visualizer.visualize_html(
        graph, 
        filename="knowledge_graph.html",
        title="Knowledge Graph",
        generate_report=True
    )
    logger.info(f"Graph visualization saved to {html_path}")
    
    # Find patterns
    logger.info("Finding patterns...")
    theories_dir = get_subdirectory_path(output_dir, "theories")
    
    # Monkey patch the LLMProviderFactory again
    LLMProviderFactory.get_provider = lambda name=None: patched_provider
    
    pattern_finder = PatternFinder()
    patterns = await pattern_finder.find_patterns(graph)
    
    # Save patterns to file
    import json
    patterns_path = os.path.join(theories_dir, "patterns.json")
    with open(patterns_path, "w", encoding="utf-8") as f:
        json.dump(patterns, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Found {len(patterns)} patterns and saved to {patterns_path}")
    
    # Generate theories
    logger.info("Generating theories...")
    theory_generator = TheoryGenerator()
    theories = await theory_generator.generate_theories(
        graph, segmented_collection, max_theories=3
    )
    
    # Save theories to file
    theories_path = os.path.join(theories_dir, "theories.json")
    with open(theories_path, "w", encoding="utf-8") as f:
        json.dump(theories, f, ensure_ascii=False, indent=2)
        
    # Also save a markdown version for easier reading
    theories_md_path = os.path.join(theories_dir, "theories.md")
    with open(theories_md_path, "w", encoding="utf-8") as f:
        f.write("# Generated Theories\n\n")
        for i, theory in enumerate(theories):
            f.write(f"## Theory {i+1}: {theory.get('name', f'Theory {i+1}')}\n\n")
            f.write(f"**Description:** {theory.get('description', 'No description')}\n\n")
            f.write("**Evidence:**\n\n")
            for evidence in theory.get('evidence', []):
                f.write(f"- {evidence.get('description', 'No evidence description')}\n")
            f.write("\n")
    
    logger.info(f"Generated {len(theories)} theories and saved to {theories_path}")
    
    # Expand graph
    logger.info("Expanding graph...")
    expanded_dir = get_subdirectory_path(graphs_dir, "expanded")
    graph_expander = expansion.GraphExpander()
    
    # Import here (already imported in expansion.py)
    # This is redundant but solves the error since ExpansionReportGenerator is created inside expand_graph
    
    try:
        # The expand_graph method only returns the expanded graph, not the expansion results
        expanded_graph = await graph_expander.expand_graph(
            graph,
            segmented_collection,
            max_iterations=2,
            output_dir=str(expanded_dir)
        )
        
        # Load expansion results from the file
        import json
        expansion_data_file = os.path.join(expanded_dir, "graphs", "expanded", "expansion_data.json")
        if os.path.exists(expansion_data_file):
            with open(expansion_data_file, "r", encoding="utf-8") as f:
                expansion_results = json.load(f)
        else:
            expansion_results = {"iterations": [], "targets": [], "questions": [], "answers": []}
        
        # Save expansion data
        expansion_data_path = os.path.join(expanded_dir, "expansion_data.json")
        with open(expansion_data_path, "w", encoding="utf-8") as f:
            json.dump(expansion_results, f, ensure_ascii=False, indent=2)
            
        # Generate expansion report
        expansion_report = expansion.ExpansionReportGenerator()
        expansion_report_path = os.path.join(expanded_dir, "expansion_process.md")
        with open(expansion_report_path, "w", encoding="utf-8") as f:
            f.write(expansion_report.generate_report(expansion_results))
        
        logger.info(f"Graph expanded to {len(expanded_graph.entities)} entities and {len(expanded_graph.relationships)} relationships")
        
        # Visualize expanded graph
        expanded_html_path = visualizer.visualize_html(
            expanded_graph,
            filename="expanded_graph.html",
            title="Expanded Knowledge Graph",
            generate_report=True,
            output_dir=str(expanded_dir)
        )
        logger.info(f"Expanded graph visualization saved to {expanded_html_path}")
        
    except Exception as e:
        logger.error(f"Error expanding graph: {str(e)}")
        logger.warning("Using original graph without expansion")
        expanded_graph = graph
    
    # Build meta-graph
    logger.info("Building meta-graph...")
    meta_builder = metagraph.MetaGraphBuilder()
    try:
        meta_graph = await meta_builder.build_metagraph(graph)
        if len(meta_graph.entities) > 0:
            logger.info(f"Created meta-graph with {len(meta_graph.entities)} meta-concepts")
            
            # Visualize meta-graph
            meta_graphs_dir = get_subdirectory_path(graphs_dir, "meta")
            meta_html_path = visualizer.visualize_html(
                meta_graph, 
                filename="meta_graph.html",
                title="Meta-Graph",
                generate_report=True,
                output_dir=str(meta_graphs_dir)
            )
            logger.info(f"Meta-graph visualization saved to {meta_html_path}")
        else:
            logger.warning("No meta-concepts found. Unable to create meta-graph.")
    except Exception as e:
        logger.error(f"Error building meta-graph: {str(e)}")
        logger.warning("Skipping meta-graph generation")
    
    # Generate a comprehensive report
    from knowledge_graph_synth.output.report.generator import ReportGenerator
    logger.info("Generating comprehensive report...")
    reporter = ReportGenerator()
    report_path = os.path.join(output_dir, "research_report.html")
    
    from datetime import datetime
    import json
    
    # Get template
    template = reporter.env.get_template("research_report.html")
    
    # Calculate graph metrics
    metrics = reporter._calculate_graph_metrics(graph)
    
    # Generate executive summary
    executive_summary = reporter._generate_executive_summary(graph, metrics, theories)
    
    # Generate conclusion
    conclusion = reporter._generate_conclusion(graph, metrics, theories)
    
    # Prepare data for template
    data = {
        "title": "Knowledge Graph Analysis",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "graph_html": reporter._create_plotly_graph(graph),
        "expanded_graph_html": reporter._create_plotly_graph(expanded_graph) if 'expanded_graph' in locals() else "",
        "executive_summary": executive_summary,
        "graph": graph,
        "metrics": metrics,
        "theories": theories,
        "patterns": patterns,
        "conclusion": conclusion,
    }
    
    # Render the template
    html = template.render(**data)
    
    # Write to file
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    logger.info(f"Comprehensive report generated at {report_path}")
    
    return graph

async def main():
    """Main function to run the analysis."""
    parser = argparse.ArgumentParser(description="Analyze a subset of lines from a text file")
    parser.add_argument("--input", type=str, default="/Users/shipaleks/Documents/graph_reasoner_claude_code/merged.txt",
                      help="Path to the input file")
    parser.add_argument("--lines", type=int, default=100,
                      help="Number of lines to extract")
    parser.add_argument("--output", type=str, default="output",
                      help="Directory to save output")
    parser.add_argument("--provider", type=str, default="gemini",
                      help="LLM provider to use")
    args = parser.parse_args()
    
    logger.info(f"Extracting first {args.lines} lines from {args.input}")
    
    # Extract the first n lines
    text_content = extract_first_n_lines(args.input, args.lines)
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
        tmp_file.write(text_content)
        tmp_path = tmp_file.name
    
    logger.info(f"Saved {args.lines} lines to temporary file: {tmp_path}")
    
    try:
        # Create output directory with timestamp
        output_dir, timestamp = create_timestamped_dir(args.output)
        logger.info(f"Using output directory: {output_dir}")
        
        # Load the text
        loader = TextLoader()
        segments = loader.load(tmp_path)
        logger.info(f"Loaded {len(segments.segments)} segments")
        
        # Normalize the text
        normalizer = TextNormalizer()
        normalized_segments = []
        for segment in segments.segments.values():
            normalized_segment = normalizer.normalize(segment)
            normalized_segments.append(normalized_segment)
            segments.add_segment(normalized_segment)
        logger.info(f"Normalized {len(normalized_segments)} segments")
        
        # Segment the text
        segmenter = TextSegmenter()
        segmented_collection = segmenter.segment(segments)
        logger.info(f"Segmented into {len(segmented_collection.segments)} segments")
        
        # Process the segment collection
        await process_segment_collection(output_dir, segmented_collection, args.provider)
        
        # Print API usage report
        api_tracker.print_report()
        
        logger.info(f"Analysis complete. Results saved to {output_dir}")
        
    finally:
        # Remove the temporary file
        os.unlink(tmp_path)

if __name__ == "__main__":
    asyncio.run(main())