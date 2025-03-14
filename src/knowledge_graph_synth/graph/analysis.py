"""Graph analysis for the knowledge graph synthesis system."""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID

import networkx as nx

from ..models import KnowledgeGraph, Entity
from ..config import settings

logger = logging.getLogger(__name__)


class GraphAnalyzer:
    """Analyzes knowledge graphs to identify important structures.
    
    This class implements algorithms for analyzing knowledge graphs,
    including centrality metrics, community detection, and pattern identification.
    """
    
    def __init__(self):
        """Initialize the graph analyzer."""
        pass
    
    def get_central_entities(self, 
                          graph: KnowledgeGraph, 
                          top_n: int = 10,
                          algorithm: str = "degree") -> List[Tuple[Entity, float]]:
        """Get the most central entities in the graph.
        
        Args:
            graph: Knowledge graph to analyze
            top_n: Number of entities to return
            algorithm: Centrality algorithm to use
            
        Returns:
            List of (entity, score) tuples
        """
        # Get the NetworkX graph
        nx_graph = graph.to_networkx()
        
        # Calculate centrality based on the specified algorithm
        if algorithm == "degree":
            centrality = nx.degree_centrality(nx_graph)
        elif algorithm == "eigenvector":
            centrality = nx.eigenvector_centrality_numpy(nx_graph)
        elif algorithm == "betweenness":
            centrality = nx.betweenness_centrality(nx_graph)
        elif algorithm == "closeness":
            centrality = nx.closeness_centrality(nx_graph)
        elif algorithm == "pagerank":
            centrality = nx.pagerank(nx_graph)
        else:
            logger.warning(f"Unknown centrality algorithm: {algorithm}, using degree centrality")
            centrality = nx.degree_centrality(nx_graph)
        
        # Get the top-N entities by centrality
        top_ids = sorted(centrality.keys(), key=lambda k: centrality[k], reverse=True)[:top_n]
        
        # Convert to (entity, score) tuples
        result = []
        for entity_id in top_ids:
            entity = graph.get_entity(entity_id)
            if entity:
                result.append((entity, centrality[entity_id]))
        
        return result
    
    def detect_communities(self, 
                        graph: KnowledgeGraph,
                        algorithm: str = "louvain") -> Dict[int, List[Entity]]:
        """Detect communities in the graph.
        
        Args:
            graph: Knowledge graph to analyze
            algorithm: Community detection algorithm to use
            
        Returns:
            Dictionary mapping community IDs to lists of entities
        """
        # Get the NetworkX graph
        nx_graph = graph.to_networkx()
        
        # Default to Louvain algorithm
        communities = {}
        
        try:
            if algorithm == "louvain":
                # Louvain algorithm requires the community library
                # If not available, fall back to Girvan-Newman
                try:
                    import community as community_louvain
                    partition = community_louvain.best_partition(nx_graph.to_undirected())
                    
                    # Group entities by community
                    for node, community_id in partition.items():
                        if community_id not in communities:
                            communities[community_id] = []
                        
                        entity = graph.get_entity(node)
                        if entity:
                            communities[community_id].append(entity)
                    
                except ImportError:
                    logger.warning("Community detection library not available, falling back to k-clique")
                    algorithm = "kclique"
            
            if algorithm == "kclique":
                # Use k-clique communities
                try:
                    k = 3  # Minimum size of cliques
                    k_cliques = list(nx.algorithms.community.k_clique_communities(nx_graph.to_undirected(), k))
                    
                    for i, clique in enumerate(k_cliques):
                        communities[i] = []
                        for node in clique:
                            entity = graph.get_entity(node)
                            if entity:
                                communities[i].append(entity)
                
                except Exception as e:
                    logger.warning(f"Error in k-clique detection: {str(e)}")
                    algorithm = "connected"
            
            if algorithm == "connected" or not communities:
                # Use connected components as communities
                components = list(nx.weakly_connected_components(nx_graph))
                
                for i, component in enumerate(components):
                    communities[i] = []
                    for node in component:
                        entity = graph.get_entity(node)
                        if entity:
                            communities[i].append(entity)
        
        except Exception as e:
            logger.error(f"Error in community detection: {str(e)}")
            # Fall back to treating the whole graph as one community
            communities[0] = []
            for entity_id, entity in graph.entities.items():
                communities[0].append(entity)
        
        return communities
    
    def get_important_relationships(self, 
                                 graph: KnowledgeGraph,
                                 top_n: int = 10) -> List[Tuple[str, int]]:
        """Get the most important relationship types in the graph.
        
        Args:
            graph: Knowledge graph to analyze
            top_n: Number of relationship types to return
            
        Returns:
            List of (relationship_type, count) tuples
        """
        # Count relationships by type
        type_counts = {}
        
        for rel_id, rel in graph.relationships.items():
            rel_type = rel.type.lower()
            
            if rel_type not in type_counts:
                type_counts[rel_type] = 0
            
            type_counts[rel_type] += 1
        
        # Get the top-N relationship types by count
        top_types = sorted(type_counts.keys(), key=lambda k: type_counts[k], reverse=True)[:top_n]
        
        # Convert to (type, count) tuples
        result = [(rel_type, type_counts[rel_type]) for rel_type in top_types]
        
        return result
    
    def get_graph_statistics(self, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Get general statistics about the graph.
        
        Args:
            graph: Knowledge graph to analyze
            
        Returns:
            Dictionary of graph statistics
        """
        nx_graph = graph.to_networkx()
        
        # Entity type statistics
        entity_types = {}
        for entity_id, entity in graph.entities.items():
            entity_type = entity.type.lower()
            
            if entity_type not in entity_types:
                entity_types[entity_type] = 0
            
            entity_types[entity_type] += 1
        
        # Relationship type statistics
        relation_types = {}
        for rel_id, rel in graph.relationships.items():
            rel_type = rel.type.lower()
            
            if rel_type not in relation_types:
                relation_types[rel_type] = 0
            
            relation_types[rel_type] += 1
        
        # Graph structure statistics
        try:
            avg_degree = sum(dict(nx_graph.degree()).values()) / float(nx_graph.number_of_nodes())
            density = nx.density(nx_graph)
            components = list(nx.weakly_connected_components(nx_graph))
            
            # Try to compute average clustering coefficient
            try:
                avg_clustering = nx.average_clustering(nx_graph.to_undirected())
            except:
                avg_clustering = None
            
            # Try to compute average shortest path length
            try:
                if nx.is_weakly_connected(nx_graph):
                    avg_path_length = nx.average_shortest_path_length(nx_graph)
                else:
                    avg_path_length = None
            except:
                avg_path_length = None
            
        except Exception as e:
            logger.warning(f"Error computing graph statistics: {str(e)}")
            avg_degree = None
            density = None
            components = []
            avg_clustering = None
            avg_path_length = None
        
        # Assemble statistics
        statistics = {
            "num_entities": len(graph.entities),
            "num_relationships": len(graph.relationships),
            "entity_types": entity_types,
            "relationship_types": relation_types,
            "avg_degree": avg_degree,
            "density": density,
            "num_components": len(components),
            "avg_clustering": avg_clustering,
            "avg_path_length": avg_path_length,
        }
        
        return statistics