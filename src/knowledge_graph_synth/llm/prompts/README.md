# Prompt Templates

This directory contains prompt templates for different LLM tasks in the knowledge graph synthesis system. The prompts are organized by language (English and Russian) and by category.

## Directory Structure

```
prompts/
├── en/                  # English prompts
│   ├── *.txt            # Root-level prompts
│   ├── contextual/      # Contextual text analysis prompts
│   ├── expansion/       # Graph expansion prompts
│   ├── metagraph/       # Meta-graph prompts
│   └── theory/          # Theory and hypothesis prompts
├── ru/                  # Russian prompts
│   ├── *.txt            # Root-level prompts
│   ├── contextual/      # Contextual text analysis prompts
│   ├── expansion/       # Graph expansion prompts
│   ├── metagraph/       # Meta-graph prompts
│   └── theory/          # Theory and hypothesis prompts
└── __init__.py          # Prompt manager module
```

## Prompt Categories

### Core Prompts (Root Level)

- `entity_extraction.txt`: Extract entities from text
- `relationship_extraction.txt`: Extract relationships between entities
- `domain_entity_extraction.txt`: Domain-specific entity extraction
- `coreference_resolution.txt`: Resolve entity coreferences

### Contextual Analysis Prompts

- `contextual/hierarchical_segmentation.txt`: Segment text hierarchically
- `contextual/segment_summarization.txt`: Summarize text segments
- `contextual/cross_segment_analysis.txt`: Analyze connections between segments

### Graph Expansion Prompts

- `expansion/identify_targets.txt`: Identify targets for expansion
- `expansion/deep_reasoning.txt`: Generate in-depth reasoning
- `expansion/extract_knowledge.txt`: Extract knowledge from reasoning

### Meta-Graph Prompts

- `metagraph/cluster_analysis.txt`: Analyze clusters for meta-concepts
- `metagraph/metaconcept_generation.txt`: Generate meta-concepts
- `metagraph/metarelationship_analysis.txt`: Analyze meta-relationships

### Theory Prompts

- `theory/pattern_identification.txt`: Identify patterns in the graph
- `theory/theory_formulation.txt`: Formulate theories
- `theory/hypothesis_generation.txt`: Generate hypotheses
- `theory/hypothesis_testing.txt`: Test hypotheses

## Usage

Access prompts through the `prompt_manager` singleton:

```python
from knowledge_graph_synth.llm import prompt_manager

# Get a prompt by name and language
prompt = prompt_manager.get_prompt("entity_extraction", "en")

# Get a prompt from a category
prompt = prompt_manager.get_prompt("contextual/hierarchical_segmentation", "en")

# Format a prompt with variables
formatted_prompt = prompt_manager.format_prompt(
    "entity_extraction", 
    "en", 
    text="Sample text to analyze",
    schema=json_schema
)
```

## Template Variables

Prompt templates use the `{{variable_name}}` syntax for substitution. Common variables include:

- `{{text}}`: Text content to analyze
- `{{schema}}`: JSON schema for structured output
- Domain-specific variables depending on the prompt

## Adding New Prompts

1. Create a `.txt` file in the appropriate language and category directory
2. Use `{{variable_name}}` for template variables
3. Restart the application for the prompts to be reloaded

The `PromptManager` will automatically detect and load new prompt files.