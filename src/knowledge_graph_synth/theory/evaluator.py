"""Evaluation of hypotheses and theories for the knowledge graph synthesis system."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID

from ..models import KnowledgeGraph, SegmentCollection
from ..llm import LLMProviderFactory
from ..config import settings

logger = logging.getLogger(__name__)


class TheoryEvaluator:
    """Evaluates the quality of theories and hypotheses.
    
    This class implements methods for evaluating the quality, coherence,
    and evidence support of theories and hypotheses generated from knowledge graphs.
    """
    
    def __init__(self, 
               provider_name: Optional[str] = None):
        """Initialize the theory evaluator.
        
        Args:
            provider_name: Name of the LLM provider to use
        """
        self.provider_name = provider_name
    
    async def evaluate_theory(self, 
                         theory: Dict[str, Any],
                         graph: KnowledgeGraph,
                         collection: Optional[SegmentCollection] = None) -> Dict[str, Any]:
        """Evaluate a theory's quality and evidence support.
        
        Args:
            theory: Theory to evaluate
            graph: Knowledge graph the theory is based on
            collection: Optional segment collection for evidence verification
            
        Returns:
            Evaluation results
        """
        # Get the LLM provider
        try:
            # Use reasoning provider for theory evaluation
            provider = LLMProviderFactory.get_reasoning_provider()
            if not provider:
                provider = LLMProviderFactory.get_provider(self.provider_name)
                
            if not provider:
                logger.error("No LLM provider available for theory evaluation")
                return self._create_default_evaluation(theory)
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return self._create_default_evaluation(theory)
        
        # Get theory details
        title = theory.get("title", "Unnamed Theory")
        summary = theory.get("summary", "")
        description = theory.get("description", "")
        key_entities = theory.get("key_entities", [])
        key_relationships = theory.get("key_relationships", [])
        evidence = theory.get("evidence", [])
        
        # Create a summary of the graph
        graph_summary = self._create_graph_summary(graph)
        
        # Create a prompt for theory evaluation
        prompt = f"""
Evaluate the following theory against the provided knowledge graph and assess its quality, coherence, and evidence support.

Theory: {title}
Summary: {summary}
Description: {description}

Knowledge graph summary:
{graph_summary}

Your task is to provide a rigorous, systematic evaluation of this theory by assessing:

1. Evidence Support (0-10):
   - How well is the theory grounded in specific evidence from the knowledge graph?
   - Are the claims directly supported by entities and relationships in the graph?
   - Are there important pieces of evidence that the theory ignores or contradicts?

2. Coherence (0-10):
   - How logically consistent is the theory internally?
   - Does the theory provide a unified explanation for the observed patterns?
   - Are there contradictions or inconsistencies in the theory's reasoning?

3. Parsimony (0-10):
   - How efficiently does the theory explain the data without unnecessary complexity?
   - Does the theory invoke unnecessary entities or mechanisms?
   - Does it apply Occam's razor appropriately?

4. Explanatory Power (0-10):
   - How much of the knowledge graph does the theory explain?
   - Does it account for the most significant patterns and relationships?
   - Does it provide genuine insights rather than merely restating the obvious?

5. Falsifiability (0-10):
   - How testable is this theory against new evidence?
   - Does it make specific predictions that could be verified or disproven?
   - Does it avoid unfalsifiable claims?

For each criterion, provide:
- A numeric score (0-10)
- A brief but specific justification for your score
- Suggestions for improvement

Then provide an overall assessment (0-10) that weighs all five criteria, with a detailed explanation of your reasoning.
"""
        
        # Generate the evaluation
        try:
            response = await provider.generate_text(prompt)
            
            # Parse the response
            criteria = {
                "evidence_support": {"score": 0, "justification": "", "suggestions": ""},
                "coherence": {"score": 0, "justification": "", "suggestions": ""},
                "parsimony": {"score": 0, "justification": "", "suggestions": ""},
                "explanatory_power": {"score": 0, "justification": "", "suggestions": ""},
                "falsifiability": {"score": 0, "justification": "", "suggestions": ""}
            }
            
            overall_score = 0
            overall_assessment = ""
            
            current_criterion = None
            current_section = None
            
            for line in response.split("\n"):
                line = line.strip()
                
                if not line:
                    continue
                
                # Check for criteria headers
                if line.startswith("1. Evidence Support") or "Evidence Support" in line:
                    current_criterion = "evidence_support"
                    current_section = None
                elif line.startswith("2. Coherence") or "Coherence" in line:
                    current_criterion = "coherence"
                    current_section = None
                elif line.startswith("3. Parsimony") or "Parsimony" in line:
                    current_criterion = "parsimony"
                    current_section = None
                elif line.startswith("4. Explanatory Power") or "Explanatory Power" in line:
                    current_criterion = "explanatory_power"
                    current_section = None
                elif line.startswith("5. Falsifiability") or "Falsifiability" in line:
                    current_criterion = "falsifiability"
                    current_section = None
                elif line.startswith("Overall") or "Overall" in line:
                    current_criterion = "overall"
                    current_section = None
                
                # Extract scores
                if current_criterion:
                    # Look for scores
                    if "Score:" in line or "score:" in line:
                        try:
                            # Extract the score value
                            score_text = line.split(":", 1)[1].strip()
                            score = int(score_text.split("/")[0])
                            
                            if current_criterion == "overall":
                                overall_score = score
                            elif current_criterion in criteria:
                                criteria[current_criterion]["score"] = score
                        except:
                            pass
                    
                    # Look for sections within criteria
                    if "Justification:" in line or "justification:" in line:
                        current_section = "justification"
                        value = line.split(":", 1)[1].strip()
                        if current_criterion in criteria and value:
                            criteria[current_criterion]["justification"] = value
                    elif "Suggestions:" in line or "suggestions:" in line:
                        current_section = "suggestions"
                        value = line.split(":", 1)[1].strip()
                        if current_criterion in criteria and value:
                            criteria[current_criterion]["suggestions"] = value
                    elif current_criterion == "overall" and current_section != "justification" and "assessment" not in line.lower():
                        current_section = "justification"
                        overall_assessment += line + " "
                    elif current_section == "justification" and current_criterion != "overall":
                        if current_criterion in criteria:
                            criteria[current_criterion]["justification"] += " " + line
                    elif current_section == "suggestions":
                        if current_criterion in criteria:
                            criteria[current_criterion]["suggestions"] += " " + line
                    elif current_section == "justification" and current_criterion == "overall":
                        overall_assessment += line + " "
            
            # Calculate composite score
            composite_score = sum(c["score"] for c in criteria.values()) / len(criteria)
            
            # Create the evaluation result
            evaluation = {
                "criteria": criteria,
                "composite_score": composite_score,
                "overall_score": overall_score,
                "overall_assessment": overall_assessment
            }
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating theory: {str(e)}")
            return self._create_default_evaluation(theory)
    
    async def evaluate_hypothesis(self, 
                             hypothesis: Dict[str, Any],
                             test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a hypothesis and its test results.
        
        Args:
            hypothesis: Hypothesis to evaluate
            test_result: Results of testing the hypothesis
            
        Returns:
            Evaluation results
        """
        # Get the LLM provider
        try:
            # Use reasoning provider for hypothesis evaluation
            provider = LLMProviderFactory.get_reasoning_provider()
            if not provider:
                provider = LLMProviderFactory.get_provider(self.provider_name)
                
            if not provider:
                logger.error("No LLM provider available for hypothesis evaluation")
                return self._create_default_hypothesis_evaluation(hypothesis, test_result)
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return self._create_default_hypothesis_evaluation(hypothesis, test_result)
        
        # Get hypothesis details
        statement = hypothesis.get("statement", "")
        hypothesis_type = hypothesis.get("type", "unknown")
        
        # Get test result details
        supported = test_result.get("supported", False)
        confidence = test_result.get("confidence", 0)
        evidence_for = test_result.get("evidence_for", [])
        evidence_against = test_result.get("evidence_against", [])
        reasoning = test_result.get("reasoning", "")
        
        # Create a prompt for hypothesis evaluation
        prompt = f"""
Evaluate the following hypothesis and its test results to assess its quality, significance, and reliability.

Hypothesis: {statement}
Type: {hypothesis_type}

Test Results:
- Supported: {"Yes" if supported else "No"}
- Confidence: {confidence}
- Evidence For: {"; ".join(evidence_for)}
- Evidence Against: {"; ".join(evidence_against)}
- Reasoning: {reasoning}

Your task is to provide a systematic evaluation of this hypothesis by assessing:

1. Formulation Quality (0-10):
   - How clear, specific, and well-formulated is the hypothesis?
   - Is it properly scoped and focused?
   - Is it free from ambiguity and vague terminology?

2. Evidence Quality (0-10):
   - How strong and relevant is the supporting evidence?
   - How compelling is the evidence against the hypothesis?
   - Is the evidence specific and concrete rather than general or abstract?

3. Significance (0-10):
   - How important or consequential is this hypothesis?
   - Does it address a central rather than peripheral aspect of the domain?
   - Would confirming or refuting it substantially advance understanding?

4. Novelty (0-10):
   - How original or innovative is this hypothesis?
   - Does it offer a new perspective or insight?
   - Does it avoid merely restating established knowledge?

5. Methodological Soundness (0-10):
   - How appropriate is the testing methodology?
   - Are the conclusions well-supported by the testing approach?
   - Is the confidence level appropriate given the evidence?

For each criterion, provide:
- A numeric score (0-10)
- A brief justification for your score

Then provide an overall assessment (0-10) that weighs all five criteria, with an explanation of your reasoning.
"""
        
        # Generate the evaluation
        try:
            response = await provider.generate_text(prompt)
            
            # Parse the response
            criteria = {
                "formulation_quality": {"score": 0, "justification": ""},
                "evidence_quality": {"score": 0, "justification": ""},
                "significance": {"score": 0, "justification": ""},
                "novelty": {"score": 0, "justification": ""},
                "methodological_soundness": {"score": 0, "justification": ""}
            }
            
            overall_score = 0
            overall_assessment = ""
            
            current_criterion = None
            current_section = None
            
            for line in response.split("\n"):
                line = line.strip()
                
                if not line:
                    continue
                
                # Check for criteria headers
                if line.startswith("1. Formulation Quality") or "Formulation Quality" in line:
                    current_criterion = "formulation_quality"
                    current_section = None
                elif line.startswith("2. Evidence Quality") or "Evidence Quality" in line:
                    current_criterion = "evidence_quality"
                    current_section = None
                elif line.startswith("3. Significance") or "Significance" in line:
                    current_criterion = "significance"
                    current_section = None
                elif line.startswith("4. Novelty") or "Novelty" in line:
                    current_criterion = "novelty"
                    current_section = None
                elif line.startswith("5. Methodological Soundness") or "Methodological Soundness" in line:
                    current_criterion = "methodological_soundness"
                    current_section = None
                elif line.startswith("Overall") or "Overall" in line:
                    current_criterion = "overall"
                    current_section = None
                
                # Extract scores
                if current_criterion:
                    # Look for scores
                    if "Score:" in line or "score:" in line:
                        try:
                            # Extract the score value
                            score_text = line.split(":", 1)[1].strip()
                            score = int(score_text.split("/")[0])
                            
                            if current_criterion == "overall":
                                overall_score = score
                            elif current_criterion in criteria:
                                criteria[current_criterion]["score"] = score
                        except:
                            pass
                    
                    # Look for sections within criteria
                    if "Justification:" in line or "justification:" in line:
                        current_section = "justification"
                        value = line.split(":", 1)[1].strip()
                        if current_criterion in criteria and value:
                            criteria[current_criterion]["justification"] = value
                    elif current_criterion == "overall" and current_section != "justification" and "assessment" not in line.lower():
                        current_section = "justification"
                        overall_assessment += line + " "
                    elif current_section == "justification" and current_criterion != "overall":
                        if current_criterion in criteria:
                            criteria[current_criterion]["justification"] += " " + line
                    elif current_section == "justification" and current_criterion == "overall":
                        overall_assessment += line + " "
            
            # Calculate composite score
            composite_score = sum(c["score"] for c in criteria.values()) / len(criteria)
            
            # Create the evaluation result
            evaluation = {
                "criteria": criteria,
                "composite_score": composite_score,
                "overall_score": overall_score,
                "overall_assessment": overall_assessment,
                "hypothesis_confirmed": supported and confidence >= 0.7
            }
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating hypothesis: {str(e)}")
            return self._create_default_hypothesis_evaluation(hypothesis, test_result)
    
    def _create_default_evaluation(self, theory: Dict[str, Any]) -> Dict[str, Any]:
        """Create a default evaluation when LLM evaluation fails.
        
        Args:
            theory: Theory to evaluate
            
        Returns:
            Default evaluation
        """
        theory_confidence = theory.get("confidence", 0.5)
        score = min(int(theory_confidence * 10), 10)
        
        return {
            "criteria": {
                "evidence_support": {"score": score, "justification": "Automatic score based on theory confidence", "suggestions": ""},
                "coherence": {"score": score, "justification": "Automatic score based on theory confidence", "suggestions": ""},
                "parsimony": {"score": score, "justification": "Automatic score based on theory confidence", "suggestions": ""},
                "explanatory_power": {"score": score, "justification": "Automatic score based on theory confidence", "suggestions": ""},
                "falsifiability": {"score": score, "justification": "Automatic score based on theory confidence", "suggestions": ""}
            },
            "composite_score": score,
            "overall_score": score,
            "overall_assessment": "This is an automatically generated evaluation based on the theory's confidence score."
        }
    
    def _create_default_hypothesis_evaluation(self, 
                                        hypothesis: Dict[str, Any],
                                        test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a default hypothesis evaluation when LLM evaluation fails.
        
        Args:
            hypothesis: Hypothesis to evaluate
            test_result: Test results
            
        Returns:
            Default evaluation
        """
        hypothesis_confidence = hypothesis.get("confidence", 0.5)
        test_confidence = test_result.get("confidence", 0.5)
        supported = test_result.get("supported", False)
        
        # Average the confidences
        avg_confidence = (hypothesis_confidence + test_confidence) / 2
        score = min(int(avg_confidence * 10), 10)
        
        return {
            "criteria": {
                "formulation_quality": {"score": score, "justification": "Automatic score based on hypothesis confidence"},
                "evidence_quality": {"score": score, "justification": "Automatic score based on test confidence"},
                "significance": {"score": score, "justification": "Automatic score based on average confidence"},
                "novelty": {"score": score, "justification": "Automatic score based on average confidence"},
                "methodological_soundness": {"score": score, "justification": "Automatic score based on average confidence"}
            },
            "composite_score": score,
            "overall_score": score,
            "overall_assessment": "This is an automatically generated evaluation based on confidence scores.",
            "hypothesis_confirmed": supported and test_confidence >= 0.7
        }
    
    def _create_graph_summary(self, graph: KnowledgeGraph) -> str:
        """Create a summary of a knowledge graph for evaluation.
        
        Args:
            graph: Knowledge graph to summarize
            
        Returns:
            Graph summary text
        """
        # Create entity type statistics
        entity_types = {}
        for entity_id, entity in graph.entities.items():
            entity_type = entity.type.lower()
            
            if entity_type not in entity_types:
                entity_types[entity_type] = []
            
            entity_types[entity_type].append(entity)
        
        # Create relationship type statistics
        relationship_types = {}
        for rel_id, rel in graph.relationships.items():
            rel_type = rel.type.lower()
            
            if rel_type not in relationship_types:
                relationship_types[rel_type] = []
            
            relationship_types[rel_type].append(rel)
        
        # Create the graph summary
        summary = f"A knowledge graph with {len(graph.entities)} entities and {len(graph.relationships)} relationships.\n\n"
        
        # Add entity type summary
        summary += "Entity types:\n"
        for entity_type, entities in entity_types.items():
            summary += f"- {entity_type}: {len(entities)} entities\n"
            
            # Add examples of this type
            examples = sorted(entities, key=lambda e: e.confidence, reverse=True)[:5]
            if examples:
                summary += "  Examples: " + ", ".join(e.name for e in examples) + "\n"
        
        # Add relationship type summary
        summary += "\nRelationship types:\n"
        for rel_type, relationships in relationship_types.items():
            summary += f"- {rel_type}: {len(relationships)} relationships\n"
            
            # Add examples of this type
            examples = sorted(relationships, key=lambda r: r.confidence, reverse=True)[:3]
            if examples:
                example_texts = []
                for rel in examples:
                    source = graph.get_entity(rel.source_id)
                    target = graph.get_entity(rel.target_id)
                    
                    if source and target:
                        example_texts.append(f"{source.name} → {target.name}")
                
                if example_texts:
                    summary += "  Examples: " + ", ".join(example_texts) + "\n"
        
        return summary