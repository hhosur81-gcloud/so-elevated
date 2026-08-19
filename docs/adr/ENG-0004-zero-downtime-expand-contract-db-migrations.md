# ENG-0004: Zero-Downtime Expand-and-Contract Database Schema Migrations (Alembic)

## Context
Database schema updates to `employee_sessions`, `audit_logs`, and `pending_sync_tasks` during continuous delivery deployments must never lock tables, break active sessions, or cause application downtime.

## Decision
We mandate the **Expand-and-Contract (Parallel Run) Schema Migration Pattern** managed via **Alembic**:
- **Phase 1 (Expand)**: Add new nullable columns, tables, or indexes via non-blocking DDL (`ADD COLUMN ... DEFAULT NULL`, `CREATE INDEX CONCURRENTLY`). The database is now compatible with both container version `N` (running) and version `N+1` (deploying).
- **Phase 2 (Deploy)**: Deploy container version `N+1` via Blue/Green canary rollout.
- **Phase 3 (Contract)**: After `N+1` is 100% live and stable, run a subsequent cleanup migration to drop deprecated legacy columns or backfill defaults.

## Consequences
- **Zero-Downtime Releases**: Database migrations execute seamlessly in the CI/CD pipeline without requiring maintenance windows.
- **Safe Rollbacks**: If a container rollback is triggered, the database remains 100% backward-compatible with version `N`.
