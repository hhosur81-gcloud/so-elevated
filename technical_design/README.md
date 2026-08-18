# Technical Design Package: Enterprise HR Agentic Solution (MVP 1)

**Directory**: `technical_design/`  
**Repository**: `so-elevated` (`elevate-hrproject`)  
**Branch**: `AB`  
**Target Platform**: Gemini Enterprise Agent Platform (GEAP) & Google Cloud Platform (GCP)  
**Status**: Approved & Authoritative  

---

## 1. Overview & Navigation

This directory contains the authoritative, low-level technical design documentation, architectural decision trade-off analyses, visual topology catalogs, and requirements traceability matrices for the **HR Agentic Solution (MVP 1)**, designed in accordance with [`sdd-so-elevated.md`](../sdd-so-elevated.md) and [`requirements/HR-Agentic-BRD.md`](../requirements/HR-Agentic-BRD.md).

```
so-elevated/
├── sdd-so-elevated.md                  # System Design Document (SDD)
├── requirements/
│   └── HR-Agentic-BRD.md               # Business Requirements Document (BRD)
└── technical_design/                   # Low-Level Technical Design Package
    ├── README.md                       # This Navigation Guide
    ├── technical_design_document.md    # Master Low-Level Technical Design Document (LLD)
    ├── architecture_tradeoffs.md       # Deep-Dive Architectural Trade-Off Analysis
    ├── capabilities_mapping_matrix.md  # Detailed Requirements to GCP / GEAP Product Mapping
    └── system_architecture_diagrams.md # Visual Architecture & Sequence Diagram Catalog (13 Diagrams)
```

---

## 2. Document Descriptions & Links

### 1. [Master Technical Design Document (`technical_design_document.md`)](./technical_design_document.md)
The complete, end-to-end low-level technical design specification covering:
- Executive Summary & System KPIs (95%+ Grounding, 100% Safety Interception, <10s Turn Latency, 60%+ Tier-1 Deflection).
- End-to-End System & Enterprise Network Architecture Topology.
- Detailed Product Mapping to Gemini Enterprise Agent Platform (GEAP) and Google Cloud services.
- Architectural Trade-Off Analyses (Agent Engine vs Cloud Run, Gemini Flash vs Pro, MCP vs REST, Model Armor vs Custom, Forward Recovery vs 2PC).
- Component Deep Dives (Model Armor Gateway, Primary Orchestrator, Policy Specialist, WorkWeek MCP, ServiceImmediately MCP, Forward Recovery Worker).
- Relational Database Schemas (Cloud SQL PostgreSQL 16 DDL with partitioning and indexing).
- Error-Handling, Circuit Breakers & Resilience Matrix.
- Automated CI Evaluation Harness (`agents-cli` with Gemini Flash Judge).
- Infrastructure as Code (Terraform Modules).
- FinOps Unit Economics ($1.64 / 1k turns) & Enterprise ROI Model ($3.3M+ Annualized Net ROI).

### 2. [Architectural Trade-Offs & Decision Records (`architecture_tradeoffs.md`)](./architecture_tradeoffs.md)
Detailed engineering trade-off evaluations across 7 critical architectural choices:
1. **Agent Runtime**: Vertex AI Agent Engine (Managed Runtime) vs. Google Cloud Run vs. GKE Autopilot.
2. **Foundation Model**: Gemini 3.6 Flash / 2.5 Flash vs. Gemini Pro vs. Self-Hosted Llama 3 / Gemma 2.
3. **Integration Standard**: Model Context Protocol (MCP) Servers vs. Custom REST Endpoints.
4. **Knowledge Grounding**: Google Cloud Vertex AI Search (Discovery Engine) vs. Custom Vector DBs (Pinecone / Chroma / pgvector).
5. **AI Safety Perimeter**: Google Cloud Model Armor + Cloud DLP vs. Bespoke Application Regex Filters.
6. **Transactional Integrity**: Forward Recovery with Queued Retries vs. Distributed Two-Phase Commit (2PC) / Destructive Rollbacks.
7. **Identity & Provenance**: Cryptographically Signed JWT Bearer Tokens with Scoped Claims vs. Shared Static Service Accounts.

### 3. [Capabilities Mapping Matrix (`capabilities_mapping_matrix.md`)](./capabilities_mapping_matrix.md)
Exhaustive traceability matrix linking every functional requirement (FR-1.1 to FR-5.5), cross-system orchestration use case (UC-2.1 to UC-2.3), non-functional requirement (NFR-1.1 to NFR-4.3), and 35 user stories directly to:
- Google Cloud / GEAP Product, Service, and Feature.
- Specific API, SDK, and Protocol.
- Code Module and Schema Implementation.
- Architectural Rationale and Automated Verification Suite.

### 4. [System Architecture Diagrams Catalog (`system_architecture_diagrams.md`)](./system_architecture_diagrams.md)
High-resolution Mermaid architecture diagrams and sequence workflows:
- **Figure 1**: End-to-End System & Enterprise Network Architecture Topology
- **Figure 2**: Hierarchical Multi-Agent Orchestration & Dispatcher Runtime
- **Figure 3**: Low-Level Component & Service Interaction Diagram
- **Figure 4**: Sequence Diagram — Cross-System Medical Leave Orchestration (UC-2.2)
- **Figure 5**: Sequence Diagram — Grounded Policy Q&A with Live Vertex AI Search & Deep Links (UC-1.1)
- **Figure 6**: Sequence Diagram — WorkWeek HCM PTO Inquiry & Guarded Vacation Booking (UC-1.2)
- **Figure 7**: Sequence Diagram — ServiceImmediately Incident Lifecycle & Interactive Priority 1 Downgrade (UC-1.3)
- **Figure 8**: Sequence Diagram — Event-Driven Real-Time Policy Document Sync Pipeline (Eventarc + Cloud Run)
- **Figure 9**: Sequence Diagram — Identity Authentication, OAuth OBO Exchange & Webhook Revocation
- **Figure 10**: Low-Level Database Entity-Relationship Diagram (ERD) & Data Flow
- **Figure 11**: Layer 0 Security Sentinel Gateway & Cloud DLP Tiered Redaction Pipeline
- **Figure 12**: CI/CD Deployment Pipeline & Automated `agents-cli` Evaluation Gate
- **Figure 13**: Subsystem Failure Modes, Circuit Breakers & Forward Recovery State Machine

---

## 3. Technology Stack Summary

| Layer | Product / Technology | Primary Role in Solution |
| :--- | :--- | :--- |
| **Foundation LLM** | **Gemini 3.6 Flash / 2.5 Flash** | Sub-second intent classification, native tool calling, and zero-hallucination synthesis. |
| **Agent Runtime** | **Vertex AI Agent Engine & ADK** | Managed conversational session lifecycle (15m idle TTL), multi-agent dispatching, and HITL gate. |
| **Semantic Grounding** | **Google Cloud Vertex AI Search** | Managed OCR, layout-aware chunking, hybrid search, and deep-link citation generation. |
| **Enterprise Tools** | **Model Context Protocol (MCP)** | Decoupled tool servers (`workweek-mcp`, `serviceimmediately-mcp`) with colocated guardrails. |
| **AI Security Perimeter** | **Google Cloud Model Armor** | Managed Layer 0 prompt injection defense, jailbreak mitigation, and SCC telemetry. |
| **Privacy & Redaction** | **Cloud Sensitive Data Protection (DLP)** | Tiered SPII redaction masking sensitive fields in persistent logs while allowing user self-view. |
| **Identity & Provenance** | **Signed JWT Bearer Tokens (RS256)** | Zero-trust caller provenance and least-privilege scoping (`sub`, `iss`, `scopes`). |
| **Persistence Tier** | **Cloud SQL PostgreSQL 16 (HA)** | Relational storage for sessions, partitioned audit logs (90d retention), and forward recovery queue. |
| **Event Ingestion** | **Eventarc + Cloud Run** | Real-time policy document synchronization (<60s ingestion latency). |
| **Automated Evaluation** | **Google `agents-cli` & Gemini Flash Judge** | Zero-tolerance CI gating enforcing 100% safety, 100% SPII masking, and >=95% grounding. |
