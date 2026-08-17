# 07 — Cross-System Workflow Handlers with Forward Recovery

**What to build:** Multi-system chained orchestration for UC-2.1 (Equipment Procurement), UC-2.2 (Medical Leave), and UC-2.3 (Relocation Transfer) with human confirmation turns and automated forward recovery on partial failure (ADR-0004).

**Blocked by:** 06 — Primary HR Orchestrator Agent (Vertex ADK)

**Status:** ready-for-agent

- [ ] UC-2.1 executes Policy check -> WorkWeek remote status verify -> ServiceImmediately hardware request.
- [ ] UC-2.2 executes Policy quote -> Confirmation turn -> WorkWeek LOA booking -> ServiceImmediately email routing ticket.
- [ ] UC-2.3 executes Relocation allowance check -> Confirmation turn -> WorkWeek address update -> ServiceImmediately badge ticket.
- [ ] Forward recovery handler generates high-priority audit logs and clear user guidance when any step fails.
