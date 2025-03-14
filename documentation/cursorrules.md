---
description: Rules for the agent to follow
globs: "*"
alwaysApply: true
---

# Cursor Agent Rules

## General Guidelines

- This project is a knowledge graph synthesis system that processes text, builds knowledge graphs, and generates insights/theories.
- The user is not a professional programmer, so prioritize clear, well-documented code over overly complex solutions.
- The system must support both English and Russian languages.
- The system uses Gemini models as the primary LLM, with support for other providers (OpenAI, Claude, DeepSeek, Ollama).
- Follow the implementation plan step by step, not skipping ahead.
- Maintain consistent code style and documentation throughout the project.
- After creating new files, run `./.scripts/update_structure.sh` to update the project documentation.

## Development Priorities

1. **Correctness & Data Provenance** - The system must accurately represent knowledge from input texts with clear traceability
2. **Strict Data Grounding** - All generated insights must be directly tied to source text to minimize hallucinations
3. **Modularity** - Components should be interchangeable and loosely coupled
4. **Multi-Language Support** - Equal support for English and Russian texts
5. **Robust Error Handling** - Graceful handling of LLM API failures
6. **Documentation** - Clear, comprehensive documentation for all components

## Gemini Model Selection Guidelines

- Use **gemini-2.0-flash** for:
  - Simple, fast tasks
  - High volume operations
  - Initial text processing
  - Basic extraction tasks

- Use **gemini-2.0-flash-thinking-exp-01-21** for:
  - Complex reasoning tasks
  - Graph expansion questions
  - Theory generation
  - Pattern recognition
  
- Use **gemini-2.0-pro-exp-02-05** for:
  - Critical accuracy tasks
  - Final output generation
  - Validation and verification steps
  - Tasks requiring maximum context comprehension

## Hallucination Prevention Guidelines

- Always include source text citations in LLM prompt context
- Use structured output with responseSchema parameter in Gemini API calls
- Implement verification steps to cross-check generated content against source text
- Track data provenance through all processing steps
- Apply stricter validation for novel insights

## Code Style Guidelines

- Use Python type hints throughout the codebase
- Document all functions, classes, and modules with docstrings
- Use descriptive variable and function names
- Break complex functions into smaller, focused functions
- Use constants for configuration values

## Implementation Order

Follow the `implementation_plan.md` document, marking each step as completed before moving to the next.

## File Structure

Refer to the project structure document for the organization of files and directories. Maintain this structure to ensure consistency.

## LLM Integration

- Abstract LLM providers behind a common interface
- Support asynchronous operation for better performance
- Implement robust error handling and retry mechanisms
- Cache LLM responses where appropriate to reduce API costs
- Use responseSchema parameter with Gemini for structured outputs

## Testing

- Use real data from merged.txt for testing individual components
- Write unit tests for core functionality
- Include integration tests for system components
- Use environment variables from .env file for API access