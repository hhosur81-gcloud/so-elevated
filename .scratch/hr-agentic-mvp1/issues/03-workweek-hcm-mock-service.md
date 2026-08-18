# 03 — WorkWeek HCM MCP Server & Connector Tools

**What to build:** Dedicated Model Context Protocol (MCP) server exposing WorkWeek tools (profile lookup/update, PTO query, leave booking) with built-in temporal & balance guardrails, confirmation gates (ADR-0007), and signed JWT token verification (ADR-0001, ADR-0006).

**Blocked by:** 01 — Project Scaffold, Domain Models & Signed JWT Auth

**Status:** ready-for-agent

- [ ] WorkWeek MCP Server implementing tools: `workweek_get_profile`, `workweek_update_contact`, `workweek_get_pto_balances`, `workweek_submit_leave_request`.
- [ ] Enforces signed JWT origin verification and employee identity scope.
- [ ] Rejects leave requests exceeding accrued balance or containing invalid chronological dates.
- [ ] Integrates confirmation gate before committing state mutations (leave bookings, contact updates).
- [ ] Unit & integration tests asserting full round-trip MCP tool execution against realistic stateful enterprise fixtures.
