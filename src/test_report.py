"""Utility script for testing report generation and segment page creation with our improvements."""

import json
import os
import logging
from pathlib import Path
import sys
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.knowledge_graph_synth.output.report.generator import ReportGenerator
from src.knowledge_graph_synth.models.graph import KnowledgeGraph
from src.knowledge_graph_synth.models.entity import Entity
from src.knowledge_graph_synth.models.relationship import Relationship
from src.knowledge_graph_synth.models.provenance import SourceSpan
from src.knowledge_graph_synth.graph.expansion_report import ExpansionReportGenerator
from src.knowledge_graph_synth.cli.fix_segment_links import ensure_segment_pages

# Test data for expansion report
TEST_EXPANSION_DATA = {
    "iterations": [
        {
            "iteration": 0,
            "targets": [
                {
                    "entity_name": "ТехноИнновации",
                    "entity_type": "organization",
                    "relevance": "high",
                    "rationale": "Central entity with many connections"
                },
                {
                    "entity_name": "Иван Петров",
                    "entity_type": "person",
                    "relevance": "high",
                    "rationale": "Central entity with many connections"
                }
            ]
        }
    ],
    "targets": [
        {
            "entity_name": "ТехноИнновации",
            "entity_type": "organization",
            "relevance": "high",
            "rationale": "Central entity with many connections"
        },
        {
            "entity_name": "Иван Петров",
            "entity_type": "person", 
            "relevance": "high",
            "rationale": "Central entity with many connections"
        }
    ],
    "questions": [
        {
            "iteration": 0,
            "target_name": "ТехноИнновации",
            "target_type": "organization",
            "question": "Какие основные продукты или услуги предлагает компания 'ТехноИнновации'?"
        },
        {
            "iteration": 0,
            "target_name": "ТехноИнновации",
            "target_type": "organization",
            "question": "Сколько сотрудников работает в компании 'ТехноИнновации'?"
        },
        {
            "iteration": 0,
            "target_name": "Иван Петров",
            "target_type": "person",
            "question": "Какой опыт работы был у Ивана Петрова до того, как он стал генеральным директором 'ТехноИнновации'?"
        }
    ],
    "answers": [
        {
            "iteration": 0,
            "target_name": "ТехноИнновации",
            "target_type": "organization",
            "question": "Какие основные продукты или услуги предлагает компания 'ТехноИнновации'?",
            "answer": "На основании предоставленного текста, компания 'ТехноИнновации' работает над решениями с использованием искусственного интеллекта для здравоохранения. Это видно из информации о партнерстве с 'Глобал Системс' для работы над 'Проектом Альфа', который направлен на разработку решений с использованием искусственного интеллекта для здравоохранения с бюджетом 300 миллионов рублей.",
            "confidence": 0.85,
            "new_entities": "1. ИИ-решения (тип: продукт, атрибуты: область применения - здравоохранение)\n2. Проект Альфа (тип: проект, атрибуты: бюджет - 300 миллионов рублей)",
            "new_relationships": "1. ТехноИнновации РАЗРАБАТЫВАЕТ ИИ-решения\n2. ИИ-решения ПРИМЕНЯЮТСЯ_В здравоохранение"
        }
    ]
}

def load_entities(json_path):
    """Load entities from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        entities_data = json.load(f)
    
    entities = []
    for entity_data in entities_data:
        # Create Entity manually
        entity = Entity(
            id=entity_data.get('id', ''),
            name=entity_data.get('name', ''),
            type=entity_data.get('type', ''),
            attributes=entity_data.get('attributes', []),
            confidence=entity_data.get('confidence', 0.0),
            source_span=SourceSpan(
                document_id=entity_data.get('source_span', {}).get('document_id', ''),
                segment_id=entity_data.get('source_span', {}).get('segment_id', ''),
                start=entity_data.get('source_span', {}).get('start', 0),
                end=entity_data.get('source_span', {}).get('end', 0),
                text=entity_data.get('source_span', {}).get('text', '')
            ) if entity_data.get('source_span') else None
        )
        entities.append(entity)
    
    return entities

def load_relationships(json_path):
    """Load relationships from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        relationships_data = json.load(f)
    
    relationships = []
    for rel_data in relationships_data:
        # Create Relationship manually
        relationship = Relationship(
            id=rel_data.get('id', ''),
            source_id=rel_data.get('source_id', ''),
            target_id=rel_data.get('target_id', ''),
            type=rel_data.get('type', ''),
            directed=rel_data.get('directed', True),
            attributes=rel_data.get('attributes', []),
            confidence=rel_data.get('confidence', 0.0),
            source_span=SourceSpan(
                document_id=rel_data.get('source_span', {}).get('document_id', ''),
                segment_id=rel_data.get('source_span', {}).get('segment_id', ''),
                start=rel_data.get('source_span', {}).get('start', 0),
                end=rel_data.get('source_span', {}).get('end', 0),
                text=rel_data.get('source_span', {}).get('text', '')
            ) if rel_data.get('source_span') else None
        )
        relationships.append(relationship)
    
    return relationships

def generate_report(output_dir):
    """Generate the main HTML report."""
    # Load entities and relationships
    entities_path = os.path.join(output_dir, "entities", "all_entities.json")
    relationships_path = os.path.join(output_dir, "relationships", "all_relationships.json")
    
    if not os.path.exists(entities_path) or not os.path.exists(relationships_path):
        logger.error(f"Required files not found in {output_dir}")
        return False
    
    entities = load_entities(entities_path)
    relationships = load_relationships(relationships_path)
    
    # Create graph
    graph = KnowledgeGraph()
    for entity in entities:
        try:
            graph.add_entity(entity)
        except Exception as e:
            logger.warning(f"Failed to add entity {entity.name}: {str(e)}")
    
    for relationship in relationships:
        try:
            graph.add_relationship(relationship)
        except Exception as e:
            logger.warning(f"Failed to add relationship {relationship.id}: {str(e)}")
    
    # Generate report
    generator = ReportGenerator()
    report_path = os.path.join(output_dir, "report.html")
    generator.generate_report(
        output_path=report_path,
        graph=graph,
        source_file="tests/data/samples/sample_ru.txt",
        output_dir=output_dir,
        title="Knowledge Graph Analysis: sample_ru.txt"
    )
    
    logger.info(f"Report generated: {report_path}")
    return True

def generate_expansion_report(output_dir, use_test_data=False):
    """Generate the expansion report."""
    # Create directories if needed
    expanded_dir = os.path.join(output_dir, "graphs", "expanded")
    os.makedirs(expanded_dir, exist_ok=True)
    
    # Create report generator
    report_generator = ExpansionReportGenerator(output_dir)
    
    if use_test_data:
        # Load test data into the report generator
        for iteration_data in TEST_EXPANSION_DATA["iterations"]:
            # Convert to the format expected by add_iteration_data
            targets = []
            for target_data in iteration_data["targets"]:
                targets.append({
                    "entity": Entity(
                        id=f"test-{len(targets)}", 
                        name=target_data["entity_name"],
                        type=target_data["entity_type"],
                        confidence=0.95
                    ),
                    "relevance": target_data["relevance"],
                    "rationale": target_data["rationale"]
                })
            
            # Add the iteration data
            report_generator.add_iteration_data(iteration_data["iteration"], targets)
        
        # Add questions
        for question_data in TEST_EXPANSION_DATA["questions"]:
            report_generator.add_question(
                iteration=question_data["iteration"],
                target_name=question_data["target_name"],
                target_type=question_data["target_type"],
                question=question_data["question"]
            )
        
        # Add answers
        for answer_data in TEST_EXPANSION_DATA["answers"]:
            report_generator.add_answer(
                iteration=answer_data["iteration"],
                target_name=answer_data["target_name"],
                target_type=answer_data["target_type"],
                question=answer_data["question"],
                answer=answer_data["answer"],
                confidence=answer_data["confidence"],
                new_entities_text=answer_data["new_entities"],
                new_relationships_text=answer_data["new_relationships"]
            )
    else:
        # Check if there's an existing expansion_data.json file
        expansion_data_path = os.path.join(expanded_dir, "expansion_data.json")
        if os.path.exists(expansion_data_path):
            # Load existing data
            with open(expansion_data_path, 'r', encoding='utf-8') as f:
                expansion_data = json.load(f)
            
            # Check if there are any answers
            if not expansion_data.get("answers"):
                logger.warning("No answers found in expansion data. Adding test answers...")
                
                # Add a test answer for the first question if questions exist
                questions = expansion_data.get("questions", [])
                
                if questions:
                    test_answer = {
                        "iteration": questions[0]["iteration"],
                        "target_name": questions[0]["target_name"],
                        "target_type": questions[0]["target_type"],
                        "question": questions[0]["question"],
                        "answer": "Основываясь на доступных данных, я не могу предоставить подробную информацию по запрошенному вопросу. В тексте не указаны детальные сведения по данному запросу.",
                        "confidence": 0.6,
                        "new_entities": "",
                        "new_relationships": ""
                    }
                    
                    expansion_data["answers"].append(test_answer)
                    
                    # Save updated data
                    with open(expansion_data_path, 'w', encoding='utf-8') as f:
                        json.dump(expansion_data, f, ensure_ascii=False, indent=2)
    
    # Generate the report
    report_path = report_generator.generate_report()
    logger.info(f"Expansion report generated: {report_path}")
    return True

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test report generation")
    parser.add_argument(
        "--dir", "-d",
        help="Output directory to process",
        default=None
    )
    parser.add_argument(
        "--test-data",
        help="Use test data for expansion report",
        action="store_true"
    )
    parser.add_argument(
        "--segments-only",
        help="Only generate segment pages",
        action="store_true"
    )
    parser.add_argument(
        "--expansion-only",
        help="Only generate expansion report",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Find the latest output directory if not specified
    if args.dir is None:
        base_output_dir = "output"
        subdirs = [os.path.join(base_output_dir, d) for d in os.listdir(base_output_dir) 
                  if os.path.isdir(os.path.join(base_output_dir, d)) and d.startswith("2025")]
        
        if subdirs:
            # Sort by modification time (newest first)
            subdirs.sort(key=lambda d: os.path.getmtime(d), reverse=True)
            output_dir = subdirs[0]
            logger.info(f"Using latest output directory: {output_dir}")
        else:
            logger.error("No output directories found")
            return
    else:
        output_dir = args.dir
    
    # Make sure output directory exists
    if not os.path.exists(output_dir):
        logger.error(f"Output directory does not exist: {output_dir}")
        return
    
    # Run requested operations
    if args.segments_only:
        # Only generate segment pages
        ensure_segment_pages(output_dir)
    elif args.expansion_only:
        # Only generate expansion report
        generate_expansion_report(output_dir, args.test_data)
    else:
        # Generate all reports
        generate_expansion_report(output_dir, args.test_data)
        generate_report(output_dir)
        ensure_segment_pages(output_dir)
    
    logger.info("Processing complete")

if __name__ == "__main__":
    main()