# ENG-0003: Pragmatic 3-Tier Layered MVC Codebase Architecture

## Context
To structure the codebase for rapid developer velocity, ease of maintenance, and testability across engineering squads, we must establish a clear architectural pattern that avoids both monolithic spaghetti code and overly complex abstract layering.

## Decision
We standardize on a **Pragmatic 3-Tier Layered MVC Architecture**:
1. **Controllers / Agent Handlers Layer** (`src/agents/`): Contains the Vertex ADK root orchestrator, intent routers, and declarative MCP tool definitions.
2. **Services / Business Logic Layer** (`src/services/`): Contains core domain validation, confirmation gate state machines, and cross-system workflow handlers.
3. **Repositories / Integration Clients Layer** (`src/repositories/` & `src/mcp/`): Manages data access, database queries, and downstream MCP server adapters with stateful fixtures.

## Consequences
- **Developer Velocity**: Fast onboarding for new engineers with familiar, standard design patterns.
- **Clean Test Boundaries**: Unit tests easily mock the service and repository interfaces without complex dependency injection containers.
