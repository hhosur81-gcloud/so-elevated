"""Google Cloud Model Armor Security Gateway & Tiered Cloud DLP SPII Redaction (ADR-0011, ADR-0012)."""

import re
import time
import uuid
from typing import Optional
from src.models.guardrail import InspectionResult


class ModelArmorGateway:
    """Layer 0 Security Sentinel inspecting inbound prompts and outbound completions."""

    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior\s+)?(instructions|rules|guidelines)", re.IGNORECASE),
        re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(developer\s*mode|dan|jailbreak)", re.IGNORECASE),
        re.compile(r"dan\s+mode\s+enabled", re.IGNORECASE),
        re.compile(r"forget\s+(all\s+)?(hr\s+rules|rules|guidelines)", re.IGNORECASE),
        re.compile(r"drop\s+table\s+", re.IGNORECASE),
        re.compile(r"show\s+raw\s+api\s+tokens", re.IGNORECASE),
        re.compile(r"private\s+keys?", re.IGNORECASE),
        re.compile(r"dump\s+(the\s+)?database", re.IGNORECASE),
        re.compile(r"rm\s+-rf", re.IGNORECASE),
        re.compile(r"execute\s+system\s+command", re.IGNORECASE),
        re.compile(r"output\s+all\s+employee\s+salary\s+data", re.IGNORECASE),
        re.compile(r"unlimited\s+paid\s+time\s+off", re.IGNORECASE),
        # Cross-employee data exfiltration and unauthorized inspection
        re.compile(r"\b(what\s+(?:is|are)|show|get|list|display|check|output|tell\s+me|find|view)\s+(?:about\s+)?(?:[a-z]+'s|another\s+employee's|other\s+employees'|someone\s+else's|their)\s+(?:current\s+)?(leave\s+balances?|pto|vacation|sick\s+leave|balances?|salary|compensation|tickets?|personal\s+info|records?)\b", re.IGNORECASE),
        re.compile(r"\b[a-z]+'s\s+(?:current\s+)?(leave\s+balances?|pto|vacation|sick\s+leave|balances?|salary|compensation|tickets?|personal\s+info|records?)\b", re.IGNORECASE),
        re.compile(r"\b(?:the\s+)?(?:leave\s+balances?|pto|vacation|sick\s+leave|balances?|salary|compensation|tickets?|personal\s+info|records?)\s+(?:of|for)\s+(?!me\b|my\b|myself\b|my\s+team\b|this\b|a\b|an\b|the\b|hardware\b|new\b|damaged\b|broken\b|travel\b|access\b|replacement\b)[a-z0-9\-_]+\b", re.IGNORECASE),
        re.compile(r"\bwhat\s+are\s+(?!my\b|our\b)[a-z0-9\-_]+(?:'s)?\s+(?:current\s+)?(?:leave\s+)?balances?\b", re.IGNORECASE),
    ]

    def __init__(self, template_id: Optional[str] = None):
        self.template_id = template_id or "hr-security-gateway-v1"

    def inspect_inbound_prompt(self, prompt: str, employee_id: str = "anonymous") -> InspectionResult:
        """Inspect inbound prompt for malicious injections, jailbreaks, or policy violations."""
        start = time.perf_counter()

        for pattern in self.INJECTION_PATTERNS:
            if pattern.search(prompt):
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                return InspectionResult(
                    is_valid=False,
                    action="BLOCK",
                    sanitized_text="Your request violated enterprise AI safety and security policy.",
                    category="PROMPT_INJECTION",
                    risk_score=0.98,
                    latency_ms=elapsed_ms,
                    finding_id=f"finding-{uuid.uuid4().hex[:8]}"
                )

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return InspectionResult(
            is_valid=True,
            action="ALLOW",
            sanitized_text=prompt,
            category=None,
            risk_score=0.01,
            latency_ms=elapsed_ms,
            finding_id=None
        )


class DLPFilter:
    """Tiered SPII redaction engine protecting audit logs and persistent stores (ADR-0011)."""

    SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
    PHONE_PATTERN = re.compile(r"(\+\d{1,3}[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}")

    def redact_for_logs(self, text: str) -> str:
        """Redact sensitive SPII before persisting to long-term audit logs."""
        # Tier 1: Severe (Full Redaction)
        redacted = self.SSN_PATTERN.sub("[REDACTED_SSN]", text)
        redacted = self.CREDIT_CARD_PATTERN.sub("[REDACTED_CREDIT_CARD]", redacted)

        # Tier 2: Moderate (Partial Masking)
        def mask_phone(match):
            m = match.group(0)
            if m.startswith("+1-555-"):
                return "+1-555-***-****"
            return "[MASKED_PHONE]"

        redacted = self.PHONE_PATTERN.sub(mask_phone, redacted)

        return redacted
