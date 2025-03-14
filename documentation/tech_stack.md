# Technology Stack

This document outlines the technologies, libraries, and frameworks that will be used to build the Knowledge Graph Synthesis system, with a focus on Gemini models and hallucination mitigation.

## Core Technologies

### Programming Language
- **Python 3.9+**: Selected for its simplicity, readability, and extensive libraries for NLP and graph processing.

### Development Environment
- **Visual Studio Code with Cursor**: For enhanced AI-assisted development.
- **Poetry**: For dependency management and packaging.
- **Pre-commit hooks**: For code quality enforcement.

## Key Components and Libraries

### Text Processing

- **spaCy**: For basic NLP tasks such as sentence segmentation and tokenization.
  - Supports both English and Russian languages
  - Provides good performance for text processing tasks
  - Easy to use API

- **Langdetect**: For automatic language detection to handle both English and Russian texts.

- **Diff-match-patch**: For text comparison and grounding verification.
  - Helps verify entity presence in source text
  - Facilitates citation generation

### LLM Integration

- **Google's Generative AI Python SDK**: For interacting with Gemini models.
  - Official SDK for Google's Gemini models
  - Supports structured output via `responseSchema`
  - Handles authentication and API management

- **Gemini Models**:
  - `gemini-2.0-flash`: For simple extraction tasks
  - `gemini-2.0-flash-thinking-exp-01-21`: For complex reasoning tasks (with special prompting)
  - `gemini-2.0-pro-exp-02-05`: For critical tasks requiring high accuracy

- **Optional Alternative LLMs**:
  - **OpenAI API**: Via `openai` Python package
  - **Anthropic Claude API**: Via `anthropic` Python package
  - **DeepSeek API**: Via appropriate client library
  - **Ollama**: For local LLM deployment via its REST API

### Graph Processing and Analysis

- **NetworkX**: For graph representation, analysis, and manipulation.
  - Provides comprehensive graph algorithms
  - Easy to use and extend
  - Good performance for medium-sized graphs
  - Extensive documentation

- **PyVis** or **Pyvis-Network**: For interactive graph visualization.
  - Creates interactive HTML visualizations
  - Supports various layout algorithms
  - Can be integrated into reports

- **Community**: For community detection in graphs.
  - Implements Louvain method for community detection
  - Works well with NetworkX

### Schema and Validation

- **Pydantic**: For data validation and schema definition.
  - Enforces data structure and types
  - Helps with LLM response validation
  - Integrates well with response schemas

- **JSON Schema**: For defining structured output formats for Gemini.
  - Works with Gemini's `responseSchema` parameter
  - Helps constrain LLM output to reduce hallucinations

### Provenance and Evidence Tracking

- **Span markers**: Custom implementation for text span identification.
  - Helps with precise source citation
  - Supports evidence tracking

- **Checksums**: For content verification.
  - Ensures data integrity
  - Helps validate source references

### Asynchronous Processing

- **asyncio**: For asynchronous operations.
  - Core Python library for asynchronous programming
  - Allows efficient handling of I/O-bound operations like API calls

- **aiohttp**: For asynchronous HTTP requests.
  - Works well with asyncio
  - Efficient for making multiple HTTP requests

### Storage and Caching

- **SQLite**: For lightweight data storage.
  - No additional database server required
  - Simple to set up and use
  - Sufficient for prototype and moderate usage

- **DiskcCache**: For caching LLM responses.
  - Persistent disk-based cache
  - Thread-safe and process-safe
  - Simple API

### Environment Management

- **python-dotenv**: For loading environment variables from .env files.
  - Simplifies API key management
  - Supports development and testing configurations

### Testing

- **pytest**: For unit and integration testing.
  - Widely used testing framework for Python
  - Good support for test fixtures and parameterization
  - Supports async testing

- **VCR.py**: For recording and replaying HTTP interactions in tests.
  - Reduces API costs during testing
  - Makes tests reproducible and faster

## Interface and Output

- **Rich**: For enhanced console output.
  - Provides progress bars, tables, and rich formatting
  - Makes console output more informative and readable

- **Jinja2**: For templating output reports.
  - Flexible template engine
  - Used for generating HTML and Markdown reports

- **Markdown**: As the primary format for documentation and reports.
  - Simple, widely supported text format
  - Easy to convert to other formats (HTML, PDF)

## Deployment and Distribution

- **Docker**: For containerization (optional for advanced users).
  - Ensures consistent environment
  - Simplifies deployment

- **setuptools**: For package building and distribution.
  - Standard Python packaging tool
  - Allows easy installation of the tool

## Development Tools

- **Black**: For code formatting.
  - Enforces consistent code style
  - Reduces time spent on formatting decisions

- **Flake8**: For linting.
  - Identifies common coding errors
  - Enforces PEP 8 style guide

- **mypy**: For static type checking.
  - Helps identify type-related errors early
  - Improves code documentation and IDE assistance

## Technology Selection Rationale

The technology stack was selected based on several criteria:

1. **Accessibility for non-professional programmers**: Libraries with clear documentation and straightforward APIs.
2. **Maturity and community support**: Well-established libraries with active maintenance.
3. **Performance adequate for the task**: Efficient enough for processing moderate amounts of text.
4. **Minimal infrastructure requirements**: Avoiding complex setup requirements.
5. **Flexibility for multiple LLM providers**: Allowing easy switching between different LLMs.
6. **Bilingual support**: Capabilities to handle both English and Russian texts.
7. **Hallucination mitigation**: Tools that support data provenance and verification.

## Hallucination Mitigation Technologies

The following technologies specifically address the challenge of reducing hallucinations:

1. **Pydantic & JSON Schema**: Enforce structured outputs from LLMs
2. **Span markers & checksums**: Track text provenance and validate citations
3. **Diff-match-patch**: Verify entity presence in source text
4. **Structured response schemas**: Define expected response formats for Gemini
5. **Evidence tracking library**: Custom implementation for linking claims to evidence

## Gemini Integration Specifics

Gemini integration uses the official Google Generative AI SDK with the following configuration:

```python
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Configure the API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Specific model configuration
generation_config = {
    "temperature": 0.1,  # Lower temperature for more deterministic outputs
    "top_p": 0.95,
    "top_k": 0,
    "max_output_tokens": 8192,
}

# Safety settings
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

# Response schema for structured output
entity_schema = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "attributes": {"type": "array", "items": {"type": "string"}},
                    "source_span": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "integer"},
                            "end": {"type": "integer"},
                            "text": {"type": "string"}
                        },
                        "required": ["start", "end", "text"]
                    },
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["name", "type", "source_span", "confidence"]
            }
        }
    },
    "required": ["entities"]
}

# Example Gemini API call with response schema
model = genai.GenerativeModel(
    model_name="gemini-2.0-pro-exp-02-05",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

response = model.generate_content(
    contents="Extract entities from this text: " + text_segment,
    response_schema=entity_schema
)
```

This approach ensures structured, consistent outputs from Gemini that can be easily validated and used for downstream tasks.