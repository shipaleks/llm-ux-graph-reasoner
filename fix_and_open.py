#!/usr/bin/env python3
"""
Скрипт для исправления ссылок на сегменты в отчетах и открытия последнего отчета в браузере.

Использование:
    ./fix_and_open.py [--dir <директория>]

Примеры:
    ./fix_and_open.py
    ./fix_and_open.py --dir output/20250306_065325
"""

import os
import sys
import argparse
import logging
import subprocess
import re
import json
import webbrowser
from pathlib import Path
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def fix_segment_links(report_dir):
    """Исправление ссылок на сегменты в отчете.
    
    Args:
        report_dir: Директория с отчетом report.html
    """
    report_path = os.path.join(report_dir, "report.html")
    if not os.path.exists(report_path):
        logger.warning(f"Отчет не найден: {report_path}")
        return False
        
    try:
        # Чтение файла отчета
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Исправление ссылок на сегменты
        fixed_content = re.sub(r'href="segments/', r'href="./segments/', content)
        
        # Запись только если были изменения
        if fixed_content != content:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
                
            logger.info(f"Исправлены ссылки на сегменты в отчете: {report_path}")
            return True
        else:
            logger.info(f"Ссылки на сегменты уже исправлены в: {report_path}")
            return True
    except Exception as e:
        logger.error(f"Ошибка при исправлении ссылок в {report_path}: {str(e)}")
        return False

def ensure_segment_pages(output_dir):
    """Проверка и создание страниц сегментов для отчета.
    
    Args:
        output_dir: Директория с данными отчета и контекстом
    """
    try:
        # Проверка наличия директории контекста
        context_dir = os.path.join(output_dir, "context")
        if not os.path.exists(context_dir):
            logger.warning(f"Директория контекста не найдена: {context_dir}")
            return False
            
        # Проверка наличия файлов segments.json и segment_summaries.json
        segments_path = os.path.join(context_dir, "segments.json")
        summaries_path = os.path.join(context_dir, "segment_summaries.json")
        
        if not os.path.exists(segments_path) or not os.path.exists(summaries_path):
            logger.warning(f"Отсутствуют файлы данных сегментов в {context_dir}")
            return False
            
        # Загрузка сегментов и сводок
        with open(segments_path, 'r', encoding='utf-8') as f:
            segments = json.load(f)
        
        with open(summaries_path, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
        
        # Создание директории сегментов, если не существует
        segments_dir = os.path.join(output_dir, "segments")
        os.makedirs(segments_dir, exist_ok=True)
        
        # Проверка наличия страниц сегментов
        missing_segments = []
        for segment_id in summaries.keys():
            segment_path = os.path.join(segments_dir, f"{segment_id}.html")
            if not os.path.exists(segment_path):
                missing_segments.append(segment_id)
        
        if not missing_segments:
            logger.info(f"Все страницы сегментов существуют в {segments_dir}")
            return True
        else:
            logger.info(f"Найдено {len(missing_segments)} отсутствующих страниц сегментов, создание...")
            
        # Шаблон для страниц сегментов
        segment_template = (
            "<!DOCTYPE html>\n"
            "<html lang=\"ru\">\n"
            "<head>\n"
            "    <meta charset=\"UTF-8\">\n"
            "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            "    <title>{title}</title>\n"
            "    <style>\n"
            "        body {\n"
            "            font-family: Arial, sans-serif;\n"
            "            line-height: 1.6;\n"
            "            color: #333;\n"
            "            background-color: #fff;\n"
            "            margin: 0 auto;\n"
            "            padding: 1rem;\n"
            "            max-width: 1000px;\n"
            "        }\n"
            "        h1 {\n"
            "            font-size: 1.5rem;\n"
            "            border-bottom: 1px solid #e0e0e0;\n"
            "            padding-bottom: 0.5rem;\n"
            "        }\n"
            "        .segment-text {\n"
            "            background-color: #f9f9f9;\n"
            "            padding: 1rem;\n"
            "            border-radius: 4px;\n"
            "            white-space: pre-wrap;\n"
            "        }\n"
            "        .segment-metadata {\n"
            "            margin-top: 1rem;\n"
            "            padding: 1rem;\n"
            "            background-color: #f5f5f5;\n"
            "            border-radius: 4px;\n"
            "        }\n"
            "        .back-link {\n"
            "            margin-top: 1rem;\n"
            "            display: inline-block;\n"
            "        }\n"
            "    </style>\n"
            "</head>\n"
            "<body>\n"
            "    <h1>{title}</h1>\n"
            "    \n"
            "    <div class=\"segment-text\">{text}</div>\n"
            "    \n"
            "    <div class=\"segment-metadata\">\n"
            "        <p><strong>ID:</strong> {id}</p>\n"
            "        <p><strong>Роль:</strong> {role}</p>\n"
            "    </div>\n"
            "    \n"
            "    <a href=\"{report_path}\" class=\"back-link\">Вернуться к отчету</a>\n"
            "</body>\n"
            "</html>"
        )
        
        # Создание страниц для отсутствующих сегментов
        created_count = 0
        for segment_id in missing_segments:
            if segment_id in segments and segment_id in summaries:
                segment_text = segments[segment_id]
                summary = summaries[segment_id]
                
                # Получение заголовка и роли
                title = summary.get('title', f"Сегмент {segment_id}")
                role = summary.get('role', '')
                
                # Создание страницы сегмента
                segment_path = os.path.join(segments_dir, f"{segment_id}.html")
                
                # Относительный путь к отчету
                report_rel_path = "../report.html"
                
                # Заполнение шаблона
                segment_html = segment_template.format(
                    title=title,
                    text=segment_text,
                    id=segment_id,
                    role=role,
                    report_path=report_rel_path
                )
                
                # Запись страницы сегмента
                with open(segment_path, "w", encoding="utf-8") as f:
                    f.write(segment_html)
                    created_count += 1
        
        logger.info(f"Создано {created_count} отсутствующих страниц сегментов в {segments_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при проверке страниц сегментов: {str(e)}")
        return False

def get_latest_report_dir(base_dir="output"):
    """Получение директории с самым последним отчетом.
    
    Args:
        base_dir: Базовая директория для поиска
        
    Returns:
        Путь к директории с самым последним отчетом
    """
    try:
        if not os.path.exists(base_dir):
            logger.error(f"Директория не существует: {base_dir}")
            return None
            
        # Поиск директорий с датой в имени
        timestamped_dirs = []
        
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path) and re.match(r"\d{8}_\d{6}", item):
                # Это директория с временной меткой (yyyymmdd_hhmmss)
                dir_timestamp = datetime.strptime(item, "%Y%m%d_%H%M%S")
                timestamped_dirs.append((item_path, dir_timestamp))
        
        if not timestamped_dirs:
            # Проверка на наличие отчета в базовой директории
            if os.path.exists(os.path.join(base_dir, "report.html")):
                logger.info(f"Найден отчет в базовой директории: {base_dir}")
                return base_dir
            else:
                logger.error(f"Отчеты не найдены в {base_dir}")
                return None
        
        # Сортировка по времени (самые новые первыми)
        timestamped_dirs.sort(key=lambda x: x[1], reverse=True)
        
        # Проверка наличия отчета в найденных директориях
        for dir_path, _ in timestamped_dirs:
            report_path = os.path.join(dir_path, "report.html")
            if os.path.exists(report_path):
                logger.info(f"Найден последний отчет в: {dir_path}")
                return dir_path
        
        logger.error("Не найдены отчеты в директориях с временными метками")
        return None
    
    except Exception as e:
        logger.error(f"Ошибка при поиске последнего отчета: {str(e)}")
        return None

def fix_and_open_report(base_dir="output"):
    """Исправление ссылок и открытие отчета.
    
    Args:
        base_dir: Директория для поиска отчета
    """
    # Получение директории с последним отчетом
    if os.path.isdir(base_dir) and os.path.exists(os.path.join(base_dir, "report.html")):
        report_dir = base_dir
    else:
        report_dir = get_latest_report_dir(base_dir)
    
    if not report_dir:
        logger.error("Не удалось найти директорию с отчетом")
        return 1
    
    # Исправление ссылок в отчете
    fix_segment_links(report_dir)
    
    # Проверка и создание страниц сегментов
    ensure_segment_pages(report_dir)
    
    # Путь к отчету
    report_path = os.path.join(report_dir, "report.html")
    
    # Открытие отчета в браузере
    if os.path.exists(report_path):
        logger.info(f"Открытие отчета: {report_path}")
        
        # Преобразование пути в URL (file://)
        url = Path(report_path).absolute().as_uri()
        
        try:
            # Открытие браузера
            webbrowser.open(url)
            logger.info(f"Отчет открыт в браузере: {url}")
            return 0
        except Exception as e:
            logger.error(f"Не удалось открыть браузер: {str(e)}")
            
            # Вывод пути для ручного открытия
            print(f"\nОтчет готов: {report_path}")
            print(f"URL для открытия: {url}\n")
            return 0
    else:
        logger.error(f"Отчет не найден: {report_path}")
        return 1

def parse_arguments():
    """Разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Исправление ссылок на сегменты и открытие отчета в браузере"
    )
    
    parser.add_argument(
        "--dir", "-d",
        default="output",
        help="Директория с отчетами (по умолчанию: output)"
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    sys.exit(fix_and_open_report(args.dir))