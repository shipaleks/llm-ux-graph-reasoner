# Knowledge Graph Synthesis Scripts

This directory contains utility scripts to simplify running the knowledge graph synthesis system.

## Available Scripts

### 1. `process_text.sh`

Process a single text file with the knowledge graph synthesis system.

```bash
./process_text.sh file_path [output_dir] [chunk_size] [delay] [mode] [expand_flag] [metagraph_flag]
```

**Parameters:**
- `file_path`: Path to the input text file (required)
- `output_dir`: Directory to store the output (default: `output`)
- `chunk_size`: Number of segments to process in each chunk (default: 10)
- `delay`: Delay in seconds between processing chunks (default: 30)
- `mode`: Processing mode - `gradual` or `full` (default: `gradual`)
- `expand_flag`: Flag to enable graph expansion (--expand-graph)
- `metagraph_flag`: Flag to enable meta-graph creation (--build-metagraph)

**Examples:**
```bash
# Basic processing with gradual mode
./.scripts/process_text.sh merged.txt output/my_analysis 15 45 gradual

# With recursive graph expansion
./.scripts/process_text.sh merged.txt output/my_analysis 15 45 gradual "--expand-graph"

# With meta-graph creation
./.scripts/process_text.sh merged.txt output/my_analysis 15 45 gradual "" "--build-metagraph"

# Full analysis with all features
./.scripts/process_text.sh merged.txt output/my_analysis 15 45 gradual "--expand-graph" "--build-metagraph"
```

### 2. `analyze_large_file.sh`

Process a large text file with optimized settings to avoid API rate limits. Includes an interactive menu to select advanced analysis features.

```bash
./analyze_large_file.sh file_path [output_dir]
```

**Parameters:**
- `file_path`: Path to the input text file (required)
- `output_dir`: Directory to store the output (default: `output/large_file`)

**Features:**
- Optimized settings for processing large files
- Interactive menu to select advanced analysis options:
  1. Basic analysis (default)
  2. Include recursive graph expansion
  3. Include meta-graph creation
  4. Full analysis with all features

**Example:**
```bash
./.scripts/analyze_large_file.sh large_document.txt output/large_doc_analysis
```

### 3. `batch_process.sh`

Process multiple text files in batch mode.

```bash
./batch_process.sh input_dir [output_dir] [mode]
```

**Parameters:**
- `input_dir`: Directory containing input text files (required)
- `output_dir`: Base directory for output (default: `output/batch`)
- `mode`: Processing mode - `gradual` or `full` (default: `gradual`)

**Example:**
```bash
./.scripts/batch_process.sh data/documents output/batch_results gradual
```

### 4. `config.sh`

Configuration file for knowledge graph synthesis. Edit this file to change the default settings.

## Configuration

You can set environment variables to customize the behavior of the knowledge graph synthesis:

```bash
# Processing settings
export KGS_CHUNK_SIZE=10            # Default chunk size for gradual processing
export KGS_CHUNK_DELAY=30           # Default delay between chunks (seconds)

# Mega-batch settings
export KGS_ENTITY_MEGA_BATCH_SIZE=100   # Maximum entities per mega-batch
export KGS_RELATION_MEGA_BATCH_SIZE=50  # Maximum relationships per mega-batch
export KGS_API_DELAY=5                  # Delay between API calls (seconds)

# Language model settings
export KGS_DEFAULT_PROVIDER="gemini"    # Default LLM provider
```

You can set these variables before running any script, or modify the `config.sh` file.

## Examples

### Process a small file:
```bash
./.scripts/process_text.sh examples/sample.txt
```

### Process a large file with optimized settings:
```bash
./.scripts/analyze_large_file.sh merged.txt
```

### Process all text files in a directory:
```bash
./.scripts/batch_process.sh examples/
```