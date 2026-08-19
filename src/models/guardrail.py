"""Guardrail and Security Sentinel Models (ADR-0012, SEC-0005)."""

from dataclasses import dataclass
from typing import Optional
from src.models.common import EnterpriseBaseModel


@dataclass
class InspectionResult(EnterpriseBaseModel):
    """Result of a prompt inspection by the Model Armor gateway."""
    is_valid: bool
    action: str  # "ALLOW" or "BLOCK"
    sanitized_text: str
    category: Optional[str] = None  # None, "PROMPT_INJECTION", "JAILBREAK", "SPII_VIOLATION"
    risk_score: float = 0.0
    latency_ms: float = 0.0
    finding_id: Optional[str] = None
