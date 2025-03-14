"""Application settings for the knowledge graph synthesis system."""

import os
from pathlib import Path
from typing import Dict, Any, Optional

import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SRC_DIR = BASE_DIR / "src"
CACHE_DIR = Path(os.getenv("CACHE_DIR", BASE_DIR / ".cache"))

# Ensure cache directory exists
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Language settings
SUPPORTED_LANGUAGES = ["en", "ru"]
DEFAULT_LANGUAGE = "en"

# Text processing settings
MAX_SEGMENT_LENGTH = 25000  # Maximum characters per segment (увеличено для более смысловых кусков)
MAX_SEGMENT_OVERLAP = 800  # Overlap between segments (увеличено для лучшей связности)

# LLM settings
DEFAULT_LLM_PROVIDER = "gemini"
LLM_TIMEOUT = 300  # Seconds (увеличен для больших запросов)
LLM_MAX_RETRIES = 5  # Повышенное количество повторных попыток
LLM_DELAY_BETWEEN_REQUESTS = 5.0  # Задержка между запросами в секундах (увеличена для снижения вероятности превышения квоты)
LLM_MEGA_BATCH_SIZE = 100  # Количество сегментов для мега-батчевой обработки в одном запросе
LLM_BATCH_SIZE = 25  # Количество сегментов для обычной батчевой обработки в одном запросе
LLM_CONTEXT_WINDOW_SIZE = 500000  # Размер контекстного окна для моделей Gemini (в токенах)

# Gemini model configuration
GEMINI_MODELS = {
    "default": "gemini-2.0-pro-exp-02-05",  # Using pro-exp model as default for JSON tasks
    "fast": "gemini-2.0-flash",
    "reasoning": "gemini-2.0-pro-exp-02-05",  # Pro model for reasoning tasks requiring JSON
    "thinking": "gemini-2.0-flash-thinking-exp-01-21"  # Using thinking model for free-form text generation
}

# Default generation parameters
DEFAULT_GENERATION_CONFIG = {
    "temperature": 0.1,  # Lower temperature for more deterministic outputs
    "top_p": 0.95,
    "top_k": 0,
    "max_output_tokens": 8192,
}

# Graph settings
DEFAULT_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence score for entities and relationships

# Output settings
DEFAULT_OUTPUT_FORMAT = "markdown"
AVAILABLE_OUTPUT_FORMATS = ["markdown", "html", "json"]


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a specific provider.
    
    Args:
        provider: The LLM provider name
        
    Returns:
        API key or None if not found
    """
    key_map = {
        "gemini": "GOOGLE_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }
    
    env_var = key_map.get(provider.lower())
    if not env_var:
        return None
    
    return os.getenv(env_var)