# 02 — Security Sentinel Gateway (Google Cloud Model Armor & Tiered SPII)

**What to build:** Managed AI security gateway integrating Google Cloud Model Armor (ADR-0012) for prompt injection defense and Cloud DLP SPII redaction, with in-memory Presidio/Regex fallback for offline local unit tests.

**Blocked by:** 01 — Project Scaffold, Domain Models & Signed JWT Auth

**Status:** closed

- [x] Model Armor client integration inspecting inbound prompts for injection, jailbreaks, and harmful content (`src/services/guardrail_service.py`).
- [x] Tiered Cloud DLP / Presidio redaction masking SPII (addresses, phone numbers, SSNs) from persistent logs and audit traces while allowing ephemeral self-viewing.
- [x] Offline fallback adapter executing local regex/Presidio when Model Armor API credentials are absent.
- [x] Benchmark test suite confirming total safety gateway latency < 300ms (`tests/unit/test_guardrail_service.py`).
