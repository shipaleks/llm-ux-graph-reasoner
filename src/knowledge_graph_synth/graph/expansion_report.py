"""Expansion report generator for the knowledge graph synthesis system."""

import json
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ExpansionReportGenerator:
    """Generates reports on the graph expansion process."""
    
    def __init__(self, output_dir: str):
        """Initialize the expansion report generator.
        
        Args:
            output_dir: Directory to save the expansion report
        """
        self.output_dir = output_dir
        self.expansion_data = {
            "iterations": [],
            "targets": [],
            "questions": [],
            "answers": []
        }
    
    def add_iteration_data(self, iteration: int, targets: List[Dict[str, Any]]):
        """Add data for an expansion iteration.
        
        Args:
            iteration: Iteration number
            targets: List of expansion targets
        """
        targets_data = []
        for target in targets:
            target_data = {
                "entity_name": target["entity"].name,
                "entity_type": target["entity"].type,
                "relevance": target["relevance"],
                "rationale": target["rationale"]
            }
            targets_data.append(target_data)
        
        self.expansion_data["iterations"].append({
            "iteration": iteration,
            "targets": targets_data
        })
        
        self.expansion_data["targets"].extend(targets_data)
    
    def add_question(self, 
                  iteration: int, 
                  target_name: str, 
                  target_type: str, 
                  question: str):
        """Add a question used during expansion.
        
        Args:
            iteration: Iteration number
            target_name: Name of the target entity
            target_type: Type of the target entity
            question: Question text
        """
        self.expansion_data["questions"].append({
            "iteration": iteration,
            "target_name": target_name,
            "target_type": target_type,
            "question": question
        })
    
    def add_answer(self, 
                iteration: int, 
                target_name: str, 
                target_type: str, 
                question: str, 
                answer: str,
                confidence: float,
                new_entities_text: str = "",
                new_relationships_text: str = ""):
        """Add an answer received during expansion.
        
        Args:
            iteration: Iteration number
            target_name: Name of the target entity
            target_type: Type of the target entity
            question: Question text
            answer: Answer text
            confidence: Confidence score
            new_entities_text: Text describing new entities
            new_relationships_text: Text describing new relationships
        """
        self.expansion_data["answers"].append({
            "iteration": iteration,
            "target_name": target_name,
            "target_type": target_type,
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "new_entities": new_entities_text,
            "new_relationships": new_relationships_text
        })
    
    def get_all_data(self):
        """Get all expansion data.
        
        Returns:
            Dictionary with all expansion data
        """
        return self.expansion_data
    
    def generate_report(self):
        """Generate and save the expansion report.
        
        Returns:
            Path to the generated report
        """
        # Create the expansion directory
        from ..cli.utils import get_subdirectory_path
        expansion_dir = get_subdirectory_path(self.output_dir, "graphs/expanded")
        
        # Save the expansion data as JSON
        json_path = os.path.join(expansion_dir, "expansion_data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.expansion_data, f, ensure_ascii=False, indent=2)
        
        # Generate the markdown report
        md_path = os.path.join(expansion_dir, "expansion_process.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Процесс расширения графа знаний\n\n")
            
            # Summary
            f.write("## Общая информация\n\n")
            f.write(f"- **Количество итераций**: {len(self.expansion_data['iterations'])}\n")
            f.write(f"- **Количество целевых сущностей**: {len(self.expansion_data['targets'])}\n")
            f.write(f"- **Количество вопросов**: {len(self.expansion_data['questions'])}\n")
            f.write(f"- **Количество ответов**: {len(self.expansion_data['answers'])}\n\n")
            
            # Iterations
            f.write("## Итерации расширения\n\n")
            for iteration_data in self.expansion_data["iterations"]:
                iteration = iteration_data["iteration"]
                f.write(f"### Итерация {iteration + 1}\n\n")
                
                f.write("#### Целевые сущности\n\n")
                if iteration_data["targets"]:
                    for target in iteration_data["targets"]:
                        f.write(f"- **{target['entity_name']}** ({target['entity_type']})\n")
                        f.write(f"  - Релевантность: {target['relevance']}\n")
                        f.write(f"  - Обоснование: {target['rationale']}\n\n")
                else:
                    f.write("Целевые сущности не были выбраны для этой итерации.\n\n")
                
                # Questions and answers for this iteration
                questions_for_iteration = [q for q in self.expansion_data["questions"] if q["iteration"] == iteration]
                answers_for_iteration = [a for a in self.expansion_data["answers"] if a["iteration"] == iteration]
                
                f.write("#### Вопросы и ответы\n\n")
                if questions_for_iteration:
                    for i, question_data in enumerate(questions_for_iteration):
                        target_name = question_data["target_name"]
                        target_type = question_data["target_type"]
                        question = question_data["question"]
                        
                        f.write(f"##### Вопрос {i+1}: {question}\n\n")
                        f.write(f"Целевая сущность: **{target_name}** ({target_type})\n\n")
                        
                        # Find the corresponding answer
                        matching_answers = [a for a in answers_for_iteration if a["question"] == question and a["target_name"] == target_name]
                        if matching_answers:
                            answer = matching_answers[0]
                            f.write("**Ответ:**\n\n")
                            f.write(f"{answer['answer']}\n\n")
                            f.write(f"Уверенность: {answer['confidence']:.2f}\n\n")
                            
                            if answer["new_entities"]:
                                f.write("**Новые сущности:**\n\n")
                                f.write(f"{answer['new_entities']}\n\n")
                            
                            if answer["new_relationships"]:
                                f.write("**Новые отношения:**\n\n")
                                f.write(f"{answer['new_relationships']}\n\n")
                        else:
                            f.write("Ответ не был получен.\n\n")
                else:
                    f.write("Вопросы не были заданы в этой итерации.\n\n")
            
            # Overall summary
            f.write("## Итоги расширения графа\n\n")
            f.write("В результате расширения графа были добавлены новые сущности и отношения, ");
            f.write("что позволило получить более полное представление о предметной области. ");
            f.write("Процесс расширения помог заполнить пробелы в знаниях и установить новые связи ");
            f.write("между существующими концепциями.\n\n")
        
        logger.info(f"Expansion report generated: {md_path}")
        return md_path