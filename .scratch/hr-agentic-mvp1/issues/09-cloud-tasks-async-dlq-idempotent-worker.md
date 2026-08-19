# 09 — Cloud Tasks / PubSub Asynchronous DLQ & Idempotent Retry Worker

**What to build:** Decoupled asynchronous worker subscribing to Google Cloud Tasks / PubSub for processing `pending_sync_tasks` with exponential backoff, mandatory `Idempotency-Key: <UUID>` header verification, and routing to a Dead Letter Queue (DLQ) after 5 failed retries (ADR-0004, ENG-0002).

**Blocked by:** 01 — Project Scaffold, Domain Models & Signed JWT Auth

**Status:** closed

- [x] Cloud Tasks queue client (`hr-forward-recovery-queue`) enqueuing failed cross-system steps with `Idempotency-Key` headers (`src/services/task_queue_service.py`).
- [x] Asynchronous Cloud Run worker consuming sync tasks with exponential backoff retry policy (1s to 300s).
- [x] Idempotency deduplication table preventing duplicate leave bookings or ticket creations.
- [x] Dead Letter Queue (DLQ) topic routing tasks failing >5 attempts with automated Cloud Monitoring P2 alerts.
- [x] Integration test suite asserting exactly-once execution during simulated transient network faults (`tests/integration/test_cloud_tasks_dlq.py`).
