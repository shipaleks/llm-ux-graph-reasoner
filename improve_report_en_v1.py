#!/usr/bin/env python3
"""
Script for improving reports by adding detailed theory descriptions
and information about the knowledge graph expansion process in English.
"""

import os
import sys
import json
import logging
import time
import argparse
from pathlib import Path
import glob
import re
import shutil

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def find_latest_output_dir(base_dir="output"):
    """Finds the most recent analysis output directory."""
    output_dirs = glob.glob(f"{base_dir}/[0-9]*_[0-9]*")
    if not output_dirs:
        return None
    return sorted(output_dirs)[-1]

def find_theories_file(output_dir):
    """Finds the theories file in the output directory."""
    theories_file = os.path.join(output_dir, "theories", "theories.json")
    if os.path.exists(theories_file):
        return theories_file
    return None

def find_report_file(output_dir):
    """Finds the report file in the output directory."""
    report_file = os.path.join(output_dir, "report.html")
    if os.path.exists(report_file):
        return report_file
    return None

def find_expansion_report(output_dir):
    """Finds the graph expansion report."""
    # First check the expanded graphs folder
    expansion_report = os.path.join(output_dir, "graphs", "expanded", "expansion_report.html")
    if os.path.exists(expansion_report):
        return expansion_report
    
    # Check other possible locations
    expansion_report = os.path.join(output_dir, "expansion_report.html")
    if os.path.exists(expansion_report):
        return expansion_report
    
    # Check for expansion data json
    expansion_data = os.path.join(output_dir, "graphs", "expanded", "expansion_data.json")
    if os.path.exists(expansion_data):
        return expansion_data
    
    # Search for any HTML file related to expansion
    expansion_files = glob.glob(os.path.join(output_dir, "**", "*expansion*.html"), recursive=True)
    if expansion_files:
        return expansion_files[0]
    
    return None

def improve_theories_descriptions(theories_file):
    """Improves theory descriptions by adding details."""
    try:
        with open(theories_file, 'r', encoding='utf-8') as f:
            theories = json.load(f)
        
        if not theories:
            logger.warning("Theories file is empty")
            return False
        
        # For each theory, add an extended description if it doesn't exist
        for theory in theories:
            # If the theory doesn't have a detailed description or it's short
            if "description" not in theory or len(theory["description"]) < 100:
                # Create an extended description from available information
                name = theory.get("title", "")
                summary = theory.get("summary", "")
                
                # Get hypotheses or evidence statements
                evidence_texts = []
                evidence_items = theory.get("evidence", [])
                for evidence in evidence_items:
                    evidence_text = evidence.get("text", "")
                    if evidence_text:
                        evidence_texts.append(f"- {evidence_text}")
                
                # Get key entities
                key_entities = []
                entities = theory.get("key_entities", [])
                for entity in entities:
                    entity_name = entity.get("name", "")
                    entity_role = entity.get("role", "")
                    if entity_name and entity_role:
                        key_entities.append(f"- {entity_name}: {entity_role}")
                
                # Format the extended description
                description = f"""
{summary}

This theory is based on the analysis of the document and the relationships identified within it.

Key evidence supporting this theory:
{chr(10).join(evidence_texts) if evidence_texts else "No specific evidence provided."}

Key entities involved:
{chr(10).join(key_entities) if key_entities else "No key entities specified."}

The theory proposes to view the presented information as an interconnected structure,
where each element plays a role in the overall picture. This approach allows for a better
understanding of the context and reveals hidden patterns that may not be obvious from a
surface reading of the text.
                """
                
                theory["description"] = description.strip()
        
        # Save the updated theories
        with open(theories_file, 'w', encoding='utf-8') as f:
            json.dump(theories, f, ensure_ascii=False, indent=2)
        
        logger.info("Theories updated with extended descriptions")
        return True
    
    except Exception as e:
        logger.error(f"Error improving theory descriptions: {str(e)}")
        return False

def extract_expansion_info(expansion_report):
    """Extracts information about the graph expansion process."""
    if not expansion_report or not os.path.exists(expansion_report):
        return None
    
    try:
        # If it's a JSON file, load it directly
        if expansion_report.endswith('.json'):
            with open(expansion_report, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Create structured data for questions
                expansion_data = {
                    "questions": [],
                    "answers": []
                }
                
                # Add questions from the JSON data
                for question in data.get("questions", []):
                    expansion_data["questions"].append({
                        "target": question.get("target_name", ""),
                        "question": question.get("question", "")
                    })
                
                # Add answers if available
                for answer in data.get("answers", []):
                    expansion_data["answers"].append({
                        "question": answer.get("question", ""),
                        "answer": answer.get("answer", ""),
                        "confidence": answer.get("confidence", "Unknown")
                    })
                
                return expansion_data
        
        # Otherwise process as HTML
        with open(expansion_report, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract information using regular expressions
        expansion_data = {
            "questions": [],
            "answers": []
        }
        
        # Find all questions
        question_pattern = r'<div class="question">\s*<h4>(.*?)</h4>\s*<p>(.*?)</p>'
        question_matches = re.findall(question_pattern, content, re.DOTALL)
        
        for target, question in question_matches:
            expansion_data["questions"].append({
                "target": target.strip(),
                "question": question.strip()
            })
        
        # Find all answers
        answer_pattern = r'<div class="answer">\s*<h4>(.*?)</h4>\s*<p>(.*?)</p>\s*<div class="confidence">(.*?)</div>'
        answer_matches = re.findall(answer_pattern, content, re.DOTALL)
        
        for question, answer, confidence in answer_matches:
            expansion_data["answers"].append({
                "question": question.strip(),
                "answer": answer.strip(),
                "confidence": confidence.strip()
            })
        
        return expansion_data
    
    except Exception as e:
        logger.error(f"Error extracting expansion information: {str(e)}")
        return None

def create_expansion_section(expansion_data):
    """Creates an HTML section with information about the graph expansion."""
    if not expansion_data:
        return ""
    
    html = """
    <div class="expansion-section">
        <h2>Knowledge Graph Expansion Process</h2>
        <p>During the analysis, the system asked additional questions to expand the knowledge graph.
        This process helps reveal hidden relationships and provides a more complete picture.</p>
        
        <h3>Analysis Questions</h3>
        <div class="expansion-questions">
    """
    
    # Add questions
    questions = expansion_data.get("questions", [])
    if questions:
        html += "<ul>"
        for q in questions:
            html += f'<li><strong>{q.get("target", "")}</strong>: {q.get("question", "")}</li>'
        html += "</ul>"
    else:
        html += "<p>No question information available</p>"
    
    html += """
        </div>
        
        <h3>Answers and New Knowledge</h3>
        <div class="expansion-answers">
    """
    
    # Add answers
    answers = expansion_data.get("answers", [])
    if answers:
        for i, a in enumerate(answers):
            html += f"""
            <div class="expansion-answer">
                <h4>Question {i+1}: {a.get("question", "")}</h4>
                <div class="answer-content">
                    <p>{a.get("answer", "")}</p>
                </div>
                <div class="answer-confidence">Confidence: {a.get("confidence", "")}</div>
            </div>
            """
    else:
        html += "<p>No answer information available</p>"
    
    html += """
        </div>
    </div>
    """
    
    return html

def translate_russian_to_english(report_content):
    """Translates Russian headings and labels to English."""
    translations = {
        "Дата:": "Date:",
        "Источник:": "Source:",
        "Количество сущностей:": "Number of entities:",
        "Количество связей:": "Number of relationships:",
        "Количество текстовых сегментов:": "Number of text segments:",
        "Содержание": "Contents",
        "Аннотация": "Abstract",
        "Краткий обзор": "Summary",
        "Процесс исследования": "Research Process",
        "Контекстный анализ": "Contextual Analysis",
        "Анализ сущностей": "Entity Analysis",
        "Анализ отношений": "Relationship Analysis",
        "Визуализация графа": "Graph Visualization",
        "Метрики графа": "Graph Metrics",
        "Теории и гипотезы": "Theories and Hypotheses",
        "Заключение": "Conclusion",
        "Шаг 1: Загрузка и сегментация текста": "Step 1: Loading and Segmenting Text",
        "Шаг 2: Контекстный анализ": "Step 2: Contextual Analysis",
        "Шаг 3: Извлечение сущностей": "Step 3: Entity Extraction",
        "Шаг 4: Определение отношений": "Step 4: Relationship Identification",
        "Шаг 5: Построение графа знаний": "Step 5: Knowledge Graph Construction",
        "Шаг 6: Анализ графа и генерация теорий": "Step 6: Graph Analysis and Theory Generation",
        "Исходный текст был загружен и разделен на": "The source text was loaded and divided into",
        "логических сегментов для детального анализа.": "logical segments for detailed analysis.",
        "Выполнен анализ контекста между сегментами для выявления смысловых связей.": "Context analysis was performed between segments to identify semantic connections.",
        "Выявлено": "Identified",
        "связей между сегментами.": "connections between segments.",
        "Из текста выделены": "Extracted",
        "ключевых сущностей различных типов.": "key entities of various types.",
        "Между сущностями выявлены": "Between entities,",
        "связей и отношений.": "connections and relationships were identified.",
        "На основе выделенных сущностей и отношений построен граф знаний.": "Based on the extracted entities and relationships, a knowledge graph was constructed.",
        "Проведен анализ графа и сформированы теории, объясняющие выявленные связи.": "Graph analysis was performed and theories were formed explaining the identified connections.",
        "теорий на основе анализа графа.": "theories based on graph analysis.",
        "Сводки по сегментам": "Segment Summaries",
        "Сегмент": "Segment",
        "Сводка:": "Summary:",
        "Роль в тексте:": "Role in text:",
        "Ключевые моменты:": "Key points:",
        "Связь с родительским сегментом:": "Relationship to parent segment:",
        "Связи между сегментами": "Connections between segments",
        "От сегмента": "From segment",
        "Тип связи": "Connection type",
        "К сегменту": "To segment",
        "В этом разделе представлены ключевые сущности, выявленные в анализируемом тексте.": "This section presents the key entities identified in the analyzed text.",
        "Сущность": "Entity",
        "Тип": "Type",
        "Достоверность": "Confidence",
        "Атрибуты": "Attributes",
        "В этом разделе представлены отношения, выявленные между сущностями в анализируемом тексте.": "This section presents the relationships identified between entities in the analyzed text.",
        "Источник": "Source",
        "Отношение": "Relationship",
        "Цель": "Target",
        "Эта интерактивная визуализация представляет граф знаний, где сущности являются узлами, а отношения - связями.": "This interactive visualization represents the knowledge graph, where entities are nodes and relationships are links.",
        "Плотность графа": "Graph Density",
        "Средняя степень": "Average Degree",
        "Средний коэффициент кластеризации": "Average Clustering Coefficient",
        "Диаметр графа": "Graph Diameter",
        "Центральные сущности": "Central Entities",
        "Показатель центральности": "Centrality Score",
        "В этом разделе представлены теории и гипотезы, выведенные из анализа графа знаний.": "This section presents theories and hypotheses derived from the knowledge graph analysis.",
        "Сгенерировано системой синтеза графа знаний": "Generated by the Knowledge Graph Synthesis System"
    }
    
    # Replace Russian text with English translations
    for russian, english in translations.items():
        report_content = report_content.replace(russian, english)
    
    return report_content

def improve_report(report_file, theories_file, expansion_data):
    """Improves the HTML report by adding detailed information."""
    if not os.path.exists(report_file):
        logger.error(f"Report file not found: {report_file}")
        return False
    
    try:
        # Read the current report
        with open(report_file, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # Translate Russian text to English
        report_content = translate_russian_to_english(report_content)
        
        # Create a backup
        backup_file = report_file + ".bak"
        shutil.copy2(report_file, backup_file)
        logger.info(f"Created report backup: {backup_file}")
        
        # Read updated theories
        theories = []
        if theories_file and os.path.exists(theories_file):
            with open(theories_file, 'r', encoding='utf-8') as f:
                theories = json.load(f)
        
        # Find the theories section in HTML and replace it
        theories_section_pattern = r'<section id="theories" class="section">.*?</section>'
        
        if theories:
            # Create a new theories section
            theories_html = """
            <section id="theories" class="section">
                <h2>Theories and Hypotheses</h2>
                <p>This section presents theories and hypotheses derived from the knowledge graph analysis.</p>
            """
            
            for i, theory in enumerate(theories):
                title = theory.get("title", f"Theory {i+1}")
                description = theory.get("description", "")
                confidence = theory.get("confidence", 0.0)
                
                theories_html += f"""
                <div class="research-process">
                    <h3>{title}</h3>
                    <p><strong>Confidence:</strong> {confidence:.2f}</p>
                    <div class="theory-description">
                        {description.replace("\n", "<br>")}
                    </div>
                """
                
                # Add hypotheses if they exist
                hypotheses = theory.get("hypotheses", [])
                if hypotheses:
                    theories_html += """
                    <div class="theory-hypotheses">
                        <h4>Key Hypotheses:</h4>
                        <ul>
                    """
                    
                    for h in hypotheses:
                        statement = h.get("statement", "")
                        if statement:
                            theories_html += f"<li>{statement}</li>"
                    
                    theories_html += """
                        </ul>
                    </div>
                    """
                
                # Add evidence if it exists
                evidence = theory.get("evidence", [])
                if evidence:
                    theories_html += """
                    <div class="theory-evidence">
                        <h4>Supporting Evidence:</h4>
                        <ul>
                    """
                    
                    for e in evidence:
                        text = e.get("text", "")
                        relevance = e.get("relevance", "")
                        if text:
                            theories_html += f"<li><strong>{text}</strong>"
                            if relevance:
                                theories_html += f" - {relevance}"
                            theories_html += "</li>"
                    
                    theories_html += """
                        </ul>
                    </div>
                    """
                
                theories_html += "</div>"
            
            theories_html += """
            </section>
            """
            
            # Replace the theories section
            if re.search(theories_section_pattern, report_content, re.DOTALL):
                report_content = re.sub(theories_section_pattern, theories_html, report_content, flags=re.DOTALL)
            else:
                # If there's no theories section, add before the closing body tag
                report_content = report_content.replace("</body>", f"{theories_html}\n</body>")
        
        # Add the graph expansion information section
        expansion_html = create_expansion_section(expansion_data)
        if expansion_html:
            # Create the section id if it doesn't exist
            if '<li><a href="#expansion">Graph Expansion</a></li>' not in report_content:
                # Add to the table of contents
                toc_pattern = r'(<div class="toc">.*?</ul>)'
                replacement = r'\1\n                <li><a href="#expansion">Graph Expansion</a></li>'
                report_content = re.sub(toc_pattern, replacement, report_content, flags=re.DOTALL)
            
            # Check if there's already an expansion section
            expansion_section_pattern = r'<section id="expansion" class="section">.*?</section>'
            
            # Create the full section with id
            full_expansion_section = f'<section id="expansion" class="section">{expansion_html}</section>'
            
            if re.search(expansion_section_pattern, report_content, re.DOTALL):
                report_content = re.sub(expansion_section_pattern, full_expansion_section, report_content, flags=re.DOTALL)
            else:
                # Add before the conclusion section
                conclusion_pattern = r'<section id="conclusion" class="section">'
                report_content = report_content.replace(conclusion_pattern, f"{full_expansion_section}\n\n        {conclusion_pattern}")
        
        # Add CSS for the new sections
        css_styles = """
        <style>
            .expansion-section {
                margin: 20px 0;
                padding: 15px;
                background-color: #f5f9ff;
                border-left: 4px solid #4a90e2;
                border-radius: 4px;
            }
            .expansion-questions ul {
                list-style-type: disc;
                margin-left: 20px;
            }
            .expansion-answer {
                margin-bottom: 20px;
                background-color: #f8f8f8;
                padding: 15px;
                border-left: 3px solid #666;
                border-radius: 4px;
            }
            .answer-content {
                margin: 10px 0;
            }
            .answer-confidence {
                font-style: italic;
                color: #666;
            }
            .theory {
                margin-bottom: 30px;
                background-color: #f5f9ff;
                padding: 15px;
                border-left: 4px solid #4a90e2;
                border-radius: 4px;
            }
            .theory-description {
                margin: 15px 0;
                line-height: 1.6;
            }
            .theory-confidence {
                font-style: italic;
                color: #555;
                margin-bottom: 10px;
            }
            .theory-hypotheses, .theory-evidence {
                background-color: #f8f8f8;
                padding: 15px;
                border-radius: 4px;
                margin-top: 15px;
            }
            .theory-hypotheses ul, .theory-evidence ul {
                list-style-type: disc;
                margin-left: 20px;
            }
        </style>
        """
        
        # Add styles before the closing head tag
        if "</head>" in report_content and "<style>" not in report_content:
            report_content = report_content.replace("</head>", f"{css_styles}\n</head>")
        
        # Save the updated report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Create the improved version of the report
        improved_report_file = os.path.join(os.path.dirname(report_file), "improved_report_en.html")
        with open(improved_report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Report improved and saved: {improved_report_file}")
        return improved_report_file
    
    except Exception as e:
        logger.error(f"Error improving report: {str(e)}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Improve report by adding details about theories and graph expansion in English")
    parser.add_argument(
        "--dir", "-d",
        help="Directory with analysis results (defaults to finding the most recent)",
        default=None
    )
    parser.add_argument(
        "--force", "-f",
        help="Force create an improved report, even if it already exists",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Determine the results directory
    output_dir = args.dir
    if not output_dir:
        output_dir = find_latest_output_dir()
        if not output_dir:
            logger.error("Could not find analysis results directory")
            return 1
    
    logger.info(f"Working with directory: {output_dir}")
    
    # Check if an improved report already exists
    improved_report = os.path.join(output_dir, "improved_report_en.html")
    if os.path.exists(improved_report) and not args.force:
        logger.info(f"Improved report already exists: {improved_report}")
        print(f"\nImproved report already exists: {improved_report}")
        return 0
    
    # Find necessary files
    theories_file = find_theories_file(output_dir)
    if not theories_file:
        logger.warning("Theories file not found")
    
    report_file = find_report_file(output_dir)
    if not report_file:
        logger.error("Report file not found")
        return 1
    
    expansion_report = find_expansion_report(output_dir)
    if expansion_report:
        logger.info(f"Found graph expansion file: {expansion_report}")
        expansion_data = extract_expansion_info(expansion_report)
    else:
        logger.warning("Graph expansion file not found")
        expansion_data = None
    
    # Improve theory descriptions
    if theories_file:
        improve_theories_descriptions(theories_file)
    
    # Improve the report
    result = improve_report(report_file, theories_file, expansion_data)
    
    if result:
        print(f"\n✅ Report successfully improved: {result}")
        print("You can open it in your browser.")
        return 0
    else:
        print("\n❌ Failed to improve report.")
        return 1

if __name__ == "__main__":
    sys.exit(main())