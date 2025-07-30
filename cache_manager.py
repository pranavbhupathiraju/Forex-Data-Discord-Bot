"""
Centralized cache management for the Economic Data Discord Bot
Handles caching of configuration, database, and CSV data
"""

import time
from typing import Any, Optional, Dict
from logger import logger
from constants import DEFAULT_CACHE_TTL, CSV_CACHE_TTL


class CacheManager:
    """Centralized cache management with TTL support"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._ttl_settings: Dict[str, int] = {}

    def set(self, key: str, value: Any, ttl: int = DEFAULT_CACHE_TTL):
        """Set a value in cache with TTL"""
        self._cache[key] = value
        self._timestamps[key] = time.time()
        self._ttl_settings[key] = ttl
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if not expired"""
        if key not in self._cache:
            return None

        # Check if expired
        if self._is_expired(key):
            self.delete(key)
            return None

        logger.debug(f"Cache hit: {key}")
        return self._cache[key]

    def delete(self, key: str):
        """Delete a key from cache"""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            del self._ttl_settings[key]
            logger.debug(f"Cache deleted: {key}")

    def _is_expired(self, key: str) -> bool:
        """Check if a cache entry is expired"""
        if key not in self._timestamps:
            return True

        age = time.time() - self._timestamps[key]
        ttl = self._ttl_settings.get(key, DEFAULT_CACHE_TTL)
        return age > ttl

    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        self._timestamps.clear()
        self._ttl_settings.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for key in self._cache if self._is_expired(key))

        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries,
            'cache_size': len(self._cache)
        }

    def cleanup_expired(self):
        """Remove all expired entries from cache"""
        expired_keys = [key for key in self._cache if self._is_expired(key)]
        for key in expired_keys:
            self.delete(key)

        if expired_keys:
            logger.info(
                f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache manager instance
cache_manager = CacheManager()
