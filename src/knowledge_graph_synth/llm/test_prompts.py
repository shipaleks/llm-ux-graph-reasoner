"""Test utility for prompt templates.

This module provides a command-line utility for testing prompt templates
with LLM providers.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from .prompts import prompt_manager
from .factory import LLMProviderFactory
from ..config import settings


logger = logging.getLogger(__name__)


async def test_prompt(
    prompt_name: str,
    language: str = "en",
    provider_name: Optional[str] = None,
    variables: Optional[Dict[str, Any]] = None,
    schema: Optional[Dict[str, Any]] = None,
    structured: bool = False,
    output_file: Optional[str] = None
) -> Optional[Any]:
    """Test a prompt template with an LLM provider.
    
    Args:
        prompt_name: Name of the prompt template
        language: Language code ("en" or "ru")
        provider_name: Name of the LLM provider to use
        variables: Variables to fill in the template
        schema: JSON schema for structured output
        structured: Whether to use structured output
        output_file: Path to save the response to
        
    Returns:
        LLM response or None if an error occurred
    """
    # Get the prompt template
    if variables is None:
        variables = {}
    
    if schema is not None:
        variables["schema"] = json.dumps(schema, indent=2)
    
    formatted_prompt = prompt_manager.format_prompt(prompt_name, language, **variables)
    if not formatted_prompt:
        logger.error(f"Prompt not found: {prompt_name} ({language})")
        return None
    
    # Get the LLM provider
    try:
        if provider_name and provider_name.lower() == "reasoning":
            provider = LLMProviderFactory.get_reasoning_provider()
            if not provider:
                logger.warning("Reasoning provider not available, falling back to default")
                provider = LLMProviderFactory.get_provider()
        else:
            provider = LLMProviderFactory.get_provider(provider_name)
        
        if not provider:
            logger.error("No LLM provider available")
            return None
    except Exception as e:
        logger.error(f"Error getting LLM provider: {str(e)}")
        return None
    
    # Generate response
    try:
        if structured and schema:
            response = await provider.generate_structured(formatted_prompt, schema)
        else:
            response = await provider.generate_text(formatted_prompt)
        
        # Save the response to a file
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                if isinstance(response, dict):
                    json.dump(response, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(response))
            
            logger.info(f"Response saved to {output_path}")
        
        return response
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return None


async def main_async(args: argparse.Namespace) -> int:
    """Main async function.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code
    """
    # Load variables from file
    variables = {}
    if args.variables:
        try:
            with open(args.variables, "r", encoding="utf-8") as f:
                variables = json.load(f)
        except Exception as e:
            logger.error(f"Error loading variables: {str(e)}")
            return 1
    
    # Load schema from file
    schema = None
    if args.schema:
        try:
            with open(args.schema, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except Exception as e:
            logger.error(f"Error loading schema: {str(e)}")
            return 1
    
    # Test the prompt
    response = await test_prompt(
        prompt_name=args.prompt,
        language=args.language,
        provider_name=args.provider,
        variables=variables,
        schema=schema,
        structured=args.structured,
        output_file=args.output
    )
    
    if response is None:
        return 1
    
    # Print the response
    if isinstance(response, dict):
        print(json.dumps(response, indent=2, ensure_ascii=False))
    else:
        print(response)
    
    return 0


def main() -> int:
    """Main function.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Test prompt templates")
    parser.add_argument(
        "prompt",
        help="Name of the prompt template"
    )
    parser.add_argument(
        "--language", "-l",
        help="Language code",
        default="en",
        choices=settings.SUPPORTED_LANGUAGES
    )
    parser.add_argument(
        "--provider", "-p",
        help="Name of the LLM provider"
    )
    parser.add_argument(
        "--variables", "-v",
        help="Path to a JSON file with variables"
    )
    parser.add_argument(
        "--schema", "-s",
        help="Path to a JSON schema file"
    )
    parser.add_argument(
        "--structured",
        help="Use structured output",
        action="store_true"
    )
    parser.add_argument(
        "--output", "-o",
        help="Path to save the response to"
    )
    parser.add_argument(
        "--list",
        help="List available prompts",
        action="store_true"
    )
    parser.add_argument(
        "--log-level",
        help="Logging level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # List available prompts
    if args.list:
        prompts = prompt_manager.list_available_prompts()
        print(f"Available prompts ({len(prompts)}):")
        for prompt in sorted(prompts, key=lambda p: f"{p['language']}/{p['name']}"):
            print(f"  - {prompt['name']} ({prompt['language']})")
        return 0
    
    # Run the main async function
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())