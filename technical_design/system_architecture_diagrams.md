# System Architecture Diagrams & Visual Topology Catalog

**Document**: Visual Technical Architecture & Sequence Specifications  
**Project**: `so-elevated` (`elevate-hrproject`)  
**Target Platform**: Google Cloud & Gemini Enterprise Agent Platform (GEAP)  
**Status**: Approved & Authoritative  

---

## 1. Catalog of Architecture Diagrams

This catalog contains all 13 visual architectural diagrams, network topologies, entity-relationship models, and sequence flows governing the **HR Agentic Solution (MVP 1)**.

1. **Figure 1**: End-to-End System & Enterprise Network Architecture Topology
2. **Figure 2**: Hierarchical Multi-Agent Orchestration & Dispatcher Runtime
3. **Figure 3**: Low-Level Component & Service Interaction Diagram
4. **Figure 4**: Sequence Diagram — Cross-System Medical Leave Orchestration (UC-2.2) with HITL Gate & Forward Recovery
5. **Figure 5**: Sequence Diagram — Grounded Policy Q&A with Live Vertex AI Search & Deep-Link Citations (UC-1.1)
6. **Figure 6**: Sequence Diagram — WorkWeek HCM PTO Inquiry & Guarded Vacation Booking (UC-1.2)
7. **Figure 7**: Sequence Diagram — ServiceImmediately Incident Lifecycle & Interactive Priority 1 Downgrade (UC-1.3)
8. **Figure 8**: Sequence Diagram — Event-Driven Real-Time Policy Sync Pipeline (Eventarc + Cloud Run)
9. **Figure 9**: Sequence Diagram — Identity Authentication, OAuth OBO Exchange & Webhook Revocation
10. **Figure 10**: Low-Level Database Entity-Relationship Diagram (ERD) & Data Flow
11. **Figure 11**: Layer 0 Security Sentinel Gateway & Cloud DLP Tiered Redaction Pipeline
12. **Figure 12**: CI/CD Deployment Pipeline & Automated `agents-cli` Evaluation Gate
13. **Figure 13**: Subsystem Failure Modes, Circuit Breakers & Forward Recovery State Machine

---

## 2. Visual Architecture Diagrams

### Figure 1: End-to-End System & Enterprise Network Architecture Topology

```mermaid
flowchart TB
    subgraph EnterprisePerimeter["1. Enterprise Edge & User Ingress"]
        UserClient["Employee Workstation / Mobile Client<br>(Web Chat UI / Corporate Portal)"]
        CloudArmor["Google Cloud Armor (WAF)<br>• DDoS Protection<br>• IP Rate Limiting (100 RPS)"]
        CloudLB["Cloud Load Balancing (Internal HTTPS LB)<br>• TLS 1.3 Termination<br>• Health Check Probes"]
        
        UserClient -->|"HTTPS / TLS 1.3"| CloudArmor
        CloudArmor --> CloudLB
    end

    subgraph SecurityPerimeter["2. Managed AI Security Gateway (Layer 0)"]
        ModelArmor["Google Cloud Model Armor Gateway<br>• Inbound Prompt Injection Filter (BLOCK)<br>• Zero-Day Jailbreak Defense<br>• Outbound Toxicity & Data Leakage Guard"]
        DLPFilter["Cloud Sensitive Data Protection (DLP)<br>• InfoType Redaction (SSN, Phone, Address)<br>• Tiered Log Redaction"]
        LocalPresidio["In-Memory Presidio / Regex Fallback<br>(Offline Unit Tests & Local Dev)"]
        
        CloudLB --> ModelArmor
        ModelArmor <--> DLPFilter
        ModelArmor -.->|Offline Fallback| LocalPresidio
    end

    subgraph AgentRuntime["3. Gemini Enterprise Agent Platform (GEAP)"]
        AgentEngine["Vertex AI Agent Engine (Managed Runtime)<br>• Session Management (15m Idle TTL)<br>• Intent Dispatcher & Routing<br>• HITL Confirmation Gate<br>• Forward Recovery Engine"]
        
        PrimaryOrch["Primary HR Orchestrator (Vertex ADK)<br>(Gemini 3.6 Flash / 2.5 Flash)"]
        
        subgraph DomainSpecialists["Domain Specialist Sub-Agents"]
            PolicySpecialist["Policy Q&A Specialist<br>(Gemini 3.6 Flash)"]
            WorkWeekSpecialist["WorkWeek HCM Specialist<br>(Gemini 3.6 Flash)"]
            ITSMSpecialist["ServiceImmediately Specialist<br>(Gemini 3.6 Flash)"]
        end
        
        ModelArmor --> AgentEngine
        AgentEngine --> PrimaryOrch
        PrimaryOrch --> PolicySpecialist
        PrimaryOrch --> WorkWeekSpecialist
        PrimaryOrch --> ITSMSpecialist
    end

    subgraph KnowledgeAndIntegration["4. Knowledge & Integration Layer"]
        VertexSearch["Google Cloud Vertex AI Search<br>(Discovery Engine)<br>• Unstructured Policy Datastore<br>• Extractive QA Snippets<br>• Query-Time Metadata ACL Filters"]
        
        WW_MCP["WorkWeek HCM MCP Server<br>(Model Context Protocol over stdio/SSE)<br>• Leave & PTO Guardrails<br>• Seeded Stateful Enterprise Fixtures<br>• Signed JWT Validator"]
        
        SI_MCP["ServiceImmediately ITSM MCP Server<br>(Model Context Protocol over stdio/SSE)<br>• State Machine Guardrails<br>• Interactive P1 Downgrade<br>• Signed JWT Validator"]
        
        PolicySpecialist -->|"Search Query + ACL Filter"| VertexSearch
        WorkWeekSpecialist -->|"JSON-RPC 2.0 + Scoped JWT"| WW_MCP
        ITSMSpecialist -->|"JSON-RPC 2.0 + Scoped JWT"| SI_MCP
    end

    subgraph PersistenceAndAuditing["5. Persistence, Ingestion & Audit Tier"]
        CloudSQL[("Cloud SQL PostgreSQL (HA)<br>• employee_sessions (15m TTL)<br>• audit_logs (Partitioned, 90d)<br>• pending_sync_tasks (Forward Recovery)")]
        
        ColdlineGCS["Cloud Storage (Coldline)<br>• Immutable Audit Archives (GDPR)"]
        
        SCC["Security Command Center (SCC)<br>• High-Priority Security Telemetry"]
        
        AgentEngine --> CloudSQL
        CloudSQL -->|"90-Day Partition Detach"| ColdlineGCS
        ModelArmor -->|"Security Finding Event"| SCC
    end
```

---

### Figure 2: Hierarchical Multi-Agent Orchestration & Dispatcher Runtime

```mermaid
flowchart TD
    InboundPrompt["Inbound Clean Prompt<br>(from Model Armor Gateway)"] --> Dispatcher{"Intent Classifier & Dispatcher<br>(Primary HR Orchestrator)"}
    
    Dispatcher -->|"Policy Inquiries<br>(Leave rules, Expenses, Remote work)"| RoutePolicy["Route to Policy Q&A Specialist"]
    Dispatcher -->|"HCM Actions<br>(Profile, PTO balance, Leave booking)"| RouteWW["Route to WorkWeek HCM Specialist"]
    Dispatcher -->|"ITSM Actions<br>(Ticket status, Incidents, Comments)"| RouteSI["Route to ServiceImmediately Specialist"]
    Dispatcher -->|"Cross-System Workflows<br>(UC-2.1 Equipment, UC-2.2 Medical, UC-2.3 Relocation)"| RouteWorkflow["Execute Cross-System Workflow Engine"]
    
    subgraph ExecutionPolicies["Orchestrator Execution Policies"]
        HITLGate{"Is Operation State-Changing?<br>(Leave booking, address update, ticket close)"}
        HITLGate -->|Yes| PromptHITL["Pause Execution & Prompt User for Confirmation<br>(ADR-0007)"]
        HITLGate -->|No (Read-Only / Comment)| ExecuteDirect["Execute Directly via Sub-Agent"]
        
        PromptHITL --> WaitUser{"User Confirmed?"}
        WaitUser -->|Yes| CommitMutation["Commit Mutation via Scoped Tool Call"]
        WaitUser -->|No / Cancel| AbortMutation["Abort Action & Confirm Cancellation"]
    end
    
    RouteWW --> HITLGate
    RouteSI --> HITLGate
    RouteWorkflow --> HITLGate
    RoutePolicy --> ExecuteDirect
```

---

### Figure 3: Low-Level Component & Service Interaction Diagram

```mermaid
flowchart LR
    subgraph ClientLayer["Client Layer"]
        UI["Web Chat UI"]
    end

    subgraph SecurityGateway["Security Gateway (Layer 0)"]
        MA["Model Armor API"]
        DLP["Cloud DLP"]
    end

    subgraph CoreEngine["Agent Orchestration Engine"]
        ADK["Vertex AI ADK"]
        SessionMgr["Session Manager (15m TTL)"]
        JWTGen["Signed JWT Token Issuer"]
        FwdRec["Forward Recovery Worker"]
    end

    subgraph ToolServers["MCP Tool Servers"]
        WWMCP["WorkWeek MCP Server"]
        SIMCP["ServiceImmediately MCP Server"]
    end

    subgraph GroundingEngine["Grounding Engine"]
        VES["Vertex AI Search"]
    end

    subgraph StorageLayer["Storage Layer"]
        DB[("Cloud SQL PostgreSQL")]
        GCS[("Cloud Storage")]
    end

    UI <-->|"1. Send/Receive Turn"| MA
    MA <-->|"2. Redact SPII"| DLP
    MA <-->|"3. Clean Payload"| ADK
    ADK <-->|"4. Session State"| SessionMgr
    SessionMgr <-->|"5. Persist Session"| DB
    ADK -->|"6. Mint Scoped Token"| JWTGen
    ADK <-->|"7. Query Policy"| VES
    ADK <-->|"8. HCM Tool Call (JWT)"| WWMCP
    ADK <-->|"9. ITSM Tool Call (JWT)"| SIMCP
    ADK -->|"10. Enqueue Sync on Failure"| FwdRec
    FwdRec <-->|"11. Process Retries"| DB
    ADK -->|"12. Write Masked Audit"| DB
```

---

### Figure 4: Sequence Diagram — Cross-System Medical Leave Orchestration (UC-2.2)

```mermaid
sequenceDiagram
    autonumber
    actor Employee as Employee Client
    participant Gateway as Model Armor Gateway
    participant Orch as Primary HR Orchestrator (ADK)
    participant Policy as Policy Q&A Specialist
    participant WW as WorkWeek MCP Server
    participant SI as ServiceImmediately MCP Server
    participant DB as Cloud SQL (Audit & Sync Queue)

    Employee->>Gateway: "I need to take short-term medical leave starting next Monday. What is the process and can you set it up?"
    Gateway->>Gateway: Inbound Prompt Sanitization (Model Armor)
    Gateway->>Orch: Clean Prompt Payload
    
    Note over Orch: Step 1: Query Policy Q&A Specialist
    Orch->>Policy: get_policy_guidelines(query="Short-term medical leave policy and procedure")
    Policy-->>Orch: Returns Policy Terms + Deep-Link Citation [Handbook#MedicalLeave](https://...)
    
    Note over Orch: Step 2: Human-in-the-Loop Confirmation Gate (ADR-0007)
    Orch-->>Employee: "According to policy, short-term medical leave provides up to 12 weeks. I will submit 5 days starting Aug 24 in WorkWeek and open an IT notification ticket in ServiceImmediately. Should I proceed?"
    Employee->>Orch: "Yes, please proceed."
    
    Note over Orch: Step 3: Execute WorkWeek Leave Booking
    Orch->>WW: workweek_submit_leave_request(type="Sick/Medical", start="2026-08-24", end="2026-08-28", auth_token="<JWT:workweek:write>")
    WW-->>Orch: Leave Confirmed (Ref #LOA-9081, 5 Days Deducted)
    
    Note over Orch: Step 4: Execute ServiceImmediately IT Ticket Creation
    Orch->>SI: itsm_create_incident(category="Access/IT", priority=3, desc="Route email access to manager during Medical Leave LOA-9081", auth_token="<JWT:itsm:write>")
    
    alt Happy Path: ITSM Ticket Succeeds
        SI-->>Orch: Ticket Created (INC123456)
        Orch->>DB: Write Audit Log (Status: SUCCESS, Action: UC-2.2)
        Orch->>Gateway: Response Payload with Citations & Ticket IDs
        Gateway->>Gateway: Outbound DLP SPII Scan
        Gateway-->>Employee: "Your Medical Leave has been booked (Ref #LOA-9081) and IT Ticket #INC123456 has been opened. Policy Reference: [Medical Leave Guidelines](https://...)"
    else Failure Path: ITSM Ticket Times Out / 500 Error (Forward Recovery ADR-0004)
        SI-->>Orch: HTTP 504 GATEWAY_TIMEOUT
        Note over Orch: Forward Recovery: Preserve WorkWeek Booking, Do NOT Rollback
        Orch->>DB: Insert into pending_sync_tasks (task_id, LOA-9081, payload, status='PENDING')
        Orch->>DB: Write Audit Log (Status: PARTIAL_FAILURE_FORWARD_RECOVERY)
        Orch->>Gateway: Response Payload with Recovery Guidance
        Gateway-->>Employee: "Your Medical Leave is approved in WorkWeek (Ref #LOA-9081). However, the IT notification ticket timed out. Our system has automatically queued this task for synchronization, and your HR representative has been notified."
    end
```

---

### Figure 5: Sequence Diagram — Grounded Policy Q&A with Live Vertex AI Search & Deep-Link Citations (UC-1.1)

```mermaid
sequenceDiagram
    autonumber
    actor Employee as Employee Client
    participant Gateway as Model Armor Gateway
    participant Orch as Primary HR Orchestrator
    participant PolicyAgent as Policy Q&A Specialist
    participant VertexSearch as Vertex AI Search (Discovery Engine)
    participant Formatter as Citation Formatter

    Employee->>Gateway: "Are noise-canceling headphones an expensable item under our remote work policy?"
    Gateway->>Gateway: Ingress Safety Scan (<150ms)
    Gateway->>Orch: Clean Prompt
    Orch->>PolicyAgent: Delegate Policy Query
    
    PolicyAgent->>VertexSearch: Search Request (Query: "noise-canceling headphones expense remote work", ACL: "role=Standard, clearance=1")
    VertexSearch-->>PolicyAgent: Returns Extractive Snippets + Metadata (Doc: "Expense Guidelines 2026", Section: "Hardware Peripherals", URL: "https://...")
    
    alt High Confidence Match (Score >= 0.70)
        PolicyAgent->>PolicyAgent: Synthesize Grounded Answer (Temperature = 0.0)
        PolicyAgent->>Formatter: Build Clickable Citation ([Expense Guidelines 2026#Hardware Peripherals](https://...))
        Formatter-->>PolicyAgent: Formatted Markdown with Inline Citation
        PolicyAgent-->>Orch: Answer with Source Deep Links
        Orch-->>Gateway: Final Grounded Response
        Gateway-->>Employee: "Yes, noise-canceling headphones up to 50 are expensable once every 24 months. Source: [Expense Guidelines 2026#Hardware Peripherals](https://intranet.example.com/policies/expenses.pdf#page=14)"
    else Out of Domain / Policy Not Found (Score < 0.70)
        PolicyAgent-->>Orch: Fallback Response (No Hallucination)
        Orch-->>Gateway: Fallback Payload
        Gateway-->>Employee: "This topic is not covered in company policy. For custom expense inquiries, please consult your department manager or submit an inquiry to the Finance team."
    end
```

---

### Figure 6: Sequence Diagram — WorkWeek HCM PTO Inquiry & Guarded Vacation Booking (UC-1.2)

```mermaid
sequenceDiagram
    autonumber
    actor Employee as Employee Client
    participant Orch as Primary HR Orchestrator
    participant WW_Agent as WorkWeek HCM Specialist
    participant WW_MCP as WorkWeek MCP Server
    participant Fixture as WorkWeek Stateful Fixtures

    Employee->>Orch: "How many vacation days do I have left, and can I take off next Friday?"
    Orch->>WW_Agent: Query PTO Balance (emp_id: "EMP-1029")
    WW_Agent->>WW_MCP: workweek_get_pto_balances(auth_token="<JWT>")
    WW_MCP->>Fixture: Lookup Balances (EMP-1029)
    Fixture-->>WW_MCP: Vacation: Accrued 18d, Used 4d, Remaining 14d
    WW_MCP-->>WW_Agent: PTO Balance Response
    WW_Agent-->>Orch: 14 Vacation Days Available
    
    Orch-->>Employee: "You currently have 14 days of remaining vacation leave. Would you like me to submit a 1-day leave request for Friday, Aug 28, 2026?"
    Employee->>Orch: "Yes, submit the request."
    
    Orch->>WW_Agent: Submit Leave (start="2026-08-28", end="2026-08-28", type="Vacation")
    WW_Agent->>WW_MCP: workweek_submit_leave_request(start="2026-08-28", end="2026-08-28", type="Vacation", days=1)
    
    Note over WW_MCP: Guardrail Validation (FR-3.3):<br>1. Chronological: Aug 28 >= Today (Pass)<br>2. Balance: 1 day <= 14 remaining (Pass)
    
    WW_MCP->>Fixture: Mutate State (Deduct 1d Vacation, Record LOA-9402)
    Fixture-->>WW_MCP: Success (New Balance: 13d)
    WW_MCP-->>WW_Agent: Leave Request Confirmed (Ref #LOA-9402)
    WW_Agent-->>Orch: Booking Result
    Orch-->>Employee: "Your vacation leave for Friday, Aug 28, 2026 has been approved (Ref #LOA-9402). Your new vacation balance is 13 days."
```

---

### Figure 7: Sequence Diagram — ServiceImmediately Incident Management & Interactive Priority 1 Downgrade (UC-1.3)

```mermaid
sequenceDiagram
    autonumber
    actor Employee as Employee Client
    participant Orch as Primary HR Orchestrator
    participant ITSM_Agent as ServiceImmediately Specialist
    participant ITSM_MCP as ServiceImmediately MCP Server
    participant Fixture as ITSM Stateful Fixtures

    Employee->>Orch: "Create a Priority 1 Critical ticket because my wireless mouse battery died."
    Orch->>ITSM_Agent: Create Incident (priority=1, category="Hardware", desc="Wireless mouse battery died")
    
    ITSM_Agent->>ITSM_MCP: itsm_create_incident(priority=1, category="Hardware", desc="Wireless mouse battery died", auth_token="<JWT>")
    
    Note over ITSM_MCP: Priority 1 Guardrail Evaluation (ADR-0010):<br>Check: Description mentions enterprise outage / work stoppage?<br>Result: Single-user peripheral failure does NOT meet P1 criteria.
    
    ITSM_MCP-->>ITSM_Agent: PRIORITY_MISMATCH_PROMPT (requires justification or downgrade to P4)
    ITSM_Agent-->>Orch: Interactive Downgrade Prompt
    Orch-->>Employee: "Priority 1 - Critical is reserved for widespread system outages impacting business operations. A mouse battery issue is classified as Priority 4 - Low. Would you like me to open this ticket as Priority 4, or do you have a business justification for Critical?"
    
    Employee->>Orch: "Open it as Priority 4 Low."
    Orch->>ITSM_Agent: itsm_create_incident(priority=4, category="Hardware", desc="Wireless mouse battery replacement")
    ITSM_Agent->>ITSM_MCP: itsm_create_incident(priority=4, category="Hardware", desc="Wireless mouse battery replacement", auth_token="<JWT>")
    ITSM_MCP->>Fixture: Insert Incident (INC982104, State: 'New', Priority: 4)
    Fixture-->>ITSM_MCP: Ticket Created (INC982104)
    ITSM_MCP-->>ITSM_Agent: Success Response
    ITSM_Agent-->>Orch: Ticket Created Confirmation
    Orch-->>Employee: "Support Ticket #INC982104 has been created with Priority 4 - Low. A technician from Desktop Support will assign replacement batteries."
```

---

### Figure 8: Sequence Diagram — Event-Driven Real-Time Policy Sync Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor HRAuthor as HR Policy Author (CMS)
    participant GCS as Cloud Storage Bucket (gs://hr-policy-repo-prod)
    participant Eventarc as Cloud Eventarc Trigger
    participant CloudRun as Policy Ingestion Microservice (Cloud Run)
    participant DiscoveryEngine as Vertex AI Search (Discovery Engine)
    participant Agent as Policy Q&A Specialist Agent

    HRAuthor->>GCS: Uploads Approved PDF ("gs://hr-policy-repo-prod/active/Leave_Policy_2026_v2.pdf")
    GCS->>Eventarc: Emit Object Finalize Event (google.cloud.storage.object.v1.finalized)
    Eventarc->>CloudRun: Dispatch HTTP POST Webhook (Event Payload)
    
    CloudRun->>CloudRun: Validate PDF Structure & Compute SHA-256 Checksum
    CloudRun->>DiscoveryEngine: Import Document API (projects.locations.dataStores.branches.documents.import)
    
    Note over DiscoveryEngine: Vertex AI Search Processing (<60s):<br>1. Layout-Aware OCR & Semantic Chunking<br>2. Embedding Generation & Vector Index Upsert<br>3. Atomic Branch Replacement
    
    DiscoveryEngine-->>CloudRun: Ingestion Complete (Document ID: "doc-leave-2026-v2")
    CloudRun->>CloudRun: Log Successful Ingestion Event to Cloud Logging
    
    Note over Agent: Subsequent Employee Query (0ms Lag)
    Agent->>DiscoveryEngine: Search Query ("Parental Leave Policy")
    DiscoveryEngine-->>Agent: Returns Instant Updated 2026 Terms
```

---

### Figure 9: Sequence Diagram — Identity Authentication, OAuth OBO Exchange & Webhook Revocation

```mermaid
sequenceDiagram
    autonumber
    actor Employee as Employee Client
    participant IdP as Enterprise Identity Provider (Okta / Azure AD)
    participant AuthSvc as Agent Identity & JWT Service
    participant SessionStore as Cloud SQL (employee_sessions)
    participant MCP as WorkWeek & ITSM MCP Servers

    Note over Employee,AuthSvc: Phase 1: Authentication & Token Exchange
    Employee->>IdP: User Login (OIDC / OAuth 2.0)
    IdP-->>Employee: Returns ID Token & User Access Token
    Employee->>AuthSvc: POST /api/v1/auth/session (Passes ID Token)
    AuthSvc->>IdP: Validate ID Token & User Claims
    AuthSvc->>AuthSvc: Mint Signed Scoped Bearer JWT (sub=emp_id, iss=HR-Agent-v1, exp=15m)
    AuthSvc->>SessionStore: Insert Session (session_id, emp_id, expires_at=now+15m, is_revoked=false)
    AuthSvc-->>Employee: Session Established (Returns session_id)

    Note over Employee,MCP: Phase 2: Delegated Tool Execution
    Employee->>AuthSvc: Agent Turn Request
    AuthSvc->>MCP: Tool Execution (Authorization: Bearer <Signed JWT>)
    MCP->>MCP: Verify Cryptographic Signature & Scopes
    MCP-->>AuthSvc: Tool Result

    Note over IdP,SessionStore: Phase 3: Instant Revocation Webhook (<150ms SLA)
    IdP->>AuthSvc: Webhook: POST /api/v1/auth/revocation-events (user.session.revoke, user_id="EMP-1029")
    AuthSvc->>SessionStore: UPDATE employee_sessions SET is_revoked=TRUE WHERE user_id="EMP-1029"
    AuthSvc->>AuthSvc: Evict In-Memory Session Cache
    
    Employee->>AuthSvc: Next Inbound Turn
    AuthSvc->>SessionStore: Check Session Status
    SessionStore-->>AuthSvc: is_revoked = TRUE
    AuthSvc-->>Employee: HTTP 401 UNAUTHORIZED ("Session credentials revoked. Please re-authenticate.")
```

---

### Figure 10: Low-Level Database Entity-Relationship Diagram (ERD) & Data Flow

```mermaid
erDiagram
    EMPLOYEE_SESSION ||--o{ CONVERSATION_TURN : contains
    EMPLOYEE_SESSION ||--o{ PENDING_SYNC_TASK : triggers
    CONVERSATION_TURN ||--|| AUDIT_LOG_ENTRY : records
    POLICY_DOCUMENT_METADATA ||--o{ POLICY_CHUNK_INDEX : indexes

    EMPLOYEE_SESSION {
        varchar(64) session_id PK
        varchar(32) user_id FK
        varchar(64) auth_token_fingerprint
        timestamp created_at
        timestamp last_active_at
        timestamp expires_at
        jsonb session_state_json
        boolean is_revoked
    }

    CONVERSATION_TURN {
        uuid turn_id PK
        varchar(64) session_id FK
        int turn_number
        varchar(64) user_prompt_hash
        varchar(32) acting_agent
        varchar(64) tool_name_invoked
        jsonb tool_payload_masked
        int response_latency_ms
        timestamp created_at
    }

    AUDIT_LOG_ENTRY {
        uuid log_id PK
        uuid turn_id FK
        varchar(32) user_id
        varchar(64) action_type
        varchar(32) target_system
        int http_status_code
        varchar(64) jwt_signature_hash
        jsonb masked_evidence
        timestamp created_at
    }

    PENDING_SYNC_TASK {
        uuid task_id PK
        varchar(64) session_id FK
        varchar(32) user_id
        varchar(32) originating_system
        varchar(32) failing_system
        varchar(64) operation_name
        jsonb payload
        int retry_count
        int max_retries
        varchar(20) status
        timestamp next_retry_at
        timestamp created_at
        timestamp resolved_at
    }

    POLICY_DOCUMENT_METADATA {
        varchar(64) doc_id PK
        varchar(255) doc_title
        varchar(255) gcs_uri
        varchar(64) sha256_checksum
        jsonb authorized_roles
        int minimum_clearance
        timestamp last_synced_at
        boolean is_active
    }

    POLICY_CHUNK_INDEX {
        varchar(64) chunk_id PK
        varchar(64) doc_id FK
        int section_number
        varchar(255) section_title
        text chunk_text
        varchar(255) deep_link_url
    }
```

---

### Figure 11: Layer 0 Security Sentinel Gateway & Cloud DLP Tiered Redaction Pipeline

```mermaid
flowchart TD
    subgraph IngressPipeline["Ingress Security Pipeline (<150ms)"]
        RawPrompt["Raw User Inbound Prompt"] --> RegexCheck{"Fast Regex / Leet Filter<br>(<10ms)"}
        RegexCheck -->|Suspicious Payload| BlockRegex["Reject 400 (Syntax Violation)"]
        RegexCheck -->|Clean| ModelArmorPrompt["Model Armor Inbound Inspection<br>• Prompt Injection Classifier<br>• Jailbreak & System Prompt Exfiltration Guard"]
        
        ModelArmorPrompt -->|Injection Detected| BlockMA["Reject 403 (Security Violation)<br>Emit Alert to Security Command Center"]
        ModelArmorPrompt -->|Pass| CleanPrompt["Clean Prompt to Orchestrator"]
    end

    subgraph EgressPipeline["Egress Security Pipeline (<150ms)"]
        RawResponse["Raw Model Generated Output"] --> ToxicityCheck["Model Armor Output Filter<br>• Toxicity & Harassment Guard<br>• Hallucination / Factuality Verifier"]
        
        ToxicityCheck -->|Violation| BlockTox["Mask Output & Return Safe Fallback"]
        ToxicityCheck -->|Pass| SplitStream{"Tiered Redaction Splitter"}
        
        SplitStream -->|Ephemeral UI Stream| RenderUI["Render Full Response in Client UI<br>(Allows verified employee self-view of address/phone)"]
        SplitStream -->|Persistent Log Stream| DLPRedact["Cloud DLP InspectTemplate<br>• Mask US_SSN: [REDACTED_SSN]<br>• Mask Phone: [REDACTED_PHONE]<br>• Mask Address: [REDACTED_ADDRESS]"]
        
        DLPRedact --> CommitLog["Commit Masked JSON to audit_logs & stdout"]
    end
```

---

### Figure 12: CI/CD Deployment Pipeline & Automated `agents-cli` Evaluation Gate

```mermaid
flowchart LR
    GitPush["1. Git Push / PR<br>(Branch: main / feature)"] --> LintAndTest["2. Static Analysis & TDD<br>• ruff & black<br>• pytest (Unit & Fixtures)"]
    
    LintAndTest --> AgentsEval["3. agents-cli Evaluation Gate<br>(Gemini Flash Judge)"]
    
    subgraph EvalGatingCriteria["Strict Zero-Tolerance CI Gating (ADR-0013)"]
        AgentsEval --> GateSafety{"Safety Injection Block = 100%?"}
        GateSafety -->|No| FailBuild["FAIL BUILD (Block PR)"]
        GateSafety -->|Yes| GateSPII{"Log SPII Redaction = 100%?"}
        GateSPII -->|No| FailBuild
        GateSPII -->|Yes| GateGrounded{"Grounding Score >= 0.95?<br>(Dual Regex + Semantic)"}
        GateGrounded -->|No| FailBuild
        GateGrounded -->|Yes| GateLatency{"Turn Latency < 10.0s?<br>Safety Overhead < 300ms?"}
        GateLatency -->|No| FailBuild
        GateLatency -->|Yes| PassEval["PASS CI EVALUATION"]
    end
    
    PassEval --> IaCPlan["4. Terraform Plan & tfsec Scan"]
    IaCPlan --> CanaryDeploy["5. Canary Deployment<br>(Cloud Run 10% Traffic)"]
    CanaryDeploy --> SoakPeriod{"15-Min Error Metric Soak"}
    SoakPeriod -->|Errors > 0.1%| RollbackCanary["Automated Canary Rollback"]
    SoakPeriod -->|Healthy| FullDeploy["6. 100% Traffic Cutover"]
```

---

### Figure 13: Subsystem Failure Modes, Circuit Breakers & Forward Recovery State Machine

```mermaid
stateDiagram-v2
    [*] --> IdleState : Service Initialized

    state CircuitBreaker {
        Closed --> HalfOpen : 30s Cooldown Timer Expires
        HalfOpen --> Closed : 2 Consecutive Successful Probes
        HalfOpen --> Open : Probe Fails
        Closed --> Open : 5 Consecutive Failures in 30s
    }

    state ForwardRecoveryQueue {
        PendingTask --> RetryingTask : Exponential Backoff Timer (100ms, 300ms, 900ms)
        RetryingTask --> ResolvedTask : Downstream API Recovers
        RetryingTask --> EscalatedToHR : Max Retries (5) Exceeded -> Open HR Ops Incident
    }

    IdleState --> ProcessingTurn : Inbound Request Received
    ProcessingTurn --> Closed : Subsystem Invocation
    Open --> FallbackResponse : Fast Failover to Cached / Static Links
    ProcessingTurn --> PendingTask : Cross-System Partial Failure (ADR-0004)
```
