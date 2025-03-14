"""Specialized Gemini provider for reasoning tasks."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union

from google.genai import types

from .gemini import GeminiProvider
from ..config import settings, providers

logger = logging.getLogger(__name__)


class GeminiReasoningProvider(GeminiProvider):
    """Specialized Gemini provider optimized for reasoning tasks.
    
    This class extends the base Gemini provider with specialized prompting
    techniques for the reasoning-focused model variant.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Gemini reasoning provider.
        
        Args:
            config: Provider-specific configuration (defaults to config from providers module)
        """
        super().__init__(config)
    
    async def generate_text(self, prompt: str, 
                         model: Optional[str] = None,
                         **kwargs) -> str:
        """Generate text using the reasoning-optimized Gemini model.
        
        Args:
            prompt: The prompt text
            model: Specific model to use (defaults to the reasoning model variant)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
        
        Raises:
            Exception: On generation failure
        """
        # Override the model to always use the reasoning variant
        model = model or self.get_model("reasoning")
        
        # Construct a reasoning-optimized prompt
        reasoning_prompt = self._create_reasoning_prompt(prompt)
        
        # Generate the response using the parent class method
        response = await super().generate_text(reasoning_prompt, model, **kwargs)
        
        # Post-process the response if needed
        return self._extract_final_answer(response)
    
    async def generate_structured(self, prompt: str,
                               response_schema: Dict[str, Any],
                               model: Optional[str] = None,
                               **kwargs) -> Dict[str, Any]:
        """Generate structured output using the reasoning-optimized Gemini model.
        
        Args:
            prompt: The prompt text
            response_schema: JSON Schema definition for the response format
            model: Specific model to use (defaults to the reasoning model variant)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Structured response as a dictionary
        
        Raises:
            Exception: On generation failure
        """
        # Override the model to always use the reasoning variant
        model = model or self.get_model("reasoning")
        
        # Construct a reasoning-optimized prompt
        reasoning_prompt = self._create_reasoning_prompt(prompt, structured=True)
        
        # Create a new config specifically for the reasoning model
        reasoning_config = kwargs.copy()
        
        # Add thinking step configuration if available in the new SDK
        # This is a placeholder - actual implementation depends on the new SDK's support for thinking
        if hasattr(types, "ThinkingConfig"):
            reasoning_config["thinking"] = types.ThinkingConfig(enabled=True)
        
        # Generate the response using the parent class method
        return await super().generate_structured(reasoning_prompt, response_schema, model, **reasoning_config)
    
    def _create_reasoning_prompt(self, prompt: str, structured: bool = False) -> str:
        """Create a prompt optimized for the reasoning model variant.
        
        Args:
            prompt: The original prompt
            structured: Whether this is for structured output
            
        Returns:
            Reasoning-optimized prompt
        """
        # Special prompt template for the reasoning model variant
        # This encourages step-by-step thinking and careful analysis
        
        prefix = """I need you to carefully think through this problem, step by step.

Let's break this down with careful analysis:

1. First, understand exactly what is being asked.
2. Consider all relevant information.
3. Think carefully about each piece of the problem.
4. Connect the different pieces together.
5. Reach a well-reasoned conclusion.

Here's the task:

"""
        
        if structured:
            suffix = """

Remember to carefully organize your response according to the schema. Think step by step about each required field, making sure your information is accurate and well-grounded."""
        else:
            suffix = """

Take your time to think through this carefully. First, analyze the key aspects of the problem. Next, develop your reasoning step by step. Finally, provide your conclusion."""
        
        return f"{prefix}{prompt}{suffix}"
    
    def _extract_final_answer(self, response: str) -> str:
        """Extract the final answer from a reasoning response.
        
        This removes any intermediary reasoning steps if they're not needed
        in the final output.
        
        Args:
            response: The full response from the model
            
        Returns:
            Extracted final answer
        """
        # Check for designated conclusion markers
        conclusion_markers = [
            "In conclusion:",
            "Therefore,",
            "In summary:",
            "Thus,",
            "Final answer:",
            "To conclude:",
        ]
        
        for marker in conclusion_markers:
            if marker in response:
                parts = response.split(marker, 1)
                if len(parts) > 1:
                    return marker + parts[1]
        
        return response