"""Semantic & Exact Query Cache for High-Frequency Policy Queries (ENG-0005)."""
import hashlib
import time
from typing import Dict, Optional, Tuple


class SemanticPolicyCache:
    """High-speed in-memory cache for policy Q&A providing <50ms latency deflection."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[str, float]] = {}

    def _normalize_key(self, query: str) -> str:
        """Normalize and hash user query string."""
        cleaned = " ".join(query.lower().strip().split())
        return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

    def get(self, query: str) -> Optional[str]:
        """Fetch cached response if present and not expired."""
        key = self._normalize_key(query)
        if key in self._cache:
            response, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return response
            else:
                del self._cache[key]
        return None

    def set(self, query: str, response: str) -> None:
        """Store query response in cache."""
        key = self._normalize_key(query)
        self._cache[key] = (response, time.time())

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
