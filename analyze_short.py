#!/usr/bin/env python3
"""
Скрипт для запуска анализа текстового файла с ограничением количества сегментов для быстрой проверки.
"""

import os
import sys

# Добавляем директорию src в путь для импорта
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

# Теперь импортируем из пакета knowledge_graph_synth
from knowledge_graph_synth.cli.commands import main

if __name__ == "__main__":
    # Путь к файлу для анализа (используем merged.txt)
    file_path = "/Users/shipaleks/Documents/graph_reasoner_claude_code/merged.txt"
    
    if not os.path.exists(file_path):
        print(f"Файл не найден: {file_path}")
        sys.exit(1)
    
    # Определение аргументов для анализа с ограничением количества сегментов
    args = [
        "process",
        "-f", file_path,
        "-e",  # извлечение сущностей
        "-b",  # построение графа
        "-g",  # генерация теорий
        "--contextual-analysis",
        "--generate-report",
        "--provider", "gemini",
        "--max-segments", "20"  # ограничиваем количество сегментов для быстрой проверки
    ]
    
    # Запуск процесса анализа
    print(f"Запуск анализа с ограничением в 20 сегментов")
    sys.exit(main(args))