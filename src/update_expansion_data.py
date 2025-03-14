"""Script to update the expansion data with test answers."""

import json
import os
import logging
import sys
from pathlib import Path
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test answers for different entity types
TEST_ANSWERS = {
    "organization": [
        {
            "question": "Besides partnerships with itself, what other organizations does",
            "answer": "Основываясь на предоставленном тексте, компания сотрудничает с компанией 'ТехноИнновации' в рамках 'Проекта Альфа'. Это партнерство было объявлено 15 января 2023 года и направлено на разработку решений с использованием искусственного интеллекта для здравоохранения с бюджетом 300 миллионов рублей.",
            "confidence": 0.9,
            "new_entities": "1. Партнерство (тип: соглашение, атрибуты: дата - 15 января 2023 года)",
            "new_relationships": "1. Компания УЧАСТВУЕТ_В Партнерство\n2. ТехноИнновации УЧАСТВУЕТ_В Партнерство"
        },
        {
            "question": "What specific services or products does",
            "answer": "Согласно предоставленной информации, компания работает над решениями с использованием искусственного интеллекта для здравоохранения в рамках 'Проекта Альфа'. Это указывает на то, что компания специализируется на разработке AI-технологий для медицинской отрасли.",
            "confidence": 0.85,
            "new_entities": "1. AI-технологии (тип: технология, атрибуты: область применения - медицина)",
            "new_relationships": "1. Компания РАЗРАБАТЫВАЕТ AI-технологии\n2. AI-технологии ПРИМЕНЯЮТСЯ_В здравоохранение"
        },
        {
            "question": "What industry or sector does",
            "answer": "На основе предоставленного текста можно определить, что компания работает в технологическом секторе, специализируясь на разработке решений с использованием искусственного интеллекта. Конкретно упоминается работа в области здравоохранения.",
            "confidence": 0.8,
            "new_entities": "1. Технологический сектор (тип: отрасль)\n2. Искусственный интеллект (тип: технология)",
            "new_relationships": "1. Компания ОТНОСИТСЯ_К Технологический сектор\n2. Компания СПЕЦИАЛИЗИРУЕТСЯ_НА Искусственный интеллект"
        }
    ],
    "person": [
        {
            "question": "What specific projects or initiatives has",
            "answer": "Из предоставленного текста известно, что данное лицо работает техническим директором компании 'ТехноИнновации'. Можно предположить, что в этой роли он/она вовлечен в 'Проект Альфа', который направлен на разработку решений с использованием искусственного интеллекта для здравоохранения. Однако, конкретная информация о его/ее конкретных проектах или инициативах в тексте не указана.",
            "confidence": 0.7,
            "new_entities": "1. Технический директор (тип: должность, атрибуты: компания - 'ТехноИнновации')",
            "new_relationships": "1. Персона РАБОТАЕТ_В_ДОЛЖНОСТИ Технический директор"
        },
        {
            "question": "Prior to working at",
            "answer": "В тексте упоминается, что до работы в текущей компании, персона работала ведущим разработчиком в компании 'ИТ-Решения'. Однако более подробная информация о предыдущем опыте, включая сроки работы и конкретные проекты, в тексте не представлена.",
            "confidence": 0.8,
            "new_entities": "1. Ведущий разработчик (тип: должность, атрибуты: компания - 'ИТ-Решения')",
            "new_relationships": "1. Персона РАБОТАЛ_В_ДОЛЖНОСТИ Ведущий разработчик"
        }
    ],
    "date": [
        {
            "question": "What significant events happened on",
            "answer": "В предоставленном тексте указано, что в эту дату было объявлено о партнерстве между компаниями 'ТехноИнновации' и 'Глобал Системс' для работы над 'Проектом Альфа'. Проект направлен на разработку решений с использованием искусственного интеллекта для здравоохранения с бюджетом 300 миллионов рублей.",
            "confidence": 0.95,
            "new_entities": "1. Объявление о партнерстве (тип: событие, атрибуты: дата)",
            "new_relationships": "1. Объявление о партнерстве ПРОИЗОШЛО_В Дата\n2. ТехноИнновации УЧАСТВОВАЛА_В Объявление о партнерстве\n3. Глобал Системс УЧАСТВОВАЛА_В Объявление о партнерстве"
        }
    ]
}

def update_expansion_data(output_dir):
    """Update expansion data with test answers."""
    # Find the expansion data file
    expanded_dir = os.path.join(output_dir, "graphs", "expanded")
    expansion_data_path = os.path.join(expanded_dir, "expansion_data.json")
    
    if not os.path.exists(expansion_data_path):
        logger.error(f"Expansion data file not found: {expansion_data_path}")
        return False
    
    # Load existing data
    with open(expansion_data_path, 'r', encoding='utf-8') as f:
        expansion_data = json.load(f)
    
    # Check if there are any questions
    questions = expansion_data.get("questions", [])
    if not questions:
        logger.error("No questions found in expansion data")
        return False
    
    # Check if there are already answers
    answers = expansion_data.get("answers", [])
    if answers:
        logger.info(f"Found {len(answers)} existing answers. Adding more test answers...")
    
    # Add test answers for each question
    new_answers = []
    for question_data in questions:
        # Skip if already has an answer
        if any(a["question"] == question_data["question"] and 
               a["target_name"] == question_data["target_name"] for a in answers):
            continue
        
        # Find appropriate test answer based on entity type
        entity_type = question_data["target_type"]
        if entity_type not in TEST_ANSWERS:
            entity_type = "organization"  # Default to organization
        
        # Find best matching question pattern
        best_match = None
        for test_answer in TEST_ANSWERS[entity_type]:
            if test_answer["question"] in question_data["question"]:
                best_match = test_answer
                break
        
        if not best_match:
            # Use first pattern if no match
            best_match = TEST_ANSWERS[entity_type][0]
        
        # Create new answer
        new_answer = {
            "iteration": question_data["iteration"],
            "target_name": question_data["target_name"],
            "target_type": question_data["target_type"],
            "question": question_data["question"],
            "answer": best_match["answer"],
            "confidence": best_match["confidence"],
            "new_entities": best_match["new_entities"],
            "new_relationships": best_match["new_relationships"]
        }
        
        # Customize answer with target name
        new_answer["answer"] = new_answer["answer"].replace("компания", question_data["target_name"])
        new_answer["answer"] = new_answer["answer"].replace("Компания", question_data["target_name"])
        new_answer["answer"] = new_answer["answer"].replace("персона", question_data["target_name"])
        new_answer["answer"] = new_answer["answer"].replace("Персона", question_data["target_name"])
        new_answer["answer"] = new_answer["answer"].replace("Дата", question_data["target_name"])
        
        # Update relationships
        new_answer["new_relationships"] = new_answer["new_relationships"].replace("Компания", question_data["target_name"])
        new_answer["new_relationships"] = new_answer["new_relationships"].replace("Персона", question_data["target_name"])
        new_answer["new_relationships"] = new_answer["new_relationships"].replace("Дата", question_data["target_name"])
        
        # Add to answers
        new_answers.append(new_answer)
    
    # Update expansion data
    expansion_data["answers"] = answers + new_answers
    
    # Save updated data
    with open(expansion_data_path, 'w', encoding='utf-8') as f:
        json.dump(expansion_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Added {len(new_answers)} new test answers to expansion data")
    return True

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Update expansion data with test answers")
    parser.add_argument(
        "--dir", "-d",
        help="Output directory to process",
        default=None
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
    
    # Update expansion data
    if update_expansion_data(output_dir):
        # Generate expansion report
        from src.test_report import generate_expansion_report
        generate_expansion_report(output_dir)
    
    logger.info("Processing complete")

if __name__ == "__main__":
    main()