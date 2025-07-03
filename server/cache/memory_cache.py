"""
In-Memory Cache Implementation
Replaces Redis for cost optimization without compromising functionality
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass
from threading import Lock
import weakref

@dataclass
class CacheEntry:
    """Cache entry with expiration support"""
    value: Any
    expires_at: Optional[float] = None
    access_count: int = 0
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def access(self) -> Any:
        """Record access and return value"""
        self.access_count += 1
        return self.value

class MemoryCache:
    """
    High-performance in-memory cache with Redis-like interface
    Features:
    - TTL support
    - LRU eviction
    - Memory management
    - Thread-safe operations
    - Session storage capability
    """
    
    def __init__(self, max_size_mb: int = 128, cleanup_interval: int = 300):
        """
        Initialize memory cache
        
        Args:
            max_size_mb: Maximum memory usage in MB
            cleanup_interval: Seconds between cleanup runs
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cleanup_interval = cleanup_interval
        
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._last_cleanup = time.time()
        
        # Start background cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(self._background_cleanup())
        except RuntimeError:
            # No event loop running, cleanup will happen on access
            pass
    
    async def _background_cleanup(self):
        """Background task to clean expired entries"""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            self._cleanup_expired()
            self._enforce_memory_limit()
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
    
    def _enforce_memory_limit(self):
        """Enforce memory limits using LRU eviction"""
        with self._lock:
            current_size = self._estimate_memory_usage()
            
            if current_size > self.max_size_bytes:
                # Sort by access count and creation time (LRU)
                sorted_items = sorted(
                    self._cache.items(),
                    key=lambda x: (x[1].access_count, x[1].created_at)
                )
                
                # Remove least recently used items
                removed_size = 0
                target_size = self.max_size_bytes * 0.8  # Remove extra to prevent thrashing
                
                for key, entry in sorted_items:
                    if current_size - removed_size < target_size:
                        break
                    
                    removed_size += self._estimate_entry_size(key, entry)
                    del self._cache[key]
    
    def _estimate_memory_usage(self) -> int:
        """Estimate current memory usage in bytes"""
        total_size = 0
        for key, entry in self._cache.items():
            total_size += self._estimate_entry_size(key, entry)
        return total_size
    
    def _estimate_entry_size(self, key: str, entry: CacheEntry) -> int:
        """Estimate size of a cache entry"""
        try:
            key_size = len(key.encode('utf-8'))
            value_size = len(json.dumps(entry.value).encode('utf-8'))
            return key_size + value_size + 64  # Base object overhead
        except (TypeError, ValueError):
            # Fallback for non-JSON serializable objects
            return len(str(key)) + len(str(entry.value)) + 64
    
    def _maybe_cleanup(self):
        """Perform cleanup if needed"""
        current_time = time.time()
        if current_time - self._last_cleanup > self.cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = current_time
    
    # Redis-compatible interface
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiration"""
        with self._lock:
            expires_at = None
            if ex is not None:
                expires_at = time.time() + ex
            
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
            self._maybe_cleanup()
            return True
    
    def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                return None
            
            return entry.access()
    
    def delete(self, key: str) -> bool:
        """Delete a key"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        return self.get(key) is not None
    
    def ttl(self, key: str) -> int:
        """Get time to live for key"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None or entry.expires_at is None:
                return -1
            
            remaining = entry.expires_at - time.time()
            return max(0, int(remaining))
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for existing key"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            
            entry.expires_at = time.time() + seconds
            return True
    
    def keys(self, pattern: str = "*") -> list:
        """Get all keys matching pattern"""
        with self._lock:
            if pattern == "*":
                return list(self._cache.keys())
            
            # Simple pattern matching for wildcards
            if "*" in pattern:
                prefix = pattern.split("*")[0]
                return [key for key in self._cache.keys() if key.startswith(prefix)]
            
            return [key for key in self._cache.keys() if key == pattern]
    
    def flush(self) -> bool:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            return True
    
    # Session management interface
    
    def set_session(self, session_id: str, session_data: Dict[str, Any], expiry: int = 3600) -> bool:
        """Store session data with expiration"""
        return self.set(f"session:{session_id}", session_data, ex=expiry)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        return self.get(f"session:{session_id}")
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session data"""
        return self.delete(f"session:{session_id}")
    
    def extend_session(self, session_id: str, expiry: int = 3600) -> bool:
        """Extend session expiration"""
        return self.expire(f"session:{session_id}", expiry)
    
    # Statistics and monitoring
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_entries = len(self._cache)
            memory_usage = self._estimate_memory_usage()
            expired_count = sum(1 for entry in self._cache.values() if entry.is_expired())
            
            return {
                "total_entries": total_entries,
                "expired_entries": expired_count,
                "memory_usage_bytes": memory_usage,
                "memory_usage_mb": round(memory_usage / 1024 / 1024, 2),
                "memory_limit_mb": self.max_size_bytes // 1024 // 1024,
                "memory_utilization": round((memory_usage / self.max_size_bytes) * 100, 2),
                "cleanup_interval": self.cleanup_interval
            }
    
    def __del__(self):
        """Cleanup when cache is destroyed"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

# Global cache instance
_cache_instance = None

def get_cache() -> MemoryCache:
    """Get or create global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        import os
        cache_size_mb = int(os.getenv('CACHE_SIZE_MB', '128'))
        _cache_instance = MemoryCache(max_size_mb=cache_size_mb)
    return _cache_instance

# Async interface for compatibility
class AsyncMemoryCache:
    """Async wrapper for MemoryCache"""
    
    def __init__(self, cache: MemoryCache = None):
        self.cache = cache or get_cache()
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        return self.cache.set(key, value, ex)
    
    async def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)
    
    async def delete(self, key: str) -> bool:
        return self.cache.delete(key)
    
    async def exists(self, key: str) -> bool:
        return self.cache.exists(key)
    
    async def flush(self) -> bool:
        return self.cache.flush()

def get_async_cache() -> AsyncMemoryCache:
    """Get async cache interface"""
    return AsyncMemoryCache()