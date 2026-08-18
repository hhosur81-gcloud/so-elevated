# 04 — ServiceImmediately ITSM MCP Server & Connector Tools

**What to build:** Dedicated Model Context Protocol (MCP) server exposing ServiceImmediately tools (incident lookup, ticket creation, timeline comments, lifecycle state transitions) with duplicate mitigation and interactive priority verification (ADR-0001, ADR-0010).

**Blocked by:** 01 — Project Scaffold, Domain Models & Signed JWT Auth

**Status:** ready-for-agent

- [ ] ServiceImmediately MCP Server implementing tools: `itsm_get_ticket`, `itsm_create_incident`, `itsm_post_comment`, `itsm_update_status`.
- [ ] Enforces signed JWT origin verification and automation provenance claims.
- [ ] Enforces valid state transitions (`New` -> `In Progress` -> `Resolved` -> `Closed`) and duplicate request mitigation.
- [ ] Interactive priority downgrade flow when Critical priority lacks major outage justification (ADR-0010).
- [ ] Unit & integration tests asserting full round-trip MCP tool execution against realistic incident timelines.
