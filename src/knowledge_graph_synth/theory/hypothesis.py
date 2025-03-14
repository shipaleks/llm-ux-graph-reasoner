"""Hypothesis generation and testing for the knowledge graph synthesis system."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID

import networkx as nx

from ..models import KnowledgeGraph, Entity, Relationship, SourceSpan, TextSegment, SegmentCollection
from ..llm import LLMProviderFactory, prompt_manager
from ..llm.schemas import get_hypothesis_generation_schema
from ..config import settings
from .evidence import EvidenceCollector

logger = logging.getLogger(__name__)


class HypothesisGenerator:
    """Generates and tests hypotheses based on knowledge graphs.
    
    This class generates specific, testable hypotheses from knowledge graphs,
    and provides methods for testing these hypotheses against the data.
    """
    
    def __init__(self, 
               provider_name: Optional[str] = None,
               confidence_threshold: float = settings.DEFAULT_CONFIDENCE_THRESHOLD):
        """Initialize the hypothesis generator.
        
        Args:
            provider_name: Name of the LLM provider to use
            confidence_threshold: Minimum confidence score for hypotheses
        """
        self.provider_name = provider_name
        self.confidence_threshold = confidence_threshold
        self.evidence_collector = EvidenceCollector()
    
    async def generate_hypotheses(self, 
                             graph: KnowledgeGraph,
                             focus_entities: Optional[List[Entity]] = None,
                             max_hypotheses: int = 5) -> List[Dict[str, Any]]:
        """Generate hypotheses from a knowledge graph.
        
        Args:
            graph: Knowledge graph to analyze
            focus_entities: Optional list of entities to focus on
            max_hypotheses: Maximum number of hypotheses to generate
            
        Returns:
            List of generated hypotheses
        """
        # Get the LLM provider
        try:
            # Use reasoning provider for hypothesis generation
            provider = LLMProviderFactory.get_reasoning_provider()
            if not provider:
                provider = LLMProviderFactory.get_provider(self.provider_name)
                
            if not provider:
                logger.error("No LLM provider available for hypothesis generation")
                return []
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
        
        # Create a summary of the graph with focus on specific entities if provided
        graph_summary = self._create_graph_summary(graph, focus_entities)
        
        # Get the response schema
        schema = get_hypothesis_generation_schema()
        
        # Create a prompt for hypothesis generation
        prompt = f"""
Generate {max_hypotheses} specific, testable hypotheses based on the provided knowledge graph. These hypotheses should be focused, evidence-based, and provide insights that could be further investigated.

The knowledge graph contains:
{graph_summary}

For each hypothesis:
1. Formulate a clear, specific statement
2. Identify the type of hypothesis (causal, correlational, predictive, etc.)
3. List the entities involved and their roles
4. Provide specific supporting evidence from the knowledge graph
5. Assess your confidence in this hypothesis (0-1)
6. Evaluate how testable this hypothesis is and suggest methods for testing it

Your hypotheses should:
- Be specific and focused rather than broad and general
- Be based on patterns and relationships in the graph
- Identify potential causal mechanisms or correlations
- Address significant or interesting aspects of the data
- Be testable against additional evidence
- Vary in focus to cover different aspects of the graph

Generate hypotheses that provide genuinely useful insights and could lead to meaningful further investigation. Prioritize quality and specificity over quantity.
"""
        
        # Generate the hypotheses
        try:
            response = await provider.generate_structured(prompt, schema)
            hypotheses_data = response.get("hypotheses", [])
            
            # Process the hypotheses
            hypotheses = []
            for hypothesis_data in hypotheses_data:
                hypothesis = {
                    "statement": hypothesis_data.get("statement", ""),
                    "type": hypothesis_data.get("type", "unknown"),
                    "related_entities": hypothesis_data.get("related_entities", []),
                    "supporting_evidence": hypothesis_data.get("supporting_evidence", []),
                    "confidence": hypothesis_data.get("confidence", 0.5),
                    "testability": hypothesis_data.get("testability", {"score": 0.5, "method": ""})
                }
                
                # Only include hypotheses with sufficient confidence
                if hypothesis["confidence"] >= self.confidence_threshold:
                    hypotheses.append(hypothesis)
            
            return hypotheses[:max_hypotheses]
            
        except Exception as e:
            logger.error(f"Error generating hypotheses: {str(e)}")
            return []
    
    async def test_hypothesis(self, 
                         hypothesis: Dict[str, Any],
                         graph: KnowledgeGraph,
                         collection: Optional[SegmentCollection] = None) -> Dict[str, Any]:
        """Test a hypothesis against the knowledge graph and source text.
        
        Args:
            hypothesis: Hypothesis to test
            graph: Knowledge graph to test against
            collection: Optional segment collection for evidence
            
        Returns:
            Test results
        """
        # Get the LLM provider
        try:
            # Use reasoning provider for hypothesis testing
            provider = LLMProviderFactory.get_reasoning_provider()
            if not provider:
                provider = LLMProviderFactory.get_provider(self.provider_name)
                
            if not provider:
                logger.error("No LLM provider available for hypothesis testing")
                return {"supported": False, "confidence": 0, "evidence": [], "reasoning": "No LLM provider available"}
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return {"supported": False, "confidence": 0, "evidence": [], "reasoning": f"Error: {str(e)}"}
        
        # Get hypothesis details
        statement = hypothesis.get("statement", "")
        hypothesis_type = hypothesis.get("type", "unknown")
        related_entities = hypothesis.get("related_entities", [])
        
        # Create a graph summary focused on relevant entities
        entity_names = [entity.get("name", "") for entity in related_entities if "name" in entity]
        focus_entities = []
        
        for name in entity_names:
            # Find matching entities in the graph
            for entity_id, entity in graph.entities.items():
                if entity.name.lower() == name.lower():
                    focus_entities.append(entity)
                    break
        
        graph_summary = self._create_graph_summary(graph, focus_entities)
        
        # Create a prompt for hypothesis testing
        prompt = f"""
Evaluate the following hypothesis against the provided knowledge graph and determine whether it is supported by the evidence.

Hypothesis: {statement}
Type: {hypothesis_type}

Knowledge graph summary:
{graph_summary}

Your task is to:
1. Analyze the hypothesis carefully
2. Identify specific evidence in the knowledge graph that supports or contradicts the hypothesis
3. Consider alternative explanations for the observed patterns
4. Determine whether the hypothesis is supported, partially supported, or not supported
5. Assign a confidence score to your conclusion (0-1)
6. Provide a detailed reasoning that explains your evaluation

Format your response as follows:
- Supported: [yes/partially/no]
- Confidence: [0-1 score]
- Evidence For: [list specific evidence supporting the hypothesis]
- Evidence Against: [list specific evidence contradicting the hypothesis]
- Alternative Explanations: [list alternative explanations for the observed patterns]
- Reasoning: [detailed explanation of your evaluation]
"""
        
        # Test the hypothesis
        try:
            response = await provider.generate_text(prompt)
            
            # Parse the response
            supported = False
            confidence = 0.0
            evidence_for = []
            evidence_against = []
            alternatives = []
            reasoning = ""
            
            current_section = ""
            
            for line in response.split("\n"):
                line = line.strip()
                
                if line.startswith("- Supported:") or line.startswith("Supported:"):
                    value = line.split(":", 1)[1].strip().lower()
                    supported = "yes" in value or "partially" in value
                elif line.startswith("- Confidence:") or line.startswith("Confidence:"):
                    try:
                        value = line.split(":", 1)[1].strip()
                        confidence = float(value.split()[0])  # Extract the first number
                    except:
                        pass
                elif line.startswith("- Evidence For:") or line.startswith("Evidence For:"):
                    current_section = "evidence_for"
                    value = line.split(":", 1)[1].strip()
                    if value:
                        evidence_for.append(value)
                elif line.startswith("- Evidence Against:") or line.startswith("Evidence Against:"):
                    current_section = "evidence_against"
                    value = line.split(":", 1)[1].strip()
                    if value:
                        evidence_against.append(value)
                elif line.startswith("- Alternative Explanations:") or line.startswith("Alternative Explanations:"):
                    current_section = "alternatives"
                    value = line.split(":", 1)[1].strip()
                    if value:
                        alternatives.append(value)
                elif line.startswith("- Reasoning:") or line.startswith("Reasoning:"):
                    current_section = "reasoning"
                    value = line.split(":", 1)[1].strip()
                    if value:
                        reasoning = value
                elif line.startswith("- "):
                    # Bullet point in the current section
                    value = line[2:].strip()
                    if current_section == "evidence_for" and value:
                        evidence_for.append(value)
                    elif current_section == "evidence_against" and value:
                        evidence_against.append(value)
                    elif current_section == "alternatives" and value:
                        alternatives.append(value)
                elif current_section == "reasoning" and line:
                    reasoning += " " + line
            
            # Collect evidence from the source text if available
            evidence_spans = []
            if collection:
                # Collect evidence for supporting points
                for evidence_text in evidence_for:
                    spans = self.evidence_collector.find_evidence(evidence_text, collection)
                    evidence_spans.extend(spans)
                
                # Collect evidence for contradicting points
                for evidence_text in evidence_against:
                    spans = self.evidence_collector.find_evidence(evidence_text, collection)
                    evidence_spans.extend(spans)
            
            # Create the test result
            result = {
                "supported": supported,
                "confidence": confidence,
                "evidence_for": evidence_for,
                "evidence_against": evidence_against,
                "alternative_explanations": alternatives,
                "reasoning": reasoning,
                "evidence_spans": [span.to_dict() for span in evidence_spans]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing hypothesis: {str(e)}")
            return {"supported": False, "confidence": 0, "evidence": [], "reasoning": f"Error: {str(e)}"}
    
    def _create_graph_summary(self, 
                          graph: KnowledgeGraph, 
                          focus_entities: Optional[List[Entity]] = None) -> str:
        """Create a summary of a knowledge graph for hypothesis generation.
        
        Args:
            graph: Knowledge graph to summarize
            focus_entities: Optional list of entities to focus on
            
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
        
        # If focus entities are provided, include them prominently
        if focus_entities:
            summary += "Focus entities:\n"
            for entity in focus_entities:
                summary += f"- {entity.name} (Type: {entity.type})\n"
                
                # Add attributes
                if entity.attributes:
                    summary += "  Attributes:\n"
                    for attr in entity.attributes:
                        summary += f"  - {attr.key}: {attr.value}\n"
                
                # Add relationships
                connections = graph.get_entity_relationships(entity.id)
                if connections:
                    summary += "  Relationships:\n"
                    for rel in connections[:5]:  # Limit to 5 relationships
                        source = graph.get_entity(rel.source_id)
                        target = graph.get_entity(rel.target_id)
                        
                        if source and target:
                            if source.id == entity.id:
                                summary += f"  - {entity.name} → {rel.type} → {target.name}\n"
                            else:
                                summary += f"  - {source.name} → {rel.type} → {entity.name}\n"
            
            summary += "\n"
        
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