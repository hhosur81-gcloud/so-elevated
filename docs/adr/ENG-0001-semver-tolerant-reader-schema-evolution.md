# ENG-0001: Semantic Versioning (SemVer 2.0.0) & Tolerant Reader Schema Evolution

## Context
Upstream enterprise platforms (WorkWeek HCM and ServiceImmediately ITSM) frequently update their REST API schemas, adding new fields or modifying non-breaking data structures. The agent orchestration layer must accommodate these updates without throwing serialization exceptions or requiring synchronized zero-day agent deployments.

## Decision
We enforce Semantic Versioning (SemVer 2.0.0) on all MCP tool definitions and adopt the **Pydantic Tolerant Reader Pattern** across all domain schemas:
- Models set `model_config = ConfigDict(extra="ignore")` to safely ingest and ignore unexpected new fields from upstream APIs.
- Optional fields specify explicit, safe defaults rather than failing on `None` or missing keys.
- Breaking schema changes increment the major tool version (e.g. `workweek_submit_leave_v2`) and run in parallel with deprecated versions for a 60-day migration window.

## Consequences
- **Resilience**: Upstream API additions will never crash active conversational sessions.
- **Contract Stability**: MCP tool interfaces remain strictly versioned and predictable for the Vertex AI Agent Development Kit.
