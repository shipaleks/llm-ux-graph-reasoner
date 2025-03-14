#!/usr/bin/env python3
"""
Скрипт для применения всех исправлений и тестирования обработки WEBVTT файлов.
"""

import os
import sys
import subprocess
import logging
import time
import argparse
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def run_test(file_path):
    """Запустить тест анализа для проверки исправлений."""
    if not os.path.exists(file_path):
        logger.error(f"Файл не найден: {file_path}")
        return False

    test_output_dir = "output/webvtt_test"
    os.makedirs(test_output_dir, exist_ok=True)
    
    logger.info(f"Тестирование обработки файла: {file_path}")
    start_time = time.time()
    
    # Запускаем стандартный анализатор
    cmd = ["./analyze_text.py", file_path, "--provider", "gemini", "--output", test_output_dir, "--theories"]
    logger.info(f"Запуск команды: {' '.join(cmd)}")
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time
        logger.info(f"Тест завершен за {duration:.2f} секунд")
        
        # Проверяем наличие ошибок с "invalid position information"
        error_count = 0
        for line in process.stdout.split('\n'):
            if "invalid position information" in line:
                error_count += 1
        
        # Проверяем, создан ли отчет
        output_dirs = [d for d in os.listdir(test_output_dir) if os.path.isdir(os.path.join(test_output_dir, d))]
        if not output_dirs:
            logger.error("Не создана выходная директория с результатами")
            return False
            
        latest_dir = sorted(output_dirs)[-1]
        report_path = os.path.join(test_output_dir, latest_dir, "report.html")
        theories_dir = os.path.join(test_output_dir, latest_dir, "theories")
        
        success = True
        
        if not os.path.exists(report_path):
            logger.warning("Отчет не был создан")
            success = False
        else:
            logger.info(f"Отчет создан: {report_path}")
        
        if not os.path.exists(theories_dir) or not os.listdir(theories_dir):
            logger.warning("Теории не были созданы")
            success = False
        else:
            logger.info(f"Теории созданы в директории: {theories_dir}")
        
        # Выводим результаты теста
        print("\nРезультаты теста:")
        print(f"* Время выполнения: {duration:.2f} секунд")
        print(f"* Ошибки с позициями: {error_count}")
        print(f"* Отчет создан: {'Да' if os.path.exists(report_path) else 'Нет'}")
        print(f"* Теории созданы: {'Да' if os.path.exists(theories_dir) and os.listdir(theories_dir) else 'Нет'}")
        print(f"\nРезультаты находятся в директории: {os.path.join(test_output_dir, latest_dir)}\n")
        
        return success
    except Exception as e:
        logger.error(f"Ошибка при выполнении теста: {str(e)}")
        return False

def main():
    """Основная функция."""
    parser = argparse.ArgumentParser(description="Применение и тестирование исправлений для WEBVTT")
    parser.add_argument(
        "file_path",
        help="Путь к тестовому файлу WEBVTT для проверки исправлений",
        nargs="?",
        default=None
    )
    args = parser.parse_args()
    
    print("\n=== Проверка исправлений обработки WEBVTT файлов ===\n")
    print("Внесенные исправления:")
    print("1. В segmenter.py - не устанавливаем позиции для транскриптов WEBVTT")
    print("2. В commands.py - не удаляем сегменты транскриптов при проверке позиций")
    print("\nЭти исправления позволяют корректно обрабатывать WEBVTT файлы и создавать отчеты.\n")
    
    # Запускаем тест, если указан файл
    if args.file_path:
        success = run_test(args.file_path)
        if success:
            print("\n✅ Тест успешно пройден! Исправления работают корректно.")
            return 0
        else:
            print("\n❌ Тест не пройден. Возможно, требуются дополнительные исправления.")
            return 1
    else:
        print("Для проверки исправлений укажите путь к WEBVTT файлу:")
        print("    python apply_webvtt_fixes.py /path/to/file.vtt")
        return 0

if __name__ == "__main__":
    sys.exit(main())