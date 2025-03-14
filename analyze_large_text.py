#!/usr/bin/env python3
"""
Скрипт для запуска анализа большого текстового файла с оптимизированными настройками
для предотвращения ошибки с индексами и памятью.
"""

import os
import sys
import argparse
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Добавляем директорию src в путь для импорта
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

# Теперь импортируем из пакета knowledge_graph_synth
from knowledge_graph_synth.cli.commands import main

def parse_arguments():
    """Разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Запуск анализа большого текстового файла с оптимизированными настройками"
    )
    
    parser.add_argument(
        "file_path",
        help="Путь к текстовому файлу для анализа"
    )
    
    parser.add_argument(
        "--max-segments", "-m",
        type=int,
        default=1000,
        help="Максимальное количество сегментов для обработки (по умолчанию: 1000)"
    )
    
    parser.add_argument(
        "--provider", "-p",
        default="gemini",
        choices=["gemini", "openai"],
        help="Провайдер LLM для анализа (по умолчанию: gemini)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="Директория для вывода результатов (по умолчанию: output)"
    )
    
    parser.add_argument(
        "--theories", "-t",
        action="store_true",
        help="Генерировать теории на основе графа"
    )
    
    return parser.parse_args()

def run_safe_analysis(args):
    """Запуск анализа с оптимизированными настройками."""
    logger.info(f"Запуск безопасного анализа для большого файла: {args.file_path}")
    
    if not os.path.exists(args.file_path):
        logger.error(f"Файл не найден: {args.file_path}")
        return 1
    
    # Проверка доступности директории вывода
    if not os.path.exists(args.output):
        try:
            os.makedirs(args.output)
            logger.info(f"Создана директория вывода: {args.output}")
        except Exception as e:
            logger.error(f"Ошибка при создании директории вывода: {str(e)}")
            return 1
    
    # Составление аргументов для анализа - с оптимизированными настройками
    cmd_args = [
        "process",
        "-f", args.file_path,
        "-e",  # извлечение сущностей
        "-b",  # построение графа
        "--provider", args.provider,
        "--generate-report",  # генерация отчета
        "--contextual-analysis",  # контекстный анализ
        "--output", args.output,
        "--max-segments", str(args.max_segments),  # лимит сегментов
        "--batch-size", "5",  # малый размер пакета для API
        "--delay", "0.5",  # задержка между запросами
        "--gradual"  # постепенная обработка
    ]
    
    # Добавляем опциональные параметры
    if args.theories:
        cmd_args.append("-g")  # генерация теорий
    
    # Запуск процесса анализа
    logger.info(f"Запуск анализа с параметрами: {' '.join(cmd_args)}")
    
    try:
        result = main(cmd_args)
        
        # Если анализ успешно завершен, создаем улучшенный отчет
        if result == 0:
            # Определяем путь к последней созданной директории
            import glob
            
            # Найти самую последнюю директорию с отметкой времени
            output_dirs = sorted(glob.glob(f"{args.output}/[0-9]*_[0-9]*"), reverse=True)
            
            if output_dirs:
                latest_dir = output_dirs[0]
                logger.info(f"Создание улучшенного отчета для {latest_dir}")
                
                try:
                    # Импортируем и используем функцию создания улучшенного отчета
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from fix_report_improved import create_improved_report
                    
                    report_path = create_improved_report(latest_dir, args.file_path)
                    logger.info(f"Улучшенный отчет создан: {report_path}")
                    print(f"\nСоздан улучшенный отчет: {report_path}")
                    print("Вы можете просмотреть его в браузере.")
                except Exception as report_error:
                    logger.error(f"Ошибка при создании улучшенного отчета: {str(report_error)}")
        
        return result
    except Exception as e:
        logger.error(f"Ошибка при выполнении анализа: {str(e)}")
        
        # Попытка восстановления отчета
        try:
            from fix_report_improved import create_improved_report
            
            # Определение директории вывода
            output_dirs = [d for d in os.listdir(args.output) if os.path.isdir(os.path.join(args.output, d))]
            output_dirs.sort(reverse=True)
            
            if output_dirs:
                latest_dir = os.path.join(args.output, output_dirs[0])
                logger.info(f"Попытка создания отчета из директории: {latest_dir}")
                
                # Создание улучшенного отчета
                report_path = create_improved_report(latest_dir, args.file_path)
                
                if report_path:
                    logger.info(f"Отчет успешно создан: {report_path}")
                    print(f"\nОтчет создан: {report_path}")
                    print("Вы можете просмотреть его в браузере.")
                    return 0
            
            logger.error("Не удалось создать отчет")
        except Exception as recovery_error:
            logger.error(f"Ошибка при создании отчета: {str(recovery_error)}")
        
        return 1

if __name__ == "__main__":
    args = parse_arguments()
    sys.exit(run_safe_analysis(args))