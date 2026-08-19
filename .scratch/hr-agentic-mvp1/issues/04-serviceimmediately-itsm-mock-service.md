# 04 — ServiceImmediately ITSM MCP Server & Connector Tools

**What to build:** Dedicated Model Context Protocol (MCP) server exposing ServiceImmediately tools (incident lookup, ticket creation, timeline comments, lifecycle state transitions) with duplicate mitigation, automated P1 security alert creation, and interactive priority verification (ADR-0001, ADR-0010, SEC-0005).

**Blocked by:** 01 — Project Scaffold, Domain Models & Signed JWT Auth

**Status:** closed

- [x] ServiceImmediately MCP Server implementing tools: `itsm_get_ticket`, `itsm_create_incident`, `itsm_post_comment`, `itsm_update_status`, `itsm_create_security_incident` (`src/mcp/serviceimmediately_server.py`).
- [x] Enforces signed JWT origin verification and automation provenance claims (`itsm:read`, `itsm:write`, `itsm:security:write`).
- [x] Enforces valid state transitions (`OPEN` -> `IN_PROGRESS` -> `PENDING_CUSTOMER` -> `RESOLVED` -> `CLOSED`) and duplicate request mitigation with `Idempotency-Key`.
- [x] Interactive priority downgrade flow when Critical priority lacks major outage justification (ADR-0010).
- [x] Automated P1 security incident creation for CIRT team on adversarial attacks (SEC-0005).
- [x] Unit & integration tests asserting full round-trip MCP tool execution against realistic incident timelines (`tests/integration/test_serviceimmediately_mcp.py`).
