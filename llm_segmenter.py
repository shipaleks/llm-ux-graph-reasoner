#!/usr/bin/env python3
"""
LLM-based text segmentation module для обработки текстов любой длины.
Использует Gemini Pro 2 для смыслового разбиения текста с учетом контекста.
"""

import os
import sys
import json
import logging
import argparse
import time
from pathlib import Path
import asyncio
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
from src.knowledge_graph_synth.text.segmenter import TextSegmenter
from src.knowledge_graph_synth.text.loader import TextLoader
from src.knowledge_graph_synth.cli.utils import setup_output_dir

class LLMSegmenter:
    """LLM-based text segmenter for large context understanding."""
    
    def __init__(self, provider="gemini"):
        """Initialize the LLM-based segmenter.
        
        Args:
            provider: LLM provider to use (default: gemini)
        """
        self.provider_name = provider
        self.llm = GeminiReasoningProvider()
        self.standard_segmenter = TextSegmenter()
        
    async def segment_text(self, text: str, document_id: str, language: str = None) -> SegmentCollection:
        """Segment text using LLM for a semantic understanding.
        
        Args:
            text: Text to segment
            document_id: Document ID
            language: Language of the text (auto-detected if None)
            
        Returns:
            SegmentCollection with segments
        """
        # Auto-detect language if not provided
        if language is None:
            language = self._detect_language(text)
            logger.info(f"Определен язык текста: {language}")
        
        # Create root segment
        root_segment = TextSegment(
            id=uuid4(),
            document_id=document_id,
            text=text,
            language=language,
            metadata={"segment_type": "document"}
        )
        
        # Create segment collection
        collection = SegmentCollection()
        collection.add_segment(root_segment)
        
        # Check if WEBVTT format
        if text.startswith("WEBVTT"):
            logger.info("Обнаружен формат WEBVTT, выполняем смысловое разбиение с помощью LLM")
            await self._segment_transcript_with_llm(collection, root_segment)
        else:
            logger.info("Обычный текстовый формат, используем стандартную сегментацию")
            self.standard_segmenter.segment(collection)
        
        return collection
    
    def _detect_language(self, text: str) -> str:
        """Detect language of the text.
        
        Args:
            text: Text to detect language for
            
        Returns:
            ISO 639-1 language code (e.g., "en", "ru")
        """
        # Простая эвристика для определения русского языка
        # В продакшен-системе лучше использовать специализированные библиотеки
        cyrillic_count = sum(1 for c in text if 'а' <= c.lower() <= 'я')
        total_chars = sum(1 for c in text if c.isalpha())
        
        if total_chars == 0:
            return "en"
        
        cyrillic_ratio = cyrillic_count / total_chars
        return "ru" if cyrillic_ratio > 0.3 else "en"
    
    async def _segment_transcript_with_llm(self, collection: SegmentCollection, root_segment: TextSegment):
        """Segment transcript using LLM for understanding conversational dynamics.
        
        Args:
            collection: SegmentCollection to add segments to
            root_segment: Root segment containing the transcript
            
        Returns:
            Modified SegmentCollection
        """
        text = root_segment.text
        language = root_segment.language
        
        # Remove WEBVTT header and timestamps
        clean_text = self._clean_webvtt(text)
        
        # Define segmentation prompt based on language
        if language == "ru":
            prompt = f"""
            Разбей следующий текст транскрипта на 5-10 логических частей (сегментов), 
            группируя реплики по смыслу и тематике. Каждый сегмент должен представлять 
            связанную мысль или подтему. Для каждого сегмента укажи:
            
            1. Номер сегмента
            2. Заголовок сегмента (отражающий его основное содержание)
            3. Начало сегмента (первые несколько слов)
            4. Конец сегмента (последние несколько слов)
            5. Текст сегмента полностью
            
            Вот транскрипт:
            
            {clean_text}
            """
        else:
            prompt = f"""
            Divide the following transcript into 5-10 logical segments,
            grouping utterances by meaning and topic. Each segment should 
            represent a related thought or subtopic. For each segment, provide:
            
            1. Segment number
            2. Segment title (reflecting its main content)
            3. Start of segment (first few words)
            4. End of segment (last few words)
            5. Full segment text
            
            Here's the transcript:
            
            {clean_text}
            """
        
        # Define the expected response schema
        schema = {
            "type": "object",
            "properties": {
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "number": {"type": "number"},
                            "title": {"type": "string"},
                            "start_text": {"type": "string"},
                            "end_text": {"type": "string"},
                            "full_text": {"type": "string"}
                        },
                        "required": ["number", "title", "full_text"]
                    }
                }
            },
            "required": ["segments"]
        }
        
        try:
            # Generate segmentation using LLM
            logger.info("Запрос к LLM для смыслового разбиения транскрипта...")
            response = await self.llm.generate_structured(prompt, schema)
            
            if "segments" not in response or not response["segments"]:
                logger.warning("LLM не вернул сегменты, используем стандартное разбиение")
                segments = self.standard_segmenter._segment_transcript(root_segment)
                for segment in segments:
                    collection.add_segment(segment)
                return collection
            
            # Add segments to collection
            logger.info(f"LLM вернул {len(response['segments'])} смысловых сегментов")
            for segment_data in response["segments"]:
                # Create segment
                segment = TextSegment(
                    document_id=root_segment.document_id,
                    text=segment_data["full_text"],
                    language=root_segment.language,
                    parent_id=root_segment.id,
                    metadata={
                        "segment_type": "llm_transcript_topic",
                        "parent_segment": str(root_segment.id),
                        "topic_number": segment_data["number"],
                        "topic_title": segment_data["title"]
                    }
                )
                collection.add_segment(segment)
            
            return collection
            
        except Exception as e:
            logger.error(f"Ошибка при LLM-сегментации: {str(e)}")
            logger.info("Возврат к стандартному разбиению")
            segments = self.standard_segmenter._segment_transcript(root_segment)
            for segment in segments:
                collection.add_segment(segment)
            return collection
    
    def _clean_webvtt(self, text: str) -> str:
        """Remove WEBVTT header and timestamps from text.
        
        Args:
            text: WEBVTT text
            
        Returns:
            Cleaned text with just the transcript content
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        skip_next = False
        for line in lines:
            # Skip WEBVTT header
            if line.startswith("WEBVTT"):
                continue
                
            # Skip empty lines
            if not line.strip():
                continue
                
            # Skip timestamp lines (using simple heuristic)
            if "-->" in line and any(c.isdigit() for c in line):
                skip_next = False  # Reset the flag
                continue
                
            # Skip line numbers (often appear before timestamps)
            if line.strip().isdigit():
                skip_next = True
                continue
                
            # Skip line if flag is set
            if skip_next:
                skip_next = False
                continue
                
            # Add line to cleaned content
            cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)

async def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="LLM-based text segmentation for large context understanding"
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
        default="output/llm_segmentation",
        help="Output directory (default: output/llm_segmentation)"
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.file_path):
        logger.error(f"File not found: {args.file_path}")
        return 1
    
    # Setup output directory
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    # Load text
    loader = TextLoader()
    document_id = f"doc_{timestamp}"
    document = loader.load_file(args.file_path, document_id=document_id)
    
    # Create LLM segmenter
    segmenter = LLMSegmenter(provider=args.provider)
    
    # Segment text
    logger.info(f"Starting LLM-based segmentation for {args.file_path}")
    collection = await segmenter.segment_text(
        document.text, 
        document_id=document_id,
        language=document.language
    )
    
    # Save segments
    output_file = os.path.join(output_dir, "segments.json")
    with open(output_file, "w", encoding="utf-8") as f:
        segments_data = [segment.to_dict() for segment in collection.segments.values()]
        json.dump(segments_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Segmentation complete. Created {len(collection.segments)} segments.")
    logger.info(f"Results saved to: {output_file}")
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())