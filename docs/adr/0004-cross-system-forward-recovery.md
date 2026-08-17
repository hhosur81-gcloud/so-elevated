# Forward Recovery for Cross-System Orchestration Failures

For multi-step cross-system workflows (UC-2.x), when a step succeeds in WorkWeek but fails in ServiceImmediately, the system executes forward recovery (retaining the HR record, logging a high-priority incident with full audit trail, and providing clear manual follow-up instructions) rather than destructive rollbacks.
