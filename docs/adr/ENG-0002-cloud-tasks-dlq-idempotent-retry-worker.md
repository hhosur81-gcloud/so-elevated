# ENG-0002: Asynchronous Cloud Tasks / PubSub Dead Letter Queue & Idempotent Retry Worker

## Context
During cross-system workflow execution (UC-2.x), step failures (such as ServiceImmediately API downtime during leave submission) create pending synchronization tasks in `pending_sync_tasks`. In-memory retry loops within the user-facing web container risk request timeouts, worker crashing, and duplicate transaction execution.

## Decision
We implement a decoupled, asynchronous queue worker architecture using **Google Cloud Tasks and Pub/Sub**:
- When a partial failure occurs, the Primary Orchestrator enqueues a sync task containing the serialized payload and a unique **`Idempotency-Key: <UUID>`** header.
- A dedicated background Cloud Run worker consumes tasks with exponential backoff (initial interval: 10s, max interval: 300s, multiplier: 2.0).
- If a task fails 5 consecutive times, it is automatically routed to a **Dead Letter Queue (DLQ)** and triggers a high-severity P2 alert to the platform on-call engineer.

## Consequences
- **Exactly-Once Execution**: Downstream MCP endpoints inspect `Idempotency-Key` headers in SQLite/PostgreSQL to prevent duplicate leave deductions or duplicate ticket creations.
- **Zero Request Blocking**: User sessions return immediately with forward recovery confirmation without waiting for background retries.
