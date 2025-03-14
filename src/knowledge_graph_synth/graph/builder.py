"""Graph builder for the knowledge graph synthesis system."""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID

import networkx as nx

from ..models import Entity, Relationship, KnowledgeGraph
from ..config import settings

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds a knowledge graph from entities and relationships.
    
    This class constructs a knowledge graph from extracted entities and relationships,
    handling duplicate detection, attribute merging, and graph validation.
    """
    
    def __init__(self, 
               confidence_threshold: float = settings.DEFAULT_CONFIDENCE_THRESHOLD):
        """Initialize the graph builder.
        
        Args:
            confidence_threshold: Minimum confidence score for inclusion in the graph
        """
        self.confidence_threshold = confidence_threshold
    
    def build(self, 
            entities: List[Entity], 
            relationships: List[Relationship]) -> KnowledgeGraph:
        """Build a knowledge graph from entities and relationships.
        
        Args:
            entities: List of entities to include
            relationships: List of relationships to include
            
        Returns:
            Constructed knowledge graph
        """
        # Filter entities by confidence
        filtered_entities = [
            entity for entity in entities
            if entity.confidence >= self.confidence_threshold
        ]
        
        # Create a lookup map for quick entity access
        entity_map = {entity.id: entity for entity in filtered_entities}
        
        # Filter relationships by confidence and ensure entities exist
        filtered_relationships = []
        for rel in relationships:
            if rel.confidence < self.confidence_threshold:
                continue
                
            if rel.source_id not in entity_map or rel.target_id not in entity_map:
                logger.warning(f"Skipping relationship: missing entity {rel.source_id} or {rel.target_id}")
                continue
                
            filtered_relationships.append(rel)
        
        # Create the knowledge graph
        graph = KnowledgeGraph()
        
        # Add entities
        for entity in filtered_entities:
            graph.add_entity(entity)
        
        # Add relationships
        for relationship in filtered_relationships:
            try:
                graph.add_relationship(relationship)
            except ValueError as e:
                logger.warning(f"Error adding relationship: {str(e)}")
        
        logger.info(f"Built graph with {len(graph.entities)} entities and {len(graph.relationships)} relationships")
        return graph
    
    def merge_graphs(self, graphs: List[KnowledgeGraph]) -> KnowledgeGraph:
        """Merge multiple knowledge graphs.
        
        Args:
            graphs: List of knowledge graphs to merge
            
        Returns:
            Merged knowledge graph
        """
        if not graphs:
            return KnowledgeGraph()
        
        if len(graphs) == 1:
            return graphs[0]
        
        # Create a new graph for the merged result
        merged_graph = KnowledgeGraph()
        
        # Track entities that have been merged
        merged_entities = {}
        
        # First, add all entities
        for graph in graphs:
            for entity_id, entity in graph.entities.items():
                if entity_id in merged_entities:
                    # This entity has already been added
                    continue
                
                # Check if this entity exists in the merged graph
                # (based on name and type)
                existing_entities = merged_graph.get_entities_by_type(entity.type)
                match_found = False
                
                for existing in existing_entities:
                    if existing.name.lower() == entity.name.lower():
                        # Merge attributes from this entity into the existing one
                        for attr in entity.attributes:
                            existing_attrs = existing.get_attribute(attr.key)
                            
                            if not existing_attrs:
                                # Add the attribute
                                existing.add_attribute(
                                    attr.key,
                                    attr.value,
                                    attr.confidence,
                                    attr.source_span
                                )
                            elif attr.confidence > max(e.confidence for e in existing_attrs):
                                # Replace with higher confidence attribute
                                existing.attributes = [
                                    a for a in existing.attributes
                                    if a.key != attr.key
                                ]
                                existing.add_attribute(
                                    attr.key,
                                    attr.value,
                                    attr.confidence,
                                    attr.source_span
                                )
                        
                        # Update merged entities map
                        merged_entities[entity_id] = existing.id
                        match_found = True
                        break
                
                if not match_found:
                    # Add as a new entity
                    merged_graph.add_entity(entity)
                    merged_entities[entity_id] = entity.id
        
        # Then, add all relationships
        for graph in graphs:
            for rel_id, rel in graph.relationships.items():
                # Update source and target IDs
                source_id = merged_entities.get(rel.source_id, rel.source_id)
                target_id = merged_entities.get(rel.target_id, rel.target_id)
                
                # Create a new relationship with updated IDs
                new_rel = Relationship(
                    id=rel.id,
                    source_id=source_id,
                    target_id=target_id,
                    type=rel.type,
                    directed=rel.directed,
                    attributes=rel.attributes,
                    confidence=rel.confidence,
                    source_span=rel.source_span
                )
                
                try:
                    merged_graph.add_relationship(new_rel)
                except ValueError as e:
                    logger.warning(f"Error adding relationship during merge: {str(e)}")
        
        logger.info(f"Merged {len(graphs)} graphs into a graph with {len(merged_graph.entities)} entities and {len(merged_graph.relationships)} relationships")
        return merged_graph
    
    def validate_graph(self, graph: KnowledgeGraph) -> Tuple[bool, List[str]]:
        """Validate a knowledge graph.
        
        Args:
            graph: Knowledge graph to validate
            
        Returns:
            (is_valid, error_messages) tuple
        """
        errors = []
        
        # Check for dangling relationships
        for rel_id, rel in graph.relationships.items():
            if rel.source_id not in graph.entities:
                errors.append(f"Relationship {rel_id} has dangling source entity {rel.source_id}")
            
            if rel.target_id not in graph.entities:
                errors.append(f"Relationship {rel_id} has dangling target entity {rel.target_id}")
        
        # Check for disconnected components
        nx_graph = graph.to_networkx()
        if not nx.is_weakly_connected(nx_graph):
            components = list(nx.weakly_connected_components(nx_graph))
            errors.append(f"Graph is disconnected with {len(components)} components")
        
        # Check for self-loops
        for node in nx_graph.nodes():
            if nx_graph.has_edge(node, node):
                entity = graph.get_entity(node)
                if entity:
                    errors.append(f"Entity {entity.name} has a self-loop")
        
        # Check for attribute consistency
        entity_types = {}
        for entity_id, entity in graph.entities.items():
            entity_type = entity.type.lower()
            
            if entity_type not in entity_types:
                entity_types[entity_type] = set()
            
            # Collect attribute keys for this entity
            for attr in entity.attributes:
                entity_types[entity_type].add(attr.key)
        
        # Check if entities of the same type have consistent attributes
        for entity_type, attr_keys in entity_types.items():
            entities_of_type = graph.get_entities_by_type(entity_type)
            
            for entity in entities_of_type:
                entity_attr_keys = {attr.key for attr in entity.attributes}
                missing_attrs = attr_keys - entity_attr_keys
                
                if missing_attrs and len(missing_attrs) > 3:  # Allow some flexibility
                    errors.append(f"Entity {entity.name} is missing common attributes: {', '.join(missing_attrs)}")
        
        return len(errors) == 0, errors