# 10 — OpenTelemetry Distributed Tracing & SCC Threat Automation

**What to build:** OpenTelemetry (OTel) instrumentation propagating W3C `traceparent` context across all agent hops to Google Cloud Trace, paired with Eventarc streaming from Model Armor to Security Command Center (SCC) Premium and automated P1 security incident creation in ServiceImmediately (SEC-0005, SEC-0006).

**Blocked by:** 02 — Security Sentinel Gateway, 06 — Primary HR Orchestrator (ADK)

**Status:** ready-for-agent

- [ ] OpenTelemetry middleware capturing sub-agent latency, Gemini token consumption (input/output), and Cloud DLP scan duration.
- [ ] Context propagation injector attaching W3C `traceparent` headers to all outbound MCP and REST tool calls.
- [ ] Eventarc subscriber forwarding Model Armor security violation events to Security Command Center (SCC) Premium.
- [ ] Automated security incident handler creating a Priority 1 Security Incident in ServiceImmediately for high-confidence injection attacks.
- [ ] Verification tests asserting trace spans and automated security incident creation on red-team injection payloads.
