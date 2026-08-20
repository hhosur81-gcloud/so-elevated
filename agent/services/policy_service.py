"""Policy Knowledge Service encapsulating Open Knowledge Format (OKF) retrieval (ENG-0003)."""
from pathlib import Path
from typing import Dict, List, Optional
import yaml

try:
    from .. import config
except (ImportError, ValueError):
    import config


class PolicyService:
    """Service layer managing policy grounding, concept lookup, and formal citations."""

    def __init__(self, knowledge_dir: Optional[Path] = None):
        self.knowledge_dir = knowledge_dir or config.KNOWLEDGE_DIR
        self._index_cache: Optional[str] = None

    def get_index_content(self) -> str:
        """Fetch the full index text from index.md."""
        if self._index_cache is None:
            index_file = self.knowledge_dir / "index.md"
            if not index_file.is_file():
                return "Knowledge index not found."
            content = index_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2]
            self._index_cache = content.strip()
        return self._index_cache

    def list_concepts(self, filter_keyword: str = "") -> str:
        """List policy concepts with optional keyword filtering."""
        full_index = self.get_index_content()
        if not filter_keyword:
            return full_index

        kw = filter_keyword.lower()
        matching_lines: List[str] = []
        current_section = ""

        for line in full_index.splitlines():
            if line.startswith("## Section"):
                current_section = line
            elif kw in line.lower():
                if current_section and current_section not in matching_lines:
                    matching_lines.append(current_section)
                matching_lines.append(line)

        if not matching_lines:
            return f"No concepts matched '{filter_keyword}'. Full index:\n\n{full_index}"
        return "\n".join(matching_lines)

    def read_concept(self, concept_path: str) -> str:
        """Read a concept file, parse YAML frontmatter, and return formatted citation."""
        clean_path = concept_path.strip().lstrip("/")
        if not clean_path.endswith(".md"):
            clean_path += ".md"
        target_file = self.knowledge_dir / clean_path

        if not target_file.is_file():
            # Fuzzy match fallback
            matches = list(self.knowledge_dir.glob(f"**/*{Path(concept_path).name}*"))
            if matches:
                target_file = matches[0]
            else:
                return f"Error: Policy concept file '{concept_path}' not found in knowledge base."

        raw_text = target_file.read_text(encoding="utf-8")
        metadata: Dict[str, str] = {}
        body = raw_text

        if raw_text.startswith("---"):
            parts = raw_text.split("---", 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                except Exception:
                    metadata = {}
                body = parts[2].strip()

        title = metadata.get("title", target_file.stem)
        rel_path = f"/{target_file.relative_to(self.knowledge_dir)}"

        formatted_doc = (
            f"# {title}\n"
            f"**Official Citation Link**: [{title}]({rel_path})\n\n"
            f"{body}"
        )
        return formatted_doc
