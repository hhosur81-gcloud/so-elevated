# 03 — WorkWeek HCM FastAPI Mock Service & Connector Tools

**What to build:** Employee self-service in WorkWeek: profile query/update, PTO balance query, and leave request submission with confirmation gate (ADR-0007), temporal, and balance guardrails over FastAPI REST endpoints.

**Blocked by:** 01 — Project Scaffold, Domain Models & Signed JWT Auth

**Status:** ready-for-agent

- [ ] FastAPI mock endpoints: /api/v1/employees/{id}, /api/v1/employees/{id}/pto, and /api/v1/leave/requests.
- [ ] Validates incoming Bearer <signed_jwt> token and enforces employee identity scope.
- [ ] Rejects leave requests exceeding accrued balance or containing invalid chronological dates.
- [ ] Integrates confirmation gate before executing leave bookings and contact updates.
- [ ] Integration tests demonstrating round-trip profile updates and PTO leave bookings.
