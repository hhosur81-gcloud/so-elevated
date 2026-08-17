# 01 — Project Scaffold, Domain Models & Signed JWT Auth

**What to build:** Common domain models (Employee Profile, PTO Balances, Leave Request, Incident Record, Policy Chunk) and the cryptographic Signed JWT token generator/validator for origin verification.

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] Pydantic domain schemas for WorkWeek (Employee, PTOBalance, LeaveRequest) and ServiceImmediately (IncidentTicket, Comment, StateEnum, PriorityEnum).
- [ ] Signed JWT utility generating and validating bearer tokens with claims (sub: employee_id, iss: HR-Agent-v1, scopes: list).
- [ ] Unit tests verifying serialization, field validation errors, and token signature verification.
