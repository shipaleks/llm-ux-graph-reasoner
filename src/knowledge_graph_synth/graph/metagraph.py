"""Meta-graph creation for the knowledge graph synthesis system."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID, uuid4

from ..models import KnowledgeGraph, Entity, Relationship, SourceSpan
from ..llm import LLMProviderFactory
from .analysis import GraphAnalyzer
from ..config import settings

logger = logging.getLogger(__name__)


class MetaGraphBuilder:
    """Builds a meta-graph from a knowledge graph.
    
    This class implements the creation of meta-graphs, which abstract
    the original graph into higher-level concepts and relationships,
    enabling higher-level reasoning and pattern identification.
    """
    
    def __init__(self, 
               provider_name: Optional[str] = None,
               min_cluster_size: int = 3,
               confidence_threshold: float = settings.DEFAULT_CONFIDENCE_THRESHOLD):
        """Initialize the meta-graph builder.
        
        Args:
            provider_name: Name of the LLM provider to use
            min_cluster_size: Minimum size for entity clusters
            confidence_threshold: Minimum confidence score for elements
        """
        self.provider_name = provider_name
        self.min_cluster_size = min_cluster_size
        self.confidence_threshold = confidence_threshold
        self.analyzer = GraphAnalyzer()
    
    async def build_metagraph(self, graph: KnowledgeGraph) -> KnowledgeGraph:
        """Build a meta-graph from a knowledge graph.
        
        Args:
            graph: Original knowledge graph
            
        Returns:
            Meta-graph (higher-level abstraction)
        """
        # Create a new graph for the meta-graph
        metagraph = KnowledgeGraph()
        
        # Detect communities in the original graph
        communities = self.analyzer.detect_communities(graph)
        
        # Filter out small communities
        large_communities = {
            community_id: entities 
            for community_id, entities in communities.items()
            if len(entities) >= self.min_cluster_size
        }
        
        if not large_communities:
            logger.warning("No sufficiently large communities found for meta-graph creation")
            return metagraph
        
        # Generate meta-concepts for each community
        meta_concepts = await self._generate_meta_concepts(graph, large_communities)
        
        # Add meta-concepts to the meta-graph
        for meta_concept in meta_concepts:
            metagraph.add_entity(meta_concept)
        
        # Create a mapping from original entities to meta-concept IDs
        entity_to_meta = {}
        for meta_concept in meta_concepts:
            # Get member entities from attributes
            for attr in meta_concept.attributes:
                if attr.key == "member_entities":
                    member_ids = attr.value
                    for member_id in member_ids:
                        entity_to_meta[UUID(member_id)] = meta_concept.id
        
        # Generate meta-relationships between meta-concepts
        meta_relationships = await self._generate_meta_relationships(
            graph, meta_concepts, entity_to_meta
        )
        
        # Add meta-relationships to the meta-graph
        for rel in meta_relationships:
            try:
                metagraph.add_relationship(rel)
            except ValueError as e:
                logger.warning(f"Error adding meta-relationship: {str(e)}")
        
        logger.info(f"Created meta-graph with {len(metagraph.entities)} meta-concepts and {len(metagraph.relationships)} meta-relationships")
        return metagraph
    
    async def _generate_meta_concepts(self, 
                                  graph: KnowledgeGraph,
                                  communities: Dict[int, List[Entity]]) -> List[Entity]:
        """Generate meta-concepts for entity communities.
        
        Args:
            graph: Original knowledge graph
            communities: Dictionary of entity communities
            
        Returns:
            List of meta-concept entities
        """
        # Get the LLM provider
        try:
            # Use reasoning provider for abstraction
            provider = LLMProviderFactory.get_reasoning_provider()
            if not provider:
                provider = LLMProviderFactory.get_provider(self.provider_name)
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
        
        meta_concepts = []
        
        for community_id, entities in communities.items():
            # Skip small communities
            if len(entities) < self.min_cluster_size:
                continue
            
            # Create a description of the community
            community_desc = f"Community {community_id} containing {len(entities)} entities:\n"
            
            for i, entity in enumerate(entities[:10]):  # Limit to 10 entities for clarity
                community_desc += f"{i+1}. {entity.name} (Type: {entity.type})\n"
                
                # Add up to 3 attributes per entity
                for j, attr in enumerate(entity.attributes[:3]):
                    community_desc += f"   - {attr.key}: {attr.value}\n"
            
            if len(entities) > 10:
                community_desc += f"... and {len(entities) - 10} more entities\n"
            
            # Create a prompt for generating a meta-concept
            prompt = f"""
Analyze the following community of entities from a knowledge graph and generate a higher-level meta-concept that encompasses them.

{community_desc}

Your task is to:
1. Identify a unifying theme, concept, or category that these entities belong to
2. Create a name for this meta-concept
3. Determine the most appropriate type for this meta-concept
4. List the key attributes that characterize this meta-concept
5. Explain why these entities form a coherent group

Format your response as follows:
- Name: [short, descriptive name for the meta-concept]
- Type: [appropriate type/category for the meta-concept]
- Attributes: [list key attributes that define this meta-concept]
- Justification: [explain why these entities form a coherent group]
"""
            
            # Generate the meta-concept
            try:
                response = await provider.generate_text(prompt)
                
                # Parse the response
                meta_name = ""
                meta_type = ""
                meta_attrs = []
                justification = ""
                
                for line in response.split("\n"):
                    line = line.strip()
                    
                    if line.startswith("- Name:") or line.startswith("Name:"):
                        meta_name = line.split(":", 1)[1].strip()
                    elif line.startswith("- Type:") or line.startswith("Type:"):
                        meta_type = line.split(":", 1)[1].strip()
                    elif line.startswith("- Attributes:") or line.startswith("Attributes:"):
                        attr_text = line.split(":", 1)[1].strip()
                        if attr_text:
                            meta_attrs = [attr.strip() for attr in attr_text.split(",")]
                    elif line.startswith("- Justification:") or line.startswith("Justification:"):
                        justification = line.split(":", 1)[1].strip()
                
                # Create a meta-concept entity
                if meta_name and meta_type:
                    # Create a source span from the justification
                    source_span = SourceSpan(
                        start=0,
                        end=len(justification),
                        text=justification
                    )
                    
                    meta_concept = Entity(
                        name=meta_name,
                        type=f"meta:{meta_type}",
                        confidence=0.8,  # Default confidence for meta-concepts
                        source_span=source_span
                    )
                    
                    # Add attributes
                    for i, attr_text in enumerate(meta_attrs):
                        meta_concept.add_attribute(
                            f"attribute_{i+1}",
                            attr_text,
                            confidence=0.7
                        )
                    
                    # Add justification
                    if justification:
                        meta_concept.add_attribute(
                            "justification",
                            justification,
                            confidence=0.8
                        )
                    
                    # Add member entities
                    member_ids = [str(entity.id) for entity in entities]
                    meta_concept.add_attribute(
                        "member_entities",
                        member_ids,
                        confidence=1.0
                    )
                    
                    meta_concepts.append(meta_concept)
                
            except Exception as e:
                logger.error(f"Error generating meta-concept for community {community_id}: {str(e)}")
        
        return meta_concepts
    
    async def _generate_meta_relationships(self, 
                                      graph: KnowledgeGraph,
                                      meta_concepts: List[Entity],
                                      entity_to_meta: Dict[UUID, UUID]) -> List[Relationship]:
        """Generate meta-relationships between meta-concepts.
        
        Args:
            graph: Original knowledge graph
            meta_concepts: List of meta-concept entities
            entity_to_meta: Mapping from original entities to meta-concepts
            
        Returns:
            List of meta-relationships
        """
        # Get the LLM provider
        try:
            # Use reasoning provider for relationship abstraction
            provider = LLMProviderFactory.get_reasoning_provider()
            if not provider:
                provider = LLMProviderFactory.get_provider(self.provider_name)
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
        
        # Create a map of meta-concept IDs to names
        meta_id_to_name = {concept.id: concept.name for concept in meta_concepts}
        
        # Create a map of meta-concept IDs to types
        meta_id_to_type = {concept.id: concept.type for concept in meta_concepts}
        
        # Count relationships between meta-concepts
        meta_rel_counts = {}
        
        for rel_id, rel in graph.relationships.items():
            if rel.source_id in entity_to_meta and rel.target_id in entity_to_meta:
                source_meta = entity_to_meta[rel.source_id]
                target_meta = entity_to_meta[rel.target_id]
                
                # Skip self-relationships at the meta level
                if source_meta == target_meta:
                    continue
                
                key = (source_meta, target_meta)
                
                if key not in meta_rel_counts:
                    meta_rel_counts[key] = {}
                
                rel_type = rel.type.lower()
                
                if rel_type not in meta_rel_counts[key]:
                    meta_rel_counts[key][rel_type] = 0
                
                meta_rel_counts[key][rel_type] += 1
        
        # Generate meta-relationships
        meta_relationships = []
        
        for (source_meta, target_meta), rel_types in meta_rel_counts.items():
            # Find the most common relationship type
            most_common_type = max(rel_types.items(), key=lambda x: x[1])
            rel_type = most_common_type[0]
            count = most_common_type[1]
            
            # Only create a meta-relationship if there are enough relationships
            if count < 2:
                continue
                
            # Get meta-concept names and types
            source_name = meta_id_to_name.get(source_meta, "Unknown")
            target_name = meta_id_to_name.get(target_meta, "Unknown")
            source_type = meta_id_to_type.get(source_meta, "Unknown")
            target_type = meta_id_to_type.get(target_meta, "Unknown")
            
            # Create a prompt for generating a meta-relationship
            prompt = f"""
Analyze the relationship between these two meta-concepts:

Source: {source_name} (Type: {source_type})
Target: {target_name} (Type: {target_type})

The most common relationship type between entities in these meta-concepts is: {rel_type} (occurs {count} times)

Generate a higher-level meta-relationship that captures the essence of how these two meta-concepts relate to each other.

Format your response as follows:
- Relationship Type: [concise description of the relationship]
- Description: [explain the nature of this relationship]
- Bidirectional: [yes/no - whether the relationship applies equally in both directions]
"""
            
            # Generate the meta-relationship
            try:
                response = await provider.generate_text(prompt)
                
                # Parse the response
                meta_rel_type = ""
                description = ""
                bidirectional = False
                
                for line in response.split("\n"):
                    line = line.strip()
                    
                    if line.startswith("- Relationship Type:") or line.startswith("Relationship Type:"):
                        meta_rel_type = line.split(":", 1)[1].strip()
                    elif line.startswith("- Description:") or line.startswith("Description:"):
                        description = line.split(":", 1)[1].strip()
                    elif line.startswith("- Bidirectional:") or line.startswith("Bidirectional:"):
                        bid_text = line.split(":", 1)[1].strip().lower()
                        bidirectional = "yes" in bid_text or "true" in bid_text
                
                # Create a meta-relationship
                if meta_rel_type:
                    # Create a source span from the description
                    source_span = SourceSpan(
                        start=0,
                        end=len(description),
                        text=description
                    )
                    
                    meta_relationship = Relationship(
                        source_id=source_meta,
                        target_id=target_meta,
                        type=f"meta:{meta_rel_type}",
                        directed=not bidirectional,
                        confidence=0.7,  # Default confidence for meta-relationships
                        source_span=source_span
                    )
                    
                    # Add description as an attribute
                    if description:
                        meta_relationship.add_attribute(
                            "description",
                            description,
                            confidence=0.8
                        )
                    
                    # Add count as an attribute
                    meta_relationship.add_attribute(
                        "instance_count",
                        count,
                        confidence=1.0
                    )
                    
                    meta_relationships.append(meta_relationship)
                
            except Exception as e:
                logger.error(f"Error generating meta-relationship: {str(e)}")
        
        return meta_relationships