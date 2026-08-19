# 03 — WorkWeek HCM MCP Server & Connector Tools

**What to build:** Dedicated Model Context Protocol (MCP) server exposing WorkWeek tools (profile lookup/update, PTO query, leave booking) with built-in temporal & balance guardrails, confirmation gates (ADR-0007), and signed JWT token verification (ADR-0001, ADR-0006).

**Blocked by:** 01 — Project Scaffold, Domain Models & Signed JWT Auth

**Status:** closed

- [x] WorkWeek MCP Server implementing tools: `workweek_get_profile`, `workweek_get_pto_balances`, `workweek_submit_leave_request` (`src/mcp/workweek_server.py`).
- [x] Enforces signed JWT origin verification and employee identity scope (`hcm:read`, `hcm:write`).
- [x] Rejects leave requests exceeding accrued balance or containing invalid chronological dates.
- [x] Implements atomic FileStore persistence and `Idempotency-Key` deduplication.
- [x] Unit & integration tests asserting full round-trip MCP tool execution against realistic stateful enterprise fixtures (`tests/integration/test_workweek_mcp.py`).
