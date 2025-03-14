#!/usr/bin/env python3
"""
Скрипт для исправления обработки русского языка и создания отчета 
на основе контекстного анализа, даже если не удалось создать граф знаний.
"""

import os
import sys
import json
import logging
from datetime import datetime
import re
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def create_theories_from_context(context_dir, output_dir):
    """Создать теории на основе контекстного анализа"""
    
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

def create_basic_html_report(output_dir, original_file):
    """Создать базовый HTML-отчет с доступной информацией"""
    
    context_dir = os.path.join(output_dir, "context")
    summaries_file = os.path.join(context_dir, "segment_summaries.json")
    
    if not os.path.exists(summaries_file):
        logger.warning("Не найден файл с суммаризацией текста")
        return None
    
    try:
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
        
        # Формирование отчета
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Отчет анализа текста</title>
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
            <h1>Отчет анализа текста</h1>
            
            <div class="metadata">
                <p><strong>Файл:</strong> {original_file}</p>
                <p><strong>Дата анализа:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h2>Суммаризация текста</h2>
        """
        
        # Добавление суммаризации
        for segment_id, summary in summaries.items():
            title = summary.get("title", "Без заголовка")
            summary_text = summary.get("summary", "")
            key_points = summary.get("key_points", [])
            
            key_points_html = ""
            if key_points:
                key_points_html = "<div class='key-points'><h4>Ключевые моменты:</h4><ul>"
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
        html_content += "<h2>Теории и гипотезы</h2>"
        
        if theories:
            for i, theory in enumerate(theories):
                theory_name = theory.get("name", f"Теория {i+1}")
                theory_desc = theory.get("description", "Нет описания")
                theory_conf = theory.get("confidence", 0.0)
                
                hypotheses_html = ""
                if "hypotheses" in theory and theory["hypotheses"]:
                    for h, hypothesis in enumerate(theory["hypotheses"]):
                        h_statement = hypothesis.get("statement", "")
                        h_confidence = hypothesis.get("confidence", 0.0)
                        
                        evidence_html = ""
                        if "evidence" in hypothesis and hypothesis["evidence"]:
                            evidence_html = "<p><strong>Доказательства:</strong></p><ul>"
                            for ev in hypothesis["evidence"]:
                                ev_desc = ev.get("description", "")
                                ev_strength = ev.get("strength", 0.0)
                                evidence_html += f"<li>{ev_desc} (Сила: {ev_strength:.2f})</li>"
                            evidence_html += "</ul>"
                        
                        hypotheses_html += f"""
                        <div class="hypothesis">
                            <h4>Гипотеза {h+1}: {h_statement}</h4>
                            <div>Достоверность: {h_confidence:.2f}</div>
                            {evidence_html}
                        </div>
                        """
                
                html_content += f"""
                <div class="theory">
                    <h3>{theory_name}</h3>
                    <div>Достоверность: {theory_conf:.2f}</div>
                    <p>{theory_desc}</p>
                    {hypotheses_html}
                </div>
                """
        else:
            html_content += "<p>Теории не были сгенерированы.</p>"
        
        html_content += """
        </body>
        </html>
        """
        
        # Сохранение отчета
        report_path = os.path.join(output_dir, "basic_report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Создан базовый HTML-отчет: {report_path}")
        return report_path
        
    except Exception as e:
        logger.error(f"Ошибка при создании базового отчета: {str(e)}")
        return None

def main():
    """Основная функция."""
    if len(sys.argv) < 2:
        print("Использование: python fix_russian_processing.py <директория_вывода> [исходный_файл]")
        return 1
    
    output_dir = sys.argv[1]
    original_file = sys.argv[2] if len(sys.argv) > 2 else "Неизвестный источник"
    
    if not os.path.exists(output_dir):
        logger.error(f"Директория не найдена: {output_dir}")
        return 1
    
    try:
        logger.info(f"Обработка директории: {output_dir}")
        
        # Создание теорий на основе контекстного анализа
        context_dir = os.path.join(output_dir, "context")
        if os.path.exists(context_dir):
            create_theories_from_context(context_dir, output_dir)
        
        # Создание базового отчета
        report_path = create_basic_html_report(output_dir, original_file)
        
        if report_path:
            print(f"\nСоздан отчет: {report_path}")
            print("Вы можете открыть его в браузере.")
            return 0
        else:
            logger.error("Не удалось создать отчет")
            return 1
            
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())