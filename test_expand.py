#\!/usr/bin/env python3
"""
Test script for graph expansion functionality.
"""

import asyncio
import logging
import os
import uuid
from pathlib import Path

from src.knowledge_graph_synth.models.graph import KnowledgeGraph
from src.knowledge_graph_synth.models.entity import Entity
from src.knowledge_graph_synth.models.relationship import Relationship
from src.knowledge_graph_synth.models.provenance import SourceSpan
from src.knowledge_graph_synth.models.segment import TextSegment, SegmentCollection
from src.knowledge_graph_synth.graph.expansion import GraphExpander

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_test_segments():
    """Create test segments for expansion testing."""
    collection = SegmentCollection()
    
    texts = [
        "John Smith is the CEO of Acme Corporation, which was founded in 1985. Acme Corporation is headquartered in New York City and specializes in software development.",
        "Mary Johnson is the CTO of Acme Corporation and has worked there since 2005. She previously worked at Tech Solutions Inc. as a senior developer.",
        "Acme Corporation recently partnered with Global Systems Ltd. on a new project called 'Project Alpha'. This partnership was announced on January 15, 2023, by John Smith during a press conference.",
        "The project aims to develop innovative AI solutions for healthcare. The budget for this project is estimated at $5 million.",
        "Global Systems Ltd. is based in London and is led by CEO David Brown. The company has extensive experience in systems integration and cloud computing."
    ]
    
    segments = []
    for i, text in enumerate(texts):
        segment = TextSegment(
            id=uuid.uuid4(),
            text=text,
            start_position=0,
            end_position=len(text),
            language="en"
        )
        collection.add_segment(segment)
        segments.append(segment)
    
    return collection, segments

def create_test_graph(segments):
    """Create a test knowledge graph for expansion."""
    graph = KnowledgeGraph()
    
    # Create source span for entities
    def create_source_span(text, segment):
        return SourceSpan(
            document_id="test_document",
            segment_id=str(segment.id),
            start=0,
            end=len(text),
            text=text
        )
    
    # Create test entities
    john = Entity(
        id=uuid.uuid4(),
        name="John Smith",
        type="PERSON",
        confidence=0.95,
        source_span=create_source_span("John Smith is the CEO of Acme Corporation", segments[0])
    )
    
    mary = Entity(
        id=uuid.uuid4(),
        name="Mary Johnson",
        type="PERSON",
        confidence=0.92,
        source_span=create_source_span("Mary Johnson is the CTO of Acme Corporation", segments[1])
    )
    
    acme = Entity(
        id=uuid.uuid4(),
        name="Acme Corporation",
        type="ORGANIZATION",
        confidence=0.98,
        source_span=create_source_span("Acme Corporation is headquartered in New York City", segments[0])
    )
    acme.add_attribute("founded", "1985", 0.9)
    acme.add_attribute("location", "New York City", 0.9)
    
    global_systems = Entity(
        id=uuid.uuid4(),
        name="Global Systems Ltd.",
        type="ORGANIZATION",
        confidence=0.94,
        source_span=create_source_span("Global Systems Ltd. is based in London", segments[4])
    )
    global_systems.add_attribute("location", "London", 0.9)
    
    project_alpha = Entity(
        id=uuid.uuid4(),
        name="Project Alpha",
        type="PROJECT",
        confidence=0.91,
        source_span=create_source_span("Project Alpha aims to develop innovative AI solutions", segments[3])
    )
    
    # Add entities to graph
    graph.add_entity(john)
    graph.add_entity(mary)
    graph.add_entity(acme)
    graph.add_entity(global_systems)
    graph.add_entity(project_alpha)
    
    # Create test relationships
    graph.add_relationship(Relationship(
        id=uuid.uuid4(),
        source_id=john.id,
        target_id=acme.id,
        type="WORKS_FOR",
        confidence=0.94,
        source_span=create_source_span("John Smith is the CEO of Acme Corporation", segments[0])
    ))
    
    graph.add_relationship(Relationship(
        id=uuid.uuid4(),
        source_id=mary.id,
        target_id=acme.id,
        type="WORKS_FOR",
        confidence=0.93,
        source_span=create_source_span("Mary Johnson is the CTO of Acme Corporation", segments[1])
    ))
    
    graph.add_relationship(Relationship(
        id=uuid.uuid4(),
        source_id=acme.id,
        target_id=project_alpha.id,
        type="DEVELOPS",
        confidence=0.89,
        source_span=create_source_span("Acme Corporation recently partnered with Global Systems Ltd. on a new project called Project Alpha", segments[2])
    ))
    
    graph.add_relationship(Relationship(
        id=uuid.uuid4(),
        source_id=global_systems.id,
        target_id=project_alpha.id,
        type="PARTNERS_IN",
        confidence=0.88,
        source_span=create_source_span("Acme Corporation partnered with Global Systems Ltd. on Project Alpha", segments[2])
    ))
    
    return graph

# This function is duplicated - we'll delete it

async def test_graph_expansion():
    """Test graph expansion functionality."""
    logger.info("Creating test graph and segments...")
    collection, segments = create_test_segments()
    graph = create_test_graph(segments)
    
    logger.info(f"Initial graph: {len(graph.entities)} entities, {len(graph.relationships)} relationships")
    
    # Create expander
    expander = GraphExpander(provider_name="gemini")
    
    # Expand graph
    logger.info("Expanding graph...")
    expanded_graph = await expander.expand_graph(
        graph,
        collection,
        max_iterations=1  # Only one iteration to save time
    )
    
    logger.info(f"Expanded graph: {len(expanded_graph.entities)} entities, {len(expanded_graph.relationships)} relationships")
    
    # Print new entities and relationships
    if len(expanded_graph.entities) > len(graph.entities):
        logger.info("New entities:")
        original_entity_names = {entity.name.lower() for entity in graph.entities.values()}
        for entity in expanded_graph.entities.values():
            if entity.name.lower() not in original_entity_names:
                logger.info(f"  - {entity.name} ({entity.type})")
    
    if len(expanded_graph.relationships) > len(graph.relationships):
        logger.info("New relationships:")
        original_rel_keys = {
            (str(rel.source_id), str(rel.target_id), rel.type.lower())
            for rel in graph.relationships.values()
        }
        for rel in expanded_graph.relationships.values():
            key = (str(rel.source_id), str(rel.target_id), rel.type.lower())
            if key not in original_rel_keys:
                source = expanded_graph.get_entity(rel.source_id)
                target = expanded_graph.get_entity(rel.target_id)
                if source and target:
                    logger.info(f"  - {source.name} --[{rel.type}]--> {target.name}")
    
    return expanded_graph

if __name__ == "__main__":
    asyncio.run(test_graph_expansion())