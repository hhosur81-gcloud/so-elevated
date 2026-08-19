"""Policy Search Retriever with Query-Time Role ACL Filtering (ADR-0002, ADR-0008, Section 14.3)."""

import os
import re
from typing import Any, Dict, List, Optional


class PolicySearchRetriever:
    """Retrieves grounded policy chunks from local files or Vertex AI Search Datastore."""

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

                # Parse simple frontmatter
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
        """Search policy chunks matching query and filtered by employee role (Query-time ACL)."""
        query_words = set(re.findall(r"\w+", query.lower()))
        results = []

        for doc in self._documents:
            # Query-Time Vector ACL Filtering (Section 14.3)
            auth_roles = doc.get("authorized_roles", [])
            if employee_role not in auth_roles and "All" not in auth_roles:
                continue

            doc_text = f"{doc['section_title']} {doc['content']}".lower()
            doc_words = set(re.findall(r"\w+", doc_text))
            overlap = query_words & doc_words

            # Exclude common stopwords
            stopwords = {"how", "many", "days", "of", "do", "i", "get", "what", "is", "the", "a", "for", "to", "in", "are"}
            meaningful_overlap = overlap - stopwords

            if len(meaningful_overlap) >= 1:
                score = float(len(meaningful_overlap)) / max(len(query_words - stopwords), 1)
                results.append({
                    "score": score,
                    "doc_title": doc["doc_title"],
                    "url": doc["url"],
                    "section_title": doc["section_title"],
                    "content": doc["content"]
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
