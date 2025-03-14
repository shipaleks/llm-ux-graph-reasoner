#\!/usr/bin/env python3
"""
Test script for the research report generator.
"""

import asyncio
import logging
import json
import os
from pathlib import Path
from uuid import uuid4

from src.knowledge_graph_synth.models.graph import KnowledgeGraph
from src.knowledge_graph_synth.models.entity import Entity, EntityAttribute
from src.knowledge_graph_synth.models.relationship import Relationship
from src.knowledge_graph_synth.models.provenance import SourceSpan
from src.knowledge_graph_synth.output.report.generator import ReportGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_test_graph():
    """Create a test knowledge graph."""
    graph = KnowledgeGraph()
    
    # Create source span for entities
    def create_source_span(text):
        return SourceSpan(
            document_id="test_document",
            segment_id="test_segment",
            start=0,
            end=len(text),
            text=text
        )
    
    # Create test entities
    entities = [
        Entity(
            id=uuid4(), 
            name="John Smith", 
            type="PERSON", 
            confidence=0.95,
            source_span=create_source_span("John Smith is the CEO of Acme Corporation")
        ),
        Entity(
            id=uuid4(), 
            name="Mary Johnson", 
            type="PERSON", 
            confidence=0.92,
            source_span=create_source_span("Mary Johnson is the CTO of Acme Corporation")
        ),
        Entity(
            id=uuid4(), 
            name="Acme Corporation", 
            type="ORGANIZATION", 
            confidence=0.98,
            source_span=create_source_span("Acme Corporation was founded in 1985 in New York")
        ),
        Entity(
            id=uuid4(), 
            name="Global Systems Ltd.", 
            type="ORGANIZATION", 
            confidence=0.94,
            source_span=create_source_span("Global Systems Ltd. is based in London")
        ),
        Entity(
            id=uuid4(), 
            name="Project Alpha", 
            type="PROJECT", 
            confidence=0.91,
            source_span=create_source_span("Project Alpha has a budget of $5 million")
        ),
        Entity(
            id=uuid4(), 
            name="AI solutions", 
            type="CONCEPT", 
            confidence=0.88,
            source_span=create_source_span("The project focuses on AI solutions")
        ),
        Entity(
            id=uuid4(), 
            name="Healthcare", 
            type="INDUSTRY", 
            confidence=0.89,
            source_span=create_source_span("AI solutions for healthcare")
        ),
        Entity(
            id=uuid4(), 
            name="David Brown", 
            type="PERSON", 
            confidence=0.87,
            source_span=create_source_span("David Brown is the CEO of Global Systems Ltd.")
        )
    ]
    
    # Add attributes to entities
    entities[0].add_attribute("role", "CEO", 0.95)
    entities[1].add_attribute("role", "CTO", 0.92)
    entities[2].add_attribute("founded", "1985", 0.90)
    entities[2].add_attribute("location", "New York", 0.90)
    entities[3].add_attribute("location", "London", 0.90)
    entities[4].add_attribute("budget", "$5 million", 0.90)
    entities[7].add_attribute("role", "CEO of Global Systems Ltd.", 0.90)
    
    # Add entities to graph
    entity_map = {}
    for entity in entities:
        graph.add_entity(entity)
        entity_map[entity.name] = entity
    
    # Create test relationships
    relationships = [
        Relationship(
            id=uuid4(),
            source_id=entity_map["John Smith"].id,
            target_id=entity_map["Acme Corporation"].id,
            type="WORKS_FOR",
            confidence=0.94,
            source_span=create_source_span("John Smith is the CEO of Acme Corporation")
        ),
        Relationship(
            id=uuid4(),
            source_id=entity_map["Mary Johnson"].id,
            target_id=entity_map["Acme Corporation"].id,
            type="WORKS_FOR",
            confidence=0.93,
            source_span=create_source_span("Mary Johnson is the CTO of Acme Corporation")
        ),
        Relationship(
            id=uuid4(),
            source_id=entity_map["David Brown"].id,
            target_id=entity_map["Global Systems Ltd."].id,
            type="WORKS_FOR",
            confidence=0.91,
            source_span=create_source_span("David Brown is the CEO of Global Systems Ltd.")
        ),
        Relationship(
            id=uuid4(),
            source_id=entity_map["Acme Corporation"].id,
            target_id=entity_map["Project Alpha"].id,
            type="DEVELOPS",
            confidence=0.89,
            source_span=create_source_span("Acme Corporation partnered with Global Systems Ltd. on Project Alpha")
        ),
        Relationship(
            id=uuid4(),
            source_id=entity_map["Global Systems Ltd."].id,
            target_id=entity_map["Project Alpha"].id,
            type="PARTNERS_IN",
            confidence=0.88,
            source_span=create_source_span("Acme Corporation partnered with Global Systems Ltd. on Project Alpha")
        ),
        Relationship(
            id=uuid4(),
            source_id=entity_map["Project Alpha"].id,
            target_id=entity_map["AI solutions"].id,
            type="FOCUSES_ON",
            confidence=0.87,
            source_span=create_source_span("Project Alpha focuses on developing AI solutions")
        ),
        Relationship(
            id=uuid4(),
            source_id=entity_map["AI solutions"].id,
            target_id=entity_map["Healthcare"].id,
            type="APPLIED_TO",
            confidence=0.85,
            source_span=create_source_span("AI solutions for healthcare")
        )
    ]
    
    # Add relationships to graph
    for relationship in relationships:
        graph.add_relationship(relationship)
    
    return graph

def create_test_contextual_data(output_dir):
    """Create test contextual analysis data."""
    # Create context directory
    import os
    context_dir = os.path.join(output_dir, "context")
    os.makedirs(context_dir, exist_ok=True)
    
    # Create test segment summaries
    summaries = {
        "segment-1": {
            "id": "segment-1",
            "summary": "John Smith is the CEO of Acme Corporation, a software development company founded in 1985 and headquartered in New York City.",
            "key_points": [
                "John Smith is the CEO of Acme Corporation",
                "Acme Corporation was founded in 1985",
                "Acme Corporation is headquartered in New York City",
                "Acme Corporation is a software development company"
            ],
            "role": "introduction",
            "parent_relation": None
        },
        "segment-2": {
            "id": "segment-2",
            "summary": "Mary Johnson is the CTO of Acme Corporation, having joined in 2005. Before that, she was a senior developer at Tech Solutions Inc.",
            "key_points": [
                "Mary Johnson is the CTO of Acme Corporation",
                "She joined Acme in 2005",
                "She was previously a senior developer at Tech Solutions Inc."
            ],
            "role": "background",
            "parent_relation": "Provides additional information about the company's leadership"
        },
        "segment-3": {
            "id": "segment-3",
            "summary": "Acme Corporation partnered with Global Systems Ltd. on Project Alpha, which was announced on January 15, 2023.",
            "key_points": [
                "Partnership between Acme Corporation and Global Systems Ltd.",
                "The project is called Project Alpha",
                "The announcement was made on January 15, 2023"
            ],
            "role": "development",
            "parent_relation": "Describes a recent partnership involving the company"
        }
    }
    
    # Create test segment connections
    connections = [
        {
            "source_id": "segment-1",
            "target_id": "segment-2",
            "type": "Thought development",
            "strength": 0.8,
            "direction": "one-way"
        },
        {
            "source_id": "segment-2",
            "target_id": "segment-3",
            "type": "Cause-effect",
            "strength": 0.7,
            "direction": "one-way"
        },
        {
            "source_id": "segment-1",
            "target_id": "segment-3",
            "type": "Common theme",
            "strength": 0.6,
            "direction": "bidirectional"
        }
    ]
    
    # Save test data
    with open(os.path.join(context_dir, "segment_summaries.json"), "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(context_dir, "segment_connections.json"), "w", encoding="utf-8") as f:
        json.dump(connections, f, ensure_ascii=False, indent=2)

def create_test_theories(output_dir):
    """Create test theories data."""
    # Create theories directory
    theories_dir = os.path.join(output_dir, "theories")
    os.makedirs(theories_dir, exist_ok=True)
    
    # Create test theories
    theories = [
        {
            "name": "Corporate Partnership Dynamics",
            "description": "This theory explains how technology companies form strategic partnerships to develop innovative projects in specific domains.",
            "confidence": 0.92,
            "hypotheses": [
                {
                    "statement": "Companies with complementary expertise are more likely to form successful partnerships.",
                    "confidence": 0.88,
                    "evidence": [
                        {
                            "description": "Acme Corporation (software) partnered with Global Systems Ltd. (systems integration) on Project Alpha.",
                            "strength": 0.85
                        }
                    ]
                },
                {
                    "statement": "Leadership roles significantly influence the direction of partnership projects.",
                    "confidence": 0.82,
                    "evidence": [
                        {
                            "description": "Both CEOs were involved in the announcement of Project Alpha.",
                            "strength": 0.78
                        },
                        {
                            "description": "The CTO's technical background aligns with the AI focus of the project.",
                            "strength": 0.75
                        }
                    ]
                }
            ]
        },
        {
            "name": "AI Application in Industry Verticals",
            "description": "This theory explores how AI solutions are tailored to specific industry verticals, particularly healthcare.",
            "confidence": 0.85,
            "hypotheses": [
                {
                    "statement": "Healthcare is a priority vertical for AI applications due to potential impact.",
                    "confidence": 0.83,
                    "evidence": [
                        {
                            "description": "Project Alpha specifically focuses on AI solutions for healthcare.",
                            "strength": 0.81
                        }
                    ]
                }
            ]
        }
    ]
    
    # Save test theories
    with open(os.path.join(theories_dir, "theories.json"), "w", encoding="utf-8") as f:
        json.dump(theories, f, ensure_ascii=False, indent=2)

def test_report_generation():
    """Test the research report generation."""
    logger.info("Testing research report generation...")
    
    # Create test output directory
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create test graph
    graph = create_test_graph()
    logger.info(f"Created test graph with {len(graph.entities)} entities and {len(graph.relationships)} relationships")
    
    # Create test contextual data
    create_test_contextual_data(output_dir)
    logger.info("Created test contextual analysis data")
    
    # Create test theories
    create_test_theories(output_dir)
    logger.info("Created test theories data")
    
    # Create report generator
    report_generator = ReportGenerator()
    
    # Generate report
    report_path = os.path.join(output_dir, "research_report.html")
    report_generator.generate_report(
        report_path,
        graph,
        source_file="test_file.txt",
        output_dir=output_dir,
        title="Test Knowledge Graph Analysis Report"
    )
    
    logger.info(f"Research report generated at: {report_path}")
    logger.info(f"View in browser: file://{os.path.abspath(report_path)}")

if __name__ == "__main__":
    test_report_generation()
