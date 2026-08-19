# Feature Spec: HR Agentic Solution (MVP 1)

Status: ready-for-agent

## Problem Statement

Enterprise employees currently face fragmented, high-friction access to HR services across disparate systems. Answering simple policy questions (e.g. bereavement leave, expense eligibility) requires navigating static intranet portals or opening helpdesk tickets that create heavy Tier-1 support overhead. Routine self-service actions like querying PTO balances, submitting leave requests, and filing IT or facilities support incidents require manually logging into separate, complex user interfaces (WorkWeek HCM, ServiceImmediately ITSM). Furthermore, cross-domain workflows (such as requesting remote work equipment or applying for medical leave of absence) require manual coordination across policy documents, HR systems, and IT ticketing desks with zero unified visibility.

## Solution

The HR Agentic Solution is an AI-driven, multi-turn virtual assistant built on the Google Cloud Vertex AI Agent Development Kit (ADK) that unifies enterprise HR interactions into a single conversational surface.

![HR Agentic Solution Architecture](file:///usr/local/google/home/harshahosur/Documents/elevate-hrproject/docs/assets/hr_agent_architecture.jpg)

The system:
1. Integrates with **repository-resident Open Knowledge Format (OKF)** policy files (`knowledge/`) to perform semantic document retrieval over approved corporate HR policy documents, returning strictly grounded answers with deep-link metadata citations.
2. Connects to **WorkWeek (HCM)** via signed JWT delegated authorization to perform real-time profile lookup, PTO balance queries, and guarded leave of absence submissions with an explicit **Human Confirmation Gate** on state mutations.
3. Connects to **ServiceImmediately (ITSM/HRSD)** to manage incident tickets, query status/timeline history, enforce valid lifecycle transitions, and handle interactive priority elevation verification.
4. Orchestrates complex **Cross-System Workflows** (Equipment Procurement, Medical Leave, Relocation) across policy checks, HCM transactions, and ITSM ticketing with automated forward-recovery audit tracking.
5. Employs **Google Cloud Model Armor** (ADR-0012) as the managed Layer 0 Security Gateway executing prompt sanitization, jailbreak defense, and Cloud Sensitive Data Protection (DLP) SPII redaction with **Tiered Visibility** (local Presidio/Regex fallback for offline tests) (raw viewing in user response stream, strict masking in persistent logs and audit traces) and targeted LLM-as-a-judge prompt injection guardrails.
6. Enforces **Session Lifecycle & TTL Management** (explicit reset prompts and 15-minute idle purge) to guarantee zero cross-user memory leakage.

## User Stories

1. As an employee, I want to ask questions about company bereavement leave in natural language, so that I receive an immediate, strictly grounded answer quoting official policy.
2. As an employee, I want to ask if noise-canceling headphones are an expensable item, so that I get a direct policy answer with a clickable citation to the expense guidelines document.
3. As an employee, I want to ask about remote work eligibility, so that I can understand the equipment allowance and requirements before ordering home office monitors.
4. As an employee, I want policy citations to include clickable deep links, so that I can independently verify the source section in the official policy document repository.
5. As an employee, I want the assistant to clearly state when a topic is not covered in company policy, so that I am not misled by hallucinated rules.
6. As an employee, I want to query my current accrued and remaining PTO vacation balance, so that I know how much time off I have available.
7. As an employee, I want to query my sick leave balance, so that I know my remaining sick days without logging into the WorkWeek portal.
8. As an employee, I want to submit a vacation leave request conversationally, and have the agent ask for explicit confirmation before booking, so that I can verify calculated days and dates before committing.
9. As an employee, I want the system to reject leave requests that exceed my accrued PTO balance, so that I do not submit invalid time-off bookings.
10. As an employee, I want the system to validate chronological date consistency on leave requests, so that past dates or inverted start/end dates are blocked before submission.
11. As an employee, I want to view my profile details (department, role, manager, hire date, home address, phone), so that I can verify my employee record on-screen.
12. As an employee, I want to update my personal home address and phone number conversationally with an explicit confirmation step, so that my contact details in WorkWeek stay accurate without accidental changes.
13. As an employee, I want input syntax validation on phone numbers and email formats, so that invalid contact updates are caught immediately.
14. As an employee, I want dynamic profile and PTO data to be fetched in real time on every query, so that I always see the latest state without stale AI caching.
15. As an employee, I want to query the status and priority of an existing ServiceImmediately ticket (e.g. INC123456), so that I can track resolution progress.
16. As an employee, I want to read the chronological comment history on my support tickets, so that I know what updates the support engineering team has made.
17. As an employee, I want to create a new support incident ticket with a category, description, and priority level (1-Critical to 4-Low), so that my technical or HR issues are routed for resolution.
18. As an employee, if I request a Critical priority ticket for a low-impact issue, I want an interactive explanation and option to downgrade or justify, so that I understand ticket priority standards.
19. As an employee, I want to append update comments and notes to my existing open incident tickets conversationally without extra confirmation prompts, so that I can quickly provide additional troubleshooting information.
20. As an employee, I want to mark an incident ticket as resolved with an explicit confirmation prompt, so that tickets are not accidentally closed.
21. As a support team lead, I want ticket state updates to follow valid lifecycle constraints, so that tickets cannot jump directly from New to Closed without proper resolution.
22. As a support team lead, I want duplicate ticket detection on rapid successive submissions, so that the service desk is not spammed with identical incident requests.
23. As an employee, I want to trigger a single conversational workflow for home office equipment procurement (UC-2.1), so that the agent verifies policy eligibility, checks my remote work status in WorkWeek, and files the equipment request in ServiceImmediately automatically.
24. As an employee, I want to initiate a short-term medical leave workflow (UC-2.2), so that the agent quotes the policy procedure, asks for confirmation, books the leave in WorkWeek, and opens an IT ticket in ServiceImmediately to route email access to my manager.
25. As an employee, I want to execute a London office transfer workflow (UC-2.3), so that the agent calculates my relocation allowance from policy docs, prompts address updates in WorkWeek, and opens a facilities badge ticket in ServiceImmediately.
26. As a compliance officer, I want downstream service requests to WorkWeek and ServiceImmediately to carry a signed JWT origin token, so that automated actions are cryptographically distinguished from direct manual human inputs.
27. As a compliance officer, I want all Sensitive Personally Identifiable Information (SPII) like home addresses and phone numbers redacted from persistent audit logs and traces while allowing unmasked self-viewing in the active UI stream, so that privacy is strictly maintained without degrading user experience.
28. As a security architect, I want incoming prompts screened for prompt injection, jailbreaks, and off-topic bypasses, so that the agent cannot be tricked into unauthorized actions.
29. As a security architect, I want outgoing responses validated against toxicity, hallucinations, and data leakage, so that sensitive corporate information is never exposed.
30. As an enterprise operator, I want safety scanning overhead to remain under 300ms, so that conversational responsiveness remains fast and interactive.
31. As an enterprise operator, I want cross-system workflow failures (e.g. WorkWeek success followed by ServiceImmediately failure) to execute forward recovery with high-priority audit alerts and manual follow-up guidance, so that partial transactions never corrupt enterprise state.
32. As an employee, I want to say "reset conversation" or "clear session" to immediately purge session state, so that my conversational context is wiped when I am done.
33. As an enterprise security admin, I want active sessions to automatically expire after 15 minutes of inactivity, so that unattended terminals do not leak session context.
34. As a QA engineer, I want all policy retrieval tests to execute strictly against canonical repository-resident Open Knowledge Format (OKF) policy files (`knowledge/`), so that tests validate authentic production retrieval behavior.
35. As a developer, I want all mock services and agents to run with zero external mock leaks and full end-to-end type safety, so that the solution is robust and maintainable.
36. As a security engineer, I want the agent to sign delegated JWTs using asymmetric Cloud KMS (ECDSA P-256) with dynamic JWKS discovery (SEC-0001).
37. As a CISO, I want all agent, vector search, and MCP operations restricted to an enforced VPC Service Controls perimeter (SEC-0002).
38. As a compliance officer, I want all vector indexes, policy files, and database partitions encrypted with Cloud KMS Customer Managed Encryption Keys (CMEK) (SEC-0003).
39. As an enterprise operator, I want automated dual-region active-passive failover between us-central1 and us-east4 with RTO < 60s (SEC-0004).
40. As a SOC analyst, I want high-severity prompt injection and data harvesting attacks streamed to Security Command Center (SCC) with automated Priority 1 security incidents generated in ServiceImmediately (SEC-0005).
41. As a DevOps engineer, I want W3C traceparent context propagated across all agent hops and spans exported to Cloud Trace (SEC-0006).
42. As a backend developer, I want domain schemas to use Pydantic Tolerant Reader patterns with SemVer 2.0.0 (ENG-0001).
43. As a platform engineer, I want partial cross-system failure sync tasks queued to Cloud Tasks with Idempotency-Key headers and a 5-retry Dead Letter Queue (DLQ) (ENG-0002).
44. As a database administrator, I want database schema migrations executed via Alembic using the Expand-and-Contract pattern (ENG-0004).
45. As an enterprise architect, I want a Redis vector semantic cache (<50ms) for high-frequency static policy queries, paired with an automated 4-tier model fallback cascade from Gemini 3.7 to 3.6 to 3.0 to 2.5 Flash (ENG-0005).
46. As a Site Reliability Engineer (SRE), I want an automated Cloud Scheduler canary probe executing end-to-end synthetic dialogs every 5 minutes against EMP-CANARY-01 (ENG-0006).

## Implementation Decisions

### Module Architecture & Seams
1. **Core Agent Orchestrator (Vertex AI ADK)**:
   - Built on the Google Cloud Vertex AI Agent Development Kit (ADK) interfacing with Gemini models.
   - Implements Session Lifecycle & TTL Manager (ADR-0009): Dual-trigger session purge on explicit prompts or 15-minute idle TTL.
   - Enforces Human Confirmation Gate (ADR-0007): Intercepts state-changing write operations to require explicit confirmation before execution.
   - Dispatches declarative tool declarations for WorkWeek, ServiceImmediately, and Repository-Resident Open Knowledge Format (OKF) Bundle (`knowledge/`).

2. **Policy Knowledge Retrieval Engine (Open Knowledge Format - OKF Bundle)**:
   - Connects directly to repository-resident Open Knowledge Format (OKF) Markdown files (`knowledge/`) holding approved corporate HR policy documents with structured YAML frontmatter (ADR-0002, ADR-0008).
   - Enforces strict grounding with structured citation metadata (document name, section header, source URL/Deep Link).
   - Rejects out-of-domain queries and issues explicit "not found in company policy" fallbacks when context is missing.

3. **Enterprise Backend Connectors (Model Context Protocol / MCP Servers - ADR-0001)**:
   - **WorkWeek MCP Server**: Exposes MCP tools (`workweek_get_profile`, `workweek_get_pto_balances`, `workweek_submit_leave_request`). Enforces real-time balance checks, temporal date validity, and contact validation over realistic stateful enterprise fixtures.
   - **ServiceImmediately MCP Server**: Exposes MCP tools (`itsm_get_ticket`, `itsm_create_incident`, `itsm_post_comment`, `itsm_update_status`). Enforces lifecycle state transitions, duplicate request mitigation, and interactive priority verification (ADR-0010).
   - **Origin Authentication Middleware**: Every MCP tool call validates a signed JWT bearer token containing `sub` (employee ID), `iss` (`HR-Agent-v1`), and explicit operation scopes (ADR-0006).

4. **Security Sentinel Gateway (Google Cloud Model Armor & Tiered SPII - ADR-0011 & ADR-0012)**:
   - **Managed Gateway**: Routes ingress prompts and egress responses through Google Cloud Model Armor templates for injection defense, jailbreak mitigation, and Cloud DLP SPII redaction.
   - **Tiered Visibility (ADR-0011)**: Permits unmasked ephemeral UI rendering for self-viewing while strictly masking persistent disk logs, stdout, and audit traces.
   - **Offline Local Fallback**: Seamless in-memory Presidio/Regex interceptor (<20ms) for local unit testing.

5. **Cross-System Workflow Handlers (Forward Recovery)**:
   - Encapsulates multi-system orchestration for UC-2.1 (Equipment), UC-2.2 (Medical Leave), and UC-2.3 (Relocation).
   - Implements forward recovery logic (ADR-0004): On step failure, commits an audit log entry, flags a pending sync task, and returns clear manual remediation instructions to the user.

## Requirements Traceability Matrix

| BRD Requirement ID | Requirement Name | Spec Module & Mechanism | Testing & Verification |
| :--- | :--- | :--- | :--- |
| **FR-1.1** | Capability & Lifecycle Governance | Tool registration bounding in Vertex ADK | Tool invocation boundary test suite |
| **FR-1.2** | Verification of Request Origin | Signed JWT bearer tokens (`sub`, `iss`, `scopes`) | Provenance header inspection on mock server |
| **FR-1.3** | Conversation Safety | Google Cloud Model Armor Ingress/Egress Gateway (ADR-0012) | Negative red-team injection & toxicity test suite |
| **FR-1.4** | Data Masking / Redaction | Cloud DLP / Presidio Tiered SPII redaction (ADR-0011 & ADR-0012) | Automated SPII log masking test (phone, address, SSN) |
| **FR-1.5** | RBAC & Data Isolation | Scoped delegated auth tokens per employee ID + 15m TTL | Multi-user cross-access isolation test suite |
| **FR-2.1** | Natural Language Understanding | Vertex AI ADK with Gemini model intent parser | Typo and synonym tolerance benchmark |
| **FR-2.2** | Multi-Turn Dialog | Isolated stateful session manager with TTL (ADR-0009) | Context retention & memory leak tests |
| **FR-3.1–3.4** | WorkWeek Integration | WorkWeek MCP Server + Confirmation Gate (ADR-0001 & ADR-0007) | Balance constraint, date validity & confirmation tests |
| **FR-4.1–4.3** | ServiceImmediately Integration | ServiceImmediately MCP Server + Priority Guard (ADR-0001 & ADR-0010) | State transition, duplicate detection & priority tests |
| **FR-5.1–5.5** | Policy Document Q&A | Repository-Managed Open Knowledge Format (OKF) bundle (`knowledge/`) with metadata citations (ADR-0002, ADR-0008) | Grounding precision benchmark (≥95% accuracy, 0% hallucination) |
| **UC-2.1–2.3** | Cross-System Orchestration | Cross-System Flow Engine with Forward Recovery (ADR-0004) | End-to-end workflow execution & failure recovery tests |

## Testing Decisions

### What Makes a Good Test
- Tests must strictly evaluate **external conversational and API behavior**, never private internal class variables or transient mock states.
- Tests will drive end-to-end user scenarios through the top-level Agent interface and verify both returned responses and downstream mock server state.

### Modules Tested
1. **Security Interceptor Test Suite**: Negative security testing with known prompt injections, jailbreaks, SPII log leak verification, and off-topic queries.
2. **Policy Grounding Test Suite (OKF Bundle Validation)**: Evaluation against canonical Open Knowledge Format (OKF) policy bundles verifying &ge;95% accuracy, 0% hallucinations, and valid deep-link citation formatting.
3. **WorkWeek Integration Test Suite**: Profile queries, PTO queries, confirmation gate on leave submissions, and edge cases (exceeded PTO balance, past date rejection).
4. **ServiceImmediately Integration Test Suite**: Ticket creation, interactive priority downgrade flow, status transitions, and illegal state jump rejections.
5. **Session Lifecycle Test Suite**: Multi-turn context preservation, explicit reset prompts, and 15-minute idle timeout eviction.
6. **Cross-System Orchestration Suite**: End-to-end execution of UC-2.1, UC-2.2, and UC-2.3 with human confirmation turns, plus simulated partial failure testing forward recovery.

## Out of Scope

- Multi-language translation and localization.
- Direct integration with enterprise Active Directory / Okta SSO (functional test credentials used for MVP 1).
- Multi-tenancy architecture.
- Voice conversational channels.
- Processing of payroll calculation, salary adjustments, or formal performance reviews.

## Further Notes

- Architectural decisions are formally documented in `docs/adr/0001-mcp-enterprise-servers.md` through `docs/adr/0012-google-cloud-model-armor.md`.
- Multi-agent roles and scopes are detailed in `docs/multi_agent_architecture.md`.
- Domain glossary is maintained in `CONTEXT.md`.
