#!/usr/bin/env python3
"""
Универсальный скрипт для запуска полного анализа текстового файла.
Создает граф знаний, выполняет расширение графа и генерирует отчет.

Использование:
    ./analyze_text.py <путь_к_файлу> [--provider <провайдер>] [--expand] [--theories]

Примеры:
    ./analyze_text.py test_synthetic_text.txt
    ./analyze_text.py docs/sample.txt --provider gemini --expand
"""

import os
import sys
import argparse
import logging
import time
import json
import re
from datetime import datetime

# Настройка логирования
log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_file = f"{os.path.basename(__file__)}.log"

# Создаем файловый обработчик
file_handler = logging.FileHandler(log_file, mode='w')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)  # Устанавливаем уровень DEBUG для файла

# Создаем консольный обработчик
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)  # Оставляем INFO для консоли

# Настраиваем корневой логгер
logging.basicConfig(
    level=logging.DEBUG,  # Устанавливаем DEBUG для корневого логгера
    handlers=[file_handler, console_handler]
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
        description="Запуск полного анализа текстового файла для создания графа знаний"
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
        "--expand", "-e",
        action="store_true",
        help="Расширить граф через задание вопросов"
    )
    
    parser.add_argument(
        "--theories", "-t",
        action="store_true",
        help="Генерировать теории на основе графа"
    )
    
    parser.add_argument(
        "--no-segments", "-n",
        action="store_true",
        help="Пропустить анализ по сегментам"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="Директория для вывода результатов (по умолчанию: output)"
    )
    
    parser.add_argument(
        "--max-segments", "-m",
        type=int,
        default=None,
        help="Максимальное количество сегментов для обработки (для тестирования)"
    )
    
    return parser.parse_args()

def run_analysis(args):
    """Запуск анализа с указанными параметрами."""
    start_time = time.time()
    logger.info(f"Запуск анализа файла: {args.file_path}")
    
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
    
    # Составление аргументов для анализа
    cmd_args = [
        "process",
        "-f", args.file_path,
        "-e",  # извлечение сущностей
        "-b",  # построение графа
        "--provider", args.provider,
        "--generate-report",  # генерация отчета
        "--output", args.output
    ]
    
    # Добавляем ограничение по количеству сегментов, если указано
    if args.max_segments:
        cmd_args.extend(["--max-segments", str(args.max_segments)])
    
    # Добавляем опциональные параметры
    if not args.no_segments:
        cmd_args.append("--contextual-analysis")
    
    if args.expand:
        cmd_args.append("--expand-graph")
    
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
                    # Call improve_report_en.py for English report
                    improve_cmd = ["./improve_report_en.py", "--dir", latest_dir, "--force"]
                    logger.info(f"Running English report improvement with command: {' '.join(improve_cmd)}")
                    
                    improve_result = subprocess.run(improve_cmd, capture_output=True, text=True)
                    
                    if improve_result.returncode != 0:
                        logger.warning(f"Warning when improving report: {improve_result.stderr}")
                        logger.info(f"Standard report available at: {latest_dir}")
                        print(f"\n⚠️ Warning when creating improved English report.")
                        print(f"📊 Standard report available at: {latest_dir}")
                    else:
                        # Find the path to the improved report in the output
                        improved_report_path = None
                        for line in improve_result.stdout.split('\n'):
                            if "successfully improved:" in line or "Report successfully improved:" in line:
                                improved_report_path = line.split(":")[-1].strip()
                                break
                        
                        if improved_report_path and os.path.exists(improved_report_path):
                            logger.info(f"Improved English report created: {improved_report_path}")
                            print(f"\n✅ Improved English report created: {improved_report_path}")
                            print("🌐 You can open it in your browser.")
                        else:
                            print(f"\n⚠️ Analysis completed, but the improved English report may not have been created.")
                            print(f"📊 Standard report available at: {latest_dir}")
                except Exception as report_error:
                    logger.error(f"Ошибка при создании улучшенного отчета: {str(report_error)}")
        
        # Вывод статистики использования токенов на основе логов
        try:
            # Найти самую последнюю директорию с отметкой времени
            import glob
            output_dirs = sorted(glob.glob(f"{args.output}/[0-9]*_[0-9]*"), reverse=True)
            
            if output_dirs:
                latest_dir = output_dirs[0]
                
                # Анализируем логи для извлечения данных о токенах
                api_calls = 0
                input_tokens = 0
                output_tokens = 0
                calls_by_model = {}
                tokens_by_model = {}
                duration_total = 0.0
                
                # Получить путь к последнему логу
                log_pattern = re.compile(r'API call to ([^:]+): (\d+) input tokens, (\d+) output tokens, ([0-9.]+)s')
                
                log_files = [log_file]  # Начинаем с нашего лог-файла
                
                # Перебираем все возможные источники логов
                for log_f in log_files:
                    if os.path.exists(log_f):
                        logger.info(f"Анализируем лог-файл: {log_f}")
                        with open(log_f, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            logger.info(f"Размер лог-файла: {len(content)} байт")
                            
                            # Ищем все совпадения
                            for match in log_pattern.finditer(content):
                                model = match.group(1)
                                in_tokens = int(match.group(2))
                                out_tokens = int(match.group(3))
                                duration = float(match.group(4))
                                
                                logger.info(f"Найдено использование API: {model}, {in_tokens} вх. токенов, {out_tokens} вых. токенов")
                                
                                api_calls += 1
                                input_tokens += in_tokens
                                output_tokens += out_tokens
                                duration_total += duration
                                
                                if model not in calls_by_model:
                                    calls_by_model[model] = 0
                                    tokens_by_model[model] = {"input": 0, "output": 0}
                                
                                calls_by_model[model] += 1
                                tokens_by_model[model]["input"] += in_tokens
                                tokens_by_model[model]["output"] += out_tokens
                
                # Если логи не найдены, попробуем найти строки в выводе командной строки
                if api_calls == 0:
                    # Сканируем вывод для поиска токенов
                    log_output = os.popen(f"grep 'API call to' -r {latest_dir}/").read()
                    for line in log_output.split("\n"):
                        match = log_pattern.search(line)
                        if match:
                            model = match.group(1)
                            in_tokens = int(match.group(2))
                            out_tokens = int(match.group(3))
                            duration = float(match.group(4))
                            
                            api_calls += 1
                            input_tokens += in_tokens
                            output_tokens += out_tokens
                            duration_total += duration
                            
                            if model not in calls_by_model:
                                calls_by_model[model] = 0
                                tokens_by_model[model] = {"input": 0, "output": 0}
                            
                            calls_by_model[model] += 1
                            tokens_by_model[model]["input"] += in_tokens
                            tokens_by_model[model]["output"] += out_tokens
                
                # Рассчитываем стоимость использования
                total_cost = 0.0
                model_costs = {}
                
                # Примерные цены за 1K токенов
                cost_per_1k = {
                    "gemini-2.0-flash": {"input": 0.000125, "output": 0.000375},  # $0.125/1M input, $0.375/1M output
                    "gemini-2.0-pro-exp-02-05": {"input": 0.0005, "output": 0.0015},  # $0.5/1M input, $1.5/1M output
                    "default_gemini": {"input": 0.0005, "output": 0.0015},
                    "default_openai": {"input": 0.001, "output": 0.002},
                }
                
                for model, tokens in tokens_by_model.items():
                    # Get cost rates for this model
                    if model in cost_per_1k:
                        rates = cost_per_1k[model]
                    elif "gemini" in model.lower():
                        rates = cost_per_1k["default_gemini"]
                    else:
                        rates = cost_per_1k["default_openai"]
                    
                    # Calculate costs
                    input_cost = (tokens["input"] / 1000) * rates["input"]
                    output_cost = (tokens["output"] / 1000) * rates["output"]
                    model_cost = input_cost + output_cost
                    
                    model_costs[model] = {
                        "input_tokens": tokens["input"],
                        "output_tokens": tokens["output"],
                        "input_cost": input_cost,
                        "output_cost": output_cost,
                        "total_cost": model_cost
                    }
                    
                    total_cost += model_cost
                
                # Создаем подробный отчет
                summary = [
                    "Token Usage Summary",
                    "==================="
                ]
                
                # Add general stats
                summary.extend([
                    f"Total API Calls: {api_calls}",
                    f"Total Tokens: {input_tokens + output_tokens} (Input: {input_tokens}, Output: {output_tokens})",
                    f"Estimated Cost: ${total_cost:.6f} USD",
                    f"Total API Duration: {duration_total:.2f} seconds",
                    f"Total Analysis Time: {time.time() - start_time:.2f} seconds",
                    "",
                    "Model Breakdown:",
                ])
                
                # Add per-model stats
                for model, cost_info in model_costs.items():
                    summary.extend([
                        f"  {model}:",
                        f"    Calls: {calls_by_model[model]}",
                        f"    Tokens: {cost_info['input_tokens'] + cost_info['output_tokens']} (Input: {cost_info['input_tokens']}, Output: {cost_info['output_tokens']})",
                        f"    Cost: ${cost_info['total_cost']:.6f} USD",
                        ""
                    ])
                
                token_stats = "\n".join(summary)
                print("\n" + token_stats)
                
                # Сохранение статистики в файл в выходной директории
                stats_path = os.path.join(latest_dir, "token_usage.txt")
                with open(stats_path, "w", encoding="utf-8") as f:
                    # Добавление информации о файле и времени анализа
                    f.write(f"File: {args.file_path}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total analysis time: {time.time() - start_time:.2f} seconds\n\n")
                    f.write(token_stats)
                    
                    # Добавляем также JSON-данные для машинной обработки
                    f.write("\n\nJSON DATA:\n")
                    json_data = {
                        "file": args.file_path,
                        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "analysis_time": time.time() - start_time,
                        "api_calls": api_calls,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                        "total_cost_usd": total_cost,
                        "api_duration": duration_total,
                        "models": {
                            model: {
                                "calls": calls_by_model[model],
                                "input_tokens": info["input_tokens"],
                                "output_tokens": info["output_tokens"],
                                "input_cost": info["input_cost"],
                                "output_cost": info["output_cost"],
                                "total_cost": info["total_cost"]
                            } for model, info in model_costs.items()
                        }
                    }
                    f.write(json.dumps(json_data, indent=2))
                
                print(f"Статистика использования токенов сохранена в: {stats_path}")
        except Exception as stats_error:
            logger.error(f"Ошибка при формировании статистики токенов: {str(stats_error)}")
        
        return result
    except Exception as e:
        logger.error(f"Ошибка при выполнении анализа: {str(e)}")
        return 1

if __name__ == "__main__":
    args = parse_arguments()
    sys.exit(run_analysis(args))