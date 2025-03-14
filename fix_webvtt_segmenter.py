#!/usr/bin/env python3
"""
Скрипт для исправления обработки WEBVTT файлов в системе анализа.
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция."""
    # Проверяем, внесены ли уже исправления в исходный код
    module_path = "src/knowledge_graph_synth/text/segmenter.py"
    if not os.path.exists(module_path):
        logger.error(f"Файл модуля не найден: {module_path}")
        return 1
        
    # Запускаем тест на обработку WEBVTT файла
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        if not os.path.exists(test_file):
            logger.error(f"Тестовый файл не найден: {test_file}")
            return 1
            
        logger.info(f"Тестирование обработки файла: {test_file}")
        start_time = time.time()
        
        # Запускаем стандартный анализатор
        cmd = ["./analyze_text.py", test_file, "--provider", "gemini", "--output", "output/test_webvtt"]
        logger.info(f"Запуск команды: {' '.join(cmd)}")
        
        try:
            process = subprocess.run(cmd, capture_output=True, text=True)
            logger.info(f"Тест завершен за {time.time() - start_time:.2f} секунд")
            
            # Проверяем наличие ошибок с "invalid position information"
            error_count = 0
            for line in process.stdout.split('\n'):
                if "invalid position information" in line:
                    error_count += 1
            
            if error_count > 0:
                logger.warning(f"Обнаружено {error_count} ошибок позиций сегментов.")
                logger.info("Рекомендуется проверить результаты анализа.")
            else:
                logger.info("Ошибок с позициями сегментов не обнаружено.")
                
            # Выводим результаты
            print("\nРезультаты теста:")
            print(f"* Время выполнения: {time.time() - start_time:.2f} секунд")
            print(f"* Ошибки с позициями: {error_count}")
            print("\nПроверьте выходную директорию: output/test_webvtt")
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении теста: {str(e)}")
            return 1
    else:
        print("Использование: python fix_webvtt_segmenter.py <путь_к_тестовому_файлу>")
        print("Пример: python fix_webvtt_segmenter.py /path/to/transcript.vtt")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())