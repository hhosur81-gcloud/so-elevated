"""Policy Search Retriever with Enhanced Relevance Scoring & Role ACL Filtering (ADR-0002, ADR-0008, Section 14.3)."""

import os
import re
from typing import Any, Dict, List, Optional


class PolicySearchRetriever:
    """Retrieves grounded policy chunks with weighted section matching and zero-hallucination score thresholds."""

    STOPWORDS = {
        "how", "many", "days", "weeks", "months", "of", "do", "i", "get", "what", "is", "the", "a",
        "for", "to", "in", "are", "can", "employee", "employees", "corporate", "office", "company",
        "we", "my", "our", "you", "your", "tell", "me", "about", "there", "any", "have"
    }

    def __init__(self, policy_dir: str = "fixtures/sample_policies"):
        self.policy_dir = policy_dir
        self._documents = self._load_local_policies()

    def _load_local_policies(self) -> List[Dict[str, Any]]:
        """Parse local markdown policy documents with frontmatter metadata."""
        docs = []
        if not os.path.exists(self.policy_dir):
            return docs

        for filename in os.listdir(self.policy_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(self.policy_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse frontmatter
                metadata = {}
                body = content
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        for line in parts[1].strip().splitlines():
                            if ":" in line:
                                k, v = line.split(":", 1)
                                k = k.strip()
                                v = v.strip().strip('"').strip("'")
                                if v.startswith("[") and v.endswith("]"):
                                    v = [item.strip().strip('"').strip("'") for item in v[1:-1].split(",") if item.strip()]
                                metadata[k] = v
                        body = parts[2].strip()

                # Extract sections
                sections = body.split("\n## ")
                for sec in sections:
                    lines = sec.strip().splitlines()
                    sec_title = lines[0].replace("#", "").strip() if lines else "General"
                    sec_body = "\n".join(lines[1:]).strip() if len(lines) > 1 else sec
                    docs.append({
                        "doc_title": metadata.get("title", filename),
                        "url": metadata.get("url", "https://intranet.company.com/policies/hr.pdf"),
                        "authorized_roles": metadata.get("authorized_roles", ["Employee", "Manager", "Executive"]),
                        "section_title": sec_title,
                        "content": sec_body
                    })
        return docs

    def search_policies(self, query: str, employee_role: str = "Employee") -> List[Dict[str, Any]]:
        """Search policy chunks with weighted title scoring and minimum confidence threshold."""
        query_raw_words = re.findall(r"\w+", query.lower())
        query_words = set(query_raw_words) - self.STOPWORDS

        if not query_words:
            return []

        results = []

        for doc in self._documents:
            # 1. Query-Time Role ACL Filtering (Section 14.3)
            auth_roles = doc.get("authorized_roles", [])
            if employee_role not in auth_roles and "All" not in auth_roles:
                continue

            title_words = set(re.findall(r"\w+", doc["section_title"].lower())) - self.STOPWORDS
            content_words = set(re.findall(r"\w+", doc["content"].lower())) - self.STOPWORDS

            title_matches = query_words & title_words
            content_matches = query_words & content_words

            # Weight title matches higher than incidental body matches
            weighted_score = (len(title_matches) * 3.0) + len(content_matches)
            max_possible = len(query_words) * 3.0
            normalized_score = weighted_score / max_possible if max_possible > 0 else 0.0

            # Strict relevance threshold: must match title keywords OR at least 2 distinct content words
            if len(title_matches) >= 1 or len(content_matches) >= 2 or normalized_score >= 0.35:
                results.append({
                    "score": normalized_score,
                    "doc_title": doc["doc_title"],
                    "url": doc["url"],
                    "section_title": doc["section_title"],
                    "content": doc["content"]
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
