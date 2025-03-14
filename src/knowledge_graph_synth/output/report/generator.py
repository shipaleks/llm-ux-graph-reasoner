"""HTML research report generator for the knowledge graph synthesis system."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from jinja2 import Environment, FileSystemLoader
import markdown
import networkx as nx
import plotly.graph_objects as go
import plotly.offline as opy

from ...models.graph import KnowledgeGraph
from ...models.entity import Entity
from ...models.relationship import Relationship
from ...models.provenance import SourceSpan

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates comprehensive HTML research reports from analysis results."""
    
    def __init__(self, template_path: Optional[str] = None):
        """Initialize the report generator.
        
        Args:
            template_path: Path to the template directory (optional)
        """
        # Set default template path if not provided
        if template_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(module_dir, "templates")
        
        # Ensure template directory exists
        Path(template_path).mkdir(parents=True, exist_ok=True)
        
        # Create default template if it doesn't exist
        default_template_path = os.path.join(template_path, "research_report.html")
        if not os.path.exists(default_template_path):
            self._create_default_template(default_template_path)
        
        # Set up Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(template_path))
        self.template_path = template_path
    
    def _create_default_template(self, template_path: str):
        """Create a default template if none exists.
        
        Args:
            template_path: Path to save the template
        """
        # Use existing template from the templates directory
        module_dir = os.path.dirname(os.path.abspath(__file__))
        default_template = os.path.join(module_dir, "templates", "research_report.html")
        
        if os.path.exists(default_template):
            # Copy the template
            with open(default_template, "r", encoding="utf-8") as src:
                with open(template_path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
            return
            
        # Fallback template if the template file is missing
        template_content = """
<\!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | Knowledge Graph Analysis</title>
    <style>
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --accent-color: #e74c3c;
            --text-color: #333;
            --background-color: #f9f9f9;
            --card-color: #fff;
            --border-color: #ddd;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
            margin: 0;
            padding: 0;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        header {
            background-color: var(--primary-color);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }
        
        header .container {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: var(--primary-color);
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }
        
        h1 {
            font-size: 2.5rem;
            text-align: center;
            color: white;
        }
        
        h2 {
            font-size: 2rem;
            border-bottom: 2px solid var(--secondary-color);
            padding-bottom: 0.5rem;
        }
        
        h3 {
            font-size: 1.5rem;
        }
        
        h4 {
            font-size: 1.25rem;
        }
        
        p {
            margin-bottom: 1.2rem;
        }
        
        a {
            color: var(--secondary-color);
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        .card {
            background-color: var(--card-color);
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .metadata {
            background-color: rgba(52, 152, 219, 0.1);
            border-left: 4px solid var(--secondary-color);
            padding: 1rem;
            margin-bottom: 2rem;
        }
        
        .metadata p {
            margin: 0.5rem 0;
        }
        
        .graph-container {
            width: 100%;
            height: 600px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 2rem;
        }
        
        .entity-table, .relationship-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 2rem;
        }
        
        .entity-table th, .entity-table td,
        .relationship-table th, .relationship-table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        
        .entity-table th, .relationship-table th {
            background-color: var(--primary-color);
            color: white;
        }
        
        .entity-table tr:nth-child(even),
        .relationship-table tr:nth-child(even) {
            background-color: rgba(0, 0, 0, 0.05);
        }
        
        .theory-card {
            background-color: rgba(231, 76, 60, 0.05);
            border-left: 4px solid var(--accent-color);
            padding: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .theory-card h4 {
            color: var(--accent-color);
            margin-top: 0;
        }
        
        .hypothesis {
            padding-left: 1.5rem;
            border-left: 3px solid var(--secondary-color);
            margin-bottom: 1rem;
        }
        
        .evidence {
            margin-left: 1.5rem;
            font-style: italic;
            color: #666;
        }
        
        .toc {
            background-color: var(--card-color);
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .toc ul {
            padding-left: 1.5rem;
        }
        
        .toc-title {
            margin-top: 0;
            color: var(--primary-color);
        }
        
        .segment-summary {
            background-color: rgba(52, 152, 219, 0.1);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .segment-summary h4 {
            margin-top: 0;
            color: var(--secondary-color);
        }
        
        .key-points {
            margin-left: 1rem;
        }
        
        .key-points li {
            margin-bottom: 0.5rem;
        }
        
        .connection {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            padding: 0.5rem;
            background-color: #f5f5f5;
            border-radius: 4px;
        }
        
        .connection-arrow {
            margin: 0 1rem;
            font-size: 1.5rem;
            color: var(--secondary-color);
        }
        
        .connection-details {
            flex: 1;
        }
        
        .connection-strength {
            width: 80px;
            height: 10px;
            background-color: #ddd;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 0.5rem;
        }
        
        .connection-strength-bar {
            height: 100%;
            background-color: var(--secondary-color);
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background-color: var(--card-color);
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 1rem;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: var(--secondary-color);
            margin: 0.5rem 0;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.9rem;
        }
        
        footer {
            text-align: center;
            padding: 2rem 0;
            background-color: var(--primary-color);
            color: white;
            margin-top: 3rem;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>{{ title }}</h1>
            <p>Knowledge Graph Analysis Report</p>
        </div>
    </header>
    
    <div class="container">
        <\!-- Metadata -->
        <div class="metadata">
            <p><strong>Date:</strong> {{ date }}</p>
            <p><strong>Source:</strong> {{ source_file }}</p>
            <p><strong>Entities:</strong> {{ entity_count }}</p>
            <p><strong>Relationships:</strong> {{ relationship_count }}</p>
            <p><strong>Text Segments:</strong> {{ segment_count }}</p>
        </div>
        
        <\!-- Table of Contents -->
        <div class="toc">
            <h3 class="toc-title">Table of Contents</h3>
            <ul>
                <li><a href="#abstract">Abstract</a></li>
                <li><a href="#summary">Executive Summary</a></li>
                <li><a href="#contextual-analysis">Contextual Analysis</a></li>
                <li><a href="#entity-analysis">Entity Analysis</a></li>
                <li><a href="#relationship-analysis">Relationship Analysis</a></li>
                <li><a href="#graph-visualization">Graph Visualization</a></li>
                <li><a href="#graph-metrics">Graph Metrics</a></li>
                <li><a href="#theories">Theories and Hypotheses</a></li>
                <li><a href="#conclusion">Conclusion</a></li>
            </ul>
        </div>
        
        <\!-- Abstract -->
        <section id="abstract" class="card">
            <h2>Abstract</h2>
            <p>{{ abstract }}</p>
        </section>
        
        <\!-- Executive Summary -->
        <section id="summary" class="card">
            <h2>Executive Summary</h2>
            <p>{{ executive_summary }}</p>
        </section>
        
        <\!-- Contextual Analysis -->
        <section id="contextual-analysis" class="card">
            <h2>Contextual Analysis</h2>
            
            <h3>Segment Summaries</h3>
            {% for summary in segment_summaries %}
            <div class="segment-summary">
                <h4>{{ summary.id }}</h4>
                <p><strong>Summary:</strong> {{ summary.summary }}</p>
                <p><strong>Role:</strong> {{ summary.role }}</p>
                
                <p><strong>Key Points:</strong></p>
                <ul class="key-points">
                    {% for point in summary.key_points %}
                    <li>{{ point }}</li>
                    {% endfor %}
                </ul>
                
                {% if summary.parent_relation %}
                <p><strong>Relation to Parent:</strong> {{ summary.parent_relation }}</p>
                {% endif %}
            </div>
            {% endfor %}
            
            <h3>Segment Connections</h3>
            {% for connection in segment_connections %}
            <div class="connection">
                <div class="connection-segment">{{ connection.source_id }}</div>
                <div class="connection-arrow">
                    {% if connection.direction == "bidirectional" %}
                    ↔
                    {% else %}
                    →
                    {% endif %}
                </div>
                <div class="connection-details">
                    <div><strong>{{ connection.target_id }}</strong></div>
                    <div>Type: {{ connection.type }}</div>
                    <div class="connection-strength">
                        <div class="connection-strength-bar" style="width: {{ connection.strength * 100 }}%;"></div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </section>
        
        <\!-- Entity Analysis -->
        <section id="entity-analysis" class="card">
            <h2>Entity Analysis</h2>
            
            <p>This section presents the key entities identified in the analyzed text.</p>
            
            <table class="entity-table">
                <thead>
                    <tr>
                        <th>Entity</th>
                        <th>Type</th>
                        <th>Confidence</th>
                        <th>Attributes</th>
                    </tr>
                </thead>
                <tbody>
                    {% for entity in entities %}
                    <tr>
                        <td>{{ entity.name }}</td>
                        <td>{{ entity.type }}</td>
                        <td>{{ "%.2f"|format(entity.confidence) }}</td>
                        <td>
                            {% if entity.attributes %}
                            <ul>
                                {% for attr in entity.attributes %}
                                <li><strong>{{ attr.key }}:</strong> {{ attr.value }}</li>
                                {% endfor %}
                            </ul>
                            {% else %}
                            -
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>
        
        <\!-- Relationship Analysis -->
        <section id="relationship-analysis" class="card">
            <h2>Relationship Analysis</h2>
            
            <p>This section presents the relationships identified between entities in the analyzed text.</p>
            
            <table class="relationship-table">
                <thead>
                    <tr>
                        <th>Source</th>
                        <th>Relation</th>
                        <th>Target</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>
                    {% for rel in relationships %}
                    <tr>
                        <td>{{ rel.source_name }}</td>
                        <td>{{ rel.type }}</td>
                        <td>{{ rel.target_name }}</td>
                        <td>{{ "%.2f"|format(rel.confidence) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>
        
        <\!-- Graph Visualization -->
        <section id="graph-visualization" class="card">
            <h2>Graph Visualization</h2>
            
            <p>This interactive visualization represents the knowledge graph with entities as nodes and relationships as edges.</p>
            
            <div class="graph-container">
                {{ graph_visualization|safe }}
            </div>
        </section>
        
        <\!-- Graph Metrics -->
        <section id="graph-metrics" class="card">
            <h2>Graph Metrics</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.density|round(4) }}</div>
                    <div class="metric-label">Graph Density</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.avg_degree|round(2) }}</div>
                    <div class="metric-label">Average Degree</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.avg_clustering|round(4) }}</div>
                    <div class="metric-label">Average Clustering Coefficient</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.diameter }}</div>
                    <div class="metric-label">Graph Diameter</div>
                </div>
            </div>
            
            <h3>Central Entities</h3>
            <table class="entity-table">
                <thead>
                    <tr>
                        <th>Entity</th>
                        <th>Centrality Score</th>
                        <th>Type</th>
                    </tr>
                </thead>
                <tbody>
                    {% for entity in metrics.central_entities %}
                    <tr>
                        <td>{{ entity.name }}</td>
                        <td>{{ "%.3f"|format(entity.centrality) }}</td>
                        <td>{{ entity.type }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>
        
        <\!-- Theories and Hypotheses -->
        <section id="theories" class="card">
            <h2>Theories and Hypotheses</h2>
            
            <p>This section presents theories and hypotheses derived from the knowledge graph analysis.</p>
            
            {% for theory in theories %}
            <div class="theory-card">
                <h3>{{ theory.name }}</h3>
                <p><strong>Confidence:</strong> {{ "%.2f"|format(theory.confidence) }}</p>
                <p>{{ theory.description }}</p>
                
                {% if theory.hypotheses %}
                <h4>Hypotheses:</h4>
                {% for hypothesis in theory.hypotheses %}
                <div class="hypothesis">
                    <p><strong>{{ hypothesis.statement }}</strong> (Confidence: {{ "%.2f"|format(hypothesis.confidence) }})</p>
                    
                    {% if hypothesis.evidence %}
                    <p>Evidence:</p>
                    <ul class="evidence">
                        {% for ev in hypothesis.evidence %}
                        <li>{{ ev.description }} (Strength: {{ "%.2f"|format(ev.strength) }})</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                </div>
                {% endfor %}
                {% endif %}
            </div>
            {% endfor %}
        </section>
        
        <\!-- Conclusion -->
        <section id="conclusion" class="card">
            <h2>Conclusion</h2>
            <p>{{ conclusion }}</p>
        </section>
    </div>
    
    <footer>
        <div class="container">
            <p>Generated with Knowledge Graph Synthesis System</p>
            <p>{{ date }}</p>
        </div>
    </footer>
</body>
</html>
"""
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template_content)
    
    def _calculate_graph_metrics(self, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Calculate metrics for the knowledge graph.
        
        Args:
            graph: Knowledge graph to analyze
            
        Returns:
            Dictionary with graph metrics
        """
        # Convert to NetworkX graph for analysis
        G = nx.DiGraph()
        
        # Add nodes
        for entity_id, entity in graph.entities.items():
            G.add_node(entity_id, name=entity.name, type=entity.type)
        
        # Add edges
        for rel_id, relationship in graph.relationships.items():
            G.add_edge(
                relationship.source_id,
                relationship.target_id,
                type=relationship.type,
                confidence=relationship.confidence
            )
        
        # Calculate metrics
        metrics = {}
        
        # Basic metrics
        metrics["node_count"] = G.number_of_nodes()
        metrics["edge_count"] = G.number_of_edges()
        metrics["density"] = nx.density(G)
        
        # Degree metrics
        degrees = [d for n, d in G.degree()]
        metrics["avg_degree"] = sum(degrees) / len(degrees) if degrees else 0
        metrics["max_degree"] = max(degrees) if degrees else 0
        
        # Clustering coefficient
        try:
            clustering = nx.clustering(G.to_undirected())
            metrics["avg_clustering"] = sum(clustering.values()) / len(clustering) if clustering else 0
        except:
            metrics["avg_clustering"] = 0
        
        # Centrality metrics
        try:
            centrality = nx.degree_centrality(G)
            central_entities = []
            
            for node, score in sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]:
                entity = graph.entities.get(node)
                if entity:
                    central_entities.append({
                        "name": entity.name,
                        "type": entity.type,
                        "centrality": score
                    })
            
            metrics["central_entities"] = central_entities
        except:
            metrics["central_entities"] = []
        
        # Connected components
        try:
            undirected = G.to_undirected()
            components = list(nx.connected_components(undirected))
            metrics["connected_components"] = len(components)
            
            # Find largest component
            largest_component = max(components, key=len)
            metrics["largest_component_size"] = len(largest_component)
            
            # Calculate diameter of largest component
            largest_subgraph = undirected.subgraph(largest_component)
            metrics["diameter"] = nx.diameter(largest_subgraph)
        except:
            metrics["connected_components"] = 1
            metrics["largest_component_size"] = G.number_of_nodes()
            metrics["diameter"] = 0
        
        return metrics
    
    def _create_plotly_graph(self, graph: KnowledgeGraph) -> str:
        """Create an interactive Plotly graph visualization.
        
        Args:
            graph: Knowledge graph to visualize
            
        Returns:
            HTML string with the Plotly graph
        """
        # Create node data
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []
        
        # Create a simple layout using a spring layout
        G = nx.DiGraph()
        
        # Add nodes
        for entity_id, entity in graph.entities.items():
            G.add_node(entity_id, name=entity.name, type=entity.type)
        
        # Add edges
        for rel_id, relationship in graph.relationships.items():
            G.add_edge(
                relationship.source_id,
                relationship.target_id,
                type=relationship.type
            )
        
        # Get positions using spring layout
        pos = nx.spring_layout(G, seed=42)
        
        # Prepare color map
        entity_types = set(entity.type for entity in graph.entities.values())
        color_map = {}
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        for i, entity_type in enumerate(entity_types):
            color_map[entity_type] = colors[i % len(colors)]
        
        # Calculate degree for node sizing
        degrees = dict(G.degree())
        
        # Fill node data
        for entity_id, entity in graph.entities.items():
            if entity_id in pos:
                node_x.append(pos[entity_id][0])
                node_y.append(pos[entity_id][1])
                node_text.append(f"<b>{entity.name}</b><br>Type: {entity.type}")
                node_color.append(color_map.get(entity.type, '#7f7f7f'))
                
                # Size based on degree with min/max bounds
                size = 10 + (degrees.get(entity_id, 0) * 2)
                node_size.append(min(50, max(10, size)))
        
        # Create edge data
        edge_x = []
        edge_y = []
        edge_text = []
        
        for rel_id, relationship in graph.relationships.items():
            if relationship.source_id in pos and relationship.target_id in pos:
                x0, y0 = pos[relationship.source_id]
                x1, y1 = pos[relationship.target_id]
                
                # Add trace for edge
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                
                # Create edge text
                source_name = graph.entities[relationship.source_id].name
                target_name = graph.entities[relationship.target_id].name
                edge_text.append(f"{source_name} → {target_name}<br>{relationship.type}")
        
        # Create node trace
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                color=node_color,
                size=node_size,
                line=dict(width=1, color='#888')
            )
        )
        
        # Create edge trace
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            mode='lines',
            line=dict(width=1, color='#888'),
            hoverinfo='none'
        )
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=0, l=0, r=0, t=0),
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                        ))
        
        # Convert to HTML
        return opy.plot(fig, output_type='div', include_plotlyjs='cdn')
    
    def _load_json_if_exists(self, file_path: str) -> Any:
        """Load JSON data from a file if it exists.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Parsed JSON data or None if the file doesn't exist
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading JSON from {file_path}: {str(e)}")
        
        return None
    
    def _generate_abstract(self, graph: KnowledgeGraph, segment_summaries: List[Dict[str, Any]]) -> str:
        """Generate an abstract for the report.
        
        Args:
            graph: Knowledge graph
            segment_summaries: List of segment summaries
            
        Returns:
            Generated abstract
        """
        # Extract entity types and count
        entity_types = {}
        for entity in graph.entities.values():
            entity_types[entity.type] = entity_types.get(entity.type, 0) + 1
        
        # Extract relationship types and count
        relationship_types = {}
        for rel in graph.relationships.values():
            relationship_types[rel.type] = relationship_types.get(rel.type, 0) + 1
        
        # Find main topics from segment summaries
        main_topics = []
        if segment_summaries:
            for summary in segment_summaries[:3]:  # Use first 3 summaries
                if "summary" in summary:
                    main_topics.append(summary["summary"])
        
        # Detect language based on segment summaries
        language = "ru"  # Default to Russian
        
        # Generate abstract based on language
        if language == "ru":
            abstract = f"Этот отчет представляет анализ графа знаний, построенного на основе исследуемого текста. В ходе анализа выявлено {len(graph.entities)} сущностей {len(entity_types)} различных типов и {len(graph.relationships)} связей {len(relationship_types)} различных видов. "
            
            if entity_types:
                top_entities = sorted(entity_types.items(), key=lambda x: x[1], reverse=True)[:3]
                abstract += f"Наиболее распространенные типы сущностей: {', '.join(f'{e_type} ({count})' for e_type, count in top_entities)}. "
            
            if relationship_types:
                top_relations = sorted(relationship_types.items(), key=lambda x: x[1], reverse=True)[:3]
                abstract += f"Преобладающие типы связей: {', '.join(f'{r_type} ({count})' for r_type, count in top_relations)}. "
            
            if main_topics:
                abstract += f"Ключевые темы, исследуемые в тексте: {' '.join(main_topics)}"
        else:
            abstract = f"This report presents a knowledge graph analysis of the provided text, identifying {len(graph.entities)} entities across {len(entity_types)} categories and {len(graph.relationships)} relationships of {len(relationship_types)} different types. "
            
            if entity_types:
                top_entities = sorted(entity_types.items(), key=lambda x: x[1], reverse=True)[:3]
                abstract += f"The most common entity types include {', '.join(f'{e_type} ({count})' for e_type, count in top_entities)}. "
            
            if relationship_types:
                top_relations = sorted(relationship_types.items(), key=lambda x: x[1], reverse=True)[:3]
                abstract += f"The predominant relationship types are {', '.join(f'{r_type} ({count})' for r_type, count in top_relations)}. "
            
            if main_topics:
                abstract += f"The key themes explored in the text include: {' '.join(main_topics)}"
        
        return abstract
    
    def _generate_executive_summary(self, graph: KnowledgeGraph, metrics: Dict[str, Any], theories: List[Dict[str, Any]]) -> str:
        """Generate an executive summary for the report.
        
        Args:
            graph: Knowledge graph
            metrics: Graph metrics
            theories: List of theories
            
        Returns:
            Generated executive summary
        """
        # Detect language based on metrics or graph properties
        language = "ru"  # Default to Russian
        
        if language == "ru":
            # Russian version of the executive summary
            summary = f"Построенный граф знаний содержит {len(graph.entities)} сущностей и {len(graph.relationships)} связей. "
            
            # Add information about central entities
            if "central_entities" in metrics and metrics["central_entities"]:
                central_names = [e["name"] for e in metrics["central_entities"][:3]]
                summary += f"Наиболее центральные сущности в графе: {', '.join(central_names)}, которые формируют ключевые точки связи в сети. "
            
            # Add information about graph structure
            if "connected_components" in metrics:
                if metrics["connected_components"] == 1:
                    summary += f"Граф образует единый связный компонент, что указывает на целостность повествования или темы. "
                else:
                    summary += f"Граф состоит из {metrics['connected_components']} разрозненных компонентов, что указывает на наличие нескольких отдельных тем или сюжетных линий. "
            
            # Add information about the density
            if "density" in metrics:
                if metrics["density"] < 0.1:
                    summary += "Граф имеет разреженную структуру с относительно небольшим количеством связей между сущностями. "
                elif metrics["density"] > 0.3:
                    summary += "Граф имеет плотную структуру с множеством взаимосвязей между сущностями. "
                else:
                    summary += "Граф имеет умеренную плотность связей между сущностями. "
            
            # Add information about theories
            if theories:
                top_theory = max(theories, key=lambda x: x.get("confidence", 0))
                summary += f"Наиболее значимая теория, полученная в результате анализа — '{top_theory.get('name', 'Без названия')}' с уровнем достоверности {top_theory.get('confidence', 0):.2f}. "
                if "description" in top_theory:
                    summary += f"{top_theory['description']} "
            
            # Add conclusion
            summary += "Этот краткий обзор подчеркивает ключевые выводы анализа графа и создает основу для более детального рассмотрения в последующих разделах."
        else:
            # English version of the executive summary
            summary = f"The knowledge graph constructed from the analyzed text contains {len(graph.entities)} entities and {len(graph.relationships)} relationships. "
            
            # Add information about central entities
            if "central_entities" in metrics and metrics["central_entities"]:
                central_names = [e["name"] for e in metrics["central_entities"][:3]]
                summary += f"The most central entities in the graph are {', '.join(central_names)}, which form key connection points in the network. "
            
            # Add information about graph structure
            if "connected_components" in metrics:
                if metrics["connected_components"] == 1:
                    summary += f"The graph forms a single connected component, suggesting a cohesive narrative or topic. "
                else:
                    summary += f"The graph consists of {metrics['connected_components']} disconnected components, indicating multiple distinct topics or narratives. "
            
            # Add information about the density
            if "density" in metrics:
                if metrics["density"] < 0.1:
                    summary += "The graph has a sparse structure, with relatively few connections between entities. "
                elif metrics["density"] > 0.3:
                    summary += "The graph has a dense structure, with many interconnections between entities. "
                else:
                    summary += "The graph has a moderate density of connections between entities. "
            
            # Add information about theories
            if theories:
                top_theory = max(theories, key=lambda x: x.get("confidence", 0))
                summary += f"The most significant theory derived from the analysis is '{top_theory.get('name', 'Unnamed Theory')}' with a confidence of {top_theory.get('confidence', 0):.2f}. "
                if "description" in top_theory:
                    summary += f"{top_theory['description']} "
            
            # Add conclusion
            summary += "This executive summary highlights the key findings from the graph analysis, providing a foundation for more detailed examination in the subsequent sections."
        
        return summary
    
    def _process_theories(self, theories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process theories to ensure they match the template expectations.
        
        Args:
            theories: List of theories from JSON
            
        Returns:
            Processed theories ready for template
        """
        if not theories:
            return []
        
        processed_theories = []
        
        for theory in theories:
            # Create a copy to avoid modifying the original
            processed = theory.copy()
            
            # Ensure required properties exist with defaults if needed
            if "title" in processed and "name" not in processed:
                processed["name"] = processed["title"]
            elif "name" in processed and "title" not in processed:
                processed["title"] = processed["name"]
            elif "name" not in processed and "title" not in processed:
                processed["name"] = "Unnamed Theory"
                processed["title"] = "Unnamed Theory"
                
            if "description" not in processed and "summary" in processed:
                processed["description"] = processed["summary"]
                
            if "confidence" not in processed:
                processed["confidence"] = 0.5
                
            # Add empty lists for collections if missing
            if "hypotheses" not in processed:
                processed["hypotheses"] = []
                
            # Convert postulates to hypotheses if present but no hypotheses
            if "postulates" in processed and not processed["hypotheses"]:
                for postulate in processed["postulates"]:
                    hypothesis = {
                        "statement": postulate.get("statement", ""),
                        "confidence": 0.7,
                        "evidence": []
                    }
                    processed["hypotheses"].append(hypothesis)
            
            processed_theories.append(processed)
            
        return processed_theories
        
    def _generate_conclusion(self, graph: KnowledgeGraph, metrics: Dict[str, Any], theories: List[Dict[str, Any]]) -> str:
        """Generate a conclusion for the report.
        
        Args:
            graph: Knowledge graph
            metrics: Graph metrics
            theories: List of theories
            
        Returns:
            Generated conclusion
        """
        # Detect language based on context
        language = "ru"  # Default to Russian
        
        if language == "ru":
            # Russian version of the conclusion
            conclusion = "Анализ графа знаний выявил существенные закономерности и взаимосвязи в исследуемом тексте. "
            
            # Add information about the structure
            if "central_entities" in metrics and metrics["central_entities"]:
                central_names = [e["name"] for e in metrics["central_entities"][:3]]
                conclusion += f"Анализ определил {', '.join(central_names)} как центральные концепции, связывающие несколько тем. "
            
            # Add information about relationships
            relationship_types = set(rel.type for rel in graph.relationships.values())
            if relationship_types:
                conclusion += f"Преобладающие типы отношений ({', '.join(list(relationship_types)[:3])}) подчеркивают ключевые взаимодействия в предметной области. "
            
            # Add information about theories
            if theories:
                conclusion += f"В ходе анализа было сформировано {len(theories)} теорий, объясняющих наблюдаемые закономерности. "
                
                # Get the highest confidence theory
                highest_conf = max(theories, key=lambda x: x.get("confidence", 0))
                conclusion += f"Теория '{highest_conf.get('name', 'Без названия')}' имеет наиболее сильную поддержку с достоверностью {highest_conf.get('confidence', 0):.2f}. "
            
            # Add future directions
            conclusion += "Дальнейший анализ мог бы выиграть от дополнительных данных для проверки формирующихся теорий и изучения неразвитых связей в графе. "
            conclusion += "Граф знаний обеспечивает основу для более глубокого исследования ключевых тем и взаимосвязей, выявленных в этом отчете."
        else:
            # English version of the conclusion
            conclusion = "The knowledge graph analysis has revealed significant patterns and relationships within the text. "
            
            # Add information about the structure
            if "central_entities" in metrics and metrics["central_entities"]:
                central_names = [e["name"] for e in metrics["central_entities"][:3]]
                conclusion += f"The analysis identified {', '.join(central_names)} as central concepts that connect multiple themes. "
            
            # Add information about relationships
            relationship_types = set(rel.type for rel in graph.relationships.values())
            if relationship_types:
                conclusion += f"The predominant relationship types ({', '.join(list(relationship_types)[:3])}) highlight the key interactions within the domain. "
            
            # Add information about theories
            if theories:
                conclusion += f"The analysis generated {len(theories)} theories that explain observed patterns. "
                
                # Get the highest confidence theory
                highest_conf = max(theories, key=lambda x: x.get("confidence", 0))
                conclusion += f"The theory '{highest_conf.get('name', 'Unnamed')}' has the strongest support with a confidence of {highest_conf.get('confidence', 0):.2f}. "
            
            # Add future directions
            conclusion += "Future analysis could benefit from additional data to validate emerging theories and explore underdeveloped connections within the graph. "
            conclusion += "The knowledge graph provides a foundation for deeper investigation into the key themes and relationships identified in this report."
        
        return conclusion
    
    def generate_report(self, 
                      output_path: str,
                      graph: KnowledgeGraph,
                      source_file: str,
                      output_dir: str,
                      title: str = "Knowledge Graph Analysis Report") -> str:
        """Generate a comprehensive HTML research report.
        
        Args:
            output_path: Path to save the report
            graph: Knowledge graph
            source_file: Path to the source file
            output_dir: Directory with output files
            title: Report title
            
        Returns:
            Path to the generated report
        """
        logger.info(f"Generating research report to {output_path}")
        
        # Load contextual analysis data if available
        try:
            from ...cli.utils import resolve_asset_path
            
            # Try to resolve paths for all needed files, regardless of directory structure
            segment_summaries = []
            segment_connections = []
            segment_texts = {}
            
            # Load segment summaries
            summaries_path = resolve_asset_path(output_dir, "context/segment_summaries.json")
            summaries_data = self._load_json_if_exists(summaries_path)
            if summaries_data:
                # Convert from dict to list
                for segment_id, summary in summaries_data.items():
                    segment_summaries.append(summary)
                    # Store the mapping from ID to index for later reference
                    summary['index'] = len(segment_summaries)
            
            # Load segment connections
            connections_path = resolve_asset_path(output_dir, "context/segment_connections.json")
            connections_data = self._load_json_if_exists(connections_path)
            if connections_data:
                segment_connections = connections_data
                
            # Load original segment texts
            segments_path = resolve_asset_path(output_dir, "context/segments.json")
            segments_data = self._load_json_if_exists(segments_path)
            if segments_data:
                segment_texts = segments_data
            
            # Load theories if available
            theories_path = resolve_asset_path(output_dir, "theories/theories.json")
            theories = self._load_json_if_exists(theories_path) or []
            
            # Process theories to ensure they match template expectations
            theories = self._process_theories(theories)
            
        except Exception as e:
            logger.warning(f"Error resolving asset paths: {str(e)}")
            # Fall back to standard directory structure if error
            context_dir = os.path.join(output_dir, "context")
            segment_summaries = []
            segment_connections = []
            segment_texts = {}
            
            # Load segment summaries
            summaries_path = os.path.join(context_dir, "segment_summaries.json")
            summaries_data = self._load_json_if_exists(summaries_path)
            if summaries_data:
                # Convert from dict to list
                for segment_id, summary in summaries_data.items():
                    segment_summaries.append(summary)
                    # Store the mapping from ID to index for later reference
                    summary['index'] = len(segment_summaries)
            
            # Load segment connections
            connections_path = os.path.join(context_dir, "segment_connections.json")
            connections_data = self._load_json_if_exists(connections_path)
            if connections_data:
                segment_connections = connections_data
                
            # Load original segment texts
            segments_path = os.path.join(context_dir, "segments.json")
            segments_data = self._load_json_if_exists(segments_path)
            if segments_data:
                segment_texts = segments_data
            
            # Load theories if available
            theories_path = os.path.join(output_dir, "theories", "theories.json")
            theories = self._load_json_if_exists(theories_path) or []
            
            # Process theories to ensure they match template expectations
            theories = self._process_theories(theories)
        
        # Calculate graph metrics
        metrics = self._calculate_graph_metrics(graph)
        
        # Check for static graph HTML visualization from graph visualizer
        graph_viz_path = os.path.join(output_dir, "graphs", "knowledge_graph.html")
        
        # Use paths module to find path to graph if it exists
        try:
            from ...cli.utils import get_relative_path, resolve_asset_path
            
            # First make sure we can find the graph visualization file
            resolved_graph_path = resolve_asset_path(output_dir, "graphs/knowledge_graph.html")
            
            # Create a relative path from the report to the graph
            report_dir = os.path.dirname(output_path)
            rel_path = get_relative_path(output_path, resolved_graph_path, validate=False)
            
            # Default to iframe embedding which is more reliable
            graph_visualization = f'<iframe src="{rel_path}" width="100%" height="600px" frameborder="0"></iframe>'
        except Exception as e:
            logger.warning(f"Error resolving graph path: {str(e)}")
            # Fall back to a simple path
            report_dir = os.path.dirname(output_path)
            rel_path = os.path.relpath(graph_viz_path, report_dir)
            graph_visualization = f'<iframe src="{rel_path}" width="100%" height="600px" frameborder="0"></iframe>'
        
        # Create a plotly visualization as fallback if no graph HTML exists
        if not os.path.exists(graph_viz_path):
            try:
                logger.info("No graph visualization found, creating one with Plotly")
                graph_visualization = self._create_plotly_graph(graph)
            except Exception as e:
                logger.warning(f"Failed to create plotly graph: {str(e)}")
                graph_visualization = "<div class='error'>Не удалось создать визуализацию графа</div>"
        
        # Generate abstract and executive summary
        abstract = self._generate_abstract(graph, segment_summaries)
        executive_summary = self._generate_executive_summary(graph, metrics, theories)
        conclusion = self._generate_conclusion(graph, metrics, theories)
        
        # Determine the language (default to English)
        language = "en"
        # Try to detect language from segment summaries
        if segment_summaries:
            # Limit the number of summaries to process to avoid memory issues
            max_summaries = min(len(segment_summaries), 10)  # Process at most 10 summaries for language detection
            
            # Check if any segments have Russian text
            for i in range(max_summaries):
                if i >= len(segment_summaries):
                    break
                summary = segment_summaries[i]
                summary_text = summary.get("summary", "")
                # Simple check: if there are Cyrillic characters, assume Russian
                if any(ord('а') <= ord(c) <= ord('я') or ord('А') <= ord(c) <= ord('Я') for c in summary_text):
                    language = "ru"
                    break
        
        logger.info(f"Detected language for report: {language}")
        
        # Check if expansion report and expanded graph exists
        expansion_path = None
        expanded_graph_path = None
        try:
            # Check for expansion report
            expansion_report_path = os.path.join(output_dir, "graphs", "expanded", "expansion_process.md")
            expanded_graph_html_path = os.path.join(output_dir, "graphs", "expanded", "expanded_graph.html")
            
            if os.path.exists(expansion_report_path):
                # Create relative path from the report to the expansion report
                report_dir = os.path.dirname(output_path)
                expansion_path = os.path.relpath(expansion_report_path, report_dir)
                logger.info(f"Found expansion report at: {expansion_path}")
            
            if os.path.exists(expanded_graph_html_path):
                # Create relative path to the expanded graph visualization
                report_dir = os.path.dirname(output_path)
                expanded_graph_path = os.path.relpath(expanded_graph_html_path, report_dir)
                logger.info(f"Found expanded graph visualization at: {expanded_graph_path}")
        except Exception as e:
            logger.warning(f"Error creating expansion paths: {str(e)}")
        
        # Prepare data for template
        template_data = {
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_file": source_file,
            "entity_count": len(graph.entities),
            "relationship_count": len(graph.relationships),
            "segment_count": len(segment_summaries),
            "abstract": abstract,
            "executive_summary": executive_summary,
            "conclusion": conclusion,
            "language": language,
            "segment_summaries": segment_summaries,
            "segment_connections": segment_connections,
            "entities": [entity.to_dict() for entity in graph.entities.values()],
            "relationships": [{
                "source_name": graph.entities.get(rel.source_id, Entity(
                    id=rel.source_id, 
                    name="Unknown", 
                    type="UNKNOWN",
                    confidence=0.0,
                    source_span=SourceSpan(
                        document_id="unknown",
                        start=0,
                        end=0,
                        text="Unknown"
                    )
                )).name,
                "target_name": graph.entities.get(rel.target_id, Entity(
                    id=rel.target_id, 
                    name="Unknown", 
                    type="UNKNOWN",
                    confidence=0.0,
                    source_span=SourceSpan(
                        document_id="unknown",
                        start=0,
                        end=0,
                        text="Unknown"
                    )
                )).name,
                "type": rel.type,
                "confidence": rel.confidence
            } for rel in graph.relationships.values()],
            "graph_visualization": graph_visualization,
            "metrics": metrics,
            "theories": theories,
            "expansion_path": expansion_path,
            "expanded_graph_path": expanded_graph_path
        }
        
        # Choose the template based on language
        template_name = "research_report.html"
        if language == "ru":
            # Try to use Russian template if available
            if "research_report_ru.html" in self.env.list_templates():
                template_name = "research_report_ru.html"
                logger.info(f"Using Russian template: {template_name}")
            else:
                logger.warning("Russian template not found, using default English template")
        
        # Render template
        template = self.env.get_template(template_name)
        html_content = template.render(**template_data)
        
        # Save report
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Generate individual segment pages if segment texts are available
        if segment_texts:
            try:
                from ...cli.utils import get_subdirectory_path, get_relative_path
                
                # Create segments subdirectory
                segments_dir = get_subdirectory_path(os.path.dirname(output_path), "segments")
                
                # Create a simple template for segment pages without curly braces in style
                segment_template = """<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #fff;
            margin: 0;
            padding: 0;
            max-width: 1000px;
            margin: 0 auto;
            padding: 1rem;
        }}
        
        h1 {{
            font-size: 1.5rem;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 0.5rem;
        }}
        
        .segment-text {{
            background-color: #f9f9f9;
            padding: 1rem;
            border-radius: 4px;
            white-space: pre-wrap;
        }}
        
        .segment-metadata {{
            margin-top: 1rem;
            padding: 1rem;
            background-color: #f5f5f5;
            border-radius: 4px;
        }}
        
        .back-link {{
            margin-top: 1rem;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <div class="segment-text">{text}</div>
    
    <div class="segment-metadata">
        <p><strong>ID:</strong> {id}</p>
        <p><strong>Роль:</strong> {role}</p>
    </div>
    
    <a href="{report_path}" class="back-link">Вернуться к отчету</a>
</body>
</html>
"""
                
                # Generate a page for each segment
                for i, summary in enumerate(segment_summaries):
                    segment_id = summary.get('id')
                    if segment_id and segment_id in segment_texts:
                        segment_text = segment_texts[segment_id]
                        
                        # Get title from summary or use a default
                        title = summary.get('title', f"Сегмент {i+1}")
                        role = summary.get('role', '')
                        
                        # Create the segment page file
                        segment_path = os.path.join(segments_dir, f"{segment_id}.html")
                        
                        # Calculate relative path back to report
                        report_rel_path = get_relative_path(segment_path, output_path, validate=False)
                        
                        # Fill the template
                        segment_html = segment_template.format(
                            language=language,
                            title=title,
                            text=segment_text,
                            id=segment_id,
                            role=role,
                            report_path=report_rel_path
                        )
                        
                        # Write the segment page
                        with open(segment_path, "w", encoding="utf-8") as f:
                            f.write(segment_html)
            
            except Exception as e:
                logger.warning(f"Error creating segment pages: {str(e)}")
                # Fall back to standard approach
                segments_dir = os.path.join(os.path.dirname(output_path), "segments")
                os.makedirs(segments_dir, exist_ok=True)
                
                # Create a simple template for segment pages without curly braces in style
                segment_template = """<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #fff;
            margin: 0;
            padding: 0;
            max-width: 1000px;
            margin: 0 auto;
            padding: 1rem;
        }}
        
        h1 {{
            font-size: 1.5rem;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 0.5rem;
        }}
        
        .segment-text {{
            background-color: #f9f9f9;
            padding: 1rem;
            border-radius: 4px;
            white-space: pre-wrap;
        }}
        
        .segment-metadata {{
            margin-top: 1rem;
            padding: 1rem;
            background-color: #f5f5f5;
            border-radius: 4px;
        }}
        
        .back-link {{
            margin-top: 1rem;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <div class="segment-text">{text}</div>
    
    <div class="segment-metadata">
        <p><strong>ID:</strong> {id}</p>
        <p><strong>Роль:</strong> {role}</p>
    </div>
    
    <a href="{report_path}" class="back-link">Вернуться к отчету</a>
</body>
</html>
"""
                
                # Generate a page for each segment
                for i, summary in enumerate(segment_summaries):
                    segment_id = summary.get('id')
                    if segment_id and segment_id in segment_texts:
                        segment_text = segment_texts[segment_id]
                        
                        # Get title from summary or use a default
                        title = summary.get('title', f"Сегмент {i+1}")
                        role = summary.get('role', '')
                        
                        # Fill the template with simple relative path
                        segment_html = segment_template.format(
                            language=language,
                            title=title,
                            text=segment_text,
                            id=segment_id,
                            role=role,
                            report_path="../" + os.path.basename(output_path)
                        )
                        
                        # Write the segment page
                        segment_path = os.path.join(segments_dir, f"{segment_id}.html")
                        with open(segment_path, "w", encoding="utf-8") as f:
                            f.write(segment_html)
        
        logger.info(f"Research report generated successfully: {output_path}")
        return output_path
