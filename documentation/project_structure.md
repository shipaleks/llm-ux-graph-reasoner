# Project Structure

This document outlines the recommended file and directory structure for the Knowledge Graph Synthesis project.

```
knowledge_graph_synth/              # Root project directory
│
├── .cursor/                        # Cursor editor configuration
│   └── rules/                      # Rules for Cursor agent
│       ├── cursorrules.md          # Main rules file
│       └── structure.mdc           # Auto-generated structure file
│
├── .scripts/                       # Utility scripts
│   └── update_structure.sh         # Updates project structure documentation
│
├── documentation/                  # Project documentation
│   ├── prd.md                      # Product Requirements Document
│   ├── app_flow.md                 # Application Flow Document
│   ├── tech_stack.md               # Technology Stack Document
│   ├── implementation_plan.md      # Implementation Plan
│   ├── project_structure.md        # Project Structure Document (this file)
│   └── full_description.md         # Detailed project description in Russian
│
├── src/                            # Source code
│   ├── knowledge_graph_synth/      # Main package
│   │   ├── __init__.py             # Package initialization
│   │   ├── config/                 # Configuration 
│   │   │   ├── __init__.py
│   │   │   ├── settings.py         # Application settings
│   │   │   └── providers.py        # LLM provider configurations
│   │   │
│   │   ├── models/                 # Data models
│   │   │   ├── __init__.py
│   │   │   ├── segment.py          # Text segment models
│   │   │   ├── entity.py           # Entity models
│   │   │   ├── relationship.py     # Relationship models
│   │   │   ├── graph.py            # Graph models
│   │   │   ├── provenance.py       # Data provenance tracking
│   │   │   └── output.py           # Output models
│   │   │
│   │   ├── text/                   # Text processing
│   │   │   ├── __init__.py
│   │   │   ├── loader.py           # Text file loading
│   │   │   ├── normalizer.py       # Text normalization
│   │   │   ├── segmenter.py        # Text segmentation
│   │   │   └── context.py          # Context preservation
│   │   │
│   │   ├── llm/                    # LLM integration
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Base LLM provider interface
│   │   │   ├── gemini.py           # Gemini-specific implementation
│   │   │   ├── gemini_reasoning.py # Gemini reasoning model implementation
│   │   │   ├── gpt.py              # GPT-specific implementation (optional)
│   │   │   ├── claude.py           # Claude-specific implementation (optional)
│   │   │   ├── deepseek.py         # DeepSeek-specific implementation (optional)
│   │   │   ├── ollama.py           # Ollama-specific implementation (optional)
│   │   │   ├── factory.py          # LLM provider factory
│   │   │   ├── prompts/            # Prompt templates
│   │   │   │   ├── __init__.py
│   │   │   │   ├── en/             # English templates
│   │   │   │   └── ru/             # Russian templates
│   │   │   ├── schemas/            # Response schemas for structured output
│   │   │   │   ├── __init__.py
│   │   │   │   ├── entity.py       # Entity extraction schemas
│   │   │   │   ├── relationship.py # Relationship extraction schemas
│   │   │   │   └── theory.py       # Theory generation schemas
│   │   │   ├── validation.py       # Response validation
│   │   │   └── cache.py            # Response caching
│   │   │
│   │   ├── extraction/             # Entity and relationship extraction
│   │   │   ├── __init__.py
│   │   │   ├── entity_extractor.py # Entity extraction
│   │   │   ├── relation_extractor.py # Relationship extraction
│   │   │   ├── coreference.py      # Coreference resolution
│   │   │   └── grounding.py        # Grounding extracted entities to source text
│   │   │
│   │   ├── graph/                  # Knowledge graph construction and analysis
│   │   │   ├── __init__.py
│   │   │   ├── builder.py          # Graph construction
│   │   │   ├── analysis.py         # Graph analysis
│   │   │   ├── expansion.py        # Graph expansion
│   │   │   ├── metagraph.py        # Meta-graph creation
│   │   │   ├── verification.py     # Graph consistency verification
│   │   │   └── visualization.py    # Graph visualization
│   │   │
│   │   ├── theory/                 # Theory and hypothesis generation
│   │   │   ├── __init__.py
│   │   │   ├── pattern_finder.py   # Pattern identification
│   │   │   ├── theory_generator.py # Theory generation
│   │   │   ├── hypothesis.py       # Hypothesis generation and testing
│   │   │   ├── evaluator.py        # Evaluation of hypotheses
│   │   │   └── evidence.py         # Evidence tracking and grounding
│   │   │
│   │   ├── output/                 # Output generation
│   │   │   ├── __init__.py
│   │   │   ├── formatter.py        # Output formatting
│   │   │   ├── report.py           # Report generation
│   │   │   ├── visualizer.py       # Visualization generation
│   │   │   ├── citation.py         # Source citation and evidence linking
│   │   │   └── templates/          # Output templates
│   │   │       ├── scientific.j2   # Scientific report template
│   │   │       ├── literary.j2     # Literary analysis template
│   │   │       └── interview.j2    # Interview analysis template
│   │   │
│   │   └── cli/                    # Command line interface
│   │       ├── __init__.py
│   │       ├── commands.py         # CLI commands
│   │       └── utils.py            # CLI utilities
│   │
│   └── main.py                     # Main entry point
│
├── tests/                          # Tests
│   ├── __init__.py
│   ├── conftest.py                 # Test configuration
│   ├── unit/                       # Unit tests
│   │   ├── __init__.py
│   │   ├── test_text.py            # Tests for text processing
│   │   ├── test_llm.py             # Tests for LLM integration
│   │   ├── test_extraction.py      # Tests for extraction
│   │   ├── test_graph.py           # Tests for graph operations
│   │   ├── test_theory.py          # Tests for theory generation
│   │   └── test_output.py          # Tests for output generation
│   │
│   ├── integration/                # Integration tests
│   │   ├── __init__.py
│   │   └── test_pipeline.py        # End-to-end pipeline tests
│   │
│   └── data/                       # Test data
│       ├── samples/                # Sample input texts
│       └── fixtures/               # Test fixtures
│
├── examples/                       # Example usage
│   ├── scientific_papers.py        # Example with scientific papers
│   ├── literary_analysis.py        # Example with literary text
│   └── interview_analysis.py       # Example with interviews
│
├── pyproject.toml                  # Project metadata and dependencies
├── poetry.lock                     # Locked dependencies
├── README.md                       # Project overview
├── CONTRIBUTING.md                 # Contribution guidelines
├── LICENSE                         # License information
├── .env                            # Environment variables (API keys, etc.)
└── merged.txt                      # Sample large text file for testing
```

## Key Directories and Files Explained

### `/src/knowledge_graph_synth`

This is the main package directory containing all the source code. It's organized by functional modules:

- `config`: Application configuration and settings
- `models`: Data models and domain objects, including provenance tracking
- `text`: Text processing and segmentation
- `llm`: LLM provider integration, prompting, and response schemas
- `extraction`: Entity and relationship extraction with grounding
- `graph`: Knowledge graph operations and verification
- `theory`: Theory and hypothesis generation with evidence tracking
- `output`: Output formatting and generation with citation support
- `cli`: Command-line interface

### New and Modified Components for Hallucination Reduction

- `models/provenance.py`: Tracks the origin and evidence for each piece of information
- `llm/schemas/`: Defines structured JSON response schemas for Gemini API
- `llm/gemini_reasoning.py`: Special handling for the reasoning model variant
- `extraction/grounding.py`: Ensures extracted entities are grounded in source text
- `theory/evidence.py`: Tracks supporting evidence for generated theories
- `output/citation.py`: Links output content to source text

### Gemini-Specific Components

- `llm/gemini.py`: Implementation for 'gemini-2.0-flash' and 'gemini-2.0-pro-exp-02-05'
- `llm/gemini_reasoning.py`: Implementation for 'gemini-2.0-flash-thinking-exp-01-21'
- `llm/schemas/`: Response schemas for structured JSON output with Gemini

### Testing Support Files

- `.env`: Contains API keys and configuration for testing
- `merged.txt`: Large text file for real-world testing

### `/documentation`

Contains all project documentation:

- `prd.md`: Product Requirements Document
- `app_flow.md`: Application Flow Document
- `tech_stack.md`: Technology Stack Document
- `implementation_plan.md`: Implementation Plan
- `project_structure.md`: Project Structure Document
- `full_description.md`: Detailed project description in Russian

## Design Principles

The project structure follows these design principles:

1. **Separation of Concerns**: Each module has a specific responsibility
2. **Discoverability**: File names clearly indicate their purpose
3. **Modularity**: Components can be developed and tested independently
4. **Scalability**: Structure allows for future extensions
5. **Testability**: Structured to facilitate comprehensive testing
6. **Verifiability**: Components for tracking data provenance and grounding
7. **Bilingual Support**: Structure accommodates both English and Russian

## Hallucination Mitigation Strategy

The structure includes several components designed to minimize hallucinations:

1. **Provenance Tracking**: Every piece of information is linked to its source
2. **Response Schemas**: Structured output formats to constrain LLM responses
3. **Grounding**: Explicit verification that extracted entities exist in source text
4. **Evidence Tracking**: Theories and hypotheses linked to supporting evidence
5. **Citation Generation**: Output includes links to source text
6. **Verification Steps**: Explicit verification of graph consistency