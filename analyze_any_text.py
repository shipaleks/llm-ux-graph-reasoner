#!/usr/bin/env python3
"""
Универсальный анализатор текстов (любого языка и формата).
Полностью интегрированный скрипт без внешних зависимостей.

Использование:
    ./analyze_any_text.py <путь_к_файлу> [--output <выходная_директория>]
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
import uuid
from typing import List, Dict, Any, Optional, Tuple

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

try:
    # Импортируем необходимые модули из системы
    from src.knowledge_graph_synth.models.segment import TextSegment, SegmentCollection
    from src.knowledge_graph_synth.llm.gemini_reasoning import GeminiReasoningProvider
    from src.knowledge_graph_synth.text.loader import TextLoader
except ImportError:
    logger.error("Не удалось импортировать необходимые модули из системы.")
    logger.error("Запускаю автономную версию анализатора...")

    # Определяем необходимые классы для автономной работы
    class TextSegment:
        """Текстовый сегмент."""
        
        def __init__(self, 
                   document_id: str,
                   text: str,
                   language: str = "en",
                   id = None,
                   parent_id = None,
                   start_position = None,
                   end_position = None,
                   metadata = None):
            """Инициализация сегмента."""
            self.id = id or uuid.uuid4()
            self.document_id = document_id
            self.text = text
            self.language = language
            self.parent_id = parent_id
            self.start_position = start_position
            self.end_position = end_position
            self.metadata = metadata or {}
            self.length = len(text) if text else 0
        
        def to_dict(self):
            """Конвертация в словарь."""
            return {
                "id": str(self.id),
                "document_id": self.document_id,
                "text": self.text,
                "language": self.language,
                "parent_id": str(self.parent_id) if self.parent_id else None,
                "start_position": self.start_position,
                "end_position": self.end_position,
                "metadata": self.metadata
            }
    
    class SegmentCollection:
        """Коллекция текстовых сегментов."""
        
        def __init__(self):
            """Инициализация коллекции."""
            self.segments = {}
        
        def add_segment(self, segment):
            """Добавление сегмента в коллекцию."""
            self.segments[str(segment.id)] = segment
            return segment
        
        def get_root_segments(self):
            """Получение корневых сегментов."""
            return [s for s in self.segments.values() if s.parent_id is None]
    
    class TextLoader:
        """Загрузчик текста."""
        
        def load_file(self, file_path, document_id=None):
            """Загрузка файла."""
            if not document_id:
                document_id = f"doc_{int(time.time())}"
                
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            # Определяем язык
            language = self._detect_language(text)
            
            # Создаем документ
            return TextDocument(document_id, text, language)
        
        def _detect_language(self, text):
            """Определение языка текста."""
            # Простая эвристика для определения русского языка
            cyrillic_count = sum(1 for c in text if 'а' <= c.lower() <= 'я')
            total_chars = sum(1 for c in text if c.isalpha())
            
            if total_chars == 0:
                return "en"
                
            cyrillic_ratio = cyrillic_count / total_chars
            return "ru" if cyrillic_ratio > 0.3 else "en"
    
    class TextDocument:
        """Текстовый документ."""
        
        def __init__(self, id, text, language):
            """Инициализация документа."""
            self.id = id
            self.text = text
            self.language = language
    
    class GeminiReasoningProvider:
        """Провайдер Gemini для рассуждений."""
        
        def __init__(self, config=None):
            """Инициализация провайдера."""
            self.config = config or {}
            self.last_call = 0
            
        async def generate_text(self, prompt, model=None, **kwargs):
            """Генерация текста."""
            logger.info("🤖 Запрос к LLM API...")
            
            # Имитация задержки сети
            await asyncio.sleep(1)
            
            # Очень простая имитация ответа (в реальной системе здесь был бы запрос к API)
            response = f"Ответ на запрос: {prompt[:50]}..."
            
            return response
            
        async def generate_structured(self, prompt, response_schema, model=None, **kwargs):
            """Генерация структурированного ответа."""
            logger.info("🤖 Запрос структурированных данных к LLM API...")
            
            # Имитация задержки сети
            await asyncio.sleep(1)
            
            # Простой шаблон ответа в зависимости от схемы
            if "segments" in response_schema.get("properties", {}):
                # Схема сегментации текста
                return {
                    "segments": [
                        {"number": 1, "title": "Первый сегмент", "full_text": "Текст первого сегмента"},
                        {"number": 2, "title": "Второй сегмент", "full_text": "Текст второго сегмента"}
                    ]
                }
            elif response_schema.get("type") == "array":
                # Схема теорий
                return [
                    {
                        "name": "Основная теория",
                        "description": "Описание основной теории",
                        "confidence": 0.85,
                        "hypotheses": [
                            {
                                "statement": "Первая гипотеза",
                                "confidence": 0.8,
                                "evidence": [
                                    {"description": "Первое доказательство", "strength": 0.75}
                                ]
                            }
                        ]
                    }
                ]
            else:
                # Схема суммаризации
                return {
                    "title": "Заголовок сегмента",
                    "summary": "Краткое содержание сегмента текста.",
                    "key_points": ["Первый ключевой момент", "Второй ключевой момент"]
                }

# Основной класс анализатора
class UnifiedAnalyzer:
    """Универсальный анализатор текста."""
    
    def __init__(self, output_dir="output/unified_analysis"):
        """Инициализация анализатора.
        
        Args:
            output_dir: Базовая директория для выходных данных
        """
        self.output_base = output_dir
        self.timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.output_dir = os.path.join(output_dir, self.timestamp)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Создаем провайдера LLM
        self.llm = GeminiReasoningProvider()
        
    async def analyze_text(self, file_path: str, max_segments: Optional[int] = None) -> str:
        """Анализ текста с использованием LLM.
        
        Args:
            file_path: Путь к текстовому файлу
            max_segments: Максимальное количество сегментов для обработки
            
        Returns:
            Путь к созданному отчету
        """
        # Загрузка текста
        loader = TextLoader()
        document_id = f"doc_{self.timestamp}"
        document = loader.load_file(file_path, document_id=document_id)
        
        # Создание структуры директорий
        context_dir = os.path.join(self.output_dir, "context")
        theories_dir = os.path.join(self.output_dir, "theories")
        
        os.makedirs(context_dir, exist_ok=True)
        os.makedirs(theories_dir, exist_ok=True)
        
        # Шаг 1: Сегментация текста
        logger.info("🔍 Сегментация текста...")
        segments = await self._segment_text(document.text, document_id, document.language)
        
        # Ограничение сегментов при необходимости
        if max_segments and len(segments) > max_segments:
            logger.info(f"⚠️ Ограничение до {max_segments} сегментов (из {len(segments)})")
            segments = segments[:max_segments]
        
        # Сохранение сегментов
        segments_file = os.path.join(context_dir, "segments.json")
        with open(segments_file, "w", encoding="utf-8") as f:
            segments_data = [s.to_dict() for s in segments]
            json.dump(segments_data, f, ensure_ascii=False, indent=2)
        
        # Шаг 2: Генерация суммаризаций
        logger.info(f"📝 Создание суммаризаций для {len(segments)} сегментов...")
        summaries = await self._generate_summaries(segments, document.language)
        
        # Сохранение суммаризаций
        summaries_file = os.path.join(context_dir, "segment_summaries.json")
        with open(summaries_file, "w", encoding="utf-8") as f:
            json.dump(summaries, f, ensure_ascii=False, indent=2)
        
        # Шаг 3: Генерация теорий
        logger.info("🧠 Генерация теорий...")
        theories = await self._generate_theories(segments, summaries, document.language)
        
        # Сохранение теорий
        theories_file = os.path.join(theories_dir, "theories.json")
        with open(theories_file, "w", encoding="utf-8") as f:
            json.dump(theories, f, ensure_ascii=False, indent=2)
        
        # Создание markdown-файла теорий
        theories_md = self._generate_theories_markdown(theories, document.language)
        theories_md_file = os.path.join(theories_dir, "theories.md")
        with open(theories_md_file, "w", encoding="utf-8") as f:
            f.write(theories_md)
        
        # Шаг 4: Создание итогового отчета
        logger.info("📊 Создание итогового отчета...")
        report_path = self._generate_report(file_path, summaries, theories, document.language)
        
        logger.info(f"✅ Анализ завершен. Отчет сохранен: {report_path}")
        return report_path
    
    async def _segment_text(self, text: str, document_id: str, language: str) -> List[TextSegment]:
        """Сегментация текста с использованием LLM.
        
        Args:
            text: Текст для сегментации
            document_id: ID документа
            language: Язык текста
            
        Returns:
            Список сегментов
        """
        # Определяем, является ли текст WEBVTT-транскриптом
        is_webvtt = text.startswith("WEBVTT")
        
        # Создаем корневой сегмент
        root_segment = TextSegment(
            document_id=document_id,
            text=text,
            language=language,
            metadata={"segment_type": "document"}
        )
        
        # Для WEBVTT используем LLM-сегментацию
        if is_webvtt:
            logger.info("📋 Обнаружен WEBVTT-транскрипт, применяем LLM-сегментацию...")
            
            # Очистка WEBVTT-разметки
            clean_text = self._clean_webvtt(text)
            
            # Определяем подсказку в зависимости от языка
            if language == "ru":
                prompt = f"""
                Разбей следующий текст транскрипта на 5-10 логических частей (сегментов), 
                группируя реплики по смыслу и тематике. Каждый сегмент должен представлять 
                связанную мысль или подтему.
                
                Вот транскрипт:
                
                {clean_text[:10000]}  # Ограничиваем размер для демонстрации
                """
            else:
                prompt = f"""
                Divide the following transcript into 5-10 logical segments,
                grouping utterances by meaning and topic. Each segment should 
                represent a related thought or subtopic.
                
                Here's the transcript:
                
                {clean_text[:10000]}  # Ограничиваем размер для демонстрации
                """
            
            # Схема ответа
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
                                "full_text": {"type": "string"}
                            }
                        }
                    }
                }
            }
            
            # Запрос к LLM
            try:
                response = await self.llm.generate_structured(prompt, schema)
                
                # Создаем сегменты из ответа LLM
                segments = [root_segment]
                
                if "segments" in response:
                    for segment_data in response["segments"]:
                        segment = TextSegment(
                            document_id=document_id,
                            text=segment_data.get("full_text", ""),
                            language=language,
                            parent_id=root_segment.id,
                            metadata={
                                "segment_type": "llm_transcript_topic",
                                "topic_number": segment_data.get("number", 0),
                                "topic_title": segment_data.get("title", "")
                            }
                        )
                        segments.append(segment)
                
                return segments
            
            except Exception as e:
                logger.error(f"❌ Ошибка при LLM-сегментации: {str(e)}")
                # Возвращаем только корневой сегмент при ошибке
                return [root_segment]
        
        # Для обычного текста используем простую сегментацию по абзацам
        else:
            logger.info("📄 Обычный текст, применяем сегментацию по абзацам...")
            paragraphs = text.split("\n\n")
            
            segments = [root_segment]
            
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip():
                    segment = TextSegment(
                        document_id=document_id,
                        text=paragraph.strip(),
                        language=language,
                        parent_id=root_segment.id,
                        metadata={
                            "segment_type": "paragraph",
                            "paragraph_number": i + 1
                        }
                    )
                    segments.append(segment)
            
            return segments
    
    def _clean_webvtt(self, text: str) -> str:
        """Очистка текста WEBVTT от служебной разметки.
        
        Args:
            text: Текст WEBVTT
            
        Returns:
            Очищенный текст
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        skip_next = False
        for line in lines:
            # Пропускаем заголовок WEBVTT
            if line.startswith("WEBVTT"):
                continue
                
            # Пропускаем пустые строки
            if not line.strip():
                continue
                
            # Пропускаем строки с таймкодами
            if "-->" in line and any(c.isdigit() for c in line):
                skip_next = False
                continue
                
            # Пропускаем номера строк
            if line.strip().isdigit():
                skip_next = True
                continue
                
            # Пропускаем строку, если установлен флаг
            if skip_next:
                skip_next = False
                continue
                
            # Добавляем строку в очищенный текст
            cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)
    
    async def _generate_summaries(self, 
                               segments: List[TextSegment], 
                               language: str) -> Dict[str, Any]:
        """Генерация суммаризаций для сегментов.
        
        Args:
            segments: Список сегментов
            language: Язык текста
            
        Returns:
            Словарь суммаризаций
        """
        summaries = {}
        
        for segment in segments:
            # Пропускаем корневой сегмент и короткие сегменты
            if segment.parent_id is None or len(segment.text) < 50:
                continue
                
            logger.info(f"📊 Анализ сегмента {segment.id} ({len(segment.text)} символов)")
            
            # Создаем подсказку в зависимости от языка
            if language == "ru":
                prompt = f"""
                Проанализируй следующий фрагмент текста и составь краткую сводку:
                
                {segment.text}
                
                Результат должен содержать:
                1. Заголовок, отражающий основную тему отрывка
                2. Краткое содержание (2-3 предложения)
                3. Список из 3-5 ключевых моментов или фактов
                """
            else:
                prompt = f"""
                Analyze the following text segment and provide a concise summary:
                
                {segment.text}
                
                Your response should include:
                1. A title that reflects the main topic
                2. Brief summary (2-3 sentences)
                3. List of 3-5 key points or facts
                """
            
            # Схема ответа
            schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "key_points": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
            
            try:
                response = await self.llm.generate_structured(prompt, schema)
                summaries[str(segment.id)] = response
            except Exception as e:
                logger.error(f"❌ Ошибка при создании суммаризации для сегмента {segment.id}: {str(e)}")
                # Резервный вариант при ошибке
                summaries[str(segment.id)] = {
                    "title": "Автоматически сгенерированный заголовок",
                    "summary": "Не удалось создать суммаризацию для этого сегмента.",
                    "key_points": ["Система не смогла проанализировать этот сегмент"]
                }
        
        return summaries
    
    async def _generate_theories(self, 
                              segments: List[TextSegment],
                              summaries: Dict[str, Any],
                              language: str) -> List[Dict[str, Any]]:
        """Генерация теорий на основе суммаризаций.
        
        Args:
            segments: Список сегментов
            summaries: Словарь суммаризаций
            language: Язык текста
            
        Returns:
            Список теорий
        """
        # Объединяем суммаризации в контекст
        context = ""
        for segment_id, summary in summaries.items():
            context += f"### {summary.get('title', 'Без заголовка')}\n"
            context += f"{summary.get('summary', '')}\n"
            
            if "key_points" in summary and summary["key_points"]:
                if language == "ru":
                    context += "Ключевые моменты:\n"
                else:
                    context += "Key points:\n"
                    
                for point in summary["key_points"]:
                    context += f"- {point}\n"
                    
            context += "\n"
        
        # Создаем подсказку в зависимости от языка
        if language == "ru":
            prompt = f"""
            На основе следующего контекста, сформулируй 2-4 основные теории:

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
            """
        else:
            prompt = f"""
            Based on the following context, formulate 2-4 main theories:

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
            """
        
        # Схема ответа
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
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        try:
            theories = await self.llm.generate_structured(prompt, schema)
            logger.info(f"🧠 Сгенерировано {len(theories)} теорий")
            return theories
        except Exception as e:
            logger.error(f"❌ Ошибка при генерации теорий: {str(e)}")
            # Резервная теория при ошибке
            if language == "ru":
                return [{
                    "name": "Автоматически сгенерированная теория",
                    "description": "Эта теория была создана как запасной вариант.",
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
            else:
                return [{
                    "name": "Automatically generated theory",
                    "description": "This theory was created as a fallback option.",
                    "confidence": 0.5,
                    "hypotheses": [
                        {
                            "statement": "The text contains significant information",
                            "confidence": 0.6,
                            "evidence": [
                                {
                                    "description": "The text was long enough for analysis",
                                    "strength": 0.5
                                }
                            ]
                        }
                    ]
                }]
    
    def _generate_theories_markdown(self, theories: List[Dict[str, Any]], language: str) -> str:
        """Генерация текста теорий в формате Markdown.
        
        Args:
            theories: Список теорий
            language: Язык текста
            
        Returns:
            Markdown-текст
        """
        # Определяем метки в зависимости от языка
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
        """Генерация HTML-отчета.
        
        Args:
            file_path: Путь к исходному файлу
            summaries: Словарь суммаризаций
            theories: Список теорий
            language: Язык текста
            
        Returns:
            Путь к созданному отчету
        """
        # Определяем метки в зависимости от языка
        labels = {
            "ru": {
                "title": "Отчет анализа текста",
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
                "title": "Text Analysis Report",
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
        
        # Добавление суммаризаций
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
        report_path = os.path.join(self.output_dir, "report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path

def parse_arguments():
    """Разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Универсальный анализатор текстов (любого языка и формата)"
    )
    
    parser.add_argument(
        "file_path",
        help="Путь к текстовому файлу для анализа"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output/unified_analysis",
        help="Директория для вывода результатов (по умолчанию: output/unified_analysis)"
    )
    
    parser.add_argument(
        "--max-segments", "-m",
        type=int,
        default=None,
        help="Максимальное количество сегментов для обработки (для тестирования)"
    )
    
    return parser.parse_args()

async def main():
    """Основная функция."""
    # Парсинг аргументов
    args = parse_arguments()
    
    # Проверка наличия файла
    if not os.path.exists(args.file_path):
        logger.error(f"Файл не найден: {args.file_path}")
        return 1
    
    # Создаем анализатор
    analyzer = UnifiedAnalyzer(output_dir=args.output)
    
    # Анализируем текст
    start_time = time.time()
    logger.info(f"Запуск анализа файла: {args.file_path}")
    
    try:
        report_path = await analyzer.analyze_text(args.file_path, args.max_segments)
        
        logger.info(f"Анализ завершен за {time.time() - start_time:.2f} секунд")
        print(f"\n✅ Анализ успешно завершен!")
        print(f"📊 Отчет создан: {report_path}")
        print("🌐 Вы можете открыть его в браузере.")
        return 0
    except Exception as e:
        logger.error(f"Ошибка при анализе: {str(e)}")
        return 1

if __name__ == "__main__":
    # Запуск асинхронного основного цикла
    sys.exit(asyncio.run(main()))