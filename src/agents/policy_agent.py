"""Policy Q&A Specialist Agent with Semantic Caching and Grounded Citations (ADR-0002, ADR-0008, ENG-0005)."""

import time
from typing import Any, Dict, Optional
from src.repositories.search_repository import PolicySearchRetriever
from src.services.semantic_cache_service import RedisSemanticCache


class PolicyAgent:
    """Specialist sub-agent resolving enterprise policy queries with strict grounding and citations."""

    def __init__(self, policy_dir: str = "fixtures/sample_policies"):
        self.retriever = PolicySearchRetriever(policy_dir=policy_dir)
        self.cache = RedisSemanticCache()

    def answer_policy_query(self, query: str, employee_role: str = "Employee") -> Dict[str, Any]:
        """Process user policy question with cache lookup, search retrieval, and citation synthesis."""
        start_time = time.perf_counter()

        # 1. Check Redis Vector Semantic Cache (ENG-0005)
        cached_result = self.cache.get(query, employee_role)
        if cached_result:
            return cached_result

        # 2. Query Search Retriever (with Query-Time ACL Filtering)
        search_results = self.retriever.search_policies(query, employee_role=employee_role)

        if not search_results:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "success": False,
                "has_policy_match": False,
                "answer": "I apologize, but that topic is not covered in our current published company policies. Please contact your HR Business Partner directly.",
                "citation_url": None,
                "citation_label": None,
                "latency_ms": elapsed_ms,
                "cache_hit": False
            }

        top_match = search_results[0]
        content_snippet = top_match["content"]
        section_label = top_match["section_title"]
        doc_url = top_match["url"]

        # Synthesize grounded response
        answer_text = f"According to company policy ({section_label}): {content_snippet}"
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        response = {
            "success": True,
            "has_policy_match": True,
            "answer": answer_text,
            "citation_url": doc_url,
            "citation_label": section_label,
            "latency_ms": elapsed_ms,
            "cache_hit": False
        }

        # 3. Store in Semantic Vector Cache
        self.cache.set(query, employee_role, response)

        return response
