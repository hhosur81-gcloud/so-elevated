# HR Agentic Solution

A secure, conversational AI assistant orchestrating enterprise HR services, policy knowledge, HCM transactions (WorkWeek), and ITSM incident management (ServiceImmediately).

## Language

**WorkWeek**:
The core Human Capital Management (HCM) system of record holding employee profiles, contact details, and PTO balances.
_Avoid_: HRIS, PeopleSoft, BambooHR

**ServiceImmediately**:
The enterprise IT and HR Service Desk (ITSM/HRSD) platform managing incident tickets, equipment requests, and support comments.
_Avoid_: ServiceNow, Jira Service Desk, Helpdesk

**Policy Repository**:
The centralized repository of approved corporate policy documents (PDF/Text) used for grounded informational queries.
_Avoid_: Document store, Wiki, KB

**Leave of Absence**:
An employee time-off request (Vacation or Sick) submitted and tracked within WorkWeek.
_Avoid_: PTO ticket, absence booking

**Incident**:
A support or service ticket created within ServiceImmediately with a tracked priority (1-Critical to 4-Low) and status lifecycle.
_Avoid_: Support case, issue, bug

**Origin Verification**:
The cryptographic or token-based provenance attached to automated downstream operations distinguishing agent actions from direct user input.
_Avoid_: Caller ID, system user

**Safety Interceptor**:
The dual-stage security middleware that validates user inputs against prompt injection and redacts SPII from outputs before presentation.
_Avoid_: Prompt filter, content moderator
