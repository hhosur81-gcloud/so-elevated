# 02 — Security Sentinel Interceptor (Tiered SPII & Prompt Safety)

**What to build:** Pre/post-execution security middleware executing sub-20ms Presidio/Regex Sensitive Personally Identifiable Information (SPII) tiered redaction (ADR-0011) and prompt injection/jailbreak classification.

**Blocked by:** 01 — Project Scaffold, Domain Models & Signed JWT Auth

**Status:** ready-for-agent

- [ ] Inbound prompt inspector detecting and blocking prompt injection, jailbreaks, and off-topic bypasses.
- [ ] Outbound logger redacting addresses, phone numbers, and SSNs from audit logs, stdout, and persistent storage while permitting ephemeral self-viewing in UI stream.
- [ ] Benchmark test confirming total safety interceptor latency < 300ms (< 20ms regex/Presidio).
