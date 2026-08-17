# 04 — ServiceImmediately ITSM FastAPI Mock Service & Connector Tools

**What to build:** Incident ticket management in ServiceImmediately: ticket lookup, incident creation (1-Critical to 4-Low), interactive priority verification (ADR-0010), comment appending, and lifecycle transition enforcement.

**Blocked by:** 01 — Project Scaffold, Domain Models & Signed JWT Auth

**Status:** ready-for-agent

- [ ] FastAPI mock endpoints: /api/now/table/incident and /api/now/table/incident/{id}.
- [ ] Validates incoming Bearer <signed_jwt> origin token.
- [ ] Enforces valid state transitions (New -> In Progress -> Resolved -> Closed) and duplicate request mitigation.
- [ ] Interactive priority downgrade flow when Critical priority lacks major outage justification.
- [ ] Integration tests verifying ticket creation, timeline updates, and invalid transition rejections.
