# ENG-0006: 24/7 Continuous Synthetic Production Canaries & Active Probing

## Context
Passive error logging only detects outages when real employees encounter failures. To guarantee 99.99% uptime and proactively detect degradations in downstream MCP backends, policy search, or Model Armor, engineering requires active synthetic probing.

## Decision
We deploy an automated **Synthetic Production Canary Worker** orchestrated via Google Cloud Scheduler and Cloud Run:
- Every 5 minutes, the canary worker executes an automated multi-turn synthetic conversation against an isolated synthetic test account (`EMP-CANARY-01`).
- The probe exercises the full vertical stack: Policy Search Q&A $ightarrow$ Model Armor Ingress/Egress $ightarrow$ WorkWeek PTO balance fetch $ightarrow$ ServiceImmediately ticket creation and deletion.
- Synthetic transaction latencies, success rates, and token counts are streamed directly to **Google Cloud Monitoring**; any failed canary probe triggers an immediate P1 on-call page.

## Consequences
- **Proactive Incident Detection**: Detects backend degradations and API breaking changes in < 5 minutes before real employees are impacted.
- **Verifiable SLAs**: Generates continuous, objective availability metrics for enterprise executive reporting.
