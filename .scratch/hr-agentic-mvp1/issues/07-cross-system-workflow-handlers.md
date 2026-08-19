# 07 — Cross-System Workflow Handlers with Forward Recovery

**What to build:** Multi-system chained orchestration for UC-2.1 (Equipment Procurement), UC-2.2 (Medical Leave), and UC-2.3 (Relocation Transfer) with human confirmation turns and automated forward recovery on partial failure (ADR-0004).

**Blocked by:** 06 — Primary HR Orchestrator Agent (Vertex ADK)

**Status:** closed

- [x] UC-2.1 executes Policy check -> WorkWeek profile verify -> ServiceImmediately hardware request (`src/services/workflow_service.py`).
- [x] UC-2.2 executes Policy lookup -> Confirmation turn -> WorkWeek LOA booking -> ServiceImmediately email/equipment IT routing ticket.
- [x] UC-2.3 executes Relocation policy check -> Confirmation turn -> WorkWeek address update -> ServiceImmediately badge provisioning ticket.
- [x] Forward recovery handler generates high-priority audit logs and clear user guidance when any step fails (ADR-0004).
- [x] Integration test suite verifying multi-system workflows and forward recovery resilience (`tests/integration/test_workflow_coordinator.py`).
