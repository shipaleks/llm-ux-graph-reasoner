#!/usr/bin/env python3
"""
Анализатор текстов с использованием LLM для всех этапов обработки.
Использует LLM (Gemini Pro 2) для смыслового разбиения и анализа,
что обеспечивает качественную обработку русскоязычных WEBVTT транскриптов.
"""

import os
import sys
import json
import logging
import argparse
import time
import re
import asyncio
from pathlib import Path
from datetime import datetime
import glob
from uuid import uuid4
from typing import List, Dict, Any, Optional, Tuple

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Импортируем необходимые модули
sys.path.append(str(Path(__file__).parent))
from src.knowledge_graph_synth.models.segment import TextSegment, SegmentCollection
from src.knowledge_graph_synth.llm.gemini_reasoning import GeminiReasoningProvider
from src.knowledge_graph_synth.text.loader import TextLoader
from src.knowledge_graph_synth.cli.utils import setup_output_dir
from llm_segmenter import LLMSegmenter

class LLMAnalyzer:
    """Unified analyzer using LLM for all processing stages."""
    
    def __init__(self, provider="gemini", output_dir="output/llm_analysis"):
        """Initialize the LLM analyzer.
        
        Args:
            provider: LLM provider to use (default: gemini)
            output_dir: Base output directory
        """
        self.provider_name = provider
        self.llm = GeminiReasoningProvider()
        self.output_base = output_dir
        self.timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.output_dir = os.path.join(output_dir, self.timestamp)
        os.makedirs(self.output_dir, exist_ok=True)
        
    async def analyze_text(self, file_path: str, max_segments: Optional[int] = None) -> str:
        """Analyze text using LLM for all stages.
        
        Args:
            file_path: Path to the text file
            max_segments: Maximum number of segments to process (for testing)
            
        Returns:
            Path to the generated report
        """
        # Load text
        loader = TextLoader()
        document_id = f"doc_{self.timestamp}"
        document = loader.load_file(file_path, document_id=document_id)
        
        # Create directory structure
        context_dir = os.path.join(self.output_dir, "context")
        graph_dir = os.path.join(self.output_dir, "graphs")
        theories_dir = os.path.join(self.output_dir, "theories")
        
        os.makedirs(context_dir, exist_ok=True)
        os.makedirs(graph_dir, exist_ok=True)
        os.makedirs(theories_dir, exist_ok=True)
        
        # Step 1: Segment text
        logger.info(f"Segmenting text using LLM...")
        segmenter = LLMSegmenter(provider=self.provider_name)
        collection = await segmenter.segment_text(
            document.text, 
            document_id=document_id,
            language=document.language
        )
        
        # Limit segments if needed
        segments = list(collection.segments.values())
        if max_segments and len(segments) > max_segments:
            logger.info(f"Limiting to {max_segments} segments (from {len(segments)})")
            segments = segments[:max_segments]
        
        # Save segments
        segments_file = os.path.join(context_dir, "segments.json")
        with open(segments_file, "w", encoding="utf-8") as f:
            segments_data = [s.to_dict() for s in segments]
            json.dump(segments_data, f, ensure_ascii=False, indent=2)
        
        # Step 2: Generate summaries for each segment
        logger.info(f"Generating summaries for {len(segments)} segments...")
        summaries = await self._generate_summaries(segments, document.language)
        
        # Save summaries
        summaries_file = os.path.join(context_dir, "segment_summaries.json")
        with open(summaries_file, "w", encoding="utf-8") as f:
            json.dump(summaries, f, ensure_ascii=False, indent=2)
        
        # Step 3: Generate theories
        logger.info("Generating theories...")
        theories = await self._generate_theories(segments, summaries, document.language)
        
        # Save theories
        theories_file = os.path.join(theories_dir, "theories.json")
        with open(theories_file, "w", encoding="utf-8") as f:
            json.dump(theories, f, ensure_ascii=False, indent=2)
        
        # Create theories markdown
        theories_md = self._generate_theories_markdown(theories, document.language)
        theories_md_file = os.path.join(theories_dir, "theories.md")
        with open(theories_md_file, "w", encoding="utf-8") as f:
            f.write(theories_md)
        
        # Step 4: Generate final report
        logger.info("Generating final report...")
        report_path = self._generate_report(file_path, summaries, theories, document.language)
        
        logger.info(f"Analysis complete. Report saved to: {report_path}")
        return report_path
    
    async def _generate_summaries(self, 
                               segments: List[TextSegment], 
                               language: str) -> Dict[str, Any]:
        """Generate summaries for text segments.
        
        Args:
            segments: List of text segments
            language: Language code
            
        Returns:
            Dictionary of segment summaries
        """
        summaries = {}
        
        for segment in segments:
            # Skip root and very short segments
            if segment.parent_id is None or len(segment.text) < 50:
                continue
                
            logger.info(f"Generating summary for segment {segment.id} ({len(segment.text)} chars)")
            
            # Create prompt based on language
            if language == "ru":
                prompt = f"""
                Проанализируй следующий фрагмент текста и составь краткую сводку:
                
                {segment.text}
                
                Результат предоставь в следующем формате:
                1. Заголовок, отражающий основную тему отрывка
                2. Краткое содержание (2-3 предложения)
                3. Список из 3-5 ключевых моментов или фактов
                """
            else:
                prompt = f"""
                Analyze the following text segment and provide a concise summary:
                
                {segment.text}
                
                Provide your response in the following format:
                1. A title that reflects the main topic
                2. Brief summary (2-3 sentences)
                3. List of 3-5 key points or facts
                """
            
            # Define expected response schema
            schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "key_points": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["title", "summary", "key_points"]
            }
            
            try:
                response = await self.llm.generate_structured(prompt, schema)
                summaries[str(segment.id)] = response
            except Exception as e:
                logger.error(f"Error generating summary for segment {segment.id}: {str(e)}")
                # Fallback to a simple structure
                summaries[str(segment.id)] = {
                    "title": "Error in summary generation",
                    "summary": "Failed to generate summary for this segment.",
                    "key_points": ["Error occurred during processing"]
                }
        
        return summaries
    
    async def _generate_theories(self, 
                              segments: List[TextSegment],
                              summaries: Dict[str, Any],
                              language: str) -> List[Dict[str, Any]]:
        """Generate theories based on segment summaries.
        
        Args:
            segments: List of text segments
            summaries: Dictionary of segment summaries
            language: Language code
            
        Returns:
            List of theories
        """
        # Concatenate summaries and key points for context
        context = ""
        for segment_id, summary in summaries.items():
            context += f"### {summary.get('title', 'Untitled')}\n"
            context += f"{summary.get('summary', '')}\n"
            
            if "key_points" in summary and summary["key_points"]:
                context += "Key points:\n"
                for point in summary["key_points"]:
                    context += f"- {point}\n"
                    
            context += "\n"
        
        # Create prompt based on language
        if language == "ru":
            prompt = f"""
            На основе следующего контекста, сформулируй 2-4 основные теории, которые можно вывести из текста:

            {context}

            Для каждой теории укажи:
            1. Название теории
            2. Описание теории
            3. Уровень достоверности (от 0.0 до 1.0)
            4. 2-4 гипотезы, поддерживающие теорию
            
            Для каждой гипотезы укажи:
            1. Утверждение
            2. Уровень достоверности (от 0.0 до 1.0)
            3. 1-3 доказательства, подтверждающие гипотезу
            
            Для каждого доказательства укажи:
            1. Описание доказательства
            2. Силу доказательства (от 0.0 до 1.0)
            """
        else:
            prompt = f"""
            Based on the following context, formulate 2-4 main theories that can be derived from the text:

            {context}

            For each theory, provide:
            1. Theory name
            2. Theory description
            3. Confidence level (from 0.0 to 1.0)
            4. 2-4 hypotheses supporting the theory
            
            For each hypothesis, provide:
            1. Statement
            2. Confidence level (from 0.0 to 1.0)
            3. 1-3 pieces of evidence supporting the hypothesis
            
            For each evidence, provide:
            1. Evidence description
            2. Evidence strength (from 0.0 to 1.0)
            """
        
        # Define expected response schema
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "confidence": {"type": "number"},
                    "hypotheses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "statement": {"type": "string"},
                                "confidence": {"type": "number"},
                                "evidence": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "description": {"type": "string"},
                                            "strength": {"type": "number"}
                                        },
                                        "required": ["description", "strength"]
                                    }
                                }
                            },
                            "required": ["statement", "confidence", "evidence"]
                        }
                    }
                },
                "required": ["name", "description", "confidence", "hypotheses"]
            }
        }
        
        try:
            theories = await self.llm.generate_structured(prompt, schema)
            logger.info(f"Generated {len(theories)} theories")
            return theories
        except Exception as e:
            logger.error(f"Error generating theories: {str(e)}")
            # Return a fallback theory
            return [{
                "name": "Автоматически сгенерированная теория",
                "description": "Эта теория была создана как запасной вариант из-за ошибки при генерации теорий.",
                "confidence": 0.5,
                "hypotheses": [
                    {
                        "statement": "В тексте содержится значимая информация",
                        "confidence": 0.6,
                        "evidence": [
                            {
                                "description": "Текст был достаточно длинным для анализа",
                                "strength": 0.5
                            }
                        ]
                    }
                ]
            }]
    
    def _generate_theories_markdown(self, theories: List[Dict[str, Any]], language: str) -> str:
        """Generate markdown representation of theories.
        
        Args:
            theories: List of theories
            language: Language code
            
        Returns:
            Markdown string
        """
        # Set labels based on language
        labels = {
            "ru": {
                "title": "Сгенерированные теории",
                "theory": "Теория",
                "confidence": "Достоверность",
                "description": "Описание",
                "hypotheses": "Гипотезы",
                "hypothesis": "Гипотеза",
                "evidence": "Доказательства",
                "strength": "Сила"
            },
            "en": {
                "title": "Generated Theories",
                "theory": "Theory",
                "confidence": "Confidence",
                "description": "Description",
                "hypotheses": "Hypotheses",
                "hypothesis": "Hypothesis",
                "evidence": "Evidence",
                "strength": "Strength"
            }
        }
        
        l = labels.get(language, labels["en"])
        
        md = f"# {l['title']}\n\n"
        
        for i, theory in enumerate(theories):
            md += f"## {l['theory']} {i+1}: {theory.get('name', '')}\n\n"
            md += f"**{l['confidence']}**: {theory.get('confidence', 0.0):.2f}\n\n"
            md += f"**{l['description']}**: {theory.get('description', '')}\n\n"
            
            if "hypotheses" in theory and theory["hypotheses"]:
                md += f"### {l['hypotheses']}\n\n"
                
                for j, hypothesis in enumerate(theory["hypotheses"]):
                    md += f"#### {l['hypothesis']} {j+1}: {hypothesis.get('statement', '')}\n\n"
                    md += f"**{l['confidence']}**: {hypothesis.get('confidence', 0.0):.2f}\n\n"
                    
                    if "evidence" in hypothesis and hypothesis["evidence"]:
                        md += f"**{l['evidence']}**:\n\n"
                        
                        for evidence in hypothesis["evidence"]:
                            md += f"- {evidence.get('description', '')} ({l['strength']}: {evidence.get('strength', 0.0):.2f})\n"
                    
                    md += "\n"
            
            md += "---\n\n"
        
        return md
    
    def _generate_report(self, 
                       file_path: str,
                       summaries: Dict[str, Any],
                       theories: List[Dict[str, Any]],
                       language: str) -> str:
        """Generate an HTML report.
        
        Args:
            file_path: Path to the original file
            summaries: Dictionary of segment summaries
            theories: List of theories
            language: Language code
            
        Returns:
            Path to the generated report
        """
        # Set labels based on language
        labels = {
            "ru": {
                "title": "Отчет LLM анализа текста",
                "file": "Файл",
                "date": "Дата анализа",
                "summary": "Суммаризация текста",
                "no_title": "Без заголовка",
                "key_points": "Ключевые моменты",
                "theories": "Теории и гипотезы",
                "no_theories": "Теории не были сгенерированы.",
                "theory": "Теория",
                "hypothesis": "Гипотеза",
                "confidence": "Достоверность",
                "evidence": "Доказательства",
                "strength": "Сила"
            },
            "en": {
                "title": "LLM Text Analysis Report",
                "file": "File",
                "date": "Analysis Date",
                "summary": "Text Summary",
                "no_title": "No Title",
                "key_points": "Key Points",
                "theories": "Theories and Hypotheses",
                "no_theories": "No theories were generated.",
                "theory": "Theory",
                "hypothesis": "Hypothesis",
                "confidence": "Confidence",
                "evidence": "Evidence",
                "strength": "Strength"
            }
        }
        
        l = labels.get(language, labels["en"])
        
        # Формирование отчета
        html_content = f"""
        <!DOCTYPE html>
        <html lang="{language}">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{l["title"]}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3, h4 {{
                    color: #2c3e50;
                }}
                .summary-container {{
                    background-color: #f5f9ff;
                    border-left: 4px solid #4a90e2;
                    margin-bottom: 30px;
                    padding: 15px;
                    border-radius: 4px;
                }}
                .metadata {{
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-left: 4px solid #2c3e50;
                    margin-bottom: 20px;
                }}
                .key-points {{
                    background-color: #f8f8f8;
                    padding: 15px;
                    border-radius: 4px;
                    margin-top: 10px;
                }}
                .theory {{
                    background-color: #f5f9ff;
                    border-left: 4px solid #4a90e2;
                    margin-bottom: 30px;
                    padding: 15px;
                    border-radius: 4px;
                }}
                .hypothesis {{
                    background-color: #f9f9f9;
                    padding: 15px;
                    margin: 10px 0;
                    border-left: 3px solid #666;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <h1>{l["title"]}</h1>
            
            <div class="metadata">
                <p><strong>{l["file"]}:</strong> {os.path.basename(file_path)}</p>
                <p><strong>{l["date"]}:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h2>{l["summary"]}</h2>
        """
        
        # Добавление суммаризации
        for segment_id, summary in summaries.items():
            title = summary.get("title", l["no_title"])
            summary_text = summary.get("summary", "")
            key_points = summary.get("key_points", [])
            
            key_points_html = ""
            if key_points:
                key_points_html = f"<div class='key-points'><h4>{l['key_points']}:</h4><ul>"
                for point in key_points:
                    key_points_html += f"<li>{point}</li>"
                key_points_html += "</ul></div>"
            
            html_content += f"""
            <div class="summary-container">
                <h3>{title}</h3>
                <p>{summary_text}</p>
                {key_points_html}
            </div>
            """
        
        # Добавление теорий
        html_content += f"<h2>{l['theories']}</h2>"
        
        if theories:
            for i, theory in enumerate(theories):
                theory_name = theory.get("name", f"{l['theory']} {i+1}")
                theory_desc = theory.get("description", "")
                theory_conf = theory.get("confidence", 0.0)
                
                hypotheses_html = ""
                if "hypotheses" in theory and theory["hypotheses"]:
                    for h, hypothesis in enumerate(theory["hypotheses"]):
                        h_statement = hypothesis.get("statement", "")
                        h_confidence = hypothesis.get("confidence", 0.0)
                        
                        evidence_html = ""
                        if "evidence" in hypothesis and hypothesis["evidence"]:
                            evidence_html = f"<p><strong>{l['evidence']}:</strong></p><ul>"
                            for ev in hypothesis["evidence"]:
                                ev_desc = ev.get("description", "")
                                ev_strength = ev.get("strength", 0.0)
                                evidence_html += f"<li>{ev_desc} ({l['strength']}: {ev_strength:.2f})</li>"
                            evidence_html += "</ul>"
                        
                        hypotheses_html += f"""
                        <div class="hypothesis">
                            <h4>{l['hypothesis']} {h+1}: {h_statement}</h4>
                            <div>{l['confidence']}: {h_confidence:.2f}</div>
                            {evidence_html}
                        </div>
                        """
                
                html_content += f"""
                <div class="theory">
                    <h3>{theory_name}</h3>
                    <div>{l['confidence']}: {theory_conf:.2f}</div>
                    <p>{theory_desc}</p>
                    {hypotheses_html}
                </div>
                """
        else:
            html_content += f"<p>{l['no_theories']}</p>"
        
        html_content += """
        </body>
        </html>
        """
        
        # Сохранение отчета
        report_path = os.path.join(self.output_dir, "llm_report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path

async def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="LLM-based text analyzer with complete processing pipeline"
    )
    
    parser.add_argument(
        "file_path",
        help="Path to text file to analyze"
    )
    
    parser.add_argument(
        "--provider", "-p",
        default="gemini",
        choices=["gemini", "openai"],
        help="LLM provider (default: gemini)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output/llm_analysis",
        help="Output directory (default: output/llm_analysis)"
    )
    
    parser.add_argument(
        "--max-segments", "-m",
        type=int,
        default=None,
        help="Maximum number of segments to process (for testing)"
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.file_path):
        logger.error(f"File not found: {args.file_path}")
        return 1
    
    # Create analyzer
    analyzer = LLMAnalyzer(provider=args.provider, output_dir=args.output)
    
    # Analyze text
    start_time = time.time()
    logger.info(f"Starting LLM analysis for {args.file_path}")
    
    report_path = await analyzer.analyze_text(args.file_path, args.max_segments)
    
    logger.info(f"Analysis completed in {time.time() - start_time:.2f} seconds")
    print(f"\nАнализ завершен. Создан отчет: {report_path}")
    print("Вы можете открыть его в браузере.")
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())