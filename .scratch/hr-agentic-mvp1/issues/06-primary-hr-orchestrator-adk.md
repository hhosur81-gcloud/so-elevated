# 06 — Primary HR Orchestrator Agent (Vertex ADK) & Dispatcher

**What to build:** Root conversational loop built on Vertex AI ADK with 15-minute idle TTL & explicit reset (ADR-0009), confirmation gate (ADR-0007), and sub-agent dispatching to Policy, WorkWeek, and ServiceImmediately specialists.

**Blocked by:** 02 — Security Sentinel Interceptor, 03 — WorkWeek HCM Mock, 04 — ServiceImmediately ITSM Mock, 05 — Policy Q&A Agent

**Status:** ready-for-agent

- [ ] Session manager implementing 15-minute idle TTL and immediate purge on reset prompts.
- [ ] Human confirmation gate on all state-changing write operations.
- [ ] Correctly routes single-domain user prompts (UC-1.1 Policy, UC-1.2 WorkWeek PTO, UC-1.3 IT Incident).
- [ ] End-to-end conversational test suite passing multi-turn inquiries with accurate context retention.
