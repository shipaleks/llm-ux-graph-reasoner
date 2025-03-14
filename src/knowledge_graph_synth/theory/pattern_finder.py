"""Pattern finding for the knowledge graph synthesis system."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID

import networkx as nx

from ..models import KnowledgeGraph, Entity, Relationship, SourceSpan
from ..llm import LLMProviderFactory, prompt_manager
from ..llm.schemas import get_pattern_identification_schema
from ..config import settings

logger = logging.getLogger(__name__)


class PatternFinder:
    """Finds patterns in knowledge graphs.
    
    This class implements algorithms for identifying patterns in knowledge graphs,
    including structural patterns, temporal patterns, and semantic patterns.
    """
    
    def __init__(self, 
               provider_name: Optional[str] = None,
               confidence_threshold: float = settings.DEFAULT_CONFIDENCE_THRESHOLD):
        """Initialize the pattern finder.
        
        Args:
            provider_name: Name of the LLM provider to use
            confidence_threshold: Minimum confidence score for patterns
        """
        self.provider_name = provider_name
        self.confidence_threshold = confidence_threshold
    
    async def find_patterns(self, graph: KnowledgeGraph) -> List[Dict[str, Any]]:
        """Find patterns in a knowledge graph.
        
        Args:
            graph: Knowledge graph to analyze
            
        Returns:
            List of identified patterns
        """
        patterns = []
        
        # Find structural patterns
        structural_patterns = await self._find_structural_patterns(graph)
        patterns.extend(structural_patterns)
        
        # Find semantic patterns using LLM
        semantic_patterns = await self._find_semantic_patterns(graph)
        patterns.extend(semantic_patterns)
        
        # Filter patterns by confidence
        filtered_patterns = [
            pattern for pattern in patterns
            if pattern.get("confidence", 0) >= self.confidence_threshold
        ]
        
        logger.info(f"Found {len(filtered_patterns)} patterns in the graph")
        return filtered_patterns
    
    async def _find_structural_patterns(self, graph: KnowledgeGraph) -> List[Dict[str, Any]]:
        """Find structural patterns in a knowledge graph.
        
        Args:
            graph: Knowledge graph to analyze
            
        Returns:
            List of structural patterns
        """
        patterns = []
        nx_graph = graph.to_networkx()
        
        # Check for starlike patterns (nodes with many connections)
        degrees = dict(nx_graph.degree())
        high_degree_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for node_id, degree in high_degree_nodes:
            if degree >= 5:  # Only consider high-degree nodes
                entity = graph.get_entity(node_id)
                if entity:
                    # Get connecting entities
                    connections = graph.get_connected_entities(node_id)
                    connected_names = [e.name for e, _ in connections[:5]]
                    
                    pattern = {
                        "name": f"Hub: {entity.name}",
                        "type": "structural",
                        "subtype": "hub",
                        "description": f"{entity.name} is a central entity connected to many others",
                        "entities": [str(node_id)],
                        "examples": [
                            {
                                "text": f"{entity.name} is connected to {', '.join(connected_names[:3])}",
                                "explanation": f"{entity.name} serves as a hub connecting multiple entities"
                            }
                        ],
                        "confidence": 0.8
                    }
                    patterns.append(pattern)
        
        # Check for clusters (densely connected components)
        components = list(nx.weakly_connected_components(nx_graph))
        for i, component in enumerate(components):
            if len(component) >= 5:  # Only consider larger components
                component_subgraph = nx_graph.subgraph(component)
                density = nx.density(component_subgraph)
                
                if density >= 0.4:  # Only consider dense components
                    # Get entities in this component
                    component_entities = [graph.get_entity(node_id) for node_id in component]
                    component_entities = [e for e in component_entities if e]
                    
                    if component_entities:
                        # Get entity names and types
                        entity_names = [e.name for e in component_entities[:5]]
                        entity_types = set(e.type for e in component_entities)
                        common_type = max(entity_types, key=lambda t: sum(1 for e in component_entities if e.type == t))
                        
                        pattern = {
                            "name": f"Cluster of {common_type}",
                            "type": "structural",
                            "subtype": "cluster",
                            "description": f"A densely connected group of {len(component)} entities, mostly of type {common_type}",
                            "entities": [str(e.id) for e in component_entities[:10]],
                            "examples": [
                                {
                                    "text": f"The cluster includes {', '.join(entity_names[:3])}",
                                    "explanation": f"These entities form a cohesive group with many interconnections"
                                }
                            ],
                            "confidence": 0.7 + (density * 0.3)  # Higher confidence for denser clusters
                        }
                        patterns.append(pattern)
        
        # Check for chains (path-like structures)
        for source, target in nx.dfs_edges(nx_graph.to_undirected()):
            # Find paths between these nodes
            try:
                paths = list(nx.all_simple_paths(nx_graph, source, target, cutoff=4))
                for path in paths:
                    if len(path) >= 4:  # Only consider longer paths
                        # Get entities in this path
                        path_entities = [graph.get_entity(node_id) for node_id in path]
                        path_entities = [e for e in path_entities if e]
                        
                        if len(path_entities) >= 4:
                            # Get entity names
                            entity_names = [e.name for e in path_entities]
                            
                            pattern = {
                                "name": f"Chain: {entity_names[0]} to {entity_names[-1]}",
                                "type": "structural",
                                "subtype": "chain",
                                "description": f"A sequential path of {len(path)} entities",
                                "entities": [str(e.id) for e in path_entities],
                                "examples": [
                                    {
                                        "text": f"{' → '.join(entity_names)}",
                                        "explanation": f"These entities form a sequential chain of relationships"
                                    }
                                ],
                                "confidence": 0.7
                            }
                            patterns.append(pattern)
            except nx.NetworkXNoPath:
                continue
        
        return patterns
    
    async def _find_semantic_patterns(self, graph: KnowledgeGraph) -> List[Dict[str, Any]]:
        """Find semantic patterns in a knowledge graph using LLM.
        
        Args:
            graph: Knowledge graph to analyze
            
        Returns:
            List of semantic patterns
        """
        # Get the LLM provider
        try:
            # Use reasoning provider for pattern identification
            provider = LLMProviderFactory.get_reasoning_provider()
            if not provider:
                provider = LLMProviderFactory.get_provider(self.provider_name)
                
            if not provider:
                logger.error("No LLM provider available for pattern identification")
                return []
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
        
        # Create a summary of the graph
        entities_by_type = {}
        for entity_id, entity in graph.entities.items():
            entity_type = entity.type.lower()
            
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            
            entities_by_type[entity_type].append(entity)
        
        relationships_by_type = {}
        for rel_id, rel in graph.relationships.items():
            rel_type = rel.type.lower()
            
            if rel_type not in relationships_by_type:
                relationships_by_type[rel_type] = []
            
            relationships_by_type[rel_type].append(rel)
        
        # Create the graph summary
        graph_summary = f"A knowledge graph with {len(graph.entities)} entities and {len(graph.relationships)} relationships.\n\n"
        
        # Add entity type summary
        graph_summary += "Entity types:\n"
        for entity_type, entities in entities_by_type.items():
            graph_summary += f"- {entity_type}: {len(entities)} entities\n"
            
            # Add examples of this type
            examples = entities[:3]
            if examples:
                graph_summary += "  Examples: " + ", ".join(e.name for e in examples) + "\n"
        
        # Add relationship type summary
        graph_summary += "\nRelationship types:\n"
        for rel_type, relationships in relationships_by_type.items():
            graph_summary += f"- {rel_type}: {len(relationships)} relationships\n"
            
            # Add examples of this type
            examples = relationships[:3]
            if examples:
                example_texts = []
                for rel in examples:
                    source = graph.get_entity(rel.source_id)
                    target = graph.get_entity(rel.target_id)
                    
                    if source and target:
                        example_texts.append(f"{source.name} → {target.name}")
                
                if example_texts:
                    graph_summary += "  Examples: " + ", ".join(example_texts) + "\n"
        
        # Create a prompt for pattern identification
        prompt = f"""
Analyze the following knowledge graph summary and identify meaningful patterns. These patterns can be semantic, narrative, or relational in nature.

{graph_summary}

Identify 3-5 significant patterns in this knowledge graph. For each pattern:
1. Give it a clear, descriptive name
2. Categorize it by type (semantic, narrative, relational, etc.)
3. Provide a detailed description of the pattern
4. Give specific examples from the graph that illustrate this pattern
5. Explain the significance or meaning of this pattern
6. Rate your confidence in this pattern (0-1)

Focus on non-obvious patterns that provide genuine insight. These might include:
- Recurring relationship structures
- Semantic clusters or groupings
- Temporal or causal sequences
- Narrative structures or themes
- Unexpected connections or anomalies

For each pattern, provide substantive examples and explain why they matter.
"""
        
        # Get the response schema
        schema = get_pattern_identification_schema()
        
        # Generate the patterns
        try:
            response = await provider.generate_structured(prompt, schema)
            
            # Extract patterns from the response
            patterns = response.get("patterns", [])
            
            # Process the patterns
            processed_patterns = []
            for pattern in patterns:
                # Convert to our standard pattern format
                processed_pattern = {
                    "name": pattern.get("name", "Unnamed Pattern"),
                    "type": pattern.get("type", "unknown"),
                    "subtype": "semantic",  # All LLM-generated patterns are semantic
                    "description": pattern.get("description", ""),
                    "examples": pattern.get("examples", []),
                    "confidence": pattern.get("confidence", 0.5),
                    "significance": pattern.get("significance", "")
                }
                
                processed_patterns.append(processed_pattern)
            
            return processed_patterns
            
        except Exception as e:
            logger.error(f"Error identifying semantic patterns: {str(e)}")
            return []