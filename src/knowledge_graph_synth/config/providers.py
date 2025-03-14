"""LLM provider configurations."""

from typing import Dict, Any, Optional, List

from . import settings

# Gemini API configuration
GEMINI_CONFIG = {
    "api_key": settings.get_api_key("gemini"),
    "models": settings.GEMINI_MODELS,
    "generation_config": settings.DEFAULT_GENERATION_CONFIG,
    # Safety settings are handled differently in the new SDK
    # These will be converted to the appropriate format in the provider class
    "safety_settings": {
        "HARM_CATEGORY_HARASSMENT": "BLOCK_ONLY_HIGH",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_ONLY_HIGH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_ONLY_HIGH",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_ONLY_HIGH",
    },
}

# OpenAI API configuration (optional)
OPENAI_CONFIG = {
    "api_key": settings.get_api_key("openai"),
    "models": {
        "default": "gpt-4o",
        "fast": "gpt-4o-mini",
    },
    "generation_config": {
        "temperature": 0.1,
        "max_tokens": 4096,
    },
}

# Anthropic API configuration (optional)
ANTHROPIC_CONFIG = {
    "api_key": settings.get_api_key("anthropic"),
    "models": {
        "default": "claude-3-opus-20240229",
        "fast": "claude-3-sonnet-20240229",
    },
    "generation_config": {
        "temperature": 0.1,
        "max_tokens": 4096,
    },
}

# DeepSeek API configuration (optional)
DEEPSEEK_CONFIG = {
    "api_key": settings.get_api_key("deepseek"),
    "models": {
        "default": "deepseek-coder",
    },
    "generation_config": {
        "temperature": 0.1,
        "max_tokens": 4096,
    },
}

# Map of all available providers
PROVIDER_CONFIGS = {
    "gemini": GEMINI_CONFIG,
    "openai": OPENAI_CONFIG,
    "anthropic": ANTHROPIC_CONFIG,
    "deepseek": DEEPSEEK_CONFIG,
}


def get_provider_config(provider_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific provider.
    
    Args:
        provider_name: Name of the provider
        
    Returns:
        Provider configuration or None if not available/configured
    """
    config = PROVIDER_CONFIGS.get(provider_name.lower())
    if not config:
        return None
    
    # Check if API key is available
    if not config.get("api_key"):
        return None
    
    return config


def list_available_providers() -> List[str]:
    """List names of available and configured providers.
    
    Returns:
        List of provider names that have API keys configured
    """
    return [
        name for name, config in PROVIDER_CONFIGS.items()
        if config.get("api_key")
    ]