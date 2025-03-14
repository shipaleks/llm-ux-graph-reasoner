"""LLM provider factory for the knowledge graph synthesis system."""

import logging
from typing import Dict, List, Optional, Any, Union

from .base import LLMProvider
from .gemini import GeminiProvider
from .gemini_reasoning import GeminiReasoningProvider
from ..config import settings, providers

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """Factory for creating LLM provider instances.
    
    This class manages the creation of LLM provider instances, handling
    configuration and provider selection.
    """
    
    # Registry of provider classes
    _provider_classes = {
        "gemini": GeminiProvider,
        "gemini_reasoning": GeminiReasoningProvider,
        # Add other providers here as they are implemented
    }
    
    # Cache of provider instances
    _provider_instances = {}
    
    @classmethod
    def get_provider(cls, provider_name: str = None) -> Optional[LLMProvider]:
        """Get an LLM provider instance.
        
        Args:
            provider_name: Name of the provider to get (default from settings if None)
            
        Returns:
            LLM provider instance or None if not available
        
        Raises:
            ValueError: If provider is not supported or not configured
        """
        # Use default provider if none specified
        if provider_name is None:
            provider_name = settings.DEFAULT_LLM_PROVIDER
        
        # Check if we have a cached instance
        if provider_name in cls._provider_instances:
            return cls._provider_instances[provider_name]
        
        # Get provider class
        provider_class = cls._provider_classes.get(provider_name)
        if not provider_class:
            available = ", ".join(cls._provider_classes.keys())
            raise ValueError(f"Unsupported provider: {provider_name}. Available providers: {available}")
        
        # Get provider config
        provider_config = providers.get_provider_config(provider_name)
        if not provider_config:
            available = ", ".join(providers.list_available_providers())
            raise ValueError(f"Provider {provider_name} not configured or missing API key. "
                           f"Available configured providers: {available}")
        
        # Create provider instance
        try:
            provider = provider_class(provider_config)
            cls._provider_instances[provider_name] = provider
            return provider
        except Exception as e:
            logger.error(f"Error creating provider {provider_name}: {str(e)}")
            raise
    
    @classmethod
    def list_available_providers(cls) -> List[str]:
        """List names of available providers.
        
        Returns:
            List of provider names that are implemented
        """
        return list(cls._provider_classes.keys())
    
    @classmethod
    def list_configured_providers(cls) -> List[str]:
        """List names of configured providers.
        
        Returns:
            List of provider names that have API keys configured
        """
        return providers.list_available_providers()
    
    @classmethod
    def get_reasoning_provider(cls) -> Optional[LLMProvider]:
        """Get a provider optimized for reasoning tasks.
        
        Returns:
            LLM provider instance specialized for reasoning
        """
        # Try to get the reasoning-specific provider first
        try:
            return cls.get_provider("gemini_reasoning")
        except ValueError:
            # Fall back to regular Gemini provider
            try:
                return cls.get_provider("gemini")
            except ValueError:
                # Fall back to any available provider
                available = cls.list_configured_providers()
                if available:
                    return cls.get_provider(available[0])
                
                return None
                
    @classmethod
    def get_thinking_provider(cls) -> Optional[LLMProvider]:
        """Get a provider optimized for thinking/free-form text generation tasks.
        Note: This provider may not support structured JSON output.
        
        Returns:
            LLM provider instance specialized for thinking
        """
        # Use the regular Gemini provider but specify the thinking model
        try:
            provider = cls.get_provider("gemini")
            if provider:
                # Set the model to thinking for free-form text generation
                # But keep the default model for JSON/structured output
                provider.set_preferred_model("thinking")
            return provider
        except ValueError:
            # Fall back to any available provider
            available = cls.list_configured_providers()
            if available:
                return cls.get_provider(available[0])
            
            return None