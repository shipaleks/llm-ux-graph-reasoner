# Knowledge Graph Synthesis

A system that processes text documents, extracts entities and relationships, constructs knowledge graphs, and generates insights and theories. The system supports both Russian and English texts and uses Gemini models as the LLM provider.

## Quick Start

To begin working with the system, use the following scripts:

### Text Analysis

```bash
# Currently, only the English analysis script is working
# Analyze a text file with graph expansion and theory generation
./analyze_text_en.py /path/to/file.txt --expand --theories
```

### Viewing Results

```bash
# Fix links and open the latest report
./fix_and_open.py

# Fix links and open a report in the specified directory
./fix_and_open.py --dir output/20250306_063450
```

## Features

- Bilingual support (Russian and English)
- Gemini LLM integration
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

Currently, only the English analysis script is functional:

```bash
# Analyze a text file with graph expansion and theory generation
./analyze_text_en.py /path/to/document.txt --expand --theories

# Fix links and open the report
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

### Parameters for analyze_text_en.py Script

- `file_path` - path to the text file for analysis
- `--expand`, `-e` - expand the graph by asking questions
- `--theories`, `-t` - generate theories based on the graph
- `--no-segments`, `-n` - skip segment analysis
- `--output`, `-o` - output directory (default: output)

### Analysis Results

After completing the analysis, a new folder with a timestamp is created in the output directory containing the following files:

- `report.html` - main report with analysis results
- `graphs/` - knowledge graph visualizations
  - `knowledge_graph.html` - interactive knowledge graph
  - `expanded/expanded_graph.html` - expanded graph (if requested)
- `segments/` - HTML pages with segment text
- `entities/` - extracted entities in JSON format
- `relationships/` - extracted relationships in JSON format
- `theories/` - generated theories (if requested)
- `context/` - context analysis results

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