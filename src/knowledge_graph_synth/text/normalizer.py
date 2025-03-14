"""Text normalization for the knowledge graph synthesis system."""

import re
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from ..models.segment import TextSegment
from ..config import settings

logger = logging.getLogger(__name__)

class TextNormalizer:
    """Normalizes text for processing.
    
    This class implements text normalization operations like whitespace handling,
    line break normalization, and other preprocessing steps to prepare text for
    entity extraction and relationship identification. It also ensures consistent
    language detection.
    """
    
    def __init__(self):
        """Initialize the text normalizer."""
        # Regex patterns for normalization
        self.whitespace_pattern = re.compile(r'\s+')
        self.multiple_newlines_pattern = re.compile(r'\n{3,}')
        self.control_chars_pattern = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
    
    def normalize(self, segment: TextSegment) -> TextSegment:
        """Normalize a text segment.
        
        Args:
            segment: Text segment to normalize
            
        Returns:
            Normalized text segment
        """
        text = segment.text
        
        # Remove control characters
        text = self.control_chars_pattern.sub('', text)
        
        # Normalize line breaks (replace \r\n with \n)
        text = text.replace('\r\n', '\n')
        
        # Normalize multiple newlines (more than 2) to double newlines
        text = self.multiple_newlines_pattern.sub('\n\n', text)
        
        # Normalize whitespace (not including line breaks)
        lines = text.split('\n')
        normalized_lines = [self.whitespace_pattern.sub(' ', line).strip() for line in lines]
        text = '\n'.join(normalized_lines)
        
        # Verify language detection or detect language if needed
        language = segment.language
        if not language:
            # If no language is set, detect it
            language = self._detect_language(text)
            logger.info(f"Detected language for segment {segment.id}: {language}")
        
        # Create a new segment with normalized text
        normalized_segment = TextSegment(
            id=segment.id,  # Keep the same ID
            document_id=segment.document_id,
            text=text,
            start_position=segment.start_position,
            end_position=segment.start_position + len(text),
            language=language,  # Use the verified language
            metadata=segment.metadata.copy(),
            parent_id=segment.parent_id,
            child_ids=segment.child_ids.copy()
        )
        
        # Add normalization metadata
        normalized_segment.add_metadata('normalized', True)
        normalized_segment.add_metadata('original_length', segment.length)
        normalized_segment.add_metadata('normalized_length', normalized_segment.length)
        normalized_segment.add_metadata('language', language)  # Store language in metadata for consistency
        
        return normalized_segment
    
    def normalize_collection(self, segments: List[TextSegment]) -> List[TextSegment]:
        """Normalize a collection of text segments.
        
        Args:
            segments: List of text segments to normalize
            
        Returns:
            List of normalized text segments
        """
        return [self.normalize(segment) for segment in segments]
        
    def _detect_language(self, text: str) -> str:
        """Detect language of the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code ("en", "ru", etc.)
        """
        # Check for Cyrillic characters as a strong signal for Russian
        sample = text[:1000]  # Use first 1000 characters for detection
        if any(ord('а') <= ord(c) <= ord('я') or ord('А') <= ord(c) <= ord('Я') for c in sample):
            return "ru"
        
        try:
            # Try to use langdetect if available
            import langdetect
            detected = langdetect.detect(sample)
            
            # Only return supported languages
            if detected in settings.SUPPORTED_LANGUAGES:
                return detected
            
        except (ImportError, Exception) as e:
            logger.warning(f"Language detection failed: {str(e)}")
        
        # Default to English if detection fails or language not supported
        return settings.DEFAULT_LANGUAGE