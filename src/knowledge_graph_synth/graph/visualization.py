"""Graph visualization for the knowledge graph synthesis system."""

import logging
import os
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID
from pathlib import Path

import networkx as nx
from pyvis.network import Network

from ..models import KnowledgeGraph, Entity, Relationship
from ..config import settings

logger = logging.getLogger(__name__)


class GraphVisualizer:
    """Visualizes knowledge graphs.
    
    This class implements visualization of knowledge graphs using various
    formats and layouts, with support for highlighting important structures
    and interactive exploration.
    """
    
    def __init__(self, 
               output_dir: Optional[str] = None,
               height: str = "600px",
               width: str = "100%"):
        """Initialize the graph visualizer.
        
        Args:
            output_dir: Directory to save visualization files
            height: Height of the visualization
            width: Width of the visualization
        """
        self.output_dir = output_dir or os.getcwd()
        self.height = height
        self.width = width
    
    def visualize_html(self, 
                     graph: KnowledgeGraph,
                     filename: str = "knowledge_graph.html",
                     title: str = "Knowledge Graph",
                     show_labels: bool = True,
                     filter_threshold: Optional[float] = None,
                     generate_report: bool = True) -> str:
        """Visualize a knowledge graph as an interactive HTML file.
        
        Args:
            graph: Knowledge graph to visualize
            filename: Output HTML filename
            title: Title for the visualization
            show_labels: Whether to show labels on edges
            filter_threshold: Optional confidence threshold to filter elements
            
        Returns:
            Path to the generated HTML file
        """
        # Filter the graph if a threshold is provided
        if filter_threshold is not None:
            filtered_graph = graph.filter_by_confidence(filter_threshold)
        else:
            filtered_graph = graph
        
        # Create network
        net = Network(height=self.height, width=self.width, directed=True, notebook=False)
        net.set_options("""
        var options = {
            "nodes": {
                "font": {
                    "size": 14,
                    "face": "Tahoma"
                },
                "shape": "dot",
                "size": 20
            },
            "edges": {
                "font": {
                    "size": 12,
                    "align": "middle"
                },
                "arrows": {
                    "to": {
                        "enabled": true,
                        "scaleFactor": 0.5
                    }
                },
                "smooth": {
                    "type": "continuous",
                    "forceDirection": "none"
                }
            },
            "physics": {
                "barnesHut": {
                    "gravitationalConstant": -8000,
                    "centralGravity": 0.5,
                    "springLength": 300,
                    "springConstant": 0.04
                },
                "minVelocity": 0.75,
                "solver": "barnesHut"
            }
        }
        """)
        
        # Create a color map for entity types
        entity_types = set(entity.type.lower() for entity in filtered_graph.entities.values())
        color_map = self._generate_color_map(entity_types)
        
        # Add nodes
        for entity_id, entity in filtered_graph.entities.items():
            entity_type = entity.type.lower()
            color = color_map.get(entity_type, "#97c2fc")
            
            # Prepare tooltip with entity attributes
            tooltip = f"<b>{entity.name}</b> ({entity_type})<br>"
            tooltip += f"Confidence: {entity.confidence:.2f}<br>"
            
            if entity.attributes:
                tooltip += "<b>Attributes:</b><br>"
                for attr in entity.attributes:
                    tooltip += f"- {attr.key}: {attr.value}<br>"
            
            net.add_node(
                str(entity_id),
                label=entity.name,
                title=tooltip,
                color=color,
                size=20 + (entity.confidence * 10)  # Size based on confidence
            )
        
        # Add edges
        for rel_id, rel in filtered_graph.relationships.items():
            # Prepare tooltip with relationship details
            tooltip = f"<b>{rel.type}</b><br>"
            tooltip += f"Confidence: {rel.confidence:.2f}<br>"
            
            if rel.attributes:
                tooltip += "<b>Attributes:</b><br>"
                for attr in rel.attributes:
                    tooltip += f"- {attr.key}: {attr.value}<br>"
            
            # Add the edge
            label = rel.type if show_labels else ""
            net.add_edge(
                str(rel.source_id),
                str(rel.target_id),
                label=label,
                title=tooltip,
                width=1 + (rel.confidence * 3),  # Width based on confidence
                arrows="to" if rel.directed else "to;from"
            )
        
        # Generate the visualization
        output_path = os.path.join(self.output_dir, filename)
        net.save_graph(output_path)
        
        # Generate a report if requested
        if generate_report:
            report_filename = os.path.splitext(filename)[0] + "_report.md"
            report_path = os.path.join(self.output_dir, report_filename)
            self._generate_graph_report(graph, report_path, title)
        
        logger.info(f"Graph visualization saved to {output_path}")
        return output_path
        
    def _generate_graph_report(self, graph: KnowledgeGraph, output_path: str, title: str = "Knowledge Graph Report"):
        """Generate a Markdown report about the knowledge graph.
        
        Args:
            graph: Knowledge graph to report on
            output_path: Path to save the report
            title: Title for the report
        """
        # Determine the document language by checking entities language
        # Default to English if no language preference can be determined
        language = self._detect_graph_language(graph)
        
        # Get the report templates for the detected language
        templates = self._get_report_templates(language)
        
        # Count entity types
        entity_types = {}
        for entity in graph.entities.values():
            entity_type = entity.type.lower()
            if entity_type not in entity_types:
                entity_types[entity_type] = 0
            entity_types[entity_type] += 1
        
        # Count relationship types
        relationship_types = {}
        for rel in graph.relationships.values():
            rel_type = rel.type
            if rel_type not in relationship_types:
                relationship_types[rel_type] = 0
            relationship_types[rel_type] += 1
        
        # Generate the report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {templates['title']}\n\n")
            
            # Summary statistics
            f.write(f"## {templates['summary']}\n\n")
            f.write(f"- **{templates['total_entities']}**: {len(graph.entities)}\n")
            f.write(f"- **{templates['total_relationships']}**: {len(graph.relationships)}\n")
            f.write(f"- **{templates['entity_types']}**: {len(entity_types)}\n")
            f.write(f"- **{templates['relationship_types']}**: {len(relationship_types)}\n\n")
            
            # Entity types breakdown
            f.write(f"## {templates['entity_types']}\n\n")
            f.write(f"| {templates['type']} | {templates['count']} | {templates['percentage']} |\n")
            f.write("|------|-------|------------|\n")
            
            for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(graph.entities)) * 100
                f.write(f"| {entity_type} | {count} | {percentage:.1f}% |\n")
            
            f.write("\n")
            
            # Relationship types breakdown
            f.write(f"## {templates['relationship_types']}\n\n")
            f.write(f"| {templates['type']} | {templates['count']} | {templates['percentage']} |\n")
            f.write("|------|-------|------------|\n")
            
            for rel_type, count in sorted(relationship_types.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(graph.relationships)) * 100
                f.write(f"| {rel_type} | {count} | {percentage:.1f}% |\n")
            
            f.write("\n")
            
            # Key entities (highest degree)
            f.write(f"## {templates['key_entities']}\n\n")
            f.write(f"{templates['entities_with_most_connections']}:\n\n")
            f.write(f"| {templates['entity']} | {templates['type']} | {templates['connections']} |\n")
            f.write("|--------|------|-------------|\n")
            
            # Create a NetworkX graph for degree calculation
            nx_graph = graph.to_networkx()
            
            # Get degree for each node
            degrees = {}
            for node in nx_graph.nodes():
                degrees[node] = nx_graph.degree(node)
            
            # Get top 10 entities by degree
            top_entities = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:10]
            
            for entity_id, degree in top_entities:
                entity = graph.get_entity(entity_id)
                if entity:
                    f.write(f"| {entity.name} | {entity.type} | {degree} |\n")
            
            f.write("\n")
            
            # Communities or clusters (if available)
            if hasattr(graph, 'communities') and graph.communities:
                f.write(f"## {templates['communities']}\n\n")
                
                for i, community in enumerate(graph.communities):
                    f.write(f"### {templates['community']} {i+1}\n\n")
                    f.write(f"{templates['size']}: {len(community)} {templates['entities']}\n\n")
                    
                    # List top entities in this community
                    top_community_entities = [
                        (entity_id, degrees[entity_id]) 
                        for entity_id in community
                        if entity_id in degrees
                    ]
                    top_community_entities.sort(key=lambda x: x[1], reverse=True)
                    
                    f.write(f"{templates['key_members']}:\n\n")
                    for entity_id, degree in top_community_entities[:5]:
                        entity = graph.get_entity(entity_id)
                        if entity:
                            f.write(f"- {entity.name} ({entity.type}): {degree} {templates['connections']}\n")
                    
                    f.write("\n")
            
            logger.info(f"Graph report saved to {output_path}")
            
    def _detect_graph_language(self, graph: KnowledgeGraph) -> str:
        """Detect the predominant language of the graph.
        
        This function tries to determine the language of the graph by checking
        the language attribute of entities or their source spans.
        
        Args:
            graph: Knowledge graph to analyze
            
        Returns:
            Language code ('en' or 'ru')
        """
        from ..config import settings
        
        # If graph has a language attribute, use it
        if hasattr(graph, 'language') and graph.language:
            return graph.language
        
        # Count languages in entities' source spans
        language_counts = {"en": 0, "ru": 0}
        
        for entity in graph.entities.values():
            # If entity has source span with language
            if hasattr(entity, 'source_span') and entity.source_span:
                if hasattr(entity.source_span, 'language') and entity.source_span.language:
                    lang = entity.source_span.language
                    if lang in language_counts:
                        language_counts[lang] += 1
            
            # Check if entity name contains Cyrillic characters (rough heuristic for Russian)
            if any(ord('а') <= ord(c) <= ord('я') or ord('А') <= ord(c) <= ord('Я') for c in entity.name):
                language_counts["ru"] += 1
        
        # Determine the predominant language
        if language_counts["ru"] > language_counts["en"]:
            return "ru"
        
        # Default to the system's default language
        return settings.DEFAULT_LANGUAGE
    
    def _get_report_templates(self, language: str) -> dict:
        """Get report templates for the specified language.
        
        Args:
            language: Language code ('en' or 'ru')
            
        Returns:
            Dictionary of templates for the report
        """
        templates = {
            "en": {
                "title": "Knowledge Graph",
                "summary": "Summary",
                "total_entities": "Total Entities",
                "total_relationships": "Total Relationships",
                "entity_types": "Entity Types",
                "relationship_types": "Relationship Types",
                "type": "Type",
                "count": "Count",
                "percentage": "Percentage",
                "key_entities": "Key Entities",
                "entities_with_most_connections": "Entities with the most connections",
                "entity": "Entity",
                "connections": "Connections",
                "communities": "Communities",
                "community": "Community",
                "size": "Size",
                "entities": "entities",
                "key_members": "Key members"
            },
            "ru": {
                "title": "Граф знаний",
                "summary": "Сводка",
                "total_entities": "Всего сущностей",
                "total_relationships": "Всего отношений",
                "entity_types": "Типы сущностей",
                "relationship_types": "Типы отношений",
                "type": "Тип",
                "count": "Количество",
                "percentage": "Процент",
                "key_entities": "Ключевые сущности",
                "entities_with_most_connections": "Сущности с наибольшим количеством связей",
                "entity": "Сущность",
                "connections": "Связи",
                "communities": "Сообщества",
                "community": "Сообщество",
                "size": "Размер",
                "entities": "сущностей",
                "key_members": "Ключевые члены"
            }
        }
        
        # Return templates for the specified language or fallback to English
        return templates.get(language, templates["en"])
    
    def visualize_community(self, 
                         graph: KnowledgeGraph,
                         communities: Dict[int, List[Entity]],
                         filename: str = "community_graph.html",
                         title: str = "Community Structure") -> str:
        """Visualize community structure in a knowledge graph.
        
        Args:
            graph: Knowledge graph to visualize
            communities: Dictionary mapping community IDs to lists of entities
            filename: Output HTML filename
            title: Title for the visualization
            
        Returns:
            Path to the generated HTML file
        """
        # Create network
        net = Network(height=self.height, width=self.width, directed=True, notebook=False)
        net.set_options("""
        var options = {
            "nodes": {
                "font": {
                    "size": 14,
                    "face": "Tahoma"
                }
            },
            "edges": {
                "color": {
                    "inherit": false
                },
                "smooth": {
                    "type": "continuous",
                    "forceDirection": "none"
                }
            },
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": 200,
                    "springConstant": 0.08
                },
                "minVelocity": 0.75,
                "solver": "forceAtlas2Based"
            }
        }
        """)
        
        # Create a color map for communities
        community_ids = list(communities.keys())
        community_colors = self._generate_color_map(community_ids)
        
        # Create a map of entity IDs to community IDs
        entity_to_community = {}
        for community_id, entities in communities.items():
            for entity in entities:
                entity_to_community[entity.id] = community_id
        
        # Add nodes
        for entity_id, entity in graph.entities.items():
            community_id = entity_to_community.get(entity_id, -1)
            color = community_colors.get(community_id, "#97c2fc")
            
            # Add node with community color
            net.add_node(
                str(entity_id),
                label=entity.name,
                title=f"{entity.name} ({entity.type})\nCommunity: {community_id}",
                color=color,
                group=community_id  # Group by community
            )
        
        # Add edges
        for rel_id, rel in graph.relationships.items():
            source_community = entity_to_community.get(rel.source_id, -1)
            target_community = entity_to_community.get(rel.target_id, -1)
            
            # Color edges based on whether they connect different communities
            if source_community == target_community:
                color = community_colors.get(source_community, "#848484")
            else:
                color = "#000000"  # Black for inter-community edges
            
            # Add the edge
            net.add_edge(
                str(rel.source_id),
                str(rel.target_id),
                title=rel.type,
                color=color,
                width=1.5 if source_community != target_community else 1
            )
        
        # Generate the visualization
        output_path = os.path.join(self.output_dir, filename)
        net.save_graph(output_path)
        
        logger.info(f"Community visualization saved to {output_path}")
        return output_path
    
    def visualize_subgraph(self, 
                        graph: KnowledgeGraph,
                        center_entity: Entity,
                        max_distance: int = 2,
                        filename: str = "subgraph.html") -> str:
        """Visualize a subgraph centered on a specific entity.
        
        Args:
            graph: Knowledge graph to visualize
            center_entity: Entity to center the subgraph on
            max_distance: Maximum distance from center entity
            filename: Output HTML filename
            
        Returns:
            Path to the generated HTML file
        """
        # Create the NetworkX graph
        nx_graph = graph.to_networkx()
        
        # Extract the subgraph
        nodes_to_include = {center_entity.id}
        current_distance = 0
        current_frontier = {center_entity.id}
        
        while current_distance < max_distance:
            new_frontier = set()
            
            for node in current_frontier:
                for neighbor in nx_graph.successors(node):
                    if neighbor not in nodes_to_include:
                        new_frontier.add(neighbor)
                
                for neighbor in nx_graph.predecessors(node):
                    if neighbor not in nodes_to_include:
                        new_frontier.add(neighbor)
            
            nodes_to_include.update(new_frontier)
            current_frontier = new_frontier
            current_distance += 1
        
        # Create a subgraph
        subgraph = graph.to_networkx().subgraph(nodes_to_include)
        
        # Create a new KnowledgeGraph from the subgraph
        sub_kg = KnowledgeGraph()
        
        for node in subgraph.nodes():
            entity = graph.get_entity(node)
            if entity:
                sub_kg.add_entity(entity)
        
        for u, v, key in subgraph.edges(keys=True):
            relationship = graph.get_relationship(key)
            if relationship:
                try:
                    sub_kg.add_relationship(relationship)
                except ValueError:
                    pass
        
        # Visualize the subgraph
        return self.visualize_html(
            sub_kg,
            filename=filename,
            title=f"Subgraph centered on {center_entity.name}",
            show_labels=True
        )
    
    def _generate_color_map(self, categories: Set[Any]) -> Dict[Any, str]:
        """Generate a color map for a set of categories.
        
        Args:
            categories: Set of categories to map to colors
            
        Returns:
            Dictionary mapping categories to color strings
        """
        # Fixed color palette for consistency
        palette = [
            "#e6194B", "#3cb44b", "#ffe119", "#4363d8", "#f58231", 
            "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4", 
            "#469990", "#dcbeff", "#9A6324", "#fffac8", "#800000", 
            "#aaffc3", "#808000", "#ffd8b1", "#000075", "#a9a9a9"
        ]
        
        # Map categories to colors
        color_map = {}
        for i, category in enumerate(categories):
            color_index = i % len(palette)
            color_map[category] = palette[color_index]
        
        return color_map