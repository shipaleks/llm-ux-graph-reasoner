#!/usr/bin/env python3
"""
Simplified script to create an HTML visualization for a processed directory.
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def load_json_file(file_path):
    """Safely load a JSON file and return its contents."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"Error loading {file_path}: {str(e)}")
    
    return None

def create_simple_report(output_dir, original_file="Unknown source"):
    """Create a simple HTML report from the processed data."""
    logger.info(f"Creating simple HTML report for {output_dir}")
    
    # Check for the knowledge graph report
    graph_report_path = os.path.join(output_dir, "graphs", "knowledge_graph_report.md")
    if not os.path.exists(graph_report_path):
        logger.warning(f"Graph report not found: {graph_report_path}")
        graph_report_content = "No graph report available."
    else:
        try:
            with open(graph_report_path, 'r', encoding='utf-8') as f:
                graph_report_content = f.read()
        except Exception as e:
            logger.error(f"Error reading graph report: {str(e)}")
            graph_report_content = f"Error loading graph report: {str(e)}"
    
    # Load entities
    entities_file = os.path.join(output_dir, "entities", "all_entities.json")
    entities = load_json_file(entities_file) or []
    
    # Load relationships
    relationships_file = os.path.join(output_dir, "relationships", "all_relationships.json")
    relationships = load_json_file(relationships_file) or []
    
    # Create entity and relationship tables
    entity_rows = ""
    for entity in entities[:100]:  # Limit to 100 to avoid huge reports
        try:
            name = entity.get("name", "Unknown")
            entity_type = entity.get("type", "Unknown")
            confidence = entity.get("confidence", 0.0)
            
            entity_rows += f"""
            <tr>
                <td>{name}</td>
                <td>{entity_type}</td>
                <td>{confidence:.2f}</td>
            </tr>
            """
        except Exception as e:
            logger.warning(f"Error processing entity: {e}")
    
    relationship_rows = ""
    for rel in relationships[:100]:  # Limit to 100
        try:
            source_name = rel.get("source_name", "Unknown")
            target_name = rel.get("target_name", "Unknown")
            rel_type = rel.get("type", "Unknown")
            confidence = rel.get("confidence", 0.0)
            
            relationship_rows += f"""
            <tr>
                <td>{source_name}</td>
                <td>{rel_type}</td>
                <td>{target_name}</td>
                <td>{confidence:.2f}</td>
            </tr>
            """
        except Exception as e:
            logger.warning(f"Error processing relationship: {e}")
    
    # Check for graph visualization
    graph_viz_path = os.path.join(output_dir, "graphs", "knowledge_graph.html")
    graph_viz_rel_path = os.path.relpath(graph_viz_path, output_dir)
    
    # Create the HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Simplified Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .graph-container {{
                border: 1px solid #ddd;
                padding: 10px;
                margin-bottom: 20px;
            }}
            iframe {{
                width: 100%;
                height: 600px;
                border: none;
            }}
            pre {{
                background-color: #f5f5f5;
                padding: 15px;
                overflow-x: auto;
                white-space: pre-wrap;
            }}
        </style>
    </head>
    <body>
        <h1>Упрощенный отчет анализа текста</h1>
        
        <div>
            <p><strong>Файл:</strong> {original_file}</p>
            <p><strong>Дата анализа:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Сущностей:</strong> {len(entities)}</p>
            <p><strong>Отношений:</strong> {len(relationships)}</p>
        </div>
        
        <h2>Визуализация графа знаний</h2>
        <div class="graph-container">
            <iframe src="{graph_viz_rel_path}"></iframe>
        </div>
        
        <h2>Отчет о графе</h2>
        <pre>{graph_report_content}</pre>
        
        <h2>Первые 100 сущностей</h2>
        <table>
            <thead>
                <tr>
                    <th>Сущность</th>
                    <th>Тип</th>
                    <th>Достоверность</th>
                </tr>
            </thead>
            <tbody>
                {entity_rows}
            </tbody>
        </table>
        
        <h2>Первые 100 отношений</h2>
        <table>
            <thead>
                <tr>
                    <th>Источник</th>
                    <th>Отношение</th>
                    <th>Цель</th>
                    <th>Достоверность</th>
                </tr>
            </thead>
            <tbody>
                {relationship_rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    
    # Write the report
    report_path = os.path.join(output_dir, "simple_report.html")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Simple report created: {report_path}")
    return report_path

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python fix_report_simple.py <output_directory> [original_file]")
        return 1
    
    output_dir = sys.argv[1]
    original_file = sys.argv[2] if len(sys.argv) > 2 else "Unknown source"
    
    if not os.path.exists(output_dir):
        logger.error(f"Output directory not found: {output_dir}")
        return 1
    
    try:
        report_path = create_simple_report(output_dir, original_file)
        print(f"\nSimple report created: {report_path}")
        print("You can now view this report in your browser.")
        return 0
    except Exception as e:
        logger.error(f"Error creating report: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())