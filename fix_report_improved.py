#!/usr/bin/env python3
"""
Improved script to create a meaningful HTML visualization for a processed directory.
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

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

def create_improved_report(output_dir, original_file="Unknown source"):
    """Create an improved HTML report from the processed data."""
    logger.info(f"Creating improved HTML report for {output_dir}")
    
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
    entities_file = os.path.join(output_dir, "entities", "resolved_entities.json")
    if not os.path.exists(entities_file):
        entities_file = os.path.join(output_dir, "entities", "all_entities.json")
    
    entities = load_json_file(entities_file) or []
    
    # Load relationships
    relationships_file = os.path.join(output_dir, "relationships", "grounded_relationships.json")
    if not os.path.exists(relationships_file):
        relationships_file = os.path.join(output_dir, "relationships", "all_relationships.json")
    
    relationships = load_json_file(relationships_file) or []
    
    # Create a mapping from entity IDs to names
    entity_map = {}
    for entity in entities:
        entity_id = entity.get("id")
        if entity_id:
            entity_map[entity_id] = {
                "name": entity.get("name", "Unknown"),
                "type": entity.get("type", "Unknown"),
                "confidence": entity.get("confidence", 0.0)
            }
    
    # Group entities by type
    entities_by_type = defaultdict(list)
    for entity in entities:
        entity_type = entity.get("type", "Unknown")
        entities_by_type[entity_type].append(entity)
    
    # Sort entity types by count
    sorted_entity_types = sorted(entities_by_type.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Group relationships by type
    relationships_by_type = defaultdict(list)
    for rel in relationships:
        rel_type = rel.get("type", "Unknown")
        relationships_by_type[rel_type].append(rel)
    
    # Sort relationship types by count
    sorted_rel_types = sorted(relationships_by_type.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Create entity table by type
    entity_tables = ""
    for entity_type, entities_of_type in sorted_entity_types[:10]:  # Top 10 entity types
        entity_rows = ""
        for entity in entities_of_type[:20]:  # Top 20 entities of this type
            try:
                name = entity.get("name", "Unknown")
                confidence = entity.get("confidence", 0.0)
                
                entity_rows += f"""
                <tr>
                    <td>{name}</td>
                    <td>{confidence:.2f}</td>
                </tr>
                """
            except Exception as e:
                logger.warning(f"Error processing entity: {e}")
        
        entity_tables += f"""
        <h3>Тип: {entity_type} ({len(entities_of_type)} сущностей)</h3>
        <table>
            <thead>
                <tr>
                    <th>Сущность</th>
                    <th>Достоверность</th>
                </tr>
            </thead>
            <tbody>
                {entity_rows}
            </tbody>
        </table>
        """
    
    # Create relationship table by type
    relationship_tables = ""
    for rel_type, rels_of_type in sorted_rel_types[:10]:  # Top 10 relationship types
        relationship_rows = ""
        for rel in rels_of_type[:20]:  # Top 20 relationships of this type
            try:
                source_id = rel.get("source_id")
                target_id = rel.get("target_id")
                confidence = rel.get("confidence", 0.0)
                
                # Get entity names from the map
                source_name = entity_map.get(source_id, {}).get("name", "Unknown")
                target_name = entity_map.get(target_id, {}).get("name", "Unknown")
                
                relationship_rows += f"""
                <tr>
                    <td>{source_name}</td>
                    <td>{target_name}</td>
                    <td>{confidence:.2f}</td>
                </tr>
                """
            except Exception as e:
                logger.warning(f"Error processing relationship: {e}")
        
        relationship_tables += f"""
        <h3>Тип отношения: {rel_type} ({len(rels_of_type)} связей)</h3>
        <table>
            <thead>
                <tr>
                    <th>Источник</th>
                    <th>Цель</th>
                    <th>Достоверность</th>
                </tr>
            </thead>
            <tbody>
                {relationship_rows}
            </tbody>
        </table>
        """
    
    # Create entity count by type chart data
    entity_type_data = []
    for entity_type, entities_of_type in sorted_entity_types[:15]:  # Top 15 for the chart
        entity_type_data.append({
            "type": entity_type,
            "count": len(entities_of_type)
        })
    
    # Load theories if available
    theories_file = os.path.join(output_dir, "theories", "theories.json")
    theories = load_json_file(theories_file) or []
    
    # Load patterns if available
    patterns_file = os.path.join(output_dir, "theories", "patterns.json") 
    patterns = load_json_file(patterns_file) or []
    
    # Load expansion data if available
    expansion_file = os.path.join(output_dir, "graphs", "expanded", "expansion_data.json")
    expansion_data = load_json_file(expansion_file) or {}
    
    # Load expansion process documentation if available
    expansion_process_file = os.path.join(output_dir, "graphs", "expanded", "expansion_process.md")
    if os.path.exists(expansion_process_file):
        try:
            with open(expansion_process_file, 'r', encoding='utf-8') as f:
                expansion_process = f.read()
        except Exception as e:
            logger.error(f"Error reading expansion process: {str(e)}")
            expansion_process = "Error loading expansion process documentation."
    else:
        expansion_process = "No expansion process documentation available."
    
    # Prepare theories section
    theories_html = ""
    if theories:
        for i, theory in enumerate(theories):
            # Extract theory data
            theory_name = theory.get("name", f"Теория {i+1}")
            theory_desc = theory.get("description", "Нет описания")
            theory_conf = theory.get("confidence", 0.0)
            
            # Extract hypotheses
            hypotheses_html = ""
            if "hypotheses" in theory and theory["hypotheses"]:
                for h, hypothesis in enumerate(theory["hypotheses"]):
                    h_statement = hypothesis.get("statement", "")
                    h_confidence = hypothesis.get("confidence", 0.0)
                    
                    # Extract evidence
                    evidence_html = ""
                    if "evidence" in hypothesis and hypothesis["evidence"]:
                        for ev in hypothesis["evidence"]:
                            ev_desc = ev.get("description", "")
                            ev_strength = ev.get("strength", 0.0)
                            evidence_html += f"""
                            <div class="evidence-item">
                                <p><strong>Доказательство:</strong> {ev_desc}</p>
                                <div class="evidence-strength">
                                    <div class="evidence-bar" style="width: {ev_strength * 100}%;"></div>
                                    <span>{ev_strength:.2f}</span>
                                </div>
                            </div>
                            """
                    
                    hypotheses_html += f"""
                    <div class="hypothesis">
                        <h4>Гипотеза {h+1}: {h_statement}</h4>
                        <div class="confidence">Достоверность: {h_confidence:.2f}</div>
                        <div class="evidence">
                            {evidence_html}
                        </div>
                    </div>
                    """
            
            theories_html += f"""
            <div class="theory">
                <h3>{theory_name}</h3>
                <div class="theory-confidence">Достоверность: {theory_conf:.2f}</div>
                <p class="theory-description">{theory_desc}</p>
                {hypotheses_html}
            </div>
            """
    else:
        theories_html = "<p>Теории не были сгенерированы или не найдены в данных.</p>"
    
    # Prepare patterns section
    patterns_html = ""
    if patterns:
        for i, pattern in enumerate(patterns):
            pattern_name = pattern.get("name", f"Паттерн {i+1}")
            pattern_desc = pattern.get("description", "Нет описания")
            pattern_entities = pattern.get("entities", [])
            pattern_relationships = pattern.get("relationships", [])
            
            entities_list = ""
            for entity in pattern_entities[:10]:  # Show at most 10 entities
                entity_name = entity.get("name", "")
                entity_type = entity.get("type", "")
                entities_list += f"<li>{entity_name} ({entity_type})</li>"
            
            relationships_list = ""
            for rel in pattern_relationships[:10]:  # Show at most 10 relationships
                source = rel.get("source", "")
                target = rel.get("target", "")
                rel_type = rel.get("type", "")
                relationships_list += f"<li>{source} → {rel_type} → {target}</li>"
            
            patterns_html += f"""
            <div class="pattern">
                <h3>{pattern_name}</h3>
                <p>{pattern_desc}</p>
                
                <div class="pattern-details">
                    <div class="pattern-entities">
                        <h4>Ключевые сущности:</h4>
                        <ul>{entities_list}</ul>
                    </div>
                    
                    <div class="pattern-relationships">
                        <h4>Ключевые отношения:</h4>
                        <ul>{relationships_list}</ul>
                    </div>
                </div>
            </div>
            """
    else:
        patterns_html = "<p>Паттерны не были обнаружены или не найдены в данных.</p>"
    
    # Prepare expansion section
    expansion_html = ""
    if expansion_data:
        # Extract targets and questions
        targets = expansion_data.get("targets", [])
        questions = expansion_data.get("questions", [])
        insights = expansion_data.get("insights", [])
        
        # Prepare targets section
        targets_html = ""
        if targets:
            targets_html = "<h3>Исследованные сущности</h3><ul>"
            for target in targets:
                if isinstance(target, str):
                    targets_html += f"<li>{target}</li>"
                elif isinstance(target, dict) and "name" in target:
                    targets_html += f"<li>{target['name']}</li>"
            targets_html += "</ul>"
        
        # Prepare questions section
        questions_html = ""
        if questions:
            questions_html = "<h3>Заданные вопросы</h3><ol>"
            for question in questions:
                if isinstance(question, str):
                    questions_html += f"<li>{question}</li>"
                elif isinstance(question, dict) and "text" in question:
                    questions_html += f"<li>{question['text']}</li>"
            questions_html += "</ol>"
        
        # Prepare insights section
        insights_html = ""
        if insights:
            insights_html = "<h3>Ключевые инсайты</h3><ul>"
            for insight in insights:
                if isinstance(insight, str):
                    insights_html += f"<li>{insight}</li>"
                elif isinstance(insight, dict) and "text" in insight:
                    insights_html += f"<li>{insight['text']}</li>"
            insights_html += "</ul>"
        
        expansion_html = f"""
        <div class="expansion-summary">
            {targets_html}
            {questions_html}
            {insights_html}
        </div>
        <div class="expansion-process">
            <h3>Процесс расширения графа знаний</h3>
            <pre>{expansion_process}</pre>
        </div>
        """
    else:
        expansion_html = "<p>Данные о расширении графа не найдены.</p>"
    
    # Create relationship count by type chart data
    rel_type_data = []
    for rel_type, rels_of_type in sorted_rel_types[:15]:  # Top 15 for the chart
        rel_type_data.append({
            "type": rel_type,
            "count": len(rels_of_type)
        })
    
    # Check for graph visualization
    graph_viz_path = os.path.join(output_dir, "graphs", "knowledge_graph.html")
    graph_viz_rel_path = os.path.relpath(graph_viz_path, output_dir)
    
    # Check for filtered graph visualization
    filtered_graph_viz_path = os.path.join(output_dir, "graphs", "knowledge_graph_filtered.html")
    if os.path.exists(filtered_graph_viz_path):
        filtered_graph_viz_rel_path = os.path.relpath(filtered_graph_viz_path, output_dir)
        filtered_graph_section = f"""
        <h2>Отфильтрованный граф знаний (высокая достоверность)</h2>
        <div class="graph-container">
            <iframe src="{filtered_graph_viz_rel_path}"></iframe>
        </div>
        """
    else:
        filtered_graph_section = ""
    
    # Create the HTML report with interactive charts
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Улучшенный отчет анализа</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
                font-size: 14px;
            }}
            .chart-container {{
                width: 100%;
                height: 400px;
                margin-bottom: 30px;
            }}
            .metadata {{
                background-color: #f9f9f9;
                padding: 15px;
                border-left: 4px solid #2c3e50;
                margin-bottom: 20px;
            }}
            .tabs {{
                overflow: hidden;
                border: 1px solid #ccc;
                background-color: #f1f1f1;
            }}
            .tabs button {{
                background-color: inherit;
                float: left;
                border: none;
                outline: none;
                cursor: pointer;
                padding: 14px 16px;
                transition: 0.3s;
                font-size: 17px;
            }}
            .tabs button:hover {{
                background-color: #ddd;
            }}
            .tabs button.active {{
                background-color: #2c3e50;
                color: white;
            }}
            .tabcontent {{
                display: none;
                padding: 6px 12px;
                border: 1px solid #ccc;
                border-top: none;
            }}
            .tabcontent.active {{
                display: block;
            }}
            
            /* Styles for theories and hypotheses */
            .theory {{
                background-color: #f5f9ff;
                border-left: 4px solid #4a90e2;
                margin-bottom: 30px;
                padding: 15px;
                border-radius: 4px;
            }}
            
            .theory-confidence {{
                color: #777;
                margin-bottom: 10px;
                font-style: italic;
            }}
            
            .theory-description {{
                line-height: 1.6;
                margin-bottom: 20px;
            }}
            
            .hypothesis {{
                background-color: #f9f9f9;
                padding: 15px;
                margin: 10px 0;
                border-left: 3px solid #666;
                border-radius: 4px;
            }}
            
            .evidence {{
                margin-top: 15px;
            }}
            
            .evidence-item {{
                margin-bottom: 10px;
                padding-left: 15px;
            }}
            
            .evidence-strength {{
                height: 6px;
                background-color: #eee;
                width: 100%;
                max-width: 300px;
                border-radius: 3px;
                margin-top: 5px;
                position: relative;
            }}
            
            .evidence-bar {{
                height: 100%;
                background-color: #4CAF50;
                border-radius: 3px;
            }}
            
            .evidence-strength span {{
                position: absolute;
                right: -30px;
                top: -7px;
                font-size: 12px;
                color: #666;
            }}
            
            /* Styles for patterns */
            .pattern {{
                background-color: #f7f7ff;
                padding: 15px;
                margin-bottom: 25px;
                border-left: 4px solid #8e44ad;
                border-radius: 4px;
            }}
            
            .pattern-details {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-top: 15px;
            }}
            
            .pattern-entities, .pattern-relationships {{
                flex: 1;
                min-width: 300px;
            }}
            
            /* Styles for expansion */
            .expansion-summary {{
                background-color: #f6fff6;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 4px;
                border-left: 4px solid #2ecc71;
            }}
            
            .expansion-process {{
                margin-top: 30px;
            }}
            
            .expansion-process pre {{
                max-height: 600px;
                overflow-y: auto;
            }}
        </style>
    </head>
    <body>
        <h1>Улучшенный отчет анализа текста</h1>
        
        <div class="metadata">
            <p><strong>Файл:</strong> {original_file}</p>
            <p><strong>Дата анализа:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Сущностей:</strong> {len(entities)}</p>
            <p><strong>Отношений:</strong> {len(relationships)}</p>
            <p><strong>Типов сущностей:</strong> {len(entities_by_type)}</p>
            <p><strong>Типов отношений:</strong> {len(relationships_by_type)}</p>
        </div>
        
        <!-- Tabs -->
        <div class="tabs">
            <button class="tablinks active" onclick="openTab(event, 'GraphTab')">Граф знаний</button>
            <button class="tablinks" onclick="openTab(event, 'EntitiesTab')">Сущности</button>
            <button class="tablinks" onclick="openTab(event, 'RelationshipsTab')">Отношения</button>
            <button class="tablinks" onclick="openTab(event, 'TheoriesTab')">Теории и гипотезы</button>
            <button class="tablinks" onclick="openTab(event, 'PatternsTab')">Паттерны</button>
            <button class="tablinks" onclick="openTab(event, 'ExpansionTab')">Расширение графа</button>
            <button class="tablinks" onclick="openTab(event, 'ReportTab')">Отчет о графе</button>
        </div>
        
        <!-- Graph Tab -->
        <div id="GraphTab" class="tabcontent active">
            <h2>Визуализация графа знаний</h2>
            <div class="graph-container">
                <iframe src="{graph_viz_rel_path}"></iframe>
            </div>
            
            {filtered_graph_section}
        </div>
        
        <!-- Entities Tab -->
        <div id="EntitiesTab" class="tabcontent">
            <h2>Анализ сущностей</h2>
            
            <div class="chart-container">
                <canvas id="entityTypeChart"></canvas>
            </div>
            
            {entity_tables}
        </div>
        
        <!-- Relationships Tab -->
        <div id="RelationshipsTab" class="tabcontent">
            <h2>Анализ отношений</h2>
            
            <div class="chart-container">
                <canvas id="relationshipTypeChart"></canvas>
            </div>
            
            {relationship_tables}
        </div>
        
        <!-- Theories Tab -->
        <div id="TheoriesTab" class="tabcontent">
            <h2>Теории и гипотезы</h2>
            {theories_html}
        </div>
        
        <!-- Patterns Tab -->
        <div id="PatternsTab" class="tabcontent">
            <h2>Паттерны в данных</h2>
            {patterns_html}
        </div>
        
        <!-- Expansion Tab -->
        <div id="ExpansionTab" class="tabcontent">
            <h2>Расширение графа знаний</h2>
            {expansion_html}
        </div>
        
        <!-- Report Tab -->
        <div id="ReportTab" class="tabcontent">
            <h2>Отчет о графе</h2>
            <pre>{graph_report_content}</pre>
        </div>
        
        <script>
            // Tab functionality
            function openTab(evt, tabName) {{
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tabcontent");
                for (i = 0; i < tabcontent.length; i++) {{
                    tabcontent[i].className = tabcontent[i].className.replace(" active", "");
                }}
                tablinks = document.getElementsByClassName("tablinks");
                for (i = 0; i < tablinks.length; i++) {{
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }}
                document.getElementById(tabName).className += " active";
                evt.currentTarget.className += " active";
            }}
            
            // Entity type chart
            var entityTypeData = {json.dumps(entity_type_data)};
            var entityTypeCtx = document.getElementById('entityTypeChart').getContext('2d');
            var entityTypeChart = new Chart(entityTypeCtx, {{
                type: 'bar',
                data: {{
                    labels: entityTypeData.map(item => item.type),
                    datasets: [{{
                        label: 'Количество сущностей по типу',
                        data: entityTypeData.map(item => item.count),
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }},
                    responsive: true,
                    maintainAspectRatio: false
                }}
            }});
            
            // Relationship type chart
            var relTypeData = {json.dumps(rel_type_data)};
            var relTypeCtx = document.getElementById('relationshipTypeChart').getContext('2d');
            var relTypeChart = new Chart(relTypeCtx, {{
                type: 'bar',
                data: {{
                    labels: relTypeData.map(item => item.type),
                    datasets: [{{
                        label: 'Количество отношений по типу',
                        data: relTypeData.map(item => item.count),
                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }},
                    responsive: true,
                    maintainAspectRatio: false
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    # Write the report
    report_path = os.path.join(output_dir, "improved_report.html")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Improved report created: {report_path}")
    return report_path

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python fix_report_improved.py <output_directory> [original_file]")
        return 1
    
    output_dir = sys.argv[1]
    original_file = sys.argv[2] if len(sys.argv) > 2 else "Unknown source"
    
    if not os.path.exists(output_dir):
        logger.error(f"Output directory not found: {output_dir}")
        return 1
    
    try:
        report_path = create_improved_report(output_dir, original_file)
        print(f"\nImproved report created: {report_path}")
        print("You can now view this report in your browser.")
        return 0
    except Exception as e:
        logger.error(f"Error creating report: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())