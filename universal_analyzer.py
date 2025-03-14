#!/usr/bin/env python3
"""
Универсальный анализатор текста с поддержкой всех языков и форматов.
Объединяет традиционный подход с построением графа знаний и улучшенный 
метод на базе Gemini 2.0 для анализа сложных текстов, включая
русскоязычные WEBVTT транскрипты.

Использование:
    ./universal_analyzer.py <путь_к_файлу> [--output <директория>] [--mode <режим>]
    
Режимы:
    standard - стандартный подход с построением графа знаний (по умолчанию)
    gemini - прямой анализ с помощью Gemini 2.0
    combined - комбинированный подход (сначала стандартный, затем Gemini)
"""

import os
import sys
import json
import logging
import argparse
import time
import subprocess
import requests
import glob
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Настройка Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.error("API ключ не найден. Убедитесь, что файл .env содержит GOOGLE_API_KEY.")
    sys.exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

def parse_arguments():
    """Разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Универсальный анализатор текста с поддержкой всех языков и форматов"
    )
    
    parser.add_argument(
        "file_path",
        help="Путь к текстовому файлу для анализа"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output/universal",
        help="Директория для вывода результатов (по умолчанию: output/universal)"
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["standard", "gemini", "combined"],
        default="combined",
        help="Режим анализа (standard/gemini/combined, по умолчанию: combined)"
    )
    
    parser.add_argument(
        "--max-segments", "-s",
        type=int,
        default=None,
        help="Максимальное количество сегментов для обработки (для тестирования)"
    )
    
    return parser.parse_args()

def run_standard_analysis(file_path, output_dir, max_segments=None):
    """Запуск стандартного анализа с построением графа знаний."""
    logger.info(f"Запуск стандартного анализа для файла: {file_path}")
    
    # Создаем директорию для вывода
    os.makedirs(output_dir, exist_ok=True)
    
    # Формируем команду для анализа с дополнительными параметрами для повышения шансов успеха
    cmd = [
        "./analyze_text.py",
        file_path,
        "--provider", "gemini", 
        "--theories",               # Создание теорий
        "--output", output_dir
    ]
    
    # Добавляем ограничение по сегментам, если указано
    if max_segments:
        cmd.extend(["--max-segments", str(max_segments)])
    
    # Запускаем анализ
    start_time = time.time()
    logger.info(f"Запуск команды: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        elapsed_time = time.time() - start_time
        logger.info(f"Стандартный анализ завершен за {elapsed_time:.2f} секунд")
        
        # Поиск созданной директории с результатами
        # Проверяем output_dir для созданных директорий в формате timestamp (YYYYMMDD_HHMMSS)
        output_dirs = sorted(glob.glob(f"{output_dir}/[0-9]*_[0-9]*"), reverse=True)
        
        if output_dirs:
            output_dir = output_dirs[0]
            logger.info(f"Обнаружена выходная директория: {output_dir}")
            
            # Проверка наличия отчетов
            if os.path.exists(os.path.join(output_dir, "context")):
                logger.info("Найден контекстный анализ")
            else:
                logger.warning("Контекстный анализ не найден")
                
            if os.path.exists(os.path.join(output_dir, "entities")):
                logger.info("Найдены извлеченные сущности")
            else:
                logger.warning("Сущности не найдены")
                
            if os.path.exists(os.path.join(output_dir, "relationships")):
                logger.info("Найдены извлеченные отношения")
            else:
                logger.warning("Отношения не найдены")
                
            if os.path.exists(os.path.join(output_dir, "graphs")):
                logger.info("Найдены графы знаний")
            else:
                logger.warning("Графы знаний не найдены")
                
            if os.path.exists(os.path.join(output_dir, "theories")):
                logger.info("Найдены теории")
            else:
                logger.warning("Теории не найдены")
            
            return output_dir, True, result.stdout
        else:
            logger.error("Не удалось найти выходную директорию")
            return None, False, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при выполнении стандартного анализа: {str(e)}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return None, False, e.stderr
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        return None, False, str(e)

def detect_language(text):
    """Определение языка текста."""
    sample = text[:10000]  # Берем часть текста для анализа
    cyrillic_count = sum(1 for c in sample if 'а' <= c.lower() <= 'я')
    total_chars = sum(1 for c in sample if c.isalpha())
    
    if total_chars == 0:
        return "en"
        
    cyrillic_ratio = cyrillic_count / total_chars
    return "ru" if cyrillic_ratio > 0.3 else "en"

def clean_webvtt(text):
    """Очистка WEBVTT от метаданных и временных меток."""
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

async def run_gemini_analysis(file_path, output_dir):
    """Запуск анализа с использованием Gemini 2.0."""
    logger.info(f"Запуск анализа Gemini 2.0 для файла: {file_path}")
    
    # Создание выходного каталога
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    gemini_output_dir = os.path.join(output_dir, f"gemini_{timestamp}")
    os.makedirs(gemini_output_dir, exist_ok=True)
    
    # Чтение файла
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        return None, False
    
    # Определение языка и формата
    language = detect_language(text)
    is_russian = language == "ru"
    is_webvtt = text.startswith("WEBVTT")
    
    logger.info(f"Определен язык: {'русский' if is_russian else 'английский'}")
    logger.info(f"Формат WEBVTT: {'да' if is_webvtt else 'нет'}")
    
    # Очистка текста WEBVTT
    if is_webvtt:
        text = clean_webvtt(text)
    
    # Создание модели Gemini 2.0
    model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')
    
    # Генерация суммаризаций
    logger.info("Генерация суммаризаций...")
    if is_russian:
        summary_prompt = f"""
        Проанализируй следующий текст и сделай подробную суммаризацию. 
        Включи заголовок, основные тезисы и 5-7 ключевых моментов.
        
        Текст:
        {text[:50000]}  # Увеличиваем размер контекста для Gemini 2.0
        """
    else:
        summary_prompt = f"""
        Analyze the following text and provide a detailed summary. 
        Include a title, main points, and 5-7 key insights.
        
        Text:
        {text[:50000]}  # Increased context size for Gemini 2.0
        """
    
    try:
        response = model.generate_content(summary_prompt)
        summary_response = response.text
    except Exception as e:
        logger.error(f"Ошибка при запросе к Gemini: {e}")
        summary_response = "Произошла ошибка при генерации суммаризации."
    
    # Генерация теорий
    logger.info("Генерация теорий...")
    if is_russian:
        theory_prompt = f"""
        На основе следующего текста, сформулируй 3-5 основных теорий или гипотез.
        Для каждой теории укажи:
        1. Название теории
        2. Описание (3-5 предложений)
        3. Степень уверенности (0-100%)
        4. 2-3 гипотезы, подтверждающие теорию
        5. 1-2 подтверждающих факта для каждой гипотезы
        
        Представь ответ в структурированном формате.
        
        Текст:
        {text[:50000]}  # Увеличиваем размер контекста для Gemini 2.0
        """
    else:
        theory_prompt = f"""
        Based on the following text, formulate 3-5 main theories.
        For each theory, include:
        1. Theory name
        2. Description (3-5 sentences)
        3. Confidence level (0-100%)
        4. 2-3 hypotheses supporting the theory
        5. 1-2 supporting facts for each hypothesis
        
        Present your answer in a structured format.
        
        Text:
        {text[:50000]}  # Increased context size for Gemini 2.0
        """
    
    try:
        response = model.generate_content(theory_prompt)
        theory_response = response.text
    except Exception as e:
        logger.error(f"Ошибка при запросе к Gemini: {e}")
        theory_response = "Произошла ошибка при генерации теорий."
    
    # Создание HTML-отчета
    if is_russian:
        title = "Анализ текста с Gemini 2.0"
        summary_title = "Суммаризация"
        theory_title = "Теории и гипотезы"
        file_label = "Файл"
        date_label = "Дата анализа"
    else:
        title = "Text Analysis with Gemini 2.0"
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
                line-height: 1.5;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        
        <div class="metadata">
            <p><strong>{file_label}:</strong> {os.path.basename(file_path)}</p>
            <p><strong>{date_label}:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Model:</strong> Gemini 2.0</p>
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
    report_path = os.path.join(gemini_output_dir, "report.html")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Сохранение JSON результатов для потенциального использования
    results = {
        "summary": summary_response,
        "theories": theory_response,
        "metadata": {
            "file": os.path.basename(file_path),
            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "language": language,
            "is_webvtt": is_webvtt,
            "model": "gemini-2.0-pro-exp-02-05"
        }
    }
    
    json_path = os.path.join(gemini_output_dir, "results.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Анализ Gemini завершен, отчет сохранен: {report_path}")
    return gemini_output_dir, True

def create_combined_report(standard_dir, gemini_dir, output_dir, file_path):
    """Создание объединенного отчета из результатов обоих подходов."""
    if not standard_dir and not gemini_dir:
        logger.error("Отсутствуют директории с результатами для создания объединенного отчета")
        return None
        
    # Проверяем наличие результатов стандартного анализа
    has_standard_graph = False
    has_standard_theories = False
    has_standard_context = False
    
    if standard_dir:
        # Проверка наличия графов
        graph_dir = os.path.join(standard_dir, "graphs")
        has_standard_graph = os.path.exists(graph_dir) and any(f.endswith(".html") for f in os.listdir(graph_dir)) if os.path.exists(graph_dir) else False
        
        # Проверка наличия теорий
        theories_dir = os.path.join(standard_dir, "theories")
        has_standard_theories = os.path.exists(theories_dir) and any(f.endswith(".md") for f in os.listdir(theories_dir)) if os.path.exists(theories_dir) else False
        
        # Проверка наличия контекстного анализа
        context_dir = os.path.join(standard_dir, "context")
        summaries_file = os.path.join(context_dir, "segment_summaries.json")
        has_standard_context = os.path.exists(summaries_file)
        
        if has_standard_context:
            logger.info("Найден контекстный анализ в стандартном режиме")
    
    # Проверяем наличие результатов Gemini
    has_gemini_results = False
    gemini_context = {}
    
    if gemini_dir:
        json_path = os.path.join(gemini_dir, "results.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    gemini_context = json.load(f)
                has_gemini_results = True
                logger.info("Найдены результаты анализа Gemini")
            except Exception as e:
                logger.error(f"Ошибка при чтении данных Gemini: {e}")
    
    # Если есть хотя бы какие-то результаты, продолжаем
    if not (has_standard_graph or has_standard_theories or has_standard_context or has_gemini_results):
        logger.error("Нет результатов для объединения в отчете")
        return None
    
    # Определение языка текста
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text_sample = f.read(10000)
        language = detect_language(text_sample)
    except Exception:
        language = "en"  # По умолчанию английский
    
    is_russian = language == "ru"
    
    # Установка заголовков в зависимости от языка
    if is_russian:
        title = "Комплексный анализ текста"
        standard_title = "Стандартный анализ (граф знаний)"
        gemini_title = "Анализ Gemini 2.0"
        summary_title = "Суммаризация"
        theory_title = "Теории и гипотезы"
        graph_title = "Граф знаний"
        file_label = "Файл"
        date_label = "Дата анализа"
        no_data = "Данные отсутствуют"
    else:
        title = "Comprehensive Text Analysis"
        standard_title = "Standard Analysis (Knowledge Graph)"
        gemini_title = "Gemini 2.0 Analysis"
        summary_title = "Summary"
        theory_title = "Theories and Hypotheses"
        graph_title = "Knowledge Graph"
        file_label = "File"
        date_label = "Analysis Date"
        no_data = "No data available"
    
    # Поиск результатов стандартного анализа
    standard_graph_path = None
    standard_theories_path = None
    
    if standard_dir and os.path.exists(standard_dir):
        graph_dir = os.path.join(standard_dir, "graphs")
        theories_dir = os.path.join(standard_dir, "theories")
        
        if os.path.exists(graph_dir):
            graph_files = [f for f in os.listdir(graph_dir) if f.endswith(".html")]
            if graph_files:
                standard_graph_path = os.path.join(graph_dir, graph_files[0])
        
        if os.path.exists(theories_dir):
            theory_files = [f for f in os.listdir(theories_dir) if f.endswith(".md")]
            if theory_files:
                standard_theories_path = os.path.join(theories_dir, theory_files[0])
    
    # Получение данных из Gemini-анализа
    gemini_summary = no_data
    gemini_theories = no_data
    
    if gemini_dir and os.path.exists(gemini_dir):
        json_path = os.path.join(gemini_dir, "results.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                    gemini_summary = results.get("summary", no_data)
                    gemini_theories = results.get("theories", no_data)
            except Exception as e:
                logger.error(f"Ошибка при чтении данных Gemini: {e}")
    
    # Чтение стандартных теорий
    standard_theories = no_data
    if standard_theories_path and os.path.exists(standard_theories_path):
        try:
            with open(standard_theories_path, 'r', encoding='utf-8') as f:
                standard_theories = f.read()
        except Exception as e:
            logger.error(f"Ошибка при чтении стандартных теорий: {e}")
            
    # Чтение контекстного анализа, если теории недоступны
    context_summaries = {}
    if has_standard_context and standard_theories == no_data:
        context_file = os.path.join(standard_dir, "context", "segment_summaries.json")
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                context_summaries = json.load(f)
                logger.info(f"Загружено {len(context_summaries)} суммаризаций из контекстного анализа")
                
                # Если есть контекстный анализ, но нет теорий, создаем текст из суммаризаций
                if context_summaries and standard_theories == no_data:
                    context_text = []
                    for segment_id, summary in context_summaries.items():
                        if "title" in summary and "summary" in summary:
                            context_text.append(f"## {summary['title']}\n\n{summary['summary']}\n")
                            if "key_points" in summary and summary["key_points"]:
                                context_text.append("### Ключевые моменты:\n")
                                for point in summary["key_points"]:
                                    context_text.append(f"- {point}\n")
                                context_text.append("\n")
                    
                    if context_text:
                        standard_theories = "# Суммаризация контекстного анализа\n\n" + "\n".join(context_text)
                        logger.info("Создана суммаризация из контекстного анализа")
        except Exception as e:
            logger.error(f"Ошибка при чтении контекстного анализа: {e}")
    
    # Формирование относительных путей для встраивания
    standard_graph_embed = ""
    if standard_graph_path:
        # Получаем относительный путь от выходной директории
        rel_path = os.path.relpath(standard_graph_path, output_dir)
        standard_graph_embed = f"""
        <div class="iframe-container">
            <iframe src="{rel_path}" width="100%" height="600px" frameborder="0"></iframe>
        </div>
        """
    else:
        standard_graph_embed = f"<p>{no_data}</p>"
    
    # Создание объединенного отчета
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    combined_dir = os.path.join(output_dir, f"combined_{timestamp}")
    os.makedirs(combined_dir, exist_ok=True)
    
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
            h1, h2, h3 {{
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
                line-height: 1.5;
                font-size: 14px;
            }}
            .section {{
                margin-bottom: 30px;
                border-bottom: 1px solid #eee;
                padding-bottom: 20px;
            }}
            .iframe-container {{
                width: 100%;
                margin: 20px 0;
            }}
            .side-by-side {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
            }}
            .side-by-side > div {{
                flex: 1;
                min-width: 300px;
            }}
            .comparison-header {{
                background-color: #e8f4fc;
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 15px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        
        <div class="metadata">
            <p><strong>{file_label}:</strong> {os.path.basename(file_path)}</p>
            <p><strong>{date_label}:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h2>{gemini_title} - {summary_title}</h2>
            <div class="container">
                <pre>{gemini_summary}</pre>
            </div>
        </div>
        
        <div class="section">
            <h2>{theory_title}</h2>
            
            <div class="side-by-side">
                <div>
                    <div class="comparison-header">{standard_title}</div>
                    <div class="container">
                        <pre>{standard_theories}</pre>
                    </div>
                </div>
                
                <div>
                    <div class="comparison-header">{gemini_title}</div>
                    <div class="container">
                        <pre>{gemini_theories}</pre>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>{graph_title}</h2>
            {standard_graph_embed}
        </div>
    </body>
    </html>
    """
    
    # Сохранение отчета
    report_path = os.path.join(combined_dir, "combined_report.html")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Создан объединенный отчет: {report_path}")
    return report_path

async def main():
    """Основная функция."""
    args = parse_arguments()
    
    # Проверка существования файла
    if not os.path.exists(args.file_path):
        logger.error(f"Файл не найден: {args.file_path}")
        return 1
    
    # Создание базовой выходной директории
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    standard_dir = None
    gemini_dir = None
    
    # Запуск анализа в зависимости от режима
    if args.mode in ["standard", "combined"]:
        logger.info("Запуск стандартного анализа...")
        standard_dir, standard_success, _ = run_standard_analysis(
            args.file_path, 
            os.path.join(output_dir, "standard"),
            args.max_segments
        )
    
    if args.mode in ["gemini", "combined"]:
        logger.info("Запуск анализа с Gemini 2.0...")
        import asyncio
        gemini_dir, gemini_success = await run_gemini_analysis(
            args.file_path, 
            output_dir
        )
    
    # Создание отчета в зависимости от режима
    if args.mode == "combined":
        # Проверяем, есть ли результаты стандартного анализа и Gemini
        has_standard_results = False
        if standard_dir:
            # Проверяем наличие графов или теорий
            has_context = os.path.exists(os.path.join(standard_dir, "context"))
            has_graphs = os.path.exists(os.path.join(standard_dir, "graphs"))
            has_theories = os.path.exists(os.path.join(standard_dir, "theories"))
            has_standard_results = has_context or has_graphs or has_theories
            
            if not (has_graphs or has_theories):
                logger.warning("Стандартный анализ не создал графы или теории")
        
        # Если есть хотя бы один результат, создаем объединенный отчет
        if gemini_dir or (standard_dir and has_standard_results):
            logger.info("Создание объединенного отчета...")
            combined_report = create_combined_report(
                standard_dir, 
                gemini_dir, 
                output_dir, 
                args.file_path
            )
            
            if combined_report:
                logger.info(f"Анализ успешно завершен!")
                print(f"\n✅ Комплексный анализ успешно завершен!")
                print(f"📊 Объединенный отчет создан: {combined_report}")
                print("🌐 Вы можете открыть его в браузере.")
                return 0
        
        # Если нет результатов стандартного анализа, но есть Gemini
        if gemini_dir:
            print(f"\n✅ Анализ успешно завершен!")
            if standard_dir:
                print(f"⚠️ Стандартный анализ выполнен, но не создал графы или теории")
                print(f"📁 Результаты стандартного анализа доступны в: {standard_dir}")
            print(f"📊 Отчет Gemini 2.0 создан: {os.path.join(gemini_dir, 'report.html')}")
            print("🌐 Вы можете открыть его в браузере.")
            return 0
    elif args.mode == "standard" and standard_dir:
        # Находим любые отчеты, которые могли быть созданы
        reports = []
        if os.path.exists(os.path.join(standard_dir, "graphs")):
            graph_files = [os.path.join(standard_dir, "graphs", f) 
                         for f in os.listdir(os.path.join(standard_dir, "graphs")) 
                         if f.endswith(".html")]
            reports.extend(graph_files)
        
        if os.path.exists(os.path.join(standard_dir, "theories")):
            theory_files = [os.path.join(standard_dir, "theories", f) 
                          for f in os.listdir(os.path.join(standard_dir, "theories")) 
                          if f.endswith(".md") or f.endswith(".html")]
            reports.extend(theory_files)
        
        print(f"\n✅ Стандартный анализ успешно завершен!")
        print(f"📁 Результаты сохранены в: {standard_dir}")
        
        if reports:
            print("📄 Сгенерированные отчеты:")
            for report in reports:
                print(f"   - {report}")
        else:
            print("⚠️ Отчеты не были сгенерированы. Доступен только контекстный анализ.")
            ctx_file = os.path.join(standard_dir, "context", "segment_summaries.json")
            if os.path.exists(ctx_file):
                print(f"📊 Контекстный анализ: {ctx_file}")
    elif args.mode == "gemini" and gemini_dir:
        print(f"\n✅ Анализ Gemini 2.0 успешно завершен!")
        print(f"📊 Отчет создан: {os.path.join(gemini_dir, 'report.html')}")
        print("🌐 Вы можете открыть его в браузере.")
    
    return 0

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))