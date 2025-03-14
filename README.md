# Knowledge Graph Synthesis

A system that processes text documents, extracts entities and relationships, constructs knowledge graphs, and generates insights and theories. The system supports both Russian and English texts and uses Gemini models as the primary LLM provider.

## Быстрый старт

Для начала работы с системой используйте следующие скрипты:

### Анализ текста

```bash
# Анализ текстового файла с созданием графа знаний
./analyze_text.py путь_к_файлу.txt

# Анализ с расширением графа и генерацией теорий
./analyze_text.py путь_к_файлу.txt --expand --theories

# Использование другого провайдера LLM
./analyze_text.py путь_к_файлу.txt --provider openai
```

### Просмотр результатов

```bash
# Исправление ссылок и открытие последнего отчета
./fix_and_open.py

# Исправление ссылок и открытие отчета в указанной директории
./fix_and_open.py --dir output/20250306_063450
```

## Features

- Bilingual support (Russian and English)
- Multiple LLM provider support (primarily Gemini)
- Strict data provenance tracking
- Modular, replaceable components
- Entity and relationship extraction
- Knowledge graph construction and analysis
- Theory and hypothesis generation
- Visualization and reporting

## Installation

1. Clone the repository:
```bash
git clone [repository_url]
cd knowledge-graph-synth
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file with your API keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Simplified Scripts

Use the simplified scripts for common operations:

```bash
# Анализ текстового файла
./analyze_text.py path/to/document.txt

# Анализ с расширением графа и генерацией теорий
./analyze_text.py path/to/document.txt --expand --theories

# Исправление ссылок и открытие отчета
./fix_and_open.py
```

### Command Line Interface

Process a text file with the command line interface:

```bash
# Basic processing
poetry run python src/main.py process --file path/to/document.txt --extract --build-graph --generate-theories

# Gradual processing for large files (prevents API rate limits)
poetry run python src/main.py process --file path/to/large_document.txt --extract --build-graph --generate-theories --gradual

# Recursive expansion of knowledge graph
poetry run python src/main.py process --file path/to/document.txt --extract --build-graph --expand-graph --generate-theories

# Building meta-graph (higher level abstractions)
poetry run python src/main.py process --file path/to/document.txt --extract --build-graph --build-metagraph --generate-theories

# Full analysis with all features
poetry run python src/main.py process --file path/to/document.txt --extract --build-graph --expand-graph --build-metagraph --generate-theories
```

### Параметры скрипта analyze_text.py

- `file_path` - путь к текстовому файлу для анализа
- `--provider`, `-p` - провайдер LLM: gemini (по умолчанию) или openai
- `--expand`, `-e` - расширить граф через задание вопросов
- `--theories`, `-t` - генерировать теории на основе графа
- `--no-segments`, `-n` - пропустить анализ по сегментам
- `--output`, `-o` - директория для вывода результатов (по умолчанию: output)

### Результаты анализа

После завершения анализа в директории output создается новая папка с временной меткой, содержащая следующие файлы:

- `report.html` - основной отчет с результатами анализа
- `graphs/` - визуализации графа знаний
  - `knowledge_graph.html` - интерактивный граф знаний
  - `expanded/expanded_graph.html` - расширенный граф (если запрошен)
- `segments/` - HTML-страницы с текстом сегментов
- `entities/` - извлеченные сущности в формате JSON
- `relationships/` - извлеченные отношения в формате JSON
- `theories/` - сгенерированные теории (если запрошены)
- `context/` - результаты контекстного анализа

### Programmatic Usage

```python
from knowledge_graph_synth.text.loader import TextLoader
from knowledge_graph_synth.extraction.entity_extractor import EntityExtractor
from knowledge_graph_synth.graph.builder import GraphBuilder

# Load text
loader = TextLoader()
segments = loader.load("path/to/document.txt")

# Extract entities and relationships
extractor = EntityExtractor()
entities = extractor.extract(segments)

# Build knowledge graph
builder = GraphBuilder()
graph = builder.build(entities)

# Analyze and expand graph
# ...
```

## Project Structure

- `src/knowledge_graph_synth/`: Main package
  - `config/`: Configuration
  - `models/`: Data models
  - `text/`: Text processing
  - `llm/`: LLM integration
  - `extraction/`: Entity and relationship extraction
  - `graph/`: Knowledge graph operations
  - `theory/`: Theory generation
  - `output/`: Output formatting
  - `cli/`: Command line interface

## Development

1. Install development dependencies:
```bash
poetry install --with dev
```

2. Run tests:
```bash
poetry run pytest
```

3. Run linting:
```bash
poetry run black .
poetry run flake8
poetry run mypy .
```

## License

[License information]