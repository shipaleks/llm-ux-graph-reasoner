"""Validation for LLM responses."""

import logging
import re
from typing import Dict, Any, List, Optional, Union, Tuple

import jsonschema

logger = logging.getLogger(__name__)


class ResponseValidator:
    """Validates LLM responses against schemas and source text.
    
    This class implements validation for LLM responses, including schema validation,
    source text verification, and consistency checks.
    """
    
    def __init__(self):
        """Initialize the response validator."""
        pass
    
    def validate_schema(self, response: Dict[str, Any], 
                       schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a response against a JSON schema.
        
        Args:
            response: Response dictionary to validate
            schema: JSON Schema to validate against
            
        Returns:
            (is_valid, error_messages) tuple
        """
        errors = []
        try:
            jsonschema.validate(instance=response, schema=schema)
            return True, []
        except jsonschema.exceptions.ValidationError as e:
            path = "/".join(str(p) for p in e.path)
            errors.append(f"Validation error at {path}: {e.message}")
            logger.warning(f"Schema validation error: {e.message}")
            return False, errors
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
            logger.error(f"Unexpected validation error: {str(e)}")
            return False, errors
    
    def validate_entity_source_spans(self, response: Dict[str, Any], 
                                   source_text: str) -> Tuple[bool, List[str]]:
        """Validate that entity source spans exist in the source text.
        
        Args:
            response: Response dictionary with entities
            source_text: Original source text
            
        Returns:
            (is_valid, error_messages) tuple
        """
        errors = []
        valid = True
        
        if "entities" not in response:
            return False, ["Response does not contain entities field"]
        
        for i, entity in enumerate(response["entities"]):
            if "source_span" not in entity:
                errors.append(f"Entity {i} ({entity.get('name', 'unknown')}) missing source_span")
                valid = False
                continue
                
            source_span = entity["source_span"]
            span_text = source_span.get("text", "")
            
            # Check if span text appears in source text
            if span_text and span_text not in source_text:
                errors.append(f"Entity {i} ({entity.get('name', 'unknown')}) "
                            f"source span text not found in source: {span_text}")
                valid = False
            
            # Verify start/end positions
            if "start" in source_span and "end" in source_span:
                start = source_span["start"]
                end = source_span["end"]
                
                if end <= start:
                    errors.append(f"Entity {i} has invalid span: end ({end}) <= start ({start})")
                    valid = False
                elif start < 0 or end > len(source_text):
                    errors.append(f"Entity {i} has out of bounds span: start={start}, end={end}, "
                                f"text length={len(source_text)}")
                    valid = False
                elif source_text[start:end] != span_text:
                    errors.append(f"Entity {i} span text does not match source text at "
                                f"positions {start}:{end}")
                    valid = False
        
        return valid, errors
    
    def validate_relationship_source_spans(self, response: Dict[str, Any],
                                        source_text: str) -> Tuple[bool, List[str]]:
        """Validate that relationship source spans exist in the source text.
        
        Args:
            response: Response dictionary with relationships
            source_text: Original source text
            
        Returns:
            (is_valid, error_messages) tuple
        """
        errors = []
        valid = True
        
        if "relationships" not in response:
            return False, ["Response does not contain relationships field"]
        
        for i, rel in enumerate(response["relationships"]):
            if "source_span" not in rel:
                errors.append(f"Relationship {i} ({rel.get('type', 'unknown')}) missing source_span")
                valid = False
                continue
                
            source_span = rel["source_span"]
            span_text = source_span.get("text", "")
            
            # Check if span text appears in source text
            if span_text and span_text not in source_text:
                errors.append(f"Relationship {i} ({rel.get('type', 'unknown')}) "
                            f"source span text not found in source: {span_text}")
                valid = False
            
            # Verify start/end positions
            if "start" in source_span and "end" in source_span:
                start = source_span["start"]
                end = source_span["end"]
                
                if end <= start:
                    errors.append(f"Relationship {i} has invalid span: end ({end}) <= start ({start})")
                    valid = False
                elif start < 0 or end > len(source_text):
                    errors.append(f"Relationship {i} has out of bounds span: start={start}, end={end}, "
                                f"text length={len(source_text)}")
                    valid = False
                elif source_text[start:end] != span_text:
                    errors.append(f"Relationship {i} span text does not match source text at "
                                f"positions {start}:{end}")
                    valid = False
        
        return valid, errors
    
    def validate_consistency(self, response: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate internal consistency of a response.
        
        Args:
            response: Response dictionary
            
        Returns:
            (is_valid, error_messages) tuple
        """
        errors = []
        valid = True
        
        # Implement specific consistency checks depending on response type
        # For example, for entity extraction responses:
        if "entities" in response:
            # Check for duplicate entity names
            entity_names = [e.get("name") for e in response["entities"] if "name" in e]
            duplicates = set([name for name in entity_names if entity_names.count(name) > 1])
            
            if duplicates:
                errors.append(f"Duplicate entity names found: {', '.join(duplicates)}")
                valid = False
        
        # For relationship extraction responses:
        if "relationships" in response:
            # Check that source and target are different
            for i, rel in enumerate(response["relationships"]):
                if "source" in rel and "target" in rel:
                    source_name = rel["source"].get("name")
                    target_name = rel["target"].get("name")
                    
                    if source_name == target_name:
                        errors.append(f"Relationship {i} has identical source and target: {source_name}")
                        valid = False
        
        return valid, errors