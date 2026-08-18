# SEC-0006: OpenTelemetry (OTel) Distributed Tracing & Token Profiling

## Context
To provide end-to-end visibility into multi-agent conversational latency, track token consumption per sub-agent, and diagnose distributed bottlenecks, the system requires standardized telemetry.

## Decision
We standardize on OpenTelemetry (OTel) with W3C `traceparent` context propagation across the entire request lifecycle:
- Ingress Client -> Model Armor Gateway -> Primary HR Orchestrator (ADK) -> Domain MCP Servers -> Enterprise APIs.
- Spans are exported to **Google Cloud Trace** and **Google Cloud Monitoring**, capturing sub-operation duration, Gemini input/output token counts, Model Armor inspection latency, and cache hit ratios.

## Consequences
- **Pinpoint Bottleneck Isolation**: Engineers can visualize exact millisecond breakdowns for every tool call and model inference.
- **Granular FinOps Profiling**: Enables exact cost-per-intent attribution by tracking token usage per sub-agent domain.
