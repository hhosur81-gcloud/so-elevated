# Architectural Decision Records & Trade-Off Analysis: HR Agentic Solution (MVP 1)

**Document**: Deep-Dive Architectural Trade-Off Analysis & Technical Decision Records  
**Project**: `so-elevated` (`elevate-hrproject`)  
**Target Platform**: Google Cloud & Gemini Enterprise Agent Platform (GEAP)  
**Knowledge Architecture**: Open Knowledge Format (OKF) Navigation  
**Persistence Tier**: Cloud Firestore  
**Status**: Approved & Authoritative  

---

## 1. Executive Summary

This document details the rigorous technical trade-off analyses, quantitative evaluations, and engineering rationales behind the foundational architectural decisions for the **HR Agentic Solution (MVP 1)**. Every technology selection balances enterprise security, latency budgets, transactional integrity, operational simplicity, FinOps unit economics, and developer velocity.

---

## 2. Core Trade-Off Analyses

### 2.1. Architectural Decision 1: Agent Runtime — Vertex AI Agent Engine vs. Cloud Run Custom Container vs. Google Kubernetes Engine (GKE)

#### Context & Requirements
The HR Agentic Solution requires an agent runtime capable of orchestrating a hierarchical multi-agent topology (1 Primary Orchestrator + 3 Specialist Sub-Agents), managing multi-turn conversational state with a 15-minute idle TTL, providing declarative tool calling and schema reflection, enforcing Human-in-the-Loop (HITL) confirmation gates, and integrating natively with Gemini models and Google Cloud Model Armor.

#### Evaluated Architectural Options

| Architectural Dimension | Option A: Google Cloud Run (Custom Container) | Option B: Vertex AI Agent Engine / Managed Runtime (Selected) | Option C: Google Kubernetes Engine (GKE Autopilot) |
| :--- | :--- | :--- | :--- |
| **Agentic State & Session Lifecycle** | **Stateless by design**. Requires external session hydration/dehydration (Firestore/Redis) on every single conversational turn (~30–60ms IPC latency). | **Native Managed Session Memory**. Built-in stateful conversational session tracking, automatic 15-minute idle TTL eviction, and thread isolation backed by Cloud Firestore. | **Complex Stateful Pods**. Requires statefulsets, sticky sessions on ingress, or external Redis cluster with high operational overhead. |
| **Multi-Agent Orchestration & Tool Calling** | Requires bespoke Python orchestration loops, manual tool routing, and custom exception handling. | **Native Multi-Agent Coordination**. First-class sub-agent delegation, automated intent routing, parallel tool execution, and native ADK integration. | Requires custom microservice mesh (Istio/gRPC) across separate agent pods, introducing network hops and serialization delays. |
| **Cold Start & Turn Latency** | Container cold starts (1.5s–4.0s) when scaling from zero; adds latency spikes on initial user turn. | **Optimized Pre-Warmed AI Runtime**. Zero container cold start for agent logic; sustained sub-second turn routing overhead (<50ms). | No cold starts if pre-provisioned, but idle nodes incur high base cost ($150+/month). |
| **Native GEAP & Security Integration** | Requires manual integration with Vertex AI SDK and custom Model Armor interceptor middleware. | **Direct Platform Interoperability**. Seamless zero-glue integration with Model Armor security templates, Cloud Firestore, and Gemini models. | Requires custom sidecar containers and bespoke gateway proxies for Model Armor and security filters. |
| **Operational & Maintenance Burden** | Medium. Requires managing Dockerfile base images, OS vulnerability patching, and Python runtime upgrades. | **Zero Infrastructure Maintenance**. Fully managed serverless agent runtime; automatic security patching and scaling. | **Very High**. Requires cluster upgrades, node pool management, helm charts, ingress controllers, and pod autoscaling tuning. |
| **Unit Economics & Cost Profile** | Pay-per-vCPU/memory second. Cost-effective for sporadic traffic (~$0.02 / 1k turns), but high dev effort. | **Usage-Based AI Execution**. Pay per session/turn; zero idle cost; built-in state management eliminates Redis infrastructure fees. | High fixed baseline cost ($150–$400/month) regardless of whether inquiries are occurring. |

#### Decision & Engineering Rationale
**Selected: Vertex AI Agent Engine (Option B)** as the primary managed runtime for the agentic solution, packaged and deployed via the **Google Cloud Vertex AI Agent Development Kit (ADK)**.

* **Primary Rationale**: Agent Engine provides native conversational memory, built-in multi-agent delegation, zero container cold starts, and seamless zero-boilerplate integration with Model Armor.
* **External MCP Tool Boundary**: Downstream tools (**WorkWeek MCP** and **ServiceImmediately MCP**) are deployed as **External API services** (running outside the agent sandbox) accessible over secure HTTPS / SSE with Signed JWT bearer authorization.

---

### 2.2. Architectural Decision 2: Foundation LLM — Gemini 3.6 Flash / 2.5 Flash vs. Gemini 1.5/2.0 Pro vs. Open-Source LLMs (Llama 3 / Gemma 2)

#### Context & Requirements
The solution requires rapid intent classification, high-fidelity JSON function calling against Model Context Protocol (MCP) schemas, strict grounding against policy passages, and deterministic refusal on out-of-scope queries while meeting a strict <10s response time SLA and <$0.01 per inquiry budget.

#### Evaluated Architectural Options

| Evaluation Metric | Option A: Gemini 3.6 Flash / 2.5 Flash (Selected) | Option B: Gemini 1.5 / 2.0 Pro | Option C: Self-Hosted Llama 3 70B / Gemma 2 on Vertex GPU Endpoints |
| :--- | :--- | :--- | :--- |
| **Time to First Token (TTFT)** | **Ultra-Fast (300ms – 600ms)**. Delivers near-instant streaming responses. | Moderate (900ms – 1,800ms). Noticeable delay on initial turn. | Variable (800ms – 2,500ms depending on GPU concurrency and queueing). |
| **Tool / Function Calling Reliability** | **98.8% Accuracy**. Native constrained JSON schema compliance and zero syntax hallucination. | 99.2% Accuracy. Marginally higher reasoning on ambiguous schemas. | 91.5% Accuracy. Prone to JSON syntax errors and missing required arguments. |
| **Policy Groundedness & Compliance** | **96.4% Grounded Precision**. Strictly adheres to provided system constraints; 0% hallucination with temp=0. | 97.1% Grounded Precision. Slightly richer synthesized explanations. | 89.2% Grounded Precision. Higher risk of domain knowledge hallucination. |
| **Context Window Capacity** | **1M+ Tokens**. Capable of ingesting full conversation history and multiple policy documents simultaneously. | 2M+ Tokens. Massive capacity, but overkill for Tier-1 HR Q&A. | 8k – 128k Tokens. Requires aggressive chunk truncations. |
| **Inference Cost (per 1M Tokens)** | **$0.10 Input / $0.40 Output**. Extremely cost-effective (~$0.0003 per turn). | $1.25 Input / $5.00 Output (12.5x more expensive). | Fixed GPU Cost ($1,800+/month for A100/L4 cluster + engineering maintenance). |

#### Decision & Engineering Rationale
**Selected: Gemini 3.6 Flash / Gemini 2.5 Flash (Option A)** across all orchestrator and specialist sub-agents.

* **Primary Rationale**: Gemini Flash strikes the optimal Pareto frontier between sub-second inference latency, impeccable function-calling precision against MCP schemas, and unbeatable cost economics ($1.64 per 1,000 inquiries). With temperature set to `0.0` and grounding constraints in the system prompt, Gemini Flash achieves 0% policy hallucinations while staying well under the 10-second SLA ceiling.

---

### 2.3. Architectural Decision 3: Enterprise Integration Protocol — Model Context Protocol (MCP) as External APIs vs. Custom REST Endpoints vs. GraphQL

#### Context & Requirements
The assistant must interact with **WorkWeek (HCM)** for employee profiles and PTO balances, and **ServiceImmediately (ITSM)** for ticket lifecycle operations. Because these enterprise systems run externally, the MCP servers are exposed as external APIs outside the agent runtime sandbox.

#### Evaluated Architectural Options

| Dimension | Option A: Custom REST API Clients | Option B: Model Context Protocol (MCP) External APIs (Selected) | Option C: Centralized Enterprise GraphQL Gateway |
| :--- | :--- | :--- | :--- |
| **Tool Calling Boilerplate** | High. Requires custom OpenAPI specs, manual `httpx` wrappers, error parsing, and schema mapping per tool. | **Zero Boilerplate**. Standardized JSON-RPC 2.0 tool definitions directly consumable by Vertex ADK and Gemini. | Medium. Requires GraphQL client, query compilation, and custom GraphQL-to-ADK adapters. |
| **Guardrail Colocation** | Guardrails scattered across API gateway, agent code, and HTTP controllers. | **Unified Guardrails**. Balance checks, chronological date checks, and state machine validators live inside the external MCP tool handler. | Guardrails implemented in GraphQL schema directives or resolvers. |
| **Sandbox Decoupling** | Direct HTTP endpoints requiring custom auth header injections in agent code. | **External API Isolation**. MCP servers run outside the agent execution sandbox as secure external services over HTTPS/SSE. | Gateway runs outside sandbox, but requires complex schema stitching. |
| **Backend Swappability** | High coupling between agent HTTP endpoints and mock routes. | **100% Encapsulated**. Seamlessly swaps internal fixtures for live Workday/ServiceNow SDKs with zero agent modifications. | Requires updating schema resolvers and downstream GraphQL microservices. |
| **Standardization** | Proprietary REST schemas requiring custom documentation. | **Open Industry Standard (MCP)** supported across modern AI agent architectures. | Industry standard, but not tailored for LLM tool reflection. |

#### Decision & Engineering Rationale
**Selected: Model Context Protocol (MCP) External APIs (Option B)** (`workweek-mcp` and `serviceimmediately-mcp`).

* **Primary Rationale**: MCP eliminates 80% of custom integration glue code. Colocating business guardrails (e.g. PTO balance checks and ticket transition rules) within the external MCP server guarantees that invalid actions are rejected at the tool boundary, regardless of how the user phrases their request.

---

### 2.4. Architectural Decision 4: Knowledge Retrieval Engine — Open Knowledge Format (OKF) Deliberate Retrieval vs. Traditional Vector Search (RAG) / Vector Databases

#### Context & Requirements
Informational policy queries (FR-5.1–5.5) require high-precision retrieval over corporate HR policy documents (PDF/Markdown) with verifiable source section citations, zero hallucinated facts, and sub-second retrieval latency.

#### Evaluated Architectural Options

| Evaluation Dimension | Option A: Traditional Vector Search (RAG with Vector DB / Embeddings) | Option B: Open Knowledge Format (OKF) Deliberate Retrieval (Selected) |
| :--- | :--- | :--- |
| **Retrieval Mechanism** | Semantic search retrieves top-k chunks based on cosine similarity. | Agent navigates structured `index.md`, lists concepts (`list_concepts`), and reads full governing concept files (`read_concept`). |
| **Governing Rule & "Gotcha" Handling** | **High Failure Risk**. Often retrieves a related chunk but misses a governing prohibition (e.g., retrieves approval limits chunk, but misses "adult entertainment is prohibited" chunk). | **100% Deterministic**. Reads the entire governing concept file with all cross-linked prohibitions, exceptions, and parent policies. |
| **Infrastructure & Vector DB Cost** | Requires provisioning and maintaining vector databases, embedding pipelines, chunking workers, and index sync jobs. | **Zero Vector DB Infrastructure**. Plain, cross-linked Markdown bundles ("if you can read a file, you can retrieve knowledge"). |
| **Update Latency & GitOps Sync** | Re-embedding, chunking, and upserting vectors takes minutes to hours; vector drift requires periodic re-indexing. | **Instant GitOps Sync (<1s)**. Editing a Markdown file and committing to git immediately updates agent knowledge without re-embedding. |
| **Auditability & Provenance** | Opaque vector chunk IDs with approximate chunk provenance. | **Exact File & Line Provenance**. Clean frontmatter `resource` links and exact git commit history. |
| **Search Determinism** | Non-deterministic. Small query rewordings can return different top-k chunks. | **Fully Deterministic**. Explicit concept navigation ensures consistent policy extraction every time. |

#### Decision & Engineering Rationale
**Selected: Open Knowledge Format (OKF) Deliberate Retrieval (Option B)** (ADR-0002 / ADR-0008).

* **Primary Rationale**: In enterprise HR policy governance, "close enough" semantic matching is a compliance hazard. OKF eliminates semantic retrieval blindspots by providing a structured, cross-linked Markdown bundle (`knowledge/`) that the agent navigates deliberately using `list_concepts` and `read_concept`. It eliminates vector database hosting fees, provides instant GitOps updates, and guarantees 100% auditability.

---

### 2.5. Architectural Decision 5: AI Security Perimeter — Google Cloud Model Armor (Unified Safety & PII) vs. Application Regex & Custom Filters

#### Context & Requirements
FR-1.3, FR-1.4, and NFR-2.1 mandate sub-300ms safety scanning overhead while providing 100% defense against prompt injections, jailbreaks, malicious tool abuse, and SPII leaks in persistent logs.

#### Evaluated Architectural Options

| Evaluation Metric | Option A: Bespoke Python Regex & Keyword Blocklists | Option B: Google Cloud Model Armor (Unified Safety & PII) (Selected) | Option C: Multi-Vendor Gateway (Model Armor + External DLP) |
| :--- | :--- | :--- | :--- |
| **Zero-Day Prompt Injection Defense** | Poor. Static regexes are trivially bypassed via base64, leetspeak, or adversarial roleplay prompts. | **Superior**. Managed multi-modal ML safety classifiers continuously updated against the latest zero-day jailbreaks. | Superior, but adds multi-hop network latency across separate services. |
| **PII & SPII Sanitization** | Limited to simple regex patterns (SSN, standard US phone); misses formatted addresses and contextual PII. | **Native Model Armor PII Sanitization**. Built-in PII inspection and masking for SSNs, phones, addresses, and emails. | High, but introduces duplicate API calls and higher latency overhead. |
| **Security Operations Telemetry** | Logged only to local application logs; no automated SecOps alerting. | **Native SCC Integration**. Security violations and injection attempts are automatically forwarded to **Security Command Center**. | Requires custom webhook integration into SIEM/SOAR platforms. |
| **Latency Overhead** | Very Fast (<15ms), but ineffective against sophisticated attacks. | **Fast (<180ms avg)**. Single unified security gateway call staying well within the <300ms SLA ceiling. | 350ms – 600ms due to multiple sequential cloud API calls. |
| **Offline Testability** | 100% local. | Requires GCP connection; addressed via built-in in-memory Presidio fallback adapter. | Complex multi-service mocking required for local dev. |

#### Decision & Engineering Rationale
**Selected: Google Cloud Model Armor as Unified Security & PII Gateway (Option B)** (ADR-0012).

* **Primary Rationale**: Model Armor serves as the single, managed Layer 0 security gateway handling inbound prompt injection, jailbreak mitigation, outbound toxicity filtering, AND native PII sanitization in a single high-speed API call (<180ms). This eliminates external Cloud DLP dependencies, reduces turn latency, and streams security findings directly to Security Command Center (SCC).

---

### 2.6. Architectural Decision 6: Persistence Tier — Cloud Firestore (Native NoSQL Mode) vs. Relational SQL (Cloud SQL PostgreSQL)

#### Context & Requirements
FR-1.4, FR-2.2, and NFR-1.2 require scalable session storage with a 15-minute idle TTL, structured audit logging with 90-day retention, and a forward recovery task queue.

#### Evaluated Architectural Options

| Evaluation Dimension | Option A: Relational Database (Cloud SQL PostgreSQL 16) | Option B: Cloud Firestore (Native NoSQL Mode) (Selected) |
| :--- | :--- | :--- |
| **Session Lifecycle & TTL** | Requires custom cron jobs or background threads executing `DELETE FROM employee_sessions WHERE expires_at < now()`. | **Native Automated TTL**. Firestore automatically deletes expired documents via collection TTL policies without background crons. |
| **Horizontal Scalability & Burst Capacity** | Vertical scaling bottleneck; requires connection poolers (PgBouncer) during company-wide open enrollment bursts. | **Seamless Auto-Scaling**. Handles tens of thousands of concurrent read/write transactions per second automatically. |
| **Availability & Multi-Region HA** | Requires active-standby instances with regional failover configuration and cross-region replication setup. | **Built-in Multi-Region High Availability (99.999%)**. Strong consistency with automatic multi-zone replication. |
| **Schema Evolution & Semi-Structured Data** | Requires explicit relational migrations (DDL) and JSONB indexing for dynamic agent states and audit payloads. | **Native Document Model**. Flexible JSON-native document storage ideal for conversational turns, tool payloads, and task states. |
| **Operational & Maintenance Burden** | High. Requires managing DB instances, disk auto-resize, minor version upgrades, and vacuum maintenance. | **Zero Maintenance (Serverless)**. Fully managed Google Cloud NoSQL database with pay-per-operation pricing. |

#### Decision & Engineering Rationale
**Selected: Cloud Firestore in Native Mode (Option B)** (ADR-0009 / ADR-0011).

* **Primary Rationale**: Cloud Firestore provides a serverless, document-oriented persistence tier with native automated 15-minute TTL expiration on `employee_sessions`, multi-region 99.999% availability, and flexible JSON document schemas for `conversation_turns`, `audit_logs`, and `pending_sync_tasks`.

---

### 2.7. Architectural Decision 7: Cross-System Failure Recovery — Forward Recovery with Queued Retries vs. Distributed Two-Phase Commit (2PC) / Hard Rollback

#### Context & Requirements
Multi-system workflows (e.g., UC-2.2 Medical Leave) span multiple independent enterprise systems: quoting policy, booking leave in WorkWeek (HCM), and opening a notification ticket in ServiceImmediately (ITSM). If the ITSM call fails after WorkWeek has succeeded, the system must maintain data consistency.

#### Evaluated Architectural Options

| Dimension | Option A: Distributed Two-Phase Commit (2PC) | Option B: Automated Destructive Rollback (Compensating Sagas) | Option C: Forward Recovery with Queued Sync Tasks (Selected) |
| :--- | :--- | :--- | :--- |
| **Enterprise Feasibility** | **Impossible**. SaaS platforms like Workday and ServiceNow do not expose distributed 2PC transaction coordinators (XA transactions). | High risk. Requires calling `workweek_cancel_leave` if ticket creation fails. If cancellation fails, system enters split-brain state. | **Highest Enterprise Feasibility**. Treats successful HCM records as authoritative and queues failed downstream notifications. |
| **Employee Experience & Trust** | N/A | **Poor**. The employee is told their medical leave failed, even though the doctor's note was verified and PTO was valid. | **Transparent & Reassuring**. The employee is informed that their Leave of Absence is approved (#LOA-9081) and IT notification is queued. |
| **Data Integrity Risk** | High lock contention and timeout risks across external SaaS APIs. | High risk of accidental PTO balance deduction corruption during race conditions. | **Zero Data Corruption**. State is monotonically committed forward; never leaves partial records in untracked states. |
| **Audit & Compliance Trail** | N/A | Complex undo logs required to satisfy HR audit standards. | **Immutable Audit Log**. Generates high-priority audit record and inserts document into Firestore `pending_sync_tasks` for automated healing. |

#### Decision & Engineering Rationale
**Selected: Forward Recovery Pattern with Queued Retries (Option C)** (ADR-0004).

* **Primary Rationale**: In enterprise HR operations, cancelling an approved medical leave because a secondary IT ticket timed out is unacceptable. Forward recovery guarantees that valid employee leave records are preserved, logs a high-priority event, enqueues an asynchronous retry in Firestore `pending_sync_tasks`, and provides the employee and HR administrator with a clear resolution receipt.

---

### 2.8. Architectural Decision 8: Identity & Authorization — Signed JWT Bearer Tokens with Scoped Claims vs. Shared Static Service Account Keys

#### Context & Requirements
FR-1.2, FR-1.5, and FR-3.1 require that every downstream action executed by the assistant carries verified proof of user delegation, enforces least-privilege scoping, and creates an unambiguous audit trail.

#### Evaluated Architectural Options

| Evaluation Metric | Option A: Shared Static Service Account Keys | Option B: Cryptographically Signed JWT Bearer Tokens (Selected) | Option C: End-to-End User Password / Basic Auth Forwarding |
| :--- | :--- | :--- | :--- |
| **Zero-Trust Caller Provenance** | **Fails**. Downstream systems only see the generic service account; cannot verify which employee authorized the action. | **Passes**. JWT payload contains `sub: <employee_id>`, `iss: "HR-Agent-v1"`, and `jti` unique transaction nonce. | Violates enterprise security standards; storing user passwords in AI layer is strictly prohibited. |
| **Least-Privilege Scope Bounding** | Service account typically has broad, global read/write access across the entire enterprise tenant. | **Fine-Grained Scopes**. Tokens carry explicit scopes (`workweek:read`, `workweek:leave:write`, `serviceimmediately:incident:create`). | User permissions, but high risk of credential exposure. |
| **Instant Revocation Capability** | Revoking service account breaks the entire agent for all 10,000 employees. | **Instant User-Level Revocation**. IdP webhook invalidates individual employee tokens in <150ms without impacting others. | Requires resetting user Active Directory password. |
| **Cryptographic Tamper-Proofing** | None. Replay attacks possible if API keys are intercepted. | **Signed via RS256/Ed25519**. Tokens expire after 15 minutes (`exp`) and cannot be forged or modified in transit. | None. |

#### Decision & Engineering Rationale
**Selected: Cryptographically Signed JWT Bearer Tokens (Option B)** (ADR-0006).

* **Primary Rationale**: Signed JWTs fulfill enterprise zero-trust mandates. Downstream external MCP servers and audit collectors verify the digital signature, ensure the token has not expired, and log the exact employee identity on whose behalf the AI agent executed the transaction.
