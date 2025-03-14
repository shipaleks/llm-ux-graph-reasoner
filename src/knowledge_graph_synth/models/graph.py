"""Graph models for the knowledge graph synthesis system."""

from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID

import networkx as nx

from pydantic import BaseModel, Field, ConfigDict

from .entity import Entity
from .relationship import Relationship


class KnowledgeGraph(BaseModel):
    """A knowledge graph constructed from entities and relationships.
    
    This class represents a knowledge graph built from entities (nodes) and
    relationships (edges) extracted from text. It provides methods for adding,
    retrieving, and querying graph elements, as well as converting to and from
    NetworkX graph objects for analysis.
    """
    
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)
    
    entities: Dict[UUID, Entity] = Field(default_factory=dict)
    relationships: Dict[UUID, Relationship] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    _graph: Optional[nx.MultiDiGraph] = None
    
    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the graph.
        
        Args:
            entity: Entity to add
        """
        self.entities[entity.id] = entity
        self._graph = None  # Invalidate cached graph
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the graph.
        
        Args:
            relationship: Relationship to add
        """
        # Verify that source and target entities exist
        if relationship.source_id not in self.entities:
            raise ValueError(f"Source entity {relationship.source_id} not found")
        
        if relationship.target_id not in self.entities:
            raise ValueError(f"Target entity {relationship.target_id} not found")
        
        self.relationships[relationship.id] = relationship
        self._graph = None  # Invalidate cached graph
    
    def get_entity(self, entity_id: UUID) -> Optional[Entity]:
        """Get an entity by ID.
        
        Args:
            entity_id: UUID of the entity to retrieve
            
        Returns:
            The entity if found, otherwise None
        """
        return self.entities.get(entity_id)
    
    def get_relationship(self, relationship_id: UUID) -> Optional[Relationship]:
        """Get a relationship by ID.
        
        Args:
            relationship_id: UUID of the relationship to retrieve
            
        Returns:
            The relationship if found, otherwise None
        """
        return self.relationships.get(relationship_id)
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type.
        
        Args:
            entity_type: Type of entities to retrieve
            
        Returns:
            List of matching entities
        """
        return [
            entity for entity in self.entities.values()
            if entity.type.lower() == entity_type.lower()
        ]
    
    def get_relationships_by_type(self, relationship_type: str) -> List[Relationship]:
        """Get all relationships of a specific type.
        
        Args:
            relationship_type: Type of relationships to retrieve
            
        Returns:
            List of matching relationships
        """
        return [
            rel for rel in self.relationships.values()
            if rel.type.lower() == relationship_type.lower()
        ]
    
    def get_entity_relationships(self, entity_id: UUID, 
                               outgoing: bool = True, 
                               incoming: bool = True) -> List[Relationship]:
        """Get all relationships involving an entity.
        
        Args:
            entity_id: UUID of the entity
            outgoing: Include relationships where entity is the source
            incoming: Include relationships where entity is the target
            
        Returns:
            List of relationships involving the entity
        """
        result = []
        
        if outgoing:
            result.extend([
                rel for rel in self.relationships.values()
                if rel.source_id == entity_id
            ])
        
        if incoming:
            result.extend([
                rel for rel in self.relationships.values()
                if rel.target_id == entity_id
            ])
        
        return result
    
    def get_connected_entities(self, entity_id: UUID,
                             outgoing: bool = True,
                             incoming: bool = True) -> List[Tuple[Entity, Relationship]]:
        """Get all entities connected to an entity.
        
        Args:
            entity_id: UUID of the entity
            outgoing: Include entities connected via outgoing relationships
            incoming: Include entities connected via incoming relationships
            
        Returns:
            List of (entity, relationship) tuples
        """
        result = []
        
        for rel in self.get_entity_relationships(entity_id, outgoing, incoming):
            if rel.source_id == entity_id and outgoing:
                target = self.get_entity(rel.target_id)
                if target:
                    result.append((target, rel))
            
            if rel.target_id == entity_id and incoming:
                source = self.get_entity(rel.source_id)
                if source:
                    result.append((source, rel))
        
        return result
    
    def to_networkx(self) -> nx.MultiDiGraph:
        """Convert to a NetworkX graph.
        
        Returns:
            NetworkX MultiDiGraph representation of the knowledge graph
        """
        if self._graph is not None:
            return self._graph
        
        G = nx.MultiDiGraph()
        
        # Add entity nodes
        for entity_id, entity in self.entities.items():
            G.add_node(
                entity_id, 
                name=entity.name,
                type=entity.type,
                attributes={attr.key: attr.value for attr in entity.attributes},
                confidence=entity.confidence,
                entity=entity
            )
        
        # Add relationship edges
        for rel_id, rel in self.relationships.items():
            G.add_edge(
                rel.source_id,
                rel.target_id,
                key=rel_id,
                type=rel.type,
                attributes={attr.key: attr.value for attr in rel.attributes},
                confidence=rel.confidence,
                relationship=rel
            )
        
        self._graph = G
        return G
    
    @classmethod
    def from_networkx(cls, G: nx.MultiDiGraph) -> 'KnowledgeGraph':
        """Create a knowledge graph from a NetworkX graph.
        
        Args:
            G: NetworkX MultiDiGraph
            
        Returns:
            KnowledgeGraph instance
        """
        kg = cls()
        
        # Add entities from nodes
        for node_id, data in G.nodes(data=True):
            if 'entity' in data:
                kg.add_entity(data['entity'])
        
        # Add relationships from edges
        for source_id, target_id, key, data in G.edges(data=True, keys=True):
            if 'relationship' in data:
                kg.add_relationship(data['relationship'])
        
        return kg
    
    def filter_by_confidence(self, threshold: float) -> 'KnowledgeGraph':
        """Create a new knowledge graph filtered by confidence.
        
        Args:
            threshold: Minimum confidence score
            
        Returns:
            New KnowledgeGraph with filtered entities and relationships
        """
        kg = KnowledgeGraph()
        
        # Filter entities by confidence
        for entity_id, entity in self.entities.items():
            if entity.confidence >= threshold:
                kg.add_entity(entity)
        
        # Filter relationships by confidence
        for rel_id, rel in self.relationships.items():
            if rel.confidence >= threshold and \
               rel.source_id in kg.entities and \
               rel.target_id in kg.entities:
                kg.add_relationship(rel)
        
        return kg