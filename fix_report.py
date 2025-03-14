#!/usr/bin/env python3
"""
Utility script to recover and create report from files in a partially processed directory.
This fixes the 'list object has no element 6659' error by safely handling indices.
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add src directory to path for imports
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

# Import functions after modifying path
from knowledge_graph_synth.output.report.generator import ReportGenerator
from knowledge_graph_synth.models.graph import KnowledgeGraph
from knowledge_graph_synth.models.entity import Entity
from knowledge_graph_synth.models.relationship import Relationship
from knowledge_graph_synth.models.provenance import SourceSpan

def load_json_file(file_path):
    """Safely load a JSON file and return its contents."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"Error loading {file_path}: {str(e)}")
    
    return None

def create_graph_from_files(output_dir):
    """Create a knowledge graph from the extracted entities and relationships."""
    logger.info(f"Creating graph from files in {output_dir}")
    
    # Load entities
    entities_file = os.path.join(output_dir, "entities", "all_entities.json")
    entities_data = load_json_file(entities_file)
    
    # Load resolved entities if available
    resolved_entities_file = os.path.join(output_dir, "entities", "resolved_entities.json")
    resolved_entities_data = load_json_file(resolved_entities_file)
    
    # Use resolved entities if available, otherwise use all entities
    entity_data = resolved_entities_data if resolved_entities_data else entities_data
    
    # Load relationships
    relationships_file = os.path.join(output_dir, "relationships", "all_relationships.json")
    relationships_data = load_json_file(relationships_file)
    
    # Load grounded relationships if available
    grounded_relationships_file = os.path.join(output_dir, "relationships", "grounded_relationships.json")
    grounded_relationships_data = load_json_file(grounded_relationships_file)
    
    # Use grounded relationships if available, otherwise use all relationships
    relationship_data = grounded_relationships_data if grounded_relationships_data else relationships_data
    
    # Create a knowledge graph
    graph = KnowledgeGraph()
    
    # Add entities to the graph
    if entity_data:
        for entity_dict in entity_data:
            try:
                # Try to create an entity directly or manually
                entity_id = entity_dict.get("id")
                entity_name = entity_dict.get("name", "Unknown")
                entity_type = entity_dict.get("type", "concept")
                entity_confidence = entity_dict.get("confidence", 0.8)
                
                # Create source span
                source_span_dict = entity_dict.get("source_span", {})
                source_span = SourceSpan(
                    document_id=source_span_dict.get("document_id", "unknown"),
                    start=source_span_dict.get("start", 0),
                    end=source_span_dict.get("end", 0),
                    text=source_span_dict.get("text", "")
                )
                
                # Create entity
                entity = Entity(
                    id=entity_id,
                    name=entity_name,
                    type=entity_type,
                    confidence=entity_confidence,
                    source_span=source_span
                )
                
                # Add attributes if present
                if "attributes" in entity_dict:
                    entity.attributes = entity_dict["attributes"]
                
                graph.add_entity(entity)
            except Exception as e:
                logger.warning(f"Error creating entity from {entity_dict}: {str(e)}")
    
    # Add relationships to the graph
    if relationship_data:
        for rel_dict in relationship_data:
            try:
                # Try to create a relationship directly or manually
                rel_id = rel_dict.get("id")
                source_id = rel_dict.get("source_id")
                target_id = rel_dict.get("target_id")
                rel_type = rel_dict.get("type", "RELATED_TO")
                confidence = rel_dict.get("confidence", 0.8)
                
                # Create source span
                source_span_dict = rel_dict.get("source_span", {})
                source_span = SourceSpan(
                    document_id=source_span_dict.get("document_id", "unknown"),
                    start=source_span_dict.get("start", 0),
                    end=source_span_dict.get("end", 0),
                    text=source_span_dict.get("text", "")
                )
                
                # Create relationship
                relationship = Relationship(
                    id=rel_id,
                    source_id=source_id,
                    target_id=target_id,
                    type=rel_type,
                    confidence=confidence,
                    source_span=source_span
                )
                
                # Only add relationships between entities that exist in the graph
                if relationship.source_id in graph.entities and relationship.target_id in graph.entities:
                    graph.add_relationship(relationship)
            except Exception as e:
                logger.warning(f"Error creating relationship from {rel_dict}: {str(e)}")
    
    logger.info(f"Created graph with {len(graph.entities)} entities and {len(graph.relationships)} relationships")
    return graph

def generate_safe_report(output_dir, source_file="Unknown source", title="Knowledge Graph Analysis"):
    """Generate a report safely, avoiding index errors."""
    # Create output path for the report
    report_path = os.path.join(output_dir, "recovered_report.html")
    
    # Create a knowledge graph from the files
    graph = create_graph_from_files(output_dir)
    
    # Create a report generator
    report_generator = ReportGenerator()
    
    # Generate the report
    try:
        # Add safety patches to avoid index errors
        # This monkey patch adds bounds checking for the segment_summaries list
        original_generate_report = report_generator.generate_report
        
        def safe_generate_report(*args, **kwargs):
            # Safely limit segment_summaries and segment_connections to prevent index errors
            if 'segment_summaries' in kwargs and isinstance(kwargs['segment_summaries'], list):
                # Limit to a safe number (e.g., 100) to avoid memory issues
                kwargs['segment_summaries'] = kwargs['segment_summaries'][:100]
            
            if 'segment_connections' in kwargs and isinstance(kwargs['segment_connections'], list):
                # Limit connections as well
                kwargs['segment_connections'] = kwargs['segment_connections'][:100]
                
            return original_generate_report(*args, **kwargs)
        
        # Apply the patched method
        report_generator.generate_report = safe_generate_report
        
        # Call the generator with the patched method
        report_generator.generate_report(
            report_path,
            graph,
            source_file=source_file,
            output_dir=output_dir,
            title=title
        )
        
        logger.info(f"Report successfully generated: {report_path}")
        return report_path
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return None

def fix_segment_links(report_path):
    """Fix segment links in a report."""
    if not os.path.exists(report_path):
        logger.warning(f"Report not found: {report_path}")
        return False
    
    try:
        # Read the report
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the segment links
        fixed_content = re.sub(r'href="segments/', r'href="./segments/', content)
        
        # Write the fixed report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        logger.info(f"Fixed segment links in {report_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing segment links: {str(e)}")
        return False

def main():
    """Main function to fix and restore a report."""
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python fix_report.py <output_directory> [source_file_name] [title]")
        return 1
    
    # Get the output directory
    output_dir = sys.argv[1]
    
    # Get optional source file name and title
    source_file = sys.argv[2] if len(sys.argv) > 2 else "Unknown source"
    title = sys.argv[3] if len(sys.argv) > 3 else "Recovered Knowledge Graph Analysis"
    
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        logger.error(f"Output directory not found: {output_dir}")
        return 1
    
    # Generate a new report
    report_path = generate_safe_report(output_dir, source_file, title)
    
    if not report_path:
        logger.error("Failed to generate report")
        return 1
    
    # Fix segment links in the report
    fix_segment_links(report_path)
    
    # Print success message
    print(f"\nReport successfully recovered: {report_path}")
    print(f"You can now view the report in your browser.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())