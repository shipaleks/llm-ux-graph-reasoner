#!/usr/bin/env python3
"""
Универсальный анализатор текстов (любого языка и формата).
Автоматически обрабатывает русскоязычные WEBVTT транскрипты и другие тексты,
используя модели Gemini с большим контекстным окном.

Использование:
    ./analyze_any.py <путь_к_файлу> [--output <выходная_директория>]
"""

import os
import sys
import logging
import time
import argparse
import asyncio
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Добавление путей для импорта
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Полные пути к необходимым модулям
llm_analyzer_path = current_dir / "llm_analyzer.py"
llm_segmenter_path = current_dir / "llm_segmenter.py"

# Проверка наличия файлов
if not llm_analyzer_path.exists():
    logger.error(f"Файл llm_analyzer.py не найден по пути: {llm_analyzer_path}")
    sys.exit(1)
if not llm_segmenter_path.exists():
    logger.error(f"Файл llm_segmenter.py не найден по пути: {llm_segmenter_path}")
    sys.exit(1)

# Импортируем анализатор напрямую
import importlib.util
spec = importlib.util.spec_from_file_location("llm_analyzer", llm_analyzer_path)
llm_analyzer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_analyzer)
LLMAnalyzer = llm_analyzer.LLMAnalyzer

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
    analyzer = LLMAnalyzer(output_dir=args.output)
    
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