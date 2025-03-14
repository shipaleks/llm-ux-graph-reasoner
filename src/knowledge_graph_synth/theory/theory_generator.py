"""Theory generation for the knowledge graph synthesis system."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID

from ..models import KnowledgeGraph, Entity, Relationship, SourceSpan, TextSegment, SegmentCollection
from ..llm import LLMProviderFactory, prompt_manager
from ..llm.schemas import get_theory_generation_schema
from .pattern_finder import PatternFinder
from ..config import settings
from .evidence import EvidenceCollector

logger = logging.getLogger(__name__)


class TheoryGenerator:
    """Generates theories from knowledge graphs.
    
    This class implements theory generation based on knowledge graphs,
    using patterns, meta-graphs, and LLM reasoning to create comprehensive
    explanations of the information.
    """
    
    def __init__(self, 
               provider_name: Optional[str] = None,
               confidence_threshold: float = settings.DEFAULT_CONFIDENCE_THRESHOLD):
        """Initialize the theory generator.
        
        Args:
            provider_name: Name of the LLM provider to use
            confidence_threshold: Minimum confidence score for theories
        """
        self.provider_name = provider_name
        self.confidence_threshold = confidence_threshold
        self.pattern_finder = PatternFinder(provider_name, confidence_threshold)
        self.evidence_collector = EvidenceCollector()
    
    async def generate_theories(self, 
                            graph: KnowledgeGraph,
                            collection: Optional[SegmentCollection] = None,
                            max_theories: int = 3) -> List[Dict[str, Any]]:
        """Generate theories from a knowledge graph.
        
        Args:
            graph: Knowledge graph to analyze
            collection: Optional segment collection for evidence
            max_theories: Maximum number of theories to generate
            
        Returns:
            List of generated theories
        """
        # Find patterns in the graph
        patterns = await self.pattern_finder.find_patterns(graph)
        
        # Generate theories based on patterns
        theories = await self._generate_theories_from_patterns(graph, patterns, collection)
        
        # Sort theories by confidence
        theories.sort(key=lambda t: t.get("confidence", 0), reverse=True)
        
        # Filter theories by confidence
        filtered_theories = [
            theory for theory in theories
            if theory.get("confidence", 0) >= self.confidence_threshold
        ]
        
        # Limit to requested number
        return filtered_theories[:max_theories]
    
    async def _generate_theories_from_patterns(self,
                                         graph: KnowledgeGraph,
                                         patterns: List[Dict[str, Any]],
                                         collection: Optional[SegmentCollection]) -> List[Dict[str, Any]]:
        """Generate theories based on identified patterns.
        
        Args:
            graph: Knowledge graph to analyze
            patterns: List of identified patterns
            collection: Optional segment collection for evidence
            
        Returns:
            List of generated theories
        """
        # Get the LLM provider
        try:
            # Use reasoning provider for theory generation (need JSON support)
            provider = LLMProviderFactory.get_reasoning_provider()
            if not provider:
                provider = LLMProviderFactory.get_provider(self.provider_name)
                
            if not provider:
                logger.error("No LLM provider available for theory generation")
                return []
                
            # Also get a thinking provider for preliminary text analysis
            thinking_provider = LLMProviderFactory.get_thinking_provider()
            if thinking_provider:
                logger.info("Using thinking model for preliminary theory analysis")
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
        
        # Create a summary of the graph
        graph_summary = self._create_graph_summary(graph, patterns)
        
        # Определяем язык для промпта по содержимому графа
        prompt_language = "en"  # По умолчанию
        # Проверяем наличие русских символов в названиях сущностей
        for entity in graph.entities.values():
            if any(ord('а') <= ord(c) <= ord('я') or ord('А') <= ord(c) <= ord('Я') for c in entity.name):
                prompt_language = "ru"
                break
        
        # Perform preliminary free-form analysis with thinking model if available
        preliminary_insights = ""
        if thinking_provider:
            try:
                # Create prompt for preliminary analysis
                preliminary_prompt = f"""
                Проанализируйте этот граф знаний и предложите глубокие идеи о закономерностях, 
                которые вы наблюдаете. Не используйте специальный формат, просто опишите ваши 
                мысли о структуре графа, ключевых взаимосвязях и возможных теориях:
                
                {graph_summary}
                
                Напишите свободный текстовый анализ без JSON или специального форматирования.
                """
                
                # Get free-form analysis from thinking model
                preliminary_insights = await thinking_provider.generate_text(preliminary_prompt)
                logger.info("Generated preliminary insights with thinking model")
            except Exception as e:
                logger.warning(f"Error during preliminary analysis: {str(e)}")
        
        # Get the response schema for structured output
        schema = get_theory_generation_schema()
        
        # Get or create a prompt for theory generation
        prompt = prompt_manager.format_prompt(
            "theory_generation",
            prompt_language,
            graph_summary=graph_summary,
            preliminary_insights=preliminary_insights,
            schema=schema
        )
        
        if not prompt:
            # Создаем расширенный детальный промпт для более глубокого анализа
            if prompt_language == "ru":
                prompt = f"""
На основе предоставленного графа знаний разработайте глубокую, продуманную теорию, которая объясняет шаблоны и связи, обнаруженные в данных. Ваша задача - создать целостное объяснение, учитывающее наблюдаемые сущности и отношения.

Граф знаний содержит:
{graph_summary}

Следуйте следующему процессу анализа:

ЭТАП 1: ПРЕДВАРИТЕЛЬНЫЙ АНАЛИЗ
- Определите ключевые тематические кластеры в графе
- Выявите центральные сущности и их взаимосвязи
- Определите возможные скрытые механизмы или принципы, объясняющие наблюдаемую структуру
- Проанализируйте контекст и область знаний, к которым относится граф

ЭТАП 2: ФОРМУЛИРОВКА ТЕОРИИ
- Разработайте основную идею, которая объясняет большинство наблюдаемых связей
- Определите причинно-следственные механизмы, лежащие в основе отношений
- Объясните, как ваша теория согласуется с наблюдаемыми закономерностями
- Рассмотрите, как различные части графа взаимодействуют в рамках вашей теории

ЭТАП 3: ДЕТАЛИЗАЦИЯ ТЕОРИИ
1. Создайте ясное, описательное название
2. Предоставьте краткую сводку (3-5 предложений)
3. Разработайте подробное описание (минимум 2-3 абзаца), объясняющее:
   - Основную концепцию теории
   - Механизмы и процессы, которые она предполагает
   - Как она объясняет ключевые шаблоны в данных
   - Возможные следствия и импликации теории
4. Определите ключевые сущности и их роли в контексте теории
5. Выделите важнейшие отношения, формирующие основу вашей теории
6. Приведите не менее 3-5 конкретных доказательств, поддерживающих теорию
7. Оцените свою уверенность в этой теории (0-1)
8. Рассмотрите не менее 2 альтернативных объяснений
9. Определите пробелы в знаниях или вопросы, требующие дальнейшего исследования

ВАЖНО: Ваша теория должна быть глубокой, обоснованной и информативной. Она должна не просто перечислять факты, а объяснять скрытые взаимосвязи и принципы. Все выводы должны опираться на данные графа знаний.
"""
            else:
                prompt = f"""
Based on the provided knowledge graph, develop a deep, well-reasoned theory that explains the patterns and connections found in the data. Your task is to create a cohesive explanation that accounts for the observed entities and relationships.

The knowledge graph contains:
{graph_summary}

Follow this analytical process:

PHASE 1: PRELIMINARY ANALYSIS
- Identify key thematic clusters in the graph
- Determine central entities and their interconnections 
- Identify possible hidden mechanisms or principles explaining the observed structure
- Analyze the context and domain knowledge relevant to the graph

PHASE 2: THEORY FORMULATION
- Develop a core idea that explains most of the observed connections
- Identify causal mechanisms underlying the relationships
- Explain how your theory aligns with the observed patterns
- Consider how different parts of the graph interact within your theory

PHASE 3: THEORY ELABORATION
1. Create a clear, descriptive title
2. Provide a concise summary (3-5 sentences)
3. Develop a detailed description (minimum 2-3 paragraphs) explaining:
   - The core concept of the theory
   - The mechanisms and processes it implies
   - How it explains key patterns in the data
   - Possible consequences and implications of the theory
4. Identify the key entities involved and their roles within the theory
5. Highlight the critical relationships that form the basis of your theory
6. Cite at least 3-5 specific pieces of evidence supporting the theory
7. Assess your confidence in this theory (0-1)
8. Consider at least 2 alternative explanations
9. Identify knowledge gaps or questions requiring further investigation

IMPORTANT: Your theory should be deep, well-reasoned, and informative. It should not merely list facts but explain underlying connections and principles. All conclusions must be based on the knowledge graph data.
"""
        
        # Generate the theory
        try:
            response = await provider.generate_structured(prompt, schema)
            theory_data = response.get("theory", {})
            
            # Process the theory
            if theory_data:
                # Collect evidence for the theory
                evidence = []
                if collection and "evidence" in theory_data:
                    evidence_items = theory_data.get("evidence", [])
                    for evidence_item in evidence_items:
                        evidence_text = evidence_item.get("text", "")
                        if evidence_text:
                            # Find this text in the source
                            found_spans = self.evidence_collector.find_evidence(evidence_text, collection)
                            evidence.extend(found_spans)
                
                # Create the theory
                theory = {
                    "title": theory_data.get("title", "Unnamed Theory"),
                    "summary": theory_data.get("summary", ""),
                    "description": theory_data.get("description", ""),
                    "key_entities": theory_data.get("key_entities", []),
                    "key_relationships": theory_data.get("key_relationships", []),
                    "evidence": theory_data.get("evidence", []),
                    "evidence_spans": [span.to_dict() for span in evidence],
                    "confidence": theory_data.get("confidence", 0.5),
                    "alternative_explanations": theory_data.get("alternative_explanations", []),
                    "gaps": theory_data.get("gaps", [])
                }
                
                # Generate alternative theories
                alternative_theories = await self._generate_alternative_theories(
                    graph, theory, patterns, collection
                )
                
                # Return all theories
                return [theory] + alternative_theories
            
            return []
            
        except Exception as e:
            logger.error(f"Error generating theory: {str(e)}")
            return []
    
    async def _generate_alternative_theories(self,
                                        graph: KnowledgeGraph,
                                        primary_theory: Dict[str, Any],
                                        patterns: List[Dict[str, Any]],
                                        collection: Optional[SegmentCollection]) -> List[Dict[str, Any]]:
        """Generate alternative theories that explain the same evidence.
        
        Args:
            graph: Knowledge graph to analyze
            primary_theory: The primary theory to provide alternatives to
            patterns: List of identified patterns
            collection: Optional segment collection for evidence
            
        Returns:
            List of alternative theories
        """
        # Get the LLM provider
        try:
            # Use reasoning provider for alternative theory generation
            provider = LLMProviderFactory.get_reasoning_provider()
            if not provider:
                provider = LLMProviderFactory.get_provider(self.provider_name)
                
            if not provider:
                logger.error("No LLM provider available for alternative theory generation")
                return []
        except Exception as e:
            logger.error(f"Error getting LLM provider: {str(e)}")
            return []
        
        # Get primary theory details
        title = primary_theory.get("title", "")
        summary = primary_theory.get("summary", "")
        
        # Create a graph summary
        graph_summary = self._create_graph_summary(graph, patterns)
        
        # Определяем язык для промпта по содержимому графа
        prompt_language = "en"  # По умолчанию
        # Проверяем наличие русских символов в названиях сущностей
        for entity in graph.entities.values():
            if any(ord('а') <= ord(c) <= ord('я') or ord('А') <= ord(c) <= ord('Я') for c in entity.name):
                prompt_language = "ru"
                break
                
        # Create a prompt for alternative theory generation with enhanced depth
        if prompt_language == "ru":
            prompt = f"""
Разработайте альтернативную теорию, которая объясняет те же данные графа знаний, но предлагает принципиально иную интерпретацию или точку зрения.

Граф знаний содержит:
{graph_summary}

Основная теория:
Название: {title}
Сводка: {summary}

ЭТАП 1: КРИТИЧЕСКИЙ АНАЛИЗ ОСНОВНОЙ ТЕОРИИ
- Определите ключевые допущения и предположения основной теории
- Выявите слабые места или недостаточно объясненные аспекты
- Определите альтернативные способы интерпретации тех же отношений и шаблонов
- Рассмотрите противоположные или дополнительные перспективы

ЭТАП 2: РАЗРАБОТКА АЛЬТЕРНАТИВНОЙ КОНЦЕПЦИИ
- Создайте принципиально иной концептуальный подход к интерпретации данных
- Предложите альтернативные причинно-следственные механизмы
- Переоцените значимость и роли ключевых сущностей
- Разработайте новую модель взаимосвязей, которая также объясняет наблюдаемые шаблоны

Ваша альтернативная теория должна:
1. Предлагать существенно иное объяснение для тех же доказательств
2. Быть внутренне согласованной и правдоподобной
3. Учитывать ключевые сущности и отношения в графе
4. Выявлять иные шаблоны или придавать другое значение тем же шаблонам
5. Сохранять интеллектуальную строгость и избегать спекуляций

Для вашей альтернативной теории:
1. Создайте чёткое, описательное название, которое явно отличает её от основной теории
2. Предоставьте краткую сводку (3-5 предложений)
3. Разработайте подробное описание (минимум 2-3 абзаца), объясняющее ключевые шаблоны
4. Определите задействованные ключевые сущности и их роли в контексте вашей теории
5. Выделите ключевые отношения, которые формируют основу вашей теории
6. Приведите не менее 3-5 конкретных доказательств, подтверждающих вашу теорию
7. Оцените свою уверенность в этой теории (0-1)
8. Объясните, почему эта альтернатива может быть предпочтительнее или точнее основной теории
9. Определите пробелы в знаниях или вопросы, которые особенно актуальны для вашей альтернативной теории

ВАЖНО: Разработайте всестороннюю альтернативную теорию, основанную исключительно на предоставленной информации. Не вводите сущности, отношения или концепции, которые не подтверждаются графом знаний. Ваша теория должна быть действительно альтернативной, а не просто вариацией основной теории.
"""
        else:
            prompt = f"""
Develop an alternative theory that explains the same knowledge graph data but offers a fundamentally different interpretation or perspective.

The knowledge graph contains:
{graph_summary}

The primary theory is:
Title: {title}
Summary: {summary}

PHASE 1: CRITICAL ANALYSIS OF PRIMARY THEORY
- Identify key assumptions and presuppositions of the primary theory
- Detect weak points or insufficiently explained aspects
- Determine alternative ways to interpret the same relationships and patterns
- Consider opposing or complementary perspectives

PHASE 2: DEVELOPING ALTERNATIVE FRAMEWORK
- Create a fundamentally different conceptual approach to interpreting the data
- Propose alternative causal mechanisms
- Reevaluate the significance and roles of key entities
- Develop a new model of relationships that also explains the observed patterns

Your alternative theory should:
1. Offer a substantially different explanation for the same evidence
2. Be internally consistent and plausible
3. Account for the key entities and relationships in the graph
4. Identify different patterns or give different significance to the same patterns
5. Maintain intellectual rigor and avoid speculation

For your alternative theory:
1. Create a clear, descriptive title that explicitly differentiates it from the primary theory
2. Provide a concise summary (3-5 sentences)
3. Develop a detailed description (minimum 2-3 paragraphs) explaining the key patterns
4. Identify the key entities involved and their roles within your theory
5. Highlight the critical relationships that form the basis of your theory
6. Cite at least 3-5 specific pieces of evidence supporting your theory
7. Assess your confidence in this theory (0-1)
8. Explain why this alternative might be preferable to or more accurate than the primary theory
9. Identify knowledge gaps or questions that are specifically relevant to your alternative theory

IMPORTANT: Develop a comprehensive alternative theory based solely on the information provided. Do not introduce entities, relationships, or concepts that aren't supported by the knowledge graph. Your theory should be truly alternative, not merely a variation of the primary theory.
"""
        
        # Get the response schema
        schema = get_theory_generation_schema()
        
        # Generate the alternative theory
        try:
            response = await provider.generate_structured(prompt, schema)
            theory_data = response.get("theory", {})
            
            # Process the theory
            if theory_data:
                # Collect evidence for the theory
                evidence = []
                if collection and "evidence" in theory_data:
                    evidence_items = theory_data.get("evidence", [])
                    for evidence_item in evidence_items:
                        evidence_text = evidence_item.get("text", "")
                        if evidence_text:
                            # Find this text in the source
                            found_spans = self.evidence_collector.find_evidence(evidence_text, collection)
                            evidence.extend(found_spans)
                
                # Create the theory
                theory = {
                    "title": theory_data.get("title", "Alternative Theory"),
                    "summary": theory_data.get("summary", ""),
                    "description": theory_data.get("description", ""),
                    "key_entities": theory_data.get("key_entities", []),
                    "key_relationships": theory_data.get("key_relationships", []),
                    "evidence": theory_data.get("evidence", []),
                    "evidence_spans": [span.to_dict() for span in evidence],
                    "confidence": theory_data.get("confidence", 0.5),
                    "alternative_explanations": theory_data.get("alternative_explanations", []),
                    "gaps": theory_data.get("gaps", []),
                    "is_alternative": True,
                    "alternative_to": primary_theory.get("title", "")
                }
                
                return [theory]
            
            return []
            
        except Exception as e:
            logger.error(f"Error generating alternative theory: {str(e)}")
            return []
    
    def _create_graph_summary(self, 
                          graph: KnowledgeGraph, 
                          patterns: List[Dict[str, Any]]) -> str:
        """Create a summary of a knowledge graph for theory generation.
        
        Args:
            graph: Knowledge graph to summarize
            patterns: List of identified patterns
            
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
        
        # Add pattern summary
        if patterns:
            summary += "\nIdentified patterns:\n"
            for pattern in patterns[:5]:  # Limit to top 5 patterns
                pattern_name = pattern.get("name", "Unnamed pattern")
                pattern_type = pattern.get("type", "unknown")
                pattern_desc = pattern.get("description", "")
                
                summary += f"- {pattern_name} ({pattern_type}): {pattern_desc}\n"
        
        return summary