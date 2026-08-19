# 06 — Primary HR Orchestrator Agent (Vertex ADK) & Dispatcher

**What to build:** Root conversational loop built on Vertex AI ADK with 15-minute idle TTL & explicit reset (ADR-0009), human confirmation gate on state mutations (ADR-0007, Q4), and sub-agent dispatching to Policy, WorkWeek, and ServiceImmediately specialists.

**Blocked by:** 02 — Security Sentinel Interceptor, 03 — WorkWeek HCM Mock, 04 — ServiceImmediately ITSM Mock, 05 — Policy Q&A Agent

**Status:** closed

- [x] Session manager implementing 15-minute idle TTL and immediate purge on reset prompts (`src/agents/orchestrator_agent.py`).
- [x] Sequential 2-turn human confirmation gate on all state-changing write operations (`requires_confirmation` & `pending_confirmation`).
- [x] Correctly routes single-domain user prompts (UC-1.1 Policy, UC-1.2 WorkWeek PTO, UC-1.3 IT Incident).
- [x] End-to-end conversational test suite passing multi-turn inquiries with accurate context retention (`tests/integration/test_orchestrator_agent.py`).
