# HR Agentic Solution (MVP 1)

A unified, AI-driven virtual assistant built on the **Google Cloud Vertex AI Agent Development Kit (ADK)** that automates Tier-1 HR inquiries and orchestrates cross-system workflows across **WorkWeek (HCM)** and **ServiceImmediately (ITSM)** with strict grounding against policy documents in **Vertex AI Search**.

👉 **[View Styled HTML Documentation (README.html)](./README.html)**
👉 **[View Google Slides Presentation Deck (docs/slides/index.html)](./docs/slides/index.html)**

---

## Architecture Topologies

### 1. System Topology
![System Architecture](./docs/assets/hr_agent_architecture.jpg)

### 2. Multi-Agent Hierarchy
![Multi-Agent Architecture](./docs/assets/multi_agent_architecture.jpg)

---

## Key Deliverables & Documentation Index

- **[Business Requirements Document (BRD)](./requirements/HR-Agentic-BRD.md)** — Core scope, 5-phase functional requirements, and success metrics.
- **[Technical Feature Specification](./.scratch/hr-agentic-mvp1/spec.md)** — 35 detailed user stories, module seams, and Requirements Traceability Matrix.
- **[Multi-Agent Architecture Specification](./docs/multi_agent_architecture.md)** — Detailed agent scopes, tools, and cross-system communication sequence.
- **[Domain Glossary (CONTEXT.md)](./CONTEXT.md)** — Canonical project domain terminology.
- **[Architectural Decision Records (ADRs)](./docs/adr/)** — ADR-0001 through ADR-0011.
- **[Tracer-Bullet Implementation Tickets](./.scratch/hr-agentic-mvp1/issues/)** — 8 atomic dependency-linked tickets ready for TDD implementation.

---

## Architectural Decision Records (ADRs)

| ADR | Title | Decision Summary |
| :--- | :--- | :--- |
| **[ADR-0001](./docs/adr/0001-fastapi-mock-services.md)** | FastAPI Mock Services | Local RESTful mock services with stateful JSON fixtures. |
| **[ADR-0002](./docs/adr/0002-vertex-ai-search-policy-rag.md)** | Vertex AI Search Policy RAG | Semantic retrieval & strict grounding with metadata citations. |
| **[ADR-0003](./docs/adr/0003-hybrid-safety-guardrails.md)** | Multi-Stage Hybrid Guardrails | <20ms Presidio/Regex SPII redaction + LLM injection classifier. |
| **[ADR-0004](./docs/adr/0004-cross-system-forward-recovery.md)** | Cross-System Forward Recovery | High-priority audit logging & manual follow-up for partial failures. |
| **[ADR-0005](./docs/adr/0005-vertex-agent-development-kit.md)** | Vertex AI Agent Development Kit | Unified agent orchestration for model invoking & session state. |
| **[ADR-0006](./docs/adr/0006-signed-jwt-delegated-authorization.md)** | Signed JWT Delegated Authorization | Bearer tokens carrying user identity and automation origin claims. |
| **[ADR-0007](./docs/adr/0007-human-confirmation-on-state-mutations.md)** | Human Confirmation Gate on Mutations | Explicit confirmation turn required before state-changing writes. |
| **[ADR-0008](./docs/adr/0008-strict-live-vertex-ai-search-testing.md)** | Strict Live Vertex AI Search Testing | Integration tests connect directly to live GCP datastores. |
| **[ADR-0009](./docs/adr/0009-session-ttl-and-explicit-purge.md)** | Session Expiry via Prompt & 15m TTL | Dual-trigger session purge on exit prompts or 15m idle. |
| **[ADR-0010](./docs/adr/0010-interactive-priority-downgrade-guardrail.md)** | Interactive Priority Verification | Interactive prompt when Critical priority lacks major outage justification. |
| **[ADR-0011](./docs/adr/0011-tiered-spii-redaction-logging.md)** | Tiered SPII Redaction | Ephemeral UI self-viewing with strict persistent log masking. |

---

## Multi-Agent Hierarchy

1. **Security Sentinel Interceptor**: Gatekeeper running prompt injection filters and sub-20ms SPII masking.
2. **Primary HR Orchestrator (ADK)**: Root router, session manager (15m TTL), confirmation gate, and workflow coordinator.
3. **Policy Q&A Specialist**: Vertex AI Search grounding, citation deep links, and zero-hallucination fallback.
4. **WorkWeek HCM Specialist**: Profile queries, PTO balances, and guarded leave of absence bookings (`workweek:*` JWT).
5. **ServiceImmediately ITSM Specialist**: Ticket lookup, incident creation, comment timeline, and lifecycle state guards (`serviceimmediately:*` JWT).
