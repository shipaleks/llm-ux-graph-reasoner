#!/usr/bin/env python3
"""
Простой анализатор текста, работающий с любыми форматами, включая русскоязычные WEBVTT.

Использование:
    ./simple_analyzer.py <путь_к_файлу>
"""

import os
import sys
import json
import time
import logging
import asyncio
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Настройка Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.error("API ключ не найден. Убедитесь, что файл .env содержит GOOGLE_API_KEY.")
    sys.exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

async def analyze_text(file_path):
    """Анализирует текст с помощью Gemini."""
    
    # Создание выходного каталога
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = f"output/simple/{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Чтение файла
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        return 1
    
    # Определение языка
    is_russian = detect_russian(text)
    language = "ru" if is_russian else "en"
    logger.info(f"Определен язык: {'русский' if is_russian else 'английский'}")
    
    # Определение формата
    is_webvtt = text.startswith("WEBVTT")
    logger.info(f"Формат WEBVTT: {'да' if is_webvtt else 'нет'}")
    
    # Очистка текста WEBVTT
    if is_webvtt:
        text = clean_webvtt(text)
    
    # Создание модели - используем Gemini 2.0 с контекстным окном в 2 миллиона токенов
    model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')
    
    # Генерация суммаризаций
    logger.info("Генерация суммаризаций...")
    if is_russian:
        summary_prompt = f"""
        Проанализируй следующий текст и сделай подробную суммаризацию. 
        Включи заголовок, основные тезисы и 5-7 ключевых моментов.
        
        Текст:
        {text[:30000]}  # Ограничение по токенам
        """
    else:
        summary_prompt = f"""
        Analyze the following text and provide a detailed summary. 
        Include a title, main points, and 5-7 key insights.
        
        Text:
        {text[:30000]}  # Token limit
        """
    
    summary_response = await run_gemini(model, summary_prompt)
    
    # Генерация теорий
    logger.info("Генерация теорий...")
    if is_russian:
        theory_prompt = f"""
        На основе следующего текста, сформулируй 3-5 основных теорий или гипотез.
        Для каждой теории укажи:
        1. Название теории
        2. Описание (3-5 предложений)
        3. Степень уверенности (0-100%)
        4. 2-3 подтверждающих факта из текста
        
        Текст:
        {text[:30000]}  # Ограничение по токенам
        """
    else:
        theory_prompt = f"""
        Based on the following text, formulate 3-5 main theories or hypotheses.
        For each theory, include:
        1. Theory name
        2. Description (3-5 sentences)
        3. Confidence level (0-100%)
        4. 2-3 supporting facts from the text
        
        Text:
        {text[:30000]}  # Token limit
        """
    
    theory_response = await run_gemini(model, theory_prompt)
    
    # Создание HTML отчета
    report_path = os.path.join(output_dir, "report.html")
    
    # Создание HTML-отчета
    if is_russian:
        title = "Анализ текста"
        summary_title = "Суммаризация"
        theory_title = "Теории и гипотезы"
        file_label = "Файл"
        date_label = "Дата анализа"
    else:
        title = "Text Analysis"
        summary_title = "Summary"
        theory_title = "Theories and Hypotheses"
        file_label = "File"
        date_label = "Analysis Date"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="{language}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }}
            h1, h2 {{
                color: #2c3e50;
            }}
            .container {{
                background-color: #f5f9ff;
                border-left: 4px solid #4a90e2;
                margin-bottom: 20px;
                padding: 15px;
                border-radius: 4px;
            }}
            .metadata {{
                background-color: #f9f9f9;
                padding: 15px;
                border-left: 4px solid #2c3e50;
                margin-bottom: 20px;
            }}
            pre {{
                white-space: pre-wrap;
                background-color: #f8f8f8;
                padding: 10px;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        
        <div class="metadata">
            <p><strong>{file_label}:</strong> {os.path.basename(file_path)}</p>
            <p><strong>{date_label}:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <h2>{summary_title}</h2>
        <div class="container">
            <pre>{summary_response}</pre>
        </div>
        
        <h2>{theory_title}</h2>
        <div class="container">
            <pre>{theory_response}</pre>
        </div>
    </body>
    </html>
    """
    
    # Сохранение отчета
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Анализ завершен, отчет сохранен: {report_path}")
    print(f"\n✅ Анализ успешно завершен!")
    print(f"📊 Отчет создан: {report_path}")
    
    return 0

async def run_gemini(model, prompt):
    """Запускает Gemini с указанным запросом."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Ошибка при запросе к Gemini: {e}")
        return "Произошла ошибка при генерации ответа."

def detect_russian(text):
    """Определяет, является ли текст русскоязычным."""
    # Простая эвристика для определения русского языка
    sample = text[:10000]  # Берем часть текста для анализа
    cyrillic_count = sum(1 for c in sample if 'а' <= c.lower() <= 'я')
    total_chars = sum(1 for c in sample if c.isalpha())
    
    if total_chars == 0:
        return False
        
    cyrillic_ratio = cyrillic_count / total_chars
    return cyrillic_ratio > 0.3

def clean_webvtt(text):
    """Очищает текст WEBVTT от метаданных и временных меток."""
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

async def main():
    """Основная функция."""
    if len(sys.argv) < 2:
        print("Использование: ./simple_analyzer.py <путь_к_файлу>")
        return 1
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        logger.error(f"Файл не найден: {file_path}")
        return 1
    
    return await analyze_text(file_path)

if __name__ == "__main__":
    asyncio.run(main())