"""Coreference resolution for the knowledge graph synthesis system."""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID
import re

from ..models import Entity, Relationship

logger = logging.getLogger(__name__)


class CoreferenceResolver:
    """Resolves coreferences between entities.
    
    This class identifies and merges entities that refer to the same real-world object,
    combining their attributes and maintaining provenance.
    """
    
    def __init__(self, 
               name_similarity_threshold: float = 0.8,
               exact_type_match: bool = False):
        """Initialize the coreference resolver.
        
        Args:
            name_similarity_threshold: Threshold for name similarity (0-1)
            exact_type_match: Whether to require exact type matches
        """
        self.name_similarity_threshold = name_similarity_threshold
        self.exact_type_match = exact_type_match
    
    def resolve_entities(self, entities: List[Entity]) -> List[Entity]:
        """Identify and merge coreferent entities.
        
        Args:
            entities: List of entities to resolve
            
        Returns:
            List of merged entities
        """
        if not entities:
            return []
        
        # Group entities by canonical form of their names
        canonical_groups = {}
        for entity in entities:
            canonical_name = self._get_canonical_name(entity.name)
            
            if canonical_name not in canonical_groups:
                canonical_groups[canonical_name] = []
            
            canonical_groups[canonical_name].append(entity)
        
        # For each group, check if they should be merged
        merged_entities = []
        
        for canonical_name, group in canonical_groups.items():
            if len(group) == 1:
                # Only one entity in this group, no need to merge
                merged_entities.append(group[0])
                continue
            
            # Group by type
            type_groups = {}
            for entity in group:
                entity_type = entity.type.lower()
                
                if entity_type not in type_groups:
                    type_groups[entity_type] = []
                
                type_groups[entity_type].append(entity)
            
            # Merge entities of the same type
            for entity_type, type_group in type_groups.items():
                if len(type_group) == 1:
                    # Only one entity of this type, no need to merge
                    merged_entities.append(type_group[0])
                else:
                    # Merge entities
                    merged_entity = self._merge_entities(type_group)
                    merged_entities.append(merged_entity)
        
        logger.info(f"Resolved {len(entities)} entities into {len(merged_entities)} unique entities")
        return merged_entities
    
    def update_relationships(self, 
                          relationships: List[Relationship],
                          old_to_new_ids: Dict[UUID, UUID]) -> List[Relationship]:
        """Update relationships to use merged entity IDs.
        
        Args:
            relationships: List of relationships to update
            old_to_new_ids: Mapping from old entity IDs to new entity IDs
            
        Returns:
            Updated list of relationships
        """
        updated_relationships = []
        
        for relationship in relationships:
            source_id = relationship.source_id
            target_id = relationship.target_id
            
            # Update source and target IDs
            if source_id in old_to_new_ids:
                source_id = old_to_new_ids[source_id]
            
            if target_id in old_to_new_ids:
                target_id = old_to_new_ids[target_id]
            
            # Skip self-relationships (where source and target are the same)
            if source_id == target_id:
                continue
            
            # Create updated relationship
            updated_relationship = Relationship(
                id=relationship.id,
                source_id=source_id,
                target_id=target_id,
                type=relationship.type,
                directed=relationship.directed,
                attributes=relationship.attributes,
                confidence=relationship.confidence,
                source_span=relationship.source_span
            )
            
            updated_relationships.append(updated_relationship)
        
        # Remove duplicate relationships
        unique_relationships = self._deduplicate_relationships(updated_relationships)
        
        logger.info(f"Updated {len(relationships)} relationships to {len(unique_relationships)} unique relationships")
        return unique_relationships
    
    def _get_canonical_name(self, name: str) -> str:
        """Get the canonical form of a name for comparison.
        
        Args:
            name: Entity name
            
        Returns:
            Canonical form of the name
        """
        # Convert to lowercase
        canonical = name.lower()
        
        # Remove common prefixes like "the", "a", "an"
        canonical = re.sub(r'^(the|a|an)\s+', '', canonical)
        
        # Remove punctuation and extra whitespace
        canonical = re.sub(r'[^\w\s]', '', canonical)
        canonical = re.sub(r'\s+', ' ', canonical).strip()
        
        return canonical
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names.
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Similarity score (0-1)
        """
        # For now, use a simple exact match of canonical forms
        canonical1 = self._get_canonical_name(name1)
        canonical2 = self._get_canonical_name(name2)
        
        if canonical1 == canonical2:
            return 1.0
        
        # Check if one is contained in the other
        if canonical1 in canonical2 or canonical2 in canonical1:
            return 0.9
        
        # TODO: Implement more sophisticated string similarity metrics
        # like Levenshtein distance, Jaccard similarity, etc.
        
        return 0.0
    
    def _merge_entities(self, entities: List[Entity]) -> Entity:
        """Merge a list of entities into a single entity.
        
        Args:
            entities: List of entities to merge
            
        Returns:
            Merged entity
        """
        if not entities:
            raise ValueError("No entities to merge")
        
        if len(entities) == 1:
            return entities[0]
        
        # Sort entities by confidence (highest first)
        sorted_entities = sorted(entities, key=lambda e: e.confidence, reverse=True)
        
        # Use the highest confidence entity as the base
        base_entity = sorted_entities[0]
        
        # Create a new entity with the same core properties
        merged_entity = Entity(
            name=base_entity.name,
            type=base_entity.type,
            confidence=base_entity.confidence,
            source_span=base_entity.source_span
        )
        
        # Collect all attributes
        all_attributes = {}
        
        for entity in sorted_entities:
            for attr in entity.attributes:
                key = attr.key.lower()
                
                if key not in all_attributes or attr.confidence > all_attributes[key].confidence:
                    all_attributes[key] = attr
        
        # Add attributes to merged entity
        for attr in all_attributes.values():
            merged_entity.add_attribute(
                attr.key,
                attr.value,
                attr.confidence,
                attr.source_span
            )
        
        return merged_entity
    
    def _deduplicate_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """Remove duplicate relationships.
        
        Args:
            relationships: List of relationships to deduplicate
            
        Returns:
            List of unique relationships
        """
        unique_relationships = {}
        
        for relationship in relationships:
            # Create a unique key for the relationship
            key = (
                str(relationship.source_id),
                str(relationship.target_id),
                relationship.type.lower()
            )
            
            # If this is a bidirectional relationship, ensure consistent ordering
            if not relationship.directed:
                source_id = str(relationship.source_id)
                target_id = str(relationship.target_id)
                
                if source_id > target_id:
                    key = (target_id, source_id, relationship.type.lower())
            
            # Keep the highest confidence relationship
            if key not in unique_relationships or relationship.confidence > unique_relationships[key].confidence:
                unique_relationships[key] = relationship
        
        return list(unique_relationships.values())