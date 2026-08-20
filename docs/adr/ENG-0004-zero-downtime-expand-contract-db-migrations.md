# ENG-0004: Durable Session Persistence & Zero-Downtime Schema Evolution

## Context
Conversational session state, authenticated user identity (`employee_id`), and pending confirmation gates must persist durably so employees can close their laptops, disconnect, and resume conversations without losing context. Furthermore, database schema updates during continuous deployment must never lock tables or break active sessions.

## Decision
We implement a dual-tier session persistence strategy paired with the **Expand-and-Contract Migration Pattern**:

1. **Session Persistence Backends**:
   - **Local Development**: Persistent SQLite database (`.adk/sessions.db`) via ADK's native `DatabaseSessionService(db_url="sqlite+aiosqlite:///...")`.
   - **Google Cloud Serverless Production**: **Google Cloud Firestore** (native JSON document storage with 15-minute automatic TTL expiration collections) or **Vertex AI Agent Engine Session Service**.
   - **Enterprise Relational Backing (Cloud SQL / PostgreSQL)**: Supported for strict compliance audit trails.

2. **Zero-Downtime Expand-and-Contract Migrations (Alembic)**:
   - **Phase 1 (Expand)**: Add new nullable columns or indexes via non-blocking DDL (`ADD COLUMN ... DEFAULT NULL`, `CREATE INDEX CONCURRENTLY`). The schema remains compatible with both container version `N` (live) and `N+1` (deploying).
   - **Phase 2 (Deploy)**: Deploy container version `N+1` via Blue/Green canary rollout.
   - **Phase 3 (Contract)**: After `N+1` is 100% live, run cleanup migrations to drop deprecated columns.

## Consequences
- **Session Durability**: Conversations survive browser refreshes, network drops, and device sleep.
- **Zero-Downtime Releases**: Database migrations execute safely in CI/CD without maintenance windows.
