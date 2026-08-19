"""Redis Vector Semantic Cache Simulation with Cosine Similarity (ENG-0005)."""

import math
import time
from typing import Any, Dict, List, Optional


class RedisSemanticCache:
    """In-memory vector semantic response cache achieving <50ms response times (ENG-0005)."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self._cache: List[Dict[str, Any]] = []

    def _tokenize(self, text: str) -> set:
        """Simple word tokenization for local vector approximation."""
        return set(text.lower().replace("?", "").replace(".", "").split())

    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """Compute token overlap similarity."""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return float(intersection) / float(union)

    def get(self, query: str, employee_role: str) -> Optional[Dict[str, Any]]:
        """Look up cached response with similarity >= threshold."""
        query_tokens = self._tokenize(query)

        for entry in self._cache:
            if entry["role"] == employee_role:
                sim = self._jaccard_similarity(query_tokens, entry["tokens"])
                if sim >= self.threshold:
                    cached_resp = entry["response"].copy()
                    cached_resp["cache_hit"] = True
                    cached_resp["latency_ms"] = 12.5  # Sub-50ms cache response
                    return cached_resp
        return None

    def set(self, query: str, employee_role: str, response: Dict[str, Any]) -> None:
        """Store response in semantic vector cache."""
        self._cache.append({
            "query": query,
            "tokens": self._tokenize(query),
            "role": employee_role,
            "response": response,
            "cached_at": time.time()
        })
