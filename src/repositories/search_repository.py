"""Policy Search Retriever with Root Stemming & Recursive Ingestion (ADR-0002, ADR-0008, Section 14.3)."""

import os
import re
from typing import Any, Dict, List, Optional


class PolicySearchRetriever:
    """Retrieves grounded policy chunks with weighted section matching and zero-hallucination score thresholds."""

    STOPWORDS = {
        "how", "many", "days", "weeks", "months", "of", "do", "i", "get", "what", "is", "the", "a",
        "for", "to", "in", "are", "can", "employee", "employees", "corporate", "office", "company",
        "we", "my", "our", "you", "your", "tell", "me", "about", "there", "any", "have", "with", "an", "during"
    }

    def __init__(self, policy_dirs: Optional[List[str]] = None, policy_dir: Optional[str] = None):
        if policy_dirs:
            self.policy_dirs = policy_dirs
        elif policy_dir:
            self.policy_dirs = [policy_dir, "knowledge", "fixtures/sample_policies"]
        else:
            self.policy_dirs = ["knowledge", "fixtures/sample_policies"]

        self._documents = self._load_all_policies()

    def _stem(self, word: str) -> str:
        """Lightweight suffix stemming for matching variants (e.g. consume -> consumption, drink -> drinking)."""
        w = word.lower().strip()
        if len(w) <= 3:
            return w
        # Common irregular roots
        irregulars = {
            "consume": "consum", "consumption": "consum", "consuming": "consum",
            "bereave": "bereav", "bereavement": "bereav",
            "parent": "parent", "parental": "parent",
            "medic": "medic", "medical": "medic", "medication": "medic",
            "smoke": "smok", "smoking": "smok",
            "alcohol": "alcohol", "alcoholic": "alcohol",
            "relocate": "relocat", "relocation": "relocat",
            "discipline": "disciplin", "disciplinary": "disciplin"
        }
        if w in irregulars:
            return irregulars[w]
        # Generic suffix removal
        return re.sub(r"(ing|tion|tions|ed|ies|es|s|al|ment)$", "", w)

    def _load_all_policies(self) -> List[Dict[str, Any]]:
        """Recursively discover and parse markdown policy documents across all knowledge directories."""
        docs = []
        seen_paths = set()

        for base_dir in self.policy_dirs:
            if not os.path.exists(base_dir):
                continue

            for root, _, files in os.walk(base_dir):
                for filename in files:
                    if filename.endswith(".md") and filename != "index.md":
                        file_path = os.path.join(root, filename)
                        if file_path in seen_paths:
                            continue
                        seen_paths.add(file_path)

                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()

                            metadata, body = self._parse_frontmatter(content, filename)
                            sections = self._extract_sections(body, metadata, file_path)
                            docs.extend(sections)
                        except Exception as e:
                            print(f"Warning: Failed to parse policy {file_path}: {e}")

        return docs

    def _parse_frontmatter(self, content: str, default_title: str) -> tuple[Dict[str, Any], str]:
        """Extract YAML frontmatter and document body."""
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

        return metadata, body

    def _extract_sections(self, body: str, metadata: Dict[str, Any], file_path: str) -> List[Dict[str, Any]]:
        """Split document into coherent, citation-tagged sections."""
        docs = []
        doc_title = metadata.get("title") or metadata.get("source") or os.path.basename(file_path)
        doc_url = metadata.get("url") or f"https://intranet.company.com/policies/{os.path.basename(file_path).replace('.md', '.pdf')}"
        auth_roles = metadata.get("authorized_roles", ["Employee", "Manager", "Executive"])
        source_name = metadata.get("source") or metadata.get("title") or doc_title

        raw_sections = body.split("\n## ")
        if len(raw_sections) > 1:
            for sec in raw_sections:
                lines = sec.strip().splitlines()
                sec_title = lines[0].replace("#", "").strip() if lines else "General Guidelines"
                sec_body = "\n".join(lines[1:]).strip() if len(lines) > 1 else sec
                docs.append({
                    "doc_title": doc_title,
                    "source_name": source_name,
                    "url": doc_url,
                    "authorized_roles": auth_roles,
                    "section_title": sec_title,
                    "content": sec_body
                })
        else:
            lines = body.strip().splitlines()
            first_line = lines[0].replace("#", "").strip() if lines else doc_title
            sec_body = "\n".join(lines[1:]).strip() if len(lines) > 1 else body
            docs.append({
                "doc_title": doc_title,
                "source_name": source_name,
                "url": doc_url,
                "authorized_roles": auth_roles,
                "section_title": first_line,
                "content": sec_body
            })

        return docs

    def search_policies(self, query: str, employee_role: str = "Employee") -> List[Dict[str, Any]]:
        """Search policy corpus with stemmed keyword matching and query-time ACL gates."""
        raw_query_words = [w for w in re.findall(r"\w+", query.lower()) if w not in self.STOPWORDS]
        if not raw_query_words:
            return []

        stemmed_query = {self._stem(w) for w in raw_query_words}
        results = []

        for doc in self._documents:
            auth_roles = doc.get("authorized_roles", [])
            if employee_role not in auth_roles and "All" not in auth_roles:
                continue

            title_stems = {self._stem(w) for w in re.findall(r"\w+", doc["section_title"].lower()) if w not in self.STOPWORDS}
            source_stems = {self._stem(w) for w in re.findall(r"\w+", doc.get("source_name", "").lower()) if w not in self.STOPWORDS}
            content_stems = {self._stem(w) for w in re.findall(r"\w+", doc["content"].lower()) if w not in self.STOPWORDS}

            title_matches = stemmed_query & (title_stems | source_stems)
            content_matches = stemmed_query & content_stems

            weighted_score = (len(title_matches) * 3.5) + len(content_matches)
            max_possible = len(stemmed_query) * 3.5
            normalized_score = weighted_score / max_possible if max_possible > 0 else 0.0

            if len(title_matches) >= 1 or len(content_matches) >= 2 or normalized_score >= 0.35:
                results.append({
                    "score": normalized_score,
                    "doc_title": doc["doc_title"],
                    "source_name": doc.get("source_name", doc["doc_title"]),
                    "url": doc["url"],
                    "section_title": doc["section_title"],
                    "content": doc["content"]
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
