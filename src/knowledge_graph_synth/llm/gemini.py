"""Gemini LLM provider implementation for the knowledge graph synthesis system."""

import json
import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Union

from google import genai
from google.genai import types

from .base import LLMProvider, token_counter
from ..config import settings, providers

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Gemini-specific implementation of the LLM provider interface.
    
    This class interacts with Google's Gemini API to generate text and
    structured responses.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Gemini provider.
        
        Args:
            config: Provider-specific configuration (defaults to config from providers module)
        """
        if config is None:
            config = providers.GEMINI_CONFIG
        
        super().__init__(config)
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        
        # Convert generation config to the new format
        self.generation_config = self._convert_generation_config(config.get("generation_config", {}))
        
        # Set up safety settings
        self.safety_settings = {}
        safety_config = config.get("safety_settings", {})
        
        # Convert string safety settings to the proper enum values
        # Note: Safety settings format needs to be updated for the new SDK
        self.safety_settings = self._convert_safety_settings(safety_config)
        
        # Verify available models
        self._list_available_models()
        
        # Track preferred model type (default, thinking, reasoning)
        self.preferred_model_type = "default"
    
    def set_preferred_model(self, model_type: str):
        """Set the preferred model type for text generation.
        
        Args:
            model_type: Type of model to use ("default", "thinking", "reasoning", etc.)
        """
        if model_type in self.models:
            self.preferred_model_type = model_type
            logger.info(f"Set preferred model type to {model_type}: {self.models.get(model_type)}")
        else:
            logger.warning(f"Unknown model type {model_type}, keeping default")
            self.preferred_model_type = "default"
    
    def _list_available_models(self):
        """Set available Gemini models."""
        try:
            # Use configured model names from settings
            # In production, we could update this to query the API for available models
            available_models = [
                "gemini-2.0-flash", 
                "gemini-2.0-pro-exp-02-05", 
                "gemini-2.0-flash-thinking-exp-01-21"
            ]
            logger.info(f"Available Gemini models (from config): {available_models}")
            
            # Get model mapping from settings
            self.models = self.config.get("models", {})
            if not self.models:
                # Fallback if models not in config
                self.models = {
                    "default": "gemini-2.0-flash", 
                    "fast": "gemini-2.0-flash",
                    "reasoning": "gemini-2.0-pro-exp-02-05",
                    "thinking": "gemini-2.0-flash-thinking-exp-01-21"
                }
            
            logger.info(f"Using models: {self.models}")
        except Exception as e:
            logger.warning(f"Failed to configure models: {str(e)}")
    
    def name(self) -> str:
        """Get the name of the LLM provider.
        
        Returns:
            Provider name
        """
        return "gemini"
    
    async def generate_text(self, prompt: str, 
                         model: Optional[str] = None,
                         **kwargs) -> str:
        """Generate text from a prompt using Gemini.
        
        Args:
            prompt: The prompt text
            model: Specific model to use (defaults to provider's default model)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
        
        Raises:
            Exception: On generation failure
        """
        # Get the actual model name from our mapping or use the provided one
        if model in self.models:
            model_name = self.models[model]
        else:
            # Use preferred model type for generate_text if no specific model requested
            model_name = model or self.models.get(self.preferred_model_type, self.models["default"])
        
        logger.debug(f"Using model: {model_name}")
        
        # Create config by combining generation_config with any additional kwargs
        config = self.generation_config.copy()
        for key, value in kwargs.items():
            config[key] = value
        
        # Apply safety settings if available
        safety_settings = self.safety_settings
        
        # Make the API request
        try:
            generation_config = types.GenerateContentConfig(**config)
            
            # Set safety settings if available
            if safety_settings:
                generation_config.safety_settings = safety_settings
            
            # Start request timing
            start_time = time.time()
            
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model_name,
                contents=prompt,
                config=generation_config
            )
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Check for errors in the response
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                raise ValueError(f"Prompt blocked: {response.prompt_feedback.block_reason}")
            
            # Estimate tokens (using character-based approximation)
            # A very rough approximation is 4 characters per token
            input_tokens = len(prompt) // 4
            output_tokens = len(response.text) // 4
            
            # Get actual token counts if available in the response
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                if hasattr(usage, 'prompt_token_count'):
                    input_tokens = usage.prompt_token_count
                if hasattr(usage, 'candidates_token_count'):
                    output_tokens = usage.candidates_token_count
            
            # Record token usage
            token_counter.add_call(model_name, input_tokens, output_tokens)
            
            # Log token usage
            logger.info(f"API call to {model_name}: {input_tokens} input tokens, {output_tokens} output tokens, {duration:.2f}s")
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {str(e)}")
            raise
    
    async def generate_structured(self, prompt: str,
                               response_schema: Dict[str, Any],
                               model: Optional[str] = None,
                               **kwargs) -> Dict[str, Any]:
        """Generate structured output from a prompt using Gemini.
        
        Args:
            prompt: The prompt text
            response_schema: JSON Schema definition for the response format
            model: Specific model to use (defaults to provider's default model)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Structured response as a dictionary
        
        Raises:
            Exception: On generation failure
        """
        # Get the actual model name from our mapping or use the provided one
        if model in self.models:
            model_name = self.models[model]
        else:
            model_name = model or self.models["default"]
        
        logger.debug(f"Using model for structured output: {model_name}")
        
        # Create config by combining generation_config with structured output settings
        config = self.generation_config.copy()
        
        # Add structured output settings
        config["response_mime_type"] = "application/json"
        config["response_schema"] = response_schema
        
        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in config:
                config[key] = value
        
        # Apply safety settings if available
        safety_settings = self.safety_settings
        
        # Make the API request
        try:
            generation_config = types.GenerateContentConfig(**config)
            
            # Set safety settings if available
            if safety_settings:
                generation_config.safety_settings = safety_settings
            
            # Start request timing
            start_time = time.time()
            
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model_name,
                contents=prompt,
                config=generation_config
            )
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Check for errors in the response
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                raise ValueError(f"Prompt blocked: {response.prompt_feedback.block_reason}")
            
            # Estimate tokens (using character-based approximation)
            # A very rough approximation is 4 characters per token
            input_tokens = len(prompt) // 4
            output_tokens = len(str(response)) // 4  # Use string representation for structured responses
            
            # Get actual token counts if available in the response
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                if hasattr(usage, 'prompt_token_count'):
                    input_tokens = usage.prompt_token_count
                if hasattr(usage, 'candidates_token_count'):
                    output_tokens = usage.candidates_token_count
            
            # Record token usage
            token_counter.add_call(model_name, input_tokens, output_tokens)
            
            # Log token usage
            logger.info(f"API call to {model_name}: {input_tokens} input tokens, {output_tokens} output tokens, {duration:.2f}s")
            
            # Try to get the parsed response
            try:
                return response.parsed
            except AttributeError:
                # Handle case where response doesn't have parsed attribute
                # Fallback to text and attempt to parse JSON
                logger.warning("Structured output not available, falling back to text parsing")
                text_output = response.text
                try:
                    return json.loads(text_output)
                except json.JSONDecodeError:
                    logger.error("Failed to parse response as JSON")
                    raise ValueError("Failed to get structured output from model")
            
        except Exception as e:
            logger.error(f"Error generating structured response with Gemini: {str(e)}")
            raise
    
    def _convert_generation_config(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert old generation config format to new SDK format.
        
        Args:
            old_config: Old generation config dictionary
            
        Returns:
            New generation config dictionary
        """
        # Map old config keys to new config keys
        config_map = {
            "temperature": "temperature",
            "top_p": "top_p",
            "top_k": "top_k",
            "max_output_tokens": "max_output_tokens",
            "candidate_count": "candidate_count"
        }
        
        new_config = {}
        for old_key, new_key in config_map.items():
            if old_key in old_config:
                new_config[new_key] = old_config[old_key]
        
        return new_config
    
    def _convert_safety_settings(self, old_safety: Dict[str, str]) -> List[Dict[str, Any]]:
        """Convert old safety settings format to new SDK format.
        
        Args:
            old_safety: Old safety settings dictionary
            
        Returns:
            New safety settings in the format expected by the new SDK
        """
        # Map harm categories to their enum values in the new SDK 
        harm_category_map = {
            "HARM_CATEGORY_HARASSMENT": types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            "HARM_CATEGORY_HATE_SPEECH": types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            "HARM_CATEGORY_DANGEROUS_CONTENT": types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        }
        
        # Map threshold values to their enum values
        threshold_map = {
            "BLOCK_NONE": types.HarmBlockThreshold.BLOCK_NONE,
            "BLOCK_ONLY_HIGH": types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            "BLOCK_MEDIUM_AND_ABOVE": types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            "BLOCK_LOW_AND_ABOVE": types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        }
        
        # Convert the settings to the new format
        safety_settings = []
        for category, threshold in old_safety.items():
            if category in harm_category_map and threshold in threshold_map:
                safety_settings.append({
                    "category": harm_category_map[category],
                    "threshold": threshold_map[threshold]
                })
        
        return safety_settings