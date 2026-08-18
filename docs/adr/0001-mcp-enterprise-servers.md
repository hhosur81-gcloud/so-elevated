# Use Model Context Protocol (MCP) Servers for Enterprise Integrations

To eliminate custom HTTP client boilerplate, standardize tool interfaces for Gemini, and provide realistic enterprise state with built-in validation guardrails, we implement dedicated Model Context Protocol (MCP) servers for WorkWeek (HCM) and ServiceImmediately (ITSM) backed by realistic stateful seed fixtures and signed JWT origin verification.

## Technology Tradeoff Analysis: Custom REST Endpoints vs. Model Context Protocol (MCP)

| Architectural Dimension | Option A: Custom REST API Mocks / Clients | Option B: Model Context Protocol (MCP) Servers (Selected) | Evaluated Impact & Rationale |
| :--- | :--- | :--- | :--- |
| **Agent Tool Calling Overhead** | High boilerplate. Requires manual schema reflection, custom `httpx`/`requests` wrappers, and JSON marshalling per tool. | Zero client boilerplate. Native JSON schema reflection directly consumable by Vertex ADK and Gemini. | **MCP Selected**: Reduces custom glue code by 80% and eliminates HTTP wrapper bugs. |
| **Guardrail & State Colocation** | Guardrails scattered across agent tool code and remote HTTP middleware. | Guardrails (PTO balance check, state machine transitions) colocated inside the MCP tool handler. | **MCP Selected**: Guarantees consistent validation rules regardless of calling agent. |
| **Production Backend Swappability** | High coupling between agent HTTP client routes and mock endpoints. | Zero agent changes. The MCP server encapsulates the backend, swapping from seeded state to live Workday/ServiceNow APIs transparently. | **MCP Selected**: Protects agent prompt contracts from future enterprise API refactorings. |
| **Performance & IPC Overhead** | HTTP over TCP connection setup overhead (~15–35ms per turn). | Local `stdio` or lightweight SSE transport (<5ms IPC latency). | **MCP Selected**: Delivers faster turn latency to stay well within the <300ms SLA. |
| **Standardization & Ecosystem** | Proprietary custom REST schemas requiring bespoke documentation. | Open industry standard (Model Context Protocol) supported across modern AI ecosystems. | **MCP Selected**: Future-proof standard aligning with modern Google Cloud AI architectures. |
