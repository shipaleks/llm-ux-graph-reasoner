"""Base LLM provider interface for the knowledge graph synthesis system."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import time
from datetime import datetime

from ..config import settings

logger = logging.getLogger(__name__)


class TokenCounter:
    """Tracks token usage and API calls for LLM interactions.
    
    This class provides methods to track and report on token usage,
    API call counts, and estimated costs for different LLM providers.
    """
    
    def __init__(self):
        """Initialize the token counter."""
        self.api_calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls_by_model = {}
        self.tokens_by_model = {}
        self.start_time = datetime.now()
        
        # Cost per 1K tokens (approximate for various providers)
        self.cost_per_1k = {
            "gemini-2.0-flash": {"input": 0.000125, "output": 0.000375},  # $0.125/1M input, $0.375/1M output
            "gemini-2.0-pro-exp-02-05": {"input": 0.0005, "output": 0.0015},  # $0.5/1M input, $1.5/1M output
            "default_gemini": {"input": 0.0005, "output": 0.0015},
            "default_openai": {"input": 0.001, "output": 0.002}, 
        }
    
    def add_call(self, model: str, input_tokens: int, output_tokens: int):
        """Record an API call with token counts.
        
        Args:
            model: The model used for the call
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self.api_calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        
        # Update model-specific counters
        if model not in self.calls_by_model:
            self.calls_by_model[model] = 0
            self.tokens_by_model[model] = {"input": 0, "output": 0}
        
        self.calls_by_model[model] += 1
        self.tokens_by_model[model]["input"] += input_tokens
        self.tokens_by_model[model]["output"] += output_tokens
    
    def estimate_cost(self) -> Dict[str, Any]:
        """Estimate the cost of API calls.
        
        Returns:
            Dictionary with cost estimates and usage statistics
        """
        total_cost = 0.0
        model_costs = {}
        
        for model, tokens in self.tokens_by_model.items():
            # Get cost rates for this model
            if model in self.cost_per_1k:
                rates = self.cost_per_1k[model]
            elif "gemini" in model.lower():
                rates = self.cost_per_1k["default_gemini"]
            else:
                rates = self.cost_per_1k["default_openai"]
            
            # Calculate costs
            input_cost = (tokens["input"] / 1000) * rates["input"]
            output_cost = (tokens["output"] / 1000) * rates["output"]
            model_cost = input_cost + output_cost
            
            model_costs[model] = {
                "input_tokens": tokens["input"],
                "output_tokens": tokens["output"],
                "input_cost": input_cost,
                "output_cost": output_cost,
                "total_cost": model_cost
            }
            
            total_cost += model_cost
        
        # Calculate duration
        duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "total_api_calls": self.api_calls,
            "total_input_tokens": self.input_tokens,
            "total_output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "total_cost_usd": total_cost,
            "duration_seconds": duration,
            "costs_by_model": model_costs,
            "calls_by_model": self.calls_by_model
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of token usage and costs.
        
        Returns:
            Summary string
        """
        stats = self.estimate_cost()
        
        summary = [
            "Token Usage Summary",
            "==================="
        ]
        
        # Add general stats
        summary.extend([
            f"Total API Calls: {stats['total_api_calls']}",
            f"Total Tokens: {stats['total_tokens']} (Input: {stats['total_input_tokens']}, Output: {stats['total_output_tokens']})",
            f"Estimated Cost: ${stats['total_cost_usd']:.6f} USD",
            f"Duration: {stats['duration_seconds']:.2f} seconds",
            "",
            "Model Breakdown:",
        ])
        
        # Add per-model stats
        for model, cost_info in stats["costs_by_model"].items():
            summary.extend([
                f"  {model}:",
                f"    Calls: {stats['calls_by_model'][model]}",
                f"    Tokens: {cost_info['input_tokens'] + cost_info['output_tokens']} (Input: {cost_info['input_tokens']}, Output: {cost_info['output_tokens']})",
                f"    Cost: ${cost_info['total_cost']:.6f} USD",
                ""
            ])
        
        return "\n".join(summary)


# Global token counter instance
token_counter = TokenCounter()


class LLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    This class defines the interface that all LLM providers must implement,
    ensuring consistent functionality across different providers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the LLM provider.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.api_key = config.get("api_key")
        self.models = config.get("models", {})
        self.generation_config = config.get("generation_config", {})
        self.timeout = config.get("timeout", settings.LLM_TIMEOUT)
        self.max_retries = config.get("max_retries", settings.LLM_MAX_RETRIES)
    
    @abstractmethod
    async def generate_text(self, prompt: str, 
                         model: Optional[str] = None,
                         **kwargs) -> str:
        """Generate text from a prompt.
        
        Args:
            prompt: The prompt text
            model: Specific model to use (defaults to provider's default model)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
        
        Raises:
            Exception: On generation failure
        """
        pass
    
    @abstractmethod
    async def generate_structured(self, prompt: str,
                               response_schema: Dict[str, Any],
                               model: Optional[str] = None,
                               **kwargs) -> Dict[str, Any]:
        """Generate structured output from a prompt.
        
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
        pass
    
    @abstractmethod
    def name(self) -> str:
        """Get the name of the LLM provider.
        
        Returns:
            Provider name
        """
        pass
    
    def get_model(self, model_key: Optional[str] = None) -> str:
        """Get the model identifier for a given model key.
        
        Args:
            model_key: Key in the models dictionary (e.g., "default", "fast")
            
        Returns:
            Model identifier string
        """
        if not model_key:
            return self.models.get("default", next(iter(self.models.values())))
        
        return self.models.get(model_key, self.models.get("default"))
    
    def validate_response(self, response: Dict[str, Any], 
                        schema: Dict[str, Any]) -> bool:
        """Validate a structured response against a schema.
        
        Args:
            response: Response dictionary to validate
            schema: JSON Schema to validate against
            
        Returns:
            True if valid, False otherwise
        """
        # TODO: Implement proper JSON Schema validation
        # For now, a simple check for required properties
        if "properties" in schema and "required" in schema:
            required_props = schema["required"]
            return all(prop in response for prop in required_props)
        
        return True