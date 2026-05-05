import asyncio
import time
import hashlib
import json
import logging
from collections import OrderedDict
from typing import Generic, TypeVar, Callable
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)

K = TypeVar("K")
V = TypeVar("V")

@dataclass
class CacheEntry(Generic[V]):
    value: V
    created_at: float
    hit_count: int = 0

class LRUCache(Generic[K, V]):
    """In-memory thread/async-safe Least Recently Used cache."""
    def __init__(self, max_size: int, ttl_seconds: int, name: str = "cache"):
        self._cache: OrderedDict[K, CacheEntry[V]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._name = name
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
    
    async def get(self, key: K) -> V | None:
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            if time.monotonic() - entry.created_at > self._ttl:
                del self._cache[key]
                self._misses += 1
                return None
            
            self._cache.move_to_end(key)
            entry.hit_count += 1
            self._hits += 1
            return entry.value
            
    async def set(self, key: K, value: V):
        async with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = CacheEntry(value=value, created_at=time.monotonic())
            
            while len(self._cache) > self._max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                logger.debug(f"Cache '{self._name}': evicted key {evicted_key}")
                
    async def invalidate(self, key: K):
        async with self._lock:
            self._cache.pop(key, None)
            
    async def clear(self):
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            
    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "name": self._name,
            "size": len(self._cache),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl,
            "total_requests": total,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total > 0 else 0.0
        }

# ━━━ PART B: APPLICATION CACHES ━━━

def _make_analysis_key(image_bytes: bytes, symptoms_text: str) -> str:
    content = image_bytes + symptoms_text.encode()
    return hashlib.md5(content).hexdigest()

def _make_rag_key(query: str) -> str:
    return hashlib.md5(query.lower().strip().encode()).hexdigest()

# Singletons initialized here for app-wide use
analysis_cache: LRUCache[str, dict] = LRUCache(max_size=50, ttl_seconds=3600, name="analysis")
rag_cache: LRUCache[str, list] = LRUCache(max_size=200, ttl_seconds=1800, name="rag")
user_cache: LRUCache[str, dict] = LRUCache(max_size=500, ttl_seconds=300, name="user")

# ━━━ PART C: CACHE DECORATOR ━━━

def cached(cache: LRUCache, key_fn: Callable):
    """Decorator for async functions. Checks cache before executing."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            cached_value = await cache.get(key)
            
            if cached_value is not None:
                logger.debug(f"Cache HIT for {func.__name__}: key={str(key)[:8]}...")
                return cached_value
                
            logger.debug(f"Cache MISS for {func.__name__}: key={str(key)[:8]}...")
            result = await func(*args, **kwargs)
            await cache.set(key, result)
            return result
        return wrapper
    return decorator
