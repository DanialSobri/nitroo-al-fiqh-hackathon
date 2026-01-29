"""
Cache manager for RAG service to improve performance.
Caches PDF content, page lookup results, and query embeddings.
"""
import hashlib
import time
from typing import Dict, Optional, Any, Tuple
from functools import lru_cache
from collections import OrderedDict
import threading


class LRUCache:
    """Thread-safe LRU cache with TTL (Time To Live) support"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: Optional[float] = None):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum number of items to cache
            ttl_seconds: Time to live in seconds (None = no expiration)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.lock = threading.Lock()
    
    def _is_expired(self, key: str) -> bool:
        """Check if a cached item has expired"""
        if self.ttl_seconds is None:
            return False
        if key not in self.timestamps:
            return True
        return time.time() - self.timestamps[key] > self.ttl_seconds
    
    def _cleanup_expired(self):
        """Remove expired items from cache"""
        if self.ttl_seconds is None:
            return
        
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self.timestamps.items()
            if current_time - timestamp > self.ttl_seconds
        ]
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            if key not in self.cache:
                return None
            
            if self._is_expired(key):
                self.cache.pop(key, None)
                self.timestamps.pop(key, None)
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
    
    def set(self, key: str, value: Any):
        """Set item in cache"""
        with self.lock:
            # Cleanup expired items first
            self._cleanup_expired()
            
            # Remove oldest if at capacity
            if key not in self.cache and len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key, None)
                self.timestamps.pop(oldest_key, None)
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
    
    def clear(self):
        """Clear all cached items"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        with self.lock:
            return len(self.cache)


class CacheManager:
    """Centralized cache manager for RAG service"""
    
    def __init__(self, max_size: int = 1000, ttl_hours: float = 24.0):
        """
        Initialize cache manager
        
        Args:
            max_size: Maximum items per cache
            ttl_hours: Cache time-to-live in hours
        """
        ttl_seconds = ttl_hours * 3600
        
        # PDF content cache: key = (pdf_url or filepath, page_num), value = page text
        # TTL: 1 hour (PDFs don't change often)
        self.pdf_content_cache = LRUCache(max_size=max_size, ttl_seconds=3600)
        
        # Page lookup cache: key = hash(pdf_url/filepath + normalized_text), value = page_num
        # TTL: configurable (page lookups are expensive)
        self.page_lookup_cache = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)
        
        # Query embedding cache: key = query text hash, value = embedding
        # TTL: 1 hour
        self.embedding_cache = LRUCache(max_size=max_size, ttl_seconds=3600)
        
        # PDF file cache: key = pdf_url, value = (filepath, download_time)
        # TTL: configurable
        self.pdf_file_cache = LRUCache(max_size=100, ttl_seconds=ttl_seconds)
    
    def _hash_key(self, *args) -> str:
        """Create a hash key from multiple arguments"""
        key_str = "|".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def get_pdf_page_text(self, pdf_identifier: str, page_num: int) -> Optional[str]:
        """Get cached PDF page text"""
        key = f"{pdf_identifier}|{page_num}"
        return self.pdf_content_cache.get(key)
    
    def set_pdf_page_text(self, pdf_identifier: str, page_num: int, text: str):
        """Cache PDF page text"""
        key = f"{pdf_identifier}|{page_num}"
        self.pdf_content_cache.set(key, text)
    
    def get_page_lookup(self, pdf_identifier: str, normalized_text: str) -> Optional[int]:
        """Get cached page lookup result"""
        key = self._hash_key(pdf_identifier, normalized_text)
        return self.page_lookup_cache.get(key)
    
    def set_page_lookup(self, pdf_identifier: str, normalized_text: str, page_num: int):
        """Cache page lookup result"""
        key = self._hash_key(pdf_identifier, normalized_text)
        self.page_lookup_cache.set(key, page_num)
    
    def get_embedding(self, query: str) -> Optional[list]:
        """Get cached query embedding"""
        key = self._hash_key(query)
        return self.embedding_cache.get(key)
    
    def set_embedding(self, query: str, embedding: list):
        """Cache query embedding"""
        key = self._hash_key(query)
        self.embedding_cache.set(key, embedding)
    
    def get_pdf_file(self, pdf_url: str) -> Optional[Tuple[str, float]]:
        """Get cached PDF file path"""
        return self.pdf_file_cache.get(pdf_url)
    
    def set_pdf_file(self, pdf_url: str, filepath: str):
        """Cache PDF file path"""
        self.pdf_file_cache.set(pdf_url, (filepath, time.time()))
    
    def clear_all(self):
        """Clear all caches"""
        self.pdf_content_cache.clear()
        self.page_lookup_cache.clear()
        self.embedding_cache.clear()
        self.pdf_file_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'pdf_content_cache_size': self.pdf_content_cache.size(),
            'page_lookup_cache_size': self.page_lookup_cache.size(),
            'embedding_cache_size': self.embedding_cache.size(),
            'pdf_file_cache_size': self.pdf_file_cache.size(),
        }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        from config import settings
        _cache_manager = CacheManager(
            max_size=settings.cache_max_size,
            ttl_hours=settings.cache_ttl_hours
        )
    return _cache_manager
