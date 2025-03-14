"""Text loading module for the knowledge graph synthesis system."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

import langdetect

from ..models.segment import TextSegment, SegmentCollection
from ..config import settings


class TextLoader:
    """Loads and processes text files.
    
    This class is responsible for loading text from files, detecting language,
    and creating an initial TextSegment for further processing.
    """
    
    def __init__(self):
        """Initialize the text loader."""
        pass
    
    def load(self, file_path: str) -> SegmentCollection:
        """Load text from a file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            SegmentCollection containing the loaded text
        
        Raises:
            FileNotFoundError: If the file does not exist
            IOError: If there is an error reading the file
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        
        try:
            text = path.read_text(encoding='utf-8')
        except Exception as e:
            raise IOError(f"Error reading file {file_path}: {str(e)}")
        
        # Create a SegmentCollection
        collection = SegmentCollection(document_id=path.name)
        
        # Create initial root segment
        language = self._detect_language(text)
        segment = TextSegment(
            text=text,
            start_position=0,
            end_position=len(text),
            language=language,
            document_id=path.name,
            metadata={
                "file_path": str(path.absolute()),
                "file_size": path.stat().st_size,
                "file_name": path.name,
            }
        )
        
        collection.add_segment(segment)
        return collection
    
    def load_text(self, text: str, document_id: Optional[str] = None) -> SegmentCollection:
        """Load text directly from a string.
        
        Args:
            text: Text content
            document_id: Optional document identifier
            
        Returns:
            SegmentCollection containing the loaded text
        """
        doc_id = document_id or f"text-{uuid4()}"
        collection = SegmentCollection(document_id=doc_id)
        
        # Create initial root segment
        language = self._detect_language(text)
        segment = TextSegment(
            text=text,
            start_position=0,
            end_position=len(text),
            language=language,
            document_id=doc_id,
            metadata={}
        )
        
        collection.add_segment(segment)
        return collection
    
    def _detect_language(self, text: str) -> str:
        """Detect the language of the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            ISO language code ('en', 'ru', etc.)
        """
        # If the text is in WEBVTT format, extract actual content for language detection
        if text.startswith("WEBVTT"):
            # Extract real speech content from transcript
            content_lines = []
            lines = text.split('\n')
            timestamp_pattern = r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}'
            
            for i, line in enumerate(lines):
                # Skip WEBVTT header, timestamps, and empty lines
                if (i > 0 and  # Not header
                    not re.match(timestamp_pattern, line) and  # Not timestamp
                    line.strip()):  # Not empty
                    content_lines.append(line)
            
            # Join all content lines together for language detection
            detection_text = " ".join(content_lines)
            # Use at most 1000 characters
            sample = detection_text[:min(len(detection_text), 1000)]
        else:
            # For normal text, just use the first 1000 characters
            sample = text[:min(len(text), 1000)]
        
        try:
            # Check for Cyrillic characters as a stronger signal for Russian
            if any(ord('а') <= ord(c) <= ord('я') or ord('А') <= ord(c) <= ord('Я') for c in sample):
                return 'ru'
                
            # Fallback to language detection library
            lang = langdetect.detect(sample)
            
            # Currently we only support English and Russian
            if lang not in settings.SUPPORTED_LANGUAGES:
                return settings.DEFAULT_LANGUAGE
            
            return lang
        except Exception:
            # Default to English if language detection fails
            return settings.DEFAULT_LANGUAGE