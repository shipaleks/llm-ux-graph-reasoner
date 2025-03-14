"""Graph expansion for the knowledge graph synthesis system."""

import logging
import asyncio
import re
import uuid
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID

from ..models import KnowledgeGraph, Entity, Relationship, TextSegment, SegmentCollection
from ..llm import LLMProviderFactory, prompt_manager, ResponseValidator
from ..extraction import EntityExtractor, RelationshipExtractor, CoreferenceResolver, Grounder
from .analysis import GraphAnalyzer
from ..config import settings

logger = logging.getLogger(__name__)


class GraphExpander:
    """Expands knowledge graphs by generating new connections and entities.
    
    This class implements methods for expanding knowledge graphs through
    targeted questioning, pattern identification, and inference generation.
    """
    
    def __init__(self, 
               provider_name: Optional[str] = None,
               confidence_threshold: float = settings.DEFAULT_CONFIDENCE_THRESHOLD):
        """Initialize the graph expander.
        
        Args:
            provider_name: Name of the LLM provider to use
            confidence_threshold: Minimum confidence score for expansion
        """
        self.provider_name = provider_name
        self.confidence_threshold = confidence_threshold
        self.analyzer = GraphAnalyzer()
    
    async def identify_expansion_targets(self, 
                                     graph: KnowledgeGraph) -> List[Dict[str, Any]]:
        """Identify promising targets for graph expansion.
        
        Args:
            graph: Knowledge graph to expand
            
        Returns:
            List of expansion targets, each with entity, relevance, and rationale
        """
        # Get the most central entities
        central_entities = self.analyzer.get_central_entities(graph, top_n=5)
        
        # Get entities with fewer connections
        nx_graph = graph.to_networkx()
        node_degrees = dict(nx_graph.degree())
        
        # Find entities with low degree but high confidence
        sparse_entities = []
        for entity_id, entity in graph.entities.items():
            degree = node_degrees.get(entity_id, 0)
            if degree < 3 and entity.confidence > 0.8:
                sparse_entities.append((entity, degree))
        
        # Sort by lowest degree
        sparse_entities.sort(key=lambda x: x[1])
        sparse_entities = sparse_entities[:5]
        
        # Combine central and sparse entities as expansion targets
        targets = []
        
        # Add central entities
        for entity, score in central_entities:
            targets.append({
                "entity": entity,
                "relevance": "high",
                "rationale": "Central entity with many connections",
                "centrality": score
            })
        
        # Add sparse entities
        for entity, degree in sparse_entities:
            targets.append({
                "entity": entity,
                "relevance": "medium",
                "rationale": f"Entity with few connections ({degree}) but high confidence",
                "centrality": degree / max(node_degrees.values()) if node_degrees else 0
            })
        
        return targets
    
    async def generate_questions(self, 
                             target: Dict[str, Any], 
                             graph: KnowledgeGraph,
                             num_questions: int = 3) -> List[str]:
        """Generate questions to expand knowledge about a target entity.
        
        Args:
            target: Expansion target (entity and metadata)
            graph: Knowledge graph context
            num_questions: Number of questions to generate
            
        Returns:
            List of questions
        """
        entity = target["entity"]
        
        # Get the LLM provider
        try:
            # Use reasoning provider for question generation
            provider = LLMProviderFactory.get_reasoning_provider()
            if not provider:
                provider = LLMProviderFactory.get_provider(self.provider_name)
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
        
        # Get connected entities
        connections = []
        for related_entity, relationship in graph.get_connected_entities(entity.id):
            connections.append({
                "entity": related_entity.name,
                "type": related_entity.type,
                "relationship": relationship.type,
                "direction": "outgoing" if relationship.source_id == entity.id else "incoming"
            })
        
        # Create a prompt for question generation
        prompt = f"""
Generate {num_questions} specific, focused questions to expand our knowledge about the following entity:

Entity: {entity.name}
Type: {entity.type}

What we know about this entity:
"""
        
        # Add attribute information
        if entity.attributes:
            prompt += "Attributes:\n"
            for attr in entity.attributes:
                prompt += f"- {attr.key}: {attr.value}\n"
        
        # Add connection information
        if connections:
            prompt += "\nConnections:\n"
            for conn in connections:
                direction = "→" if conn["direction"] == "outgoing" else "←"
                prompt += f"- {entity.name} {direction} {conn['relationship']} {direction} {conn['entity']} ({conn['type']})\n"
        
        prompt += f"""
Generate {num_questions} questions that would help expand the knowledge graph around this entity. 
The questions should:
1. Be specific and targeted
2. Focus on potential new relationships or attributes
3. Address gaps in the current knowledge
4. Be answerable based on the original source text
5. Help create a more comprehensive understanding of the entity's role

Format each question on a new line, numbered 1 to {num_questions}.
"""
        
        # Generate questions
        try:
            response = await provider.generate_text(prompt)
            
            # Extract questions from the response
            questions = []
            current_question = ""
            
            for line in response.split("\n"):
                line = line.strip()
                
                # Check if this line starts with a number
                if line and line[0].isdigit() and ". " in line:
                    if current_question:
                        questions.append(current_question)
                    
                    # Start a new question
                    current_question = line.split(". ", 1)[1]
                elif current_question and line:
                    # Continue the current question
                    current_question += " " + line
            
            # Add the last question
            if current_question:
                questions.append(current_question)
            
            # Ensure we have the requested number of questions
            while len(questions) < num_questions:
                if len(questions) == 0:
                    questions.append(f"What is the relationship between {entity.name} and other key entities?")
                elif len(questions) == 1:
                    questions.append(f"What additional attributes or characteristics does {entity.name} have?")
                else:
                    questions.append(f"How does {entity.name} fit into the larger context?")
            
            return questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return [
                f"What is the relationship between {entity.name} and other key entities?",
                f"What additional attributes or characteristics does {entity.name} have?",
                f"How does {entity.name} fit into the larger context?"
            ]
    
    async def answer_question(self, 
                          question: str, 
                          target: Dict[str, Any],
                          collection: SegmentCollection) -> Dict[str, Any]:
        """Generate an answer to an expansion question.
        
        Args:
            question: Question to answer
            target: Expansion target (entity and metadata)
            collection: Text segments to search for information
            
        Returns:
            Dictionary with answer and extracted information
        """
        entity = target["entity"]
        
        # Get the LLM provider
        try:
            # Use reasoning provider for complex answers
            provider = LLMProviderFactory.get_reasoning_provider()
            if not provider:
                provider = LLMProviderFactory.get_provider(self.provider_name)
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return {"answer": "", "entities": [], "relationships": []}
        
        # Find relevant segments
        relevant_segments = self._find_relevant_segments(entity, collection)
        
        # Log more details to help debug
        logger.debug(f"Found {len(relevant_segments)} relevant segments for entity {entity.name}")
        for segment in relevant_segments:
            logger.debug(f"Segment ID: {segment.id}, Text: {segment.text[:100]}...")
        
        if not relevant_segments:
            logger.warning(f"No relevant segments found for entity {entity.name}")
            return {"answer": "", "entities": [], "relationships": []}
        
        # Concatenate relevant text (with limiting to avoid context limits)
        max_tokens = 4000
        relevant_text = ""
        
        for segment in relevant_segments:
            if len(relevant_text) + len(segment.text) > max_tokens:
                break
                
            relevant_text += segment.text + "\n\n"
        
        # Create a prompt for answering the question
        prompt = f"""
Answer the following question about {entity.name} ({entity.type}) based ONLY on the provided text.

Question: {question}

Relevant text:
{relevant_text}

Your answer should:
1. Be factual and grounded in the provided text
2. Include specific details and evidence
3. Identify any new entities or relationships
4. Address gaps or uncertainties in the available information
5. Be concise but thorough

Format your response with these sections:
1. Answer: [Your detailed answer]
2. New Entities: [List any new entities identified, with type and attributes]
3. New Relationships: [List any new relationships identified between entities]
4. Confidence: [Rate your confidence in this answer on a scale of 0-1]
"""
        
        # Generate the answer
        try:
            logger.debug(f"Sending question to LLM: {question}")
            logger.debug(f"Prompt: {prompt[:500]}...")
            
            response = await provider.generate_text(prompt)
            logger.debug(f"Received response: {response[:500]}...")
            
            # Parse the response
            answer = ""
            new_entities_text = ""
            new_relationships_text = ""
            confidence = 0.5
            
            current_section = ""
            for line in response.split("\n"):
                line = line.strip()
                
                if line.startswith("Answer:"):
                    current_section = "answer"
                    answer = line.replace("Answer:", "").strip()
                elif line.startswith("New Entities:"):
                    current_section = "entities"
                    new_entities_text = line.replace("New Entities:", "").strip()
                elif line.startswith("New Relationships:"):
                    current_section = "relationships"
                    new_relationships_text = line.replace("New Relationships:", "").strip()
                elif line.startswith("Confidence:"):
                    conf_text = line.replace("Confidence:", "").strip()
                    try:
                        # Extract numeric confidence value
                        conf_match = re.search(r"(\d+(\.\d+)?)", conf_text)
                        if conf_match:
                            conf_value = float(conf_match.group(1))
                            if 0 <= conf_value <= 1:
                                confidence = conf_value
                    except:
                        pass
                elif current_section == "answer" and line:
                    answer += " " + line
                elif current_section == "entities" and line:
                    new_entities_text += " " + line
                elif current_section == "relationships" and line:
                    new_relationships_text += " " + line
            
            logger.debug(f"Parsed answer: {answer[:200]}...")
            logger.debug(f"Parsed entities: {new_entities_text[:200]}...")
            logger.debug(f"Parsed relationships: {new_relationships_text[:200]}...")
            
            # Process the extracted information
            new_entities = []
            new_relationships = []
            
            # TODO: Implement proper parsing of the entity and relationship information
            # This is a simplified placeholder
            
            result = {
                "answer": answer,
                "entities_text": new_entities_text,
                "relationships_text": new_relationships_text,
                "entities": new_entities,
                "relationships": new_relationships,
                "confidence": confidence
            }
            
            logger.debug(f"Returning answer result with answer length: {len(answer)}")
            return result
            
        except Exception as e:
            import traceback
            logger.error(f"Error generating answer: {str(e)}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            return {"answer": "", "entities": [], "relationships": []}
    
    async def expand_graph(self, 
                       graph: KnowledgeGraph,
                       collection: SegmentCollection,
                       max_iterations: int = 3,
                       output_dir: Optional[str] = None) -> KnowledgeGraph:
        """Expand a knowledge graph through iterative questioning.
        
        Args:
            graph: Knowledge graph to expand
            collection: Text segments for information extraction
            max_iterations: Maximum number of expansion iterations
            output_dir: Directory to save expansion reports
            
        Returns:
            Expanded knowledge graph
        """
        expanded_graph = KnowledgeGraph()
        
        # Copy the original graph
        for entity_id, entity in graph.entities.items():
            expanded_graph.add_entity(entity)
        
        for rel_id, rel in graph.relationships.items():
            try:
                expanded_graph.add_relationship(rel)
            except ValueError:
                pass
        
        # Create extractors
        entity_extractor = EntityExtractor(self.provider_name, self.confidence_threshold)
        relation_extractor = RelationshipExtractor(self.provider_name, self.confidence_threshold)
        coreference_resolver = CoreferenceResolver()
        grounder = Grounder()
        
        # Create expansion report generator if output directory is provided
        from .expansion_report import ExpansionReportGenerator
        report_generator = None
        if output_dir:
            report_generator = ExpansionReportGenerator(output_dir)
        
        # Perform expansion iterations
        for iteration in range(max_iterations):
            logger.info(f"Starting expansion iteration {iteration + 1}/{max_iterations}")
            
            # Identify expansion targets
            targets = await self.identify_expansion_targets(expanded_graph)
            
            if not targets:
                logger.warning("No expansion targets identified")
                break
            
            # Limit to top 3 targets
            targets = targets[:3]
            
            # Add target information to report
            if report_generator:
                report_generator.add_iteration_data(iteration, targets)
            
            # Generate questions for each target
            all_questions = []
            for target in targets:
                questions = await self.generate_questions(target, expanded_graph)
                for question in questions:
                    all_questions.append((target, question))
                    
                    # Add question to report
                    if report_generator:
                        report_generator.add_question(
                            iteration=iteration,
                            target_name=target["entity"].name,
                            target_type=target["entity"].type,
                            question=question
                        )
            
            # Answer questions and extract new information
            new_entities = []
            new_relationships = []
            
            for target, question in all_questions:
                logger.info(f"Processing question: {question}")
                
                # Answer the question
                answer_result = await self.answer_question(question, target, collection)
                
                # Add answer to report
                if report_generator and answer_result["answer"]:
                    report_generator.add_answer(
                        iteration=iteration,
                        target_name=target["entity"].name,
                        target_type=target["entity"].type,
                        question=question,
                        answer=answer_result["answer"],
                        confidence=answer_result["confidence"],
                        new_entities_text=answer_result.get("entities_text", ""),
                        new_relationships_text=answer_result.get("relationships_text", "")
                    )
                
                if not answer_result["answer"]:
                    continue
                
                # Extract entities from the answer
                answer_segment = TextSegment(
                    id=uuid.uuid4(),  # Generate a new UUID for the segment
                    text=answer_result["answer"],
                    start_position=0,
                    end_position=len(answer_result["answer"]),
                    language="en"  # Assuming English
                )
                
                # Add segment to collection for proper grounding later
                collection.add_segment(answer_segment)
                
                extracted_entities = await entity_extractor.extract_from_segment(answer_segment)
                
                # Extract relationships
                extracted_relationships = await relation_extractor.extract_from_segment(
                    answer_segment, 
                    extracted_entities + list(expanded_graph.entities.values())
                )
                
                new_entities.extend(extracted_entities)
                new_relationships.extend(extracted_relationships)
            
            # Resolve coreferences
            all_entities = list(expanded_graph.entities.values()) + new_entities
            merged_entities = coreference_resolver.resolve_entities(all_entities)
            
            # Create ID mapping for merged entities
            entity_id_map = {}
            for old_entity in all_entities:
                for new_entity in merged_entities:
                    if old_entity.name.lower() == new_entity.name.lower() and old_entity.type.lower() == new_entity.type.lower():
                        entity_id_map[old_entity.id] = new_entity.id
                        break
            
            # Update relationships with new entity IDs
            all_relationships = list(expanded_graph.relationships.values()) + new_relationships
            updated_relationships = coreference_resolver.update_relationships(all_relationships, entity_id_map)
            
            # Ground entities and relationships
            grounded_entities = grounder.ground_entities(merged_entities, collection)
            
            # Create entity map for relationship grounding
            entity_map = {entity.id: entity for entity in grounded_entities}
            
            grounded_relationships = grounder.ground_relationships(updated_relationships, entity_map, collection)
            
            # Create a new graph with the grounded information
            new_graph = KnowledgeGraph()
            
            for entity in grounded_entities:
                new_graph.add_entity(entity)
            
            for relationship in grounded_relationships:
                try:
                    new_graph.add_relationship(relationship)
                except ValueError:
                    pass
            
            # Update the expanded graph
            expanded_graph = new_graph
            
            logger.info(f"Expansion iteration {iteration + 1} complete: {len(expanded_graph.entities)} entities, {len(expanded_graph.relationships)} relationships")
        
        # Generate the expansion report
        if report_generator:
            report_path = report_generator.generate_report()
            logger.info(f"Expansion process report generated: {report_path}")
        
        return expanded_graph
    
    def _find_relevant_segments(self, 
                            entity: Entity, 
                            collection: SegmentCollection) -> List[TextSegment]:
        """Find text segments relevant to an entity.
        
        Args:
            entity: Entity to find segments for
            collection: Segment collection to search
            
        Returns:
            List of relevant text segments
        """
        relevant_segments = []
        
        # If the entity has a source span, get the segment it's from
        if entity.source_span and entity.source_span.segment_id:
            segment_id = UUID(entity.source_span.segment_id)
            segment = collection.get_segment(segment_id)
            
            if segment:
                relevant_segments.append(segment)
        
        # Search for the entity name in other segments
        entity_name_lower = entity.name.lower()
        
        for segment_id, segment in collection.segments.items():
            if segment in relevant_segments:
                continue
                
            if entity_name_lower in segment.text.lower():
                relevant_segments.append(segment)
                
                # Limit to 5 segments
                if len(relevant_segments) >= 5:
                    break
        
        return relevant_segments