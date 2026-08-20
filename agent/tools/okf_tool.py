"""Open Knowledge Format (OKF) retrieval tools for HR policy grounding."""
import re
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from .. import config

def _normalize_path(rel_path: str) -> Path:
    """Resolve a relative concept path against the knowledge directory."""
    clean_path = rel_path.strip().lstrip("/")
    if not clean_path.endswith(".md"):
        clean_path += ".md"
    return config.KNOWLEDGE_DIR / clean_path


def list_concepts(filter_keyword: str = "") -> str:
    """Lists all available HR policy categories, sections, and concept files in the knowledge base.
    
    Use this tool when you need to discover which policy documents or sections exist before reading them.
    
    Args:
        filter_keyword: Optional keyword to filter sections/concepts (e.g., "leave", "travel", "ethics").
    
    Returns:
        A formatted markdown summary of available policy sections and concept file paths.
    """
    index_path = config.KNOWLEDGE_DIR / "index.md"
    if not index_path.is_file():
        return f"Error: Knowledge index not found at {index_path}"

    content = index_path.read_text(encoding="utf-8")
    
    # Remove frontmatter if present
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]
            
    if not filter_keyword:
        return content.strip()

    # Filter lines matching keyword
    kw = filter_keyword.lower()
    matching_lines = []
    current_section = ""
    
    for line in content.splitlines():
        if line.startswith("## Section"):
            current_section = line
        elif kw in line.lower():
            if current_section and current_section not in matching_lines:
                matching_lines.append(current_section)
            matching_lines.append(line)
            
    if not matching_lines:
        return f"No policy concepts found matching filter '{filter_keyword}'. Here is the full index:\n\n{content.strip()}"
        
    return "\n".join(matching_lines)


def read_concept(concept_path: str) -> str:
    """Reads the full policy text and metadata of a specific OKF concept file.
    
    Always use this tool to ground answers to employee HR/IT policy questions.
    
    Args:
        concept_path: The relative path to the concept markdown file (e.g. 
                     '01-paid-time-off-leave-operations/1.1-outpatient-sick-time-hospitalization-leave-singapore.md'
                     or '04-travel-expense-te-guidelines/4.1-frugality-booking-timelines.md').
                     
    Returns:
        The verbatim policy text along with its formal source citation.
    """
    target_file = _normalize_path(concept_path)
    
    if not target_file.is_file():
        # Attempt fuzzy lookup across knowledge directory
        matches = list(config.KNOWLEDGE_DIR.glob(f"**/*{Path(concept_path).name}*"))
        if matches and matches[0].is_file():
            target_file = matches[0]
        else:
            return (
                f"Policy concept file '{concept_path}' was not found. "
                "Please call list_concepts() to verify the exact concept path."
            )
            
    raw_content = target_file.read_text(encoding="utf-8")
    
    # Parse YAML frontmatter if present
    frontmatter: Dict = {}
    body = raw_content
    if raw_content.startswith("---"):
        parts = raw_content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except Exception:
                pass
            body = parts[2].strip()
            
    title = frontmatter.get("title", target_file.stem)
    source = frontmatter.get("source", f"Altostrat Policy Handbook: {title}")
    rel_path = target_file.relative_to(config.KNOWLEDGE_DIR)
    
    return (
        f"=== POLICY CITATION: [{title}]({rel_path}) ===\n"
        f"Source: {source}\n\n"
        f"{body}"
    )
