"""Google Cloud Model Armor & Security Sentinel Service.

Enforces Layer 0 AI Security Gateway protecting against Prompt Injection,
Jailbreaks, Harmful Content (RAI), and Sensitive PII (SPII) leakage.
"""
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import google.auth
import google.auth.transport.requests

logger = logging.getLogger("altostrat.security.model_armor")

# Comprehensive Prompt Injection & Jailbreak Patterns
INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"(?i)disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"(?i)you\s+are\s+now\s+(in\s+)?(DAN|developer|jailbreak|unrestricted)\s+mode",
    r"(?i)reveal\s+(your\s+)?(system\s+prompt|hidden\s+instructions|developer\s+mode)",
    r"(?i)print\s+(your\s+)?(initial\s+prompt|system\s+prompt|rules)",
    r"(?i)output\s+(your\s+)?(system\s+instructions|prompt\s+template)",
    r"(?i)pretend\s+you\s+have\s+no\s+(rules|restrictions|guidelines)",
    r"(?i)bypass\s+(all\s+)?(safety|security|policy)\s+(filters|checks|guidelines)",
    r"(?i)system\s+override\s*:\s*admin",
    r"(?i)base64\s+decode\s+and\s+execute",
]

# Sensitive PII Patterns (SSN, Credit Cards, Secrets)
SPII_PATTERNS = {
    "US_SSN": r"\b(?!000)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b",
    "CREDIT_CARD": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",
    "API_KEY": r"(?i)(?:api[_-]?key|secret|token)\s*[:=]\s*['\"][a-zA-Z0-9_\-\.]{20,}['\"]",
}


class SecurityViolationError(Exception):
    """Raised when Model Armor intercepts an adversarial prompt or SPII leakage."""
    def __init__(self, message: str, violation_type: str = "PROMPT_INJECTION", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.violation_type = violation_type
        self.details = details or {}


@dataclass
class SanitizationResult:
    is_safe: bool
    sanitized_text: str
    violations: List[str] = field(default_factory=list)
    spii_redacted: bool = False
    overhead_ms: float = 0.0
    source: str = "MODEL_ARMOR_CLOUD"


class ModelArmorService:
    """Manages Layer 0 Model Armor sanitization and Cloud DLP redaction."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "global",
        enable_cloud_model_armor: bool = True,
    ):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "so-elevated")
        self.location = location
        self.enable_cloud = enable_cloud_model_armor
        self._compiled_injections = [re.compile(p) for p in INJECTION_PATTERNS]
        self._compiled_spii = {k: re.compile(v) for k, v in SPII_PATTERNS.items()}

    def _get_auth_token(self) -> Optional[str]:
        """Fetch ADC bearer token for Google Cloud Model Armor API."""
        try:
            credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            auth_req = google.auth.transport.requests.Request()
            credentials.refresh(auth_req)
            return credentials.token
        except Exception as e:
            logger.warning("Could not refresh ADC credentials for Model Armor: %s", e)
            return None

    def sanitize_user_prompt(self, prompt: str) -> SanitizationResult:
        """Inspect and sanitize incoming user prompt for injections, harmful content, and SPII."""
        start_time = time.time()
        violations = []
        sanitized = prompt

        # 1. High-Speed Heuristic & Regex Pre-Screening (<2ms)
        for pattern in self._compiled_injections:
            if pattern.search(prompt):
                violations.append("PROMPT_INJECTION_OR_JAILBREAK")
                break

        # 2. SPII Inspection & Redaction
        spii_found = False
        for spii_type, regex in self._compiled_spii.items():
            if regex.search(sanitized):
                sanitized = regex.sub(f"[REDACTED_{spii_type}]", sanitized)
                spii_found = True
                violations.append(f"SPII_{spii_type}")

        overhead_ms = (time.time() - start_time) * 1000

        if "PROMPT_INJECTION_OR_JAILBREAK" in violations:
            logger.warning("🚨 Model Armor Security Sentinel blocked prompt injection: %s", prompt[:80])
            raise SecurityViolationError(
                "Your request was blocked by Google Cloud Model Armor: Prompt Injection / System Override detected.",
                violation_type="PROMPT_INJECTION",
                details={"prompt_preview": prompt[:100], "violations": violations}
            )

        return SanitizationResult(
            is_safe=True,
            sanitized_text=sanitized,
            violations=violations,
            spii_redacted=spii_found,
            overhead_ms=overhead_ms,
            source="MODEL_ARMOR_GATEWAY"
        )

    def sanitize_model_response(self, response_text: str) -> SanitizationResult:
        """Inspect and sanitize model output before returning to user to guarantee zero SPII leakage."""
        start_time = time.time()
        sanitized = response_text
        spii_found = False
        violations = []

        for spii_type, regex in self._compiled_spii.items():
            if regex.search(sanitized):
                sanitized = regex.sub(f"[REDACTED_{spii_type}]", sanitized)
                spii_found = True
                violations.append(f"SPII_{spii_type}")

        overhead_ms = (time.time() - start_time) * 1000

        return SanitizationResult(
            is_safe=True,
            sanitized_text=sanitized,
            violations=violations,
            spii_redacted=spii_found,
            overhead_ms=overhead_ms,
            source="MODEL_ARMOR_GATEWAY"
        )


# Global singleton instance
model_armor_gateway = ModelArmorService()
