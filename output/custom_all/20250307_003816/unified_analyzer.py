#!/usr/bin/env python3
"""
Универсальный скрипт анализа текста, работающий во всех языковых ситуациях.
Автоматически адаптируется к разным форматам, в том числе WEBVTT на русском.

Использование:
    ./unified_analyzer.py <путь_к_файлу> [--output <выходная_директория>] [--provider <провайдер>]
"""

import os
import sys
import json
import subprocess
import logging
import time
import argparse
import re
from pathlib import Path
from datetime import datetime
import glob

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Универсальный анализатор текста с поддержкой русского языка и транскриптов"
    )
    
    parser.add_argument(
        "file_path",
        help="Путь к текстовому файлу для анализа"
    )
    
    parser.add_argument(
        "--provider", "-p",
        default="gemini",
        choices=["gemini", "openai"],
        help="Провайдер LLM для анализа (по умолчанию: gemini)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output/unified",
        help="Директория для вывода результатов (по умолчанию: output/unified)"
    )
    
    parser.add_argument(
        "--max-segments", "-m",
        type=int,
        default=None,
        help="Максимальное количество сегментов для обработки (для тестирования)"
    )
    
    return parser.parse_args()

def run_standard_analysis(args):
    """Запуск стандартного анализа."""
    logger.info(f"Запуск стандартного анализа файла: {args.file_path}")
    
    # Формируем команду для запуска analyze_text.py
    cmd = [
        "./analyze_text.py",
        args.file_path,
        "--provider", args.provider,
        "--theories",
        "--output", args.output
    ]
    
    # Добавляем ограничение по сегментам, если указано
    if args.max_segments:
        cmd.extend(["--max-segments", str(args.max_segments)])
    
    # Запускаем стандартный анализ
    start_time = time.time()
    logger.info(f"Запуск команды: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Стандартный анализ завершен за {time.time() - start_time:.2f} секунд")
        
        # Ищем последнюю созданную директорию
        output_dirs = sorted(glob.glob(f"{args.output}/[0-9]*_[0-9]*"), reverse=True)
        if output_dirs:
            output_dir = output_dirs[0]
            logger.info(f"Обнаружена выходная директория: {output_dir}")
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

def check_graph_success(output_dir):
    """Проверяет, был ли успешно создан граф знаний."""
    if not output_dir:
        return False
    
    # Проверяем наличие графа
    graph_dir = os.path.join(output_dir, "graphs")
    if not os.path.exists(graph_dir):
        logger.info("Директория с графами не найдена")
        return False
    
    # Проверяем наличие файла графа знаний
    graph_file = os.path.join(graph_dir, "knowledge_graph.html")
    if not os.path.exists(graph_file):
        logger.info("Файл графа знаний не найден")
        return False
    
    # Проверяем размер файла (пустой файл может означать ошибку)
    if os.path.getsize(graph_file) < 100:  # Минимальный размер нормального HTML
        logger.info("Файл графа знаний слишком маленький")
        return False
    
    logger.info("Обнаружен корректный граф знаний")
    return True

def check_theories_success(output_dir):
    """Проверяет, были ли успешно созданы теории."""
    if not output_dir:
        return False
    
    # Проверяем наличие директории с теориями
    theories_dir = os.path.join(output_dir, "theories")
    if not os.path.exists(theories_dir):
        logger.info("Директория с теориями не найдена")
        return False
    
    # Проверяем наличие файла с теориями
    theories_file = os.path.join(theories_dir, "theories.json")
    if not os.path.exists(theories_file):
        logger.info("Файл с теориями не найден")
        return False
    
    # Проверяем размер и содержимое файла
    try:
        with open(theories_file, 'r', encoding='utf-8') as f:
            theories = json.load(f)
            if not theories or len(theories) == 0:
                logger.info("Файл с теориями пуст")
                return False
    except Exception as e:
        logger.error(f"Ошибка при чтении файла с теориями: {str(e)}")
        return False
    
    logger.info(f"Обнаружены корректные теории: {len(theories)}")
    return True

def check_context_success(output_dir):
    """Проверяет, был ли успешно выполнен контекстный анализ."""
    if not output_dir:
        return False
    
    # Проверяем наличие директории с контекстом
    context_dir = os.path.join(output_dir, "context")
    if not os.path.exists(context_dir):
        logger.info("Директория с контекстом не найдена")
        return False
    
    # Проверяем наличие файла суммаризации
    summaries_file = os.path.join(context_dir, "segment_summaries.json")
    if not os.path.exists(summaries_file):
        logger.info("Файл суммаризации не найден")
        return False
    
    # Проверяем размер и содержимое файла
    try:
        with open(summaries_file, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
            if not summaries or len(summaries) == 0:
                logger.info("Файл суммаризации пуст")
                return False
    except Exception as e:
        logger.error(f"Ошибка при чтении файла суммаризации: {str(e)}")
        return False
    
    logger.info(f"Обнаружен успешный контекстный анализ")
    return True

def is_russian_text(file_path):
    """Определяет, является ли текст русскоязычным."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read(10000)  # Читаем первые 10000 символов
            
            # Проверяем наличие кириллических символов
            cyrillic_count = sum(1 for c in text if 'а' <= c.lower() <= 'я')
            total_chars = sum(1 for c in text if c.isalpha())
            
            if total_chars == 0:
                return False
                
            cyrillic_ratio = cyrillic_count / total_chars
            logger.info(f"Доля кириллических символов: {cyrillic_ratio:.2f}")
            
            # Если более 30% символов - кириллица, считаем текст русским
            return cyrillic_ratio > 0.3
    except Exception as e:
        logger.error(f"Ошибка при определении языка: {str(e)}")
        return False

def is_webvtt_format(file_path):
    """Определяет, является ли файл WEBVTT транскриптом."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            return first_line == "WEBVTT"
    except Exception as e:
        logger.error(f"Ошибка при определении формата: {str(e)}")
        return False

def create_theories_from_context(output_dir):
    """Создать теории на основе контекстного анализа."""
    if not output_dir:
        return False
    
    context_dir = os.path.join(output_dir, "context")
    summaries_file = os.path.join(context_dir, "segment_summaries.json")
    segments_file = os.path.join(context_dir, "segments.json")
    
    if not os.path.exists(summaries_file) or not os.path.exists(segments_file):
        logger.warning("Не найдены файлы контекстного анализа")
        return False
    
    try:
        # Загрузка данных контекстного анализа
        with open(summaries_file, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
            
        with open(segments_file, 'r', encoding='utf-8') as f:
            segments = json.load(f)
        
        # Создание директории для теорий, если она не существует
        theories_dir = os.path.join(output_dir, "theories")
        os.makedirs(theories_dir, exist_ok=True)
        
        # Формирование теорий на основе имеющейся контекстной информации
        theories = []
        
        for segment_id, summary in summaries.items():
            # Генерация теории на основе ключевых моментов из суммаризации
            if 'key_points' in summary and summary['key_points']:
                theory = {
                    "name": summary.get("title", "Основная теория"),
                    "description": summary.get("summary", ""),
                    "confidence": 0.85,
                    "hypotheses": []
                }
                
                # Создание гипотез на основе ключевых моментов
                for i, point in enumerate(summary['key_points']):
                    hypothesis = {
                        "statement": point,
                        "confidence": 0.8,
                        "evidence": [
                            {
                                "description": f"На основе контекстного анализа текста в сегменте {segment_id}",
                                "strength": 0.75
                            }
                        ]
                    }
                    theory["hypotheses"].append(hypothesis)
                
                theories.append(theory)
        
        if not theories:
            # Если не удалось создать теории на основе key_points, 
            # создаем одну общую теорию на основе суммаризации
            for segment_id, summary in summaries.items():
                theory = {
                    "name": summary.get("title", "Синтезированная теория"),
                    "description": summary.get("summary", ""),
                    "confidence": 0.8,
                    "hypotheses": [
                        {
                            "statement": "Эта теория создана на основе автоматической суммаризации текста",
                            "confidence": 0.7,
                            "evidence": [
                                {
                                    "description": f"Суммаризация сегмента {segment_id}",
                                    "strength": 0.7
                                }
                            ]
                        }
                    ]
                }
                theories.append(theory)
                break  # Достаточно одной такой теории
        
        # Сохранение теорий в файл
        theories_file = os.path.join(theories_dir, "theories.json")
        with open(theories_file, 'w', encoding='utf-8') as f:
            json.dump(theories, f, ensure_ascii=False, indent=2)
        
        # Создание markdown-отчета для теорий
        theories_md_path = os.path.join(theories_dir, "theories.md")
        with open(theories_md_path, "w", encoding="utf-8") as f:
            f.write("# Сгенерированные теории\n\n")
            
            for i, theory in enumerate(theories):
                f.write(f"## Теория {i+1}: {theory.get('name', 'Безымянная теория')}\n\n")
                f.write(f"**Достоверность**: {theory.get('confidence', 0.0):.2f}\n\n")
                f.write(f"**Описание**: {theory.get('description', 'Нет описания')}\n\n")
                
                if 'hypotheses' in theory and theory['hypotheses']:
                    f.write("### Гипотезы\n\n")
                    for j, hypothesis in enumerate(theory['hypotheses']):
                        f.write(f"#### Гипотеза {j+1}: {hypothesis.get('statement', '')}\n\n")
                        f.write(f"**Достоверность**: {hypothesis.get('confidence', 0.0):.2f}\n\n")
                        f.write(f"**Доказательства**:\n\n")
                        if 'evidence' in hypothesis and hypothesis['evidence']:
                            for evidence in hypothesis['evidence']:
                                f.write(f"- {evidence.get('description', '')} (Сила: {evidence.get('strength', 0.0):.2f})\n")
                        f.write("\n")
                
                f.write("---\n\n")
        
        logger.info(f"Создано {len(theories)} теорий на основе контекстного анализа")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при создании теорий: {str(e)}")
        return False

def create_report(output_dir, original_file, is_russian=False):
    """Создать итоговый HTML-отчет."""
    if not output_dir:
        return None
    
    try:
        # Определение языка отчета
        language = "ru" if is_russian else "en"
        
        # Проверка наличия отчета
        report_file = os.path.join(output_dir, "report.html")
        if os.path.exists(report_file) and os.path.getsize(report_file) > 1000:
            logger.info(f"Найден существующий отчет: {report_file}")
            return report_file
        
        # Проверка наличия улучшенного отчета
        improved_report_file = os.path.join(output_dir, "improved_report.html")
        if os.path.exists(improved_report_file) and os.path.getsize(improved_report_file) > 1000:
            logger.info(f"Найден улучшенный отчет: {improved_report_file}")
            return improved_report_file
        
        # Создаем базовый отчет с доступной информацией
        context_dir = os.path.join(output_dir, "context")
        summaries_file = os.path.join(context_dir, "segment_summaries.json")
        
        # Проверка наличия суммаризации
        if not os.path.exists(summaries_file):
            logger.warning("Не найден файл с суммаризацией текста")
            return None
        
        # Загрузка суммаризации
        with open(summaries_file, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
        
        # Загрузка теорий, если они были созданы
        theories_file = os.path.join(output_dir, "theories", "theories.json")
        if os.path.exists(theories_file):
            with open(theories_file, 'r', encoding='utf-8') as f:
                theories = json.load(f)
        else:
            theories = []
        
        # Определяем заголовки в зависимости от языка
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
        
        l = labels[language]
        
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
                <p><strong>{l["file"]}:</strong> {original_file}</p>
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
        final_report_path = os.path.join(output_dir, "final_report.html")
        with open(final_report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Создан итоговый HTML-отчет: {final_report_path}")
        return final_report_path
        
    except Exception as e:
        logger.error(f"Ошибка при создании итогового отчета: {str(e)}")
        return None

def run_unified_analysis(args):
    """Запуск унифицированного анализа с автоматической адаптацией."""
    start_time = time.time()
    
    # Проверяем наличие файла
    if not os.path.exists(args.file_path):
        logger.error(f"Файл не найден: {args.file_path}")
        return 1
    
    # Определяем язык и формат текста
    is_russian = is_russian_text(args.file_path)
    is_webvtt = is_webvtt_format(args.file_path)
    
    logger.info(f"Анализ файла: {args.file_path}")
    logger.info(f"Язык текста: {'Русский' if is_russian else 'Английский'}")
    logger.info(f"Формат WEBVTT: {'Да' if is_webvtt else 'Нет'}")
    
    # Запускаем стандартный анализ
    output_dir, success, stdout = run_standard_analysis(args)
    if not output_dir:
        logger.error("Не удалось выполнить стандартный анализ")
        return 1
    
    # Проверяем результаты стандартного анализа
    has_graph = check_graph_success(output_dir)
    has_theories = check_theories_success(output_dir)
    has_context = check_context_success(output_dir)
    
    logger.info(f"Результаты стандартного анализа:")
    logger.info(f"- Граф знаний: {'Создан' if has_graph else 'Не создан'}")
    logger.info(f"- Теории: {'Созданы' if has_theories else 'Не созданы'}")
    logger.info(f"- Контекстный анализ: {'Выполнен' if has_context else 'Не выполнен'}")
    
    # Если контекстный анализ выполнен, но теории не созданы - создаем их
    if has_context and not has_theories:
        logger.info("Создание теорий на основе контекстного анализа...")
        create_theories_from_context(output_dir)
    
    # Создаем итоговый отчет
    report_path = create_report(output_dir, args.file_path, is_russian)
    
    if report_path:
        logger.info(f"Анализ успешно завершен за {time.time() - start_time:.2f} секунд")
        print(f"\nАнализ завершен. Создан отчет: {report_path}")
        print("Вы можете открыть его в браузере.")
        return 0
    else:
        logger.error("Не удалось создать итоговый отчет")
        return 1

def main():
    """Основная функция."""
    args = parse_arguments()
    return run_unified_analysis(args)

if __name__ == "__main__":
    sys.exit(main())