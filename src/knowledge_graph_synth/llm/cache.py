"""Caching for LLM responses."""

import hashlib
import json
import logging
from typing import Dict, Any, Optional, Union

import diskcache

from ..config import settings

logger = logging.getLogger(__name__)


class ResponseCache:
    """Caches LLM responses to reduce API calls and costs.
    
    This class implements caching for LLM responses using a disk-based cache,
    with configurable TTL and size limits.
    """
    
    def __init__(self, 
               cache_dir: Optional[str] = None,
               ttl: int = 604800,  # 7 days in seconds
               size_limit: int = 1073741824  # 1GB
               ):
        """Initialize the response cache.
        
        Args:
            cache_dir: Directory to store cache files (defaults to CACHE_DIR/llm_responses)
            ttl: Time-to-live for cache entries in seconds
            size_limit: Maximum cache size in bytes
        """
        cache_path = cache_dir or str(settings.CACHE_DIR / "llm_responses")
        self.cache = diskcache.Cache(cache_path, size_limit=size_limit)
        self.ttl = ttl
    
    def get_key(self, prompt: str, 
              model: str, 
              response_schema: Optional[Dict[str, Any]] = None,
              **kwargs) -> str:
        """Generate a cache key from request parameters.
        
        Args:
            prompt: The prompt text
            model: Model identifier
            response_schema: Optional JSON schema for structured responses
            **kwargs: Additional parameters affecting the response
            
        Returns:
            Cache key as a string
        """
        # Combine all parameters that could affect the response
        key_dict = {
            "prompt": prompt,
            "model": model,
            "schema": response_schema,
        }
        
        # Add any other kwargs that could affect the response
        for k, v in kwargs.items():
            if k in ["temperature", "top_p", "top_k", "max_tokens"]:
                key_dict[k] = v
        
        # Convert to a stable string representation
        key_str = json.dumps(key_dict, sort_keys=True)
        
        # Hash the string to create a fixed-length key
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get a response from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached response or None if not found
        """
        try:
            return self.cache.get(key, default=None)
        except Exception as e:
            logger.warning(f"Error retrieving from cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """Store a response in the cache.
        
        Args:
            key: Cache key
            value: Response to cache
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache.set(key, value, expire=self.ttl)
            return True
        except Exception as e:
            logger.warning(f"Error storing in cache: {str(e)}")
            return False
    
    def invalidate(self, key: str) -> bool:
        """Remove a specific entry from the cache.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Error invalidating cache entry: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """Clear the entire cache.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache.clear()
            return True
        except Exception as e:
            logger.warning(f"Error clearing cache: {str(e)}")
            return False
    
    def __enter__(self):
        """Context manager entry.
        
        Returns:
            The cache instance
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit.
        
        Ensures the cache is properly closed.
        """
        self.cache.close()