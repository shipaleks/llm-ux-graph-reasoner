"""Prompt templates for LLM interactions.

This module provides access to prompt templates for different languages and tasks.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from ...config import settings

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages prompt templates for LLM interactions.
    
    This class provides access to prompt templates for different languages and tasks,
    loading them from files and filling in template variables.
    """
    
    def __init__(self):
        """Initialize the prompt manager."""
        self._prompts = {}
        self._prompt_dir = Path(__file__).parent
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompt templates from files."""
        # Load English prompts
        en_dir = self._prompt_dir / "en"
        if en_dir.exists():
            self._load_prompts_from_directory(en_dir, "en")
        
        # Load Russian prompts
        ru_dir = self._prompt_dir / "ru"
        if ru_dir.exists():
            self._load_prompts_from_directory(ru_dir, "ru")
    
    def _load_prompts_from_directory(self, directory: Path, language: str):
        """Load prompts from a directory and its subdirectories.
        
        Args:
            directory: Directory to load prompts from
            language: Language code
        """
        # Load prompts from the root directory
        for file_path in directory.glob("*.txt"):
            prompt_name = file_path.stem
            self._load_prompt_file(file_path, prompt_name, language)
        
        # Load prompts from subdirectories
        for subdir in directory.iterdir():
            if subdir.is_dir():
                category = subdir.name
                for file_path in subdir.glob("*.txt"):
                    prompt_name = f"{category}/{file_path.stem}"
                    self._load_prompt_file(file_path, prompt_name, language)
    
    def _load_prompt_file(self, file_path: Path, prompt_name: str, language: str):
        """Load a prompt from a file.
        
        Args:
            file_path: Path to the prompt file
            prompt_name: Name of the prompt
            language: Language code
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                prompt_text = f.read()
            self._prompts[(prompt_name, language)] = prompt_text
            logger.debug(f"Loaded prompt: {prompt_name} ({language})")
        except Exception as e:
            logger.error(f"Error loading prompt {prompt_name} ({language}): {str(e)}")
    
    def get_prompt(self, name: str, language: str = "en") -> Optional[str]:
        """Get a prompt template by name and language.
        
        Args:
            name: Name of the prompt template
            language: Language code ("en" or "ru")
            
        Returns:
            Prompt template or None if not found
        """
        if language not in settings.SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language: {language}, falling back to English")
            language = "en"
        
        prompt = self._prompts.get((name, language))
        if prompt is None:
            logger.warning(f"Prompt not found: {name} ({language}), falling back to English")
            prompt = self._prompts.get((name, "en"))
        
        return prompt
    
    def format_prompt(self, name: str, language: str = "en", **kwargs) -> Optional[str]:
        """Format a prompt template with variables.
        
        Args:
            name: Name of the prompt template
            language: Language code
            **kwargs: Variables to fill in the template
            
        Returns:
            Formatted prompt or None if template not found
        """
        prompt_template = self.get_prompt(name, language)
        if not prompt_template:
            return None
        
        # Simple template substitution using {{variable_name}}
        formatted_prompt = prompt_template
        for key, value in kwargs.items():
            formatted_prompt = formatted_prompt.replace("{{" + key + "}}", str(value))
        
        return formatted_prompt
    
    def list_available_prompts(self) -> List[Dict[str, str]]:
        """List all available prompt templates.
        
        Returns:
            List of {name, language} dictionaries
        """
        return [{"name": name, "language": lang} for (name, lang) in self._prompts.keys()]


# Create a singleton instance
prompt_manager = PromptManager()