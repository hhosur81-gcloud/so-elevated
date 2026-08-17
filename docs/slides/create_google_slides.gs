/**
 * Google Apps Script: Generate HR Agentic Solution Architectural Decision Deck
 * 
 * Instructions:
 * 1. Open Google Drive (https://drive.google.com).
 * 2. Open https://script.google.com and create a New Project.
 * 3. Paste this script into Code.gs and click Run -> createHRAgenticDeck().
 * 4. A 10-slide presentation will be generated in your Google Drive automatically!
 */

function createHRAgenticDeck() {
  const presentation = SlidesApp.create('HR Agentic Solution (MVP 1) — Architectural Decision Deck');
  const slides = presentation.getSlides();
  const slide1 = slides[0];

  // 1. Title Slide
  slide1.getBackground().setFillColor('#1a73e8');
  const titleBox = slide1.insertTextBox('HR Agentic Solution (MVP 1)\nArchitectural Decision Deck & Topology', 60, 160, 600, 150);
  const titleText = titleBox.getText();
  titleText.getTextStyle().setFontFamily('Google Sans').setFontSize(36).setForegroundColor('#ffffff').setBold(true);
  
  const subBox = slide1.insertTextBox('Google Cloud Vertex AI ADK • Multi-Agent System • ADRs 0001–0011', 60, 320, 600, 60);
  subBox.getText().getTextStyle().setFontFamily('Roboto').setFontSize(18).setForegroundColor('#e8f0fe');

  function addContentSlide(title, category, bulletPoints) {
    const s = presentation.appendSlide(SlidesApp.PredefinedLayout.BLANK);
    const catBox = s.insertTextBox(category.toUpperCase(), 50, 30, 620, 20);
    catBox.getText().getTextStyle().setFontFamily('Google Sans').setFontSize(11).setForegroundColor('#5f6368').setBold(true);
    
    const hBox = s.insertTextBox(title, 50, 50, 620, 40);
    hBox.getText().getTextStyle().setFontFamily('Google Sans').setFontSize(22).setForegroundColor('#1a73e8').setBold(true);
    
    s.insertLine(SlidesApp.LineCategory.STRAIGHT, 50, 95, 670, 95).setWeight(1).getLineFill().setSolidFill('#e8eaed');
    
    const bodyBox = s.insertTextBox(bulletPoints.join('\n\n'), 50, 115, 620, 250);
    bodyBox.getText().getTextStyle().setFontFamily('Roboto').setFontSize(13).setForegroundColor('#202124');
    
    s.insertTextBox('HR Agentic Solution (MVP 1) • elevate-hrproject', 50, 375, 620, 20)
      .getText().getTextStyle().setFontFamily('Roboto').setFontSize(10).setForegroundColor('#5f6368');
      
    return s;
  }

  addContentSlide(
    'Executive Context & Business Drivers',
    'Problem Statement & Objectives',
    [
      '• Fragmented Enterprise Access: Disjointed employee interfaces across WorkWeek (HCM), ServiceImmediately (ITSM), and static policy wikis.',
      '• Heavy Tier-1 Overhead: High volume of routine inquiries (PTO, bereavement leave, expense policies) taxing support teams.',
      '• The Solution: Unified conversational assistant on Vertex AI ADK with strict policy grounding, zero-trust security, and cross-system workflows.',
      '• Key SLAs: >=95% grounding accuracy (0% hallucination), <300ms safety scanning, 100% prompt injection defense.'
    ]
  );

  addContentSlide(
    'Hierarchical Multi-Agent Topology (ADK)',
    'Agent Roles & Scopes',
    [
      '• Layer 0: Security Sentinel Interceptor — Sub-20ms Presidio/Regex SPII redaction & prompt injection defense.',
      '• Agent 1: Primary HR Orchestrator (ADK) — Root router, session manager (15m TTL), confirmation gate, and workflow engine.',
      '• Agent 2: Policy Q&A Specialist — Live Vertex AI Search grounding, citation deep links, and zero-hallucination fallback.',
      '• Agent 3: WorkWeek HCM Specialist — Profile queries, PTO balances, and guarded leave bookings (Signed JWT: workweek:*).',
      '• Agent 4: ServiceImmediately ITSM Specialist — Incident creation, comments, lifecycle transitions (Signed JWT: serviceimmediately:*).'
    ]
  );

  addContentSlide(
    'Key Decisions: Backends & Policy Grounding',
    'Architectural Decision Records',
    [
      '• ADR-0001: FastAPI Mock Services — Embedded local RESTful mock services with stateful fixtures for deterministic testing.',
      '• ADR-0002 & 0008: Live Vertex AI Search Policy RAG — Strict live connection to Google Cloud datastores with structured citation deep links.',
      '• ADR-0005: Vertex AI Agent Development Kit (ADK) — Standardized unified framework for Gemini model calling, tools, and session state.',
      '• ADR-0004: Cross-System Forward Recovery — Partial failure handling with audit logs and manual follow-up rather than destructive rollbacks.'
    ]
  );

  addContentSlide(
    'Key Decisions: Zero-Trust Security & Identity',
    'Architectural Decision Records',
    [
      '• ADR-0003: Hybrid Safety Guardrails — Fast local regex/Presidio redaction (<20ms) + LLM prompt injection classifier within <300ms SLA.',
      '• ADR-0006: Signed JWT Delegated Authorization — Bearer tokens carrying employee ID (sub), automation origin (iss: HR-Agent-v1), and scopes.',
      '• ADR-0011: Tiered SPII Redaction — Unmasked self-viewing in active UI stream with strict persistent log and audit trace masking.',
      '• FR-1.5: RBAC & Tenant Isolation — Scoped session boundaries preventing cross-employee data access.'
    ]
  );

  addContentSlide(
    'Key Decisions: Operational Safety & Lifecycle',
    'Architectural Decision Records',
    [
      '• ADR-0007: Human Confirmation Gate on Mutations — Explicit confirmation required before leave bookings, contact updates, or ticket closures.',
      '• ADR-0009: Session Expiry via Prompt & 15m TTL — Dual-trigger purge on explicit reset prompts or 15 minutes of idle inactivity.',
      '• ADR-0010: Interactive Priority Guardrail — Interactive prompt when Critical priority tag lacks major business outage justification.',
      '• FR-3.4: Zero AI Caching — Real-time live fetching on every profile and PTO balance query.'
    ]
  );

  addContentSlide(
    'Cross-System Workflow Execution (UC-2.2 Medical Leave)',
    'Sequence & Interaction Flow',
    [
      '1. Employee Request: "I need to take short-term medical leave starting next Monday."',
      '2. Security Sentinel: Validates prompt against injection & toxicity (<20ms).',
      '3. Primary Orchestrator: Quotes policy procedure via Policy Q&A Agent.',
      '4. Human Confirmation Turn: Confirms dates and leave duration with the employee.',
      '5. WorkWeek Agent: Submits Leave of Absence booking in WorkWeek (Ref #LOA-9081).',
      '6. ServiceImmediately Agent: Opens IT ticket to route email to manager (INC123456).',
      '7. Response Delivery: Delivers grounded confirmation with LOA ref, ticket ID, and policy citation.'
    ]
  );

  addContentSlide(
    'Tracer-Bullet Implementation Roadmap (TDD)',
    '8 Atomic Issues (.scratch/hr-agentic-mvp1/issues/)',
    [
      '• Ticket 01: Project Scaffold, Domain Models & Signed JWT Auth (Frontier)',
      '• Ticket 02: Security Sentinel Interceptor (Tiered SPII & Prompt Safety)',
      '• Ticket 03: WorkWeek HCM FastAPI Mock Service & Connector Tools',
      '• Ticket 04: ServiceImmediately ITSM FastAPI Mock Service & Connector Tools',
      '• Ticket 05: Policy Q&A Specialist Agent & Live Vertex AI Search Grounding',
      '• Ticket 06: Primary HR Orchestrator Agent (Vertex ADK) & Dispatcher',
      '• Ticket 07: Cross-System Workflow Handlers with Forward Recovery',
      '• Ticket 08: End-to-End Evaluation Suite & Performance Benchmark'
    ]
  );

  addContentSlide(
    'Architectural Readiness & Conclusion',
    'Final Readiness Gate',
    [
      '• 100% Requirements Traceability: All 35 user stories mapped to ADRs and test suites.',
      '• Zero Architectural Ambiguity: 11 ADRs lock down all backend, security, and lifecycle decisions.',
      '• Standalone Artifacts: Interactive Google Slides deck, HTML/Markdown README, and visual diagrams.',
      '• Ready for TDD: Implementation starts at Ticket 01 whenever you are ready!'
    ]
  );

  Logger.log('Presentation created successfully! URL: ' + presentation.getUrl());
}
