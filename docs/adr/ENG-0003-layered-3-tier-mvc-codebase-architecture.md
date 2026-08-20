# ENG-0003: Pragmatic 3-Tier Layered MVC Codebase Architecture

## Context
To structure the codebase for rapid developer velocity, ease of maintenance, and testability across engineering squads, we must establish a clear architectural pattern that avoids monolithic scripts while maintaining clean separation of concerns.

## Decision
We standardize on a **Pragmatic 3-Tier Layered MVC Architecture**:
1. **Controllers / Agent Orchestrator Layer** (`agent/`):
   - Contains the Vertex ADK root `LlmAgent` orchestrator ([`agent/agent.py`](../../agent/agent.py)), system prompt instructions ([`agent/prompt.py`](../../agent/prompt.py)), and ADK Web/CLI entry points.
2. **Services / Business Logic Layer** (`agent/services/` & `agent/cache/`):
   - [`policy_service.py`](../../agent/services/policy_service.py): Open Knowledge Format (OKF) retrieval and citation generator.
   - [`workflow_service.py`](../../agent/services/workflow_service.py): Cross-system orchestration (`UC-2.1`, `UC-2.2`, `UC-2.3`).
   - [`idempotency_store.py`](../../agent/services/idempotency_store.py): Deterministic deduplication and atomic lock management.
   - [`semantic_cache.py`](../../agent/cache/semantic_cache.py) & [`fallback_cascade.py`](../../agent/cache/fallback_cascade.py): Response caching and Gemini Flash fallback cascade.
3. **Domain Models & MCP Adapters Layer** (`agent/models/` & `agent/mcp/`):
   - Pydantic V2 Tolerant Reader schemas (`ConfigDict(extra="ignore")`) for WorkWeek, ITSM, and Session records.
   - FastMCP Streamable HTTP adapters connecting directly to live external services.

## Consequences
- **Developer Velocity**: Clear component boundaries make onboarding and feature additions straightforward.
- **Clean Test Boundaries**: Unit, integration, and canary test suites independently verify services and data models without circular dependencies.
