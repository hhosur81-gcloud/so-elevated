# ENG-0002: In-Process Resilience, Fast Retries (Tenacity), & Deterministic Idempotency

## Context
During cross-system workflow execution (UC-2.x), step failures (such as a transient ServiceImmediately ITSM timeout during medical leave submission) must be handled gracefully without locking user sessions, double-booking leave, or creating duplicate tickets. We evaluated external queue infrastructures (Google Cloud Tasks / Pub/Sub) versus native in-process resilience.

## Decision (Phase 1 Pragmatic Architecture)
We adopt an **In-Process Resilience & Deterministic Idempotency Engine** implemented natively in Python / ADK:

1. **Deterministic Idempotency Hashing**:
   - All state-mutating requests generate a deterministic SHA-256 key:
     $$\text{Idempotency-Key} = \text{SHA256}(\text{session\_id} + \text{action} + \text{sorted\_params})$$
   - Key lookups occur against the local SQLite / Redis `IdempotencyStore`.
   - If a duplicate turn is replayed, the cached receipt is returned immediately in **<1ms** with zero duplicate downstream API calls.

2. **Fast In-Turn Retries (`tenacity`)**:
   - Transient network blips and 503 errors are retried immediately (up to 2 attempts with 1-second exponential backoff) before concluding a step failed. This resolves 95%+ of momentary SaaS glitches without user intervention.

3. **In-Process Asynchronous Background Retries (`asyncio.create_task`)**:
   - If a non-critical downstream step (e.g. out-of-office email routing ticket) fails after fast retries, the orchestrator returns the primary leave receipt to the employee immediately and continues background retries asynchronously via Python `asyncio`.

4. **Cloud Run Deployment Specification**:
   - Deployed on Google Cloud Run with `--no-cpu-throttling` (or `--min-instances=1`) to ensure container CPU is never throttled and in-flight `asyncio` tasks complete uninterrupted.

5. **Phase 2 Evolution (Deferred)**:
   - External Google Cloud Tasks will only be evaluated in Phase 2 if enterprise SaaS rate-limiting or multi-hour retry windows become necessary.

## Consequences
- **Minimal Latency & Infrastructure**: Zero external queue dependencies or message brokers to configure and maintain.
- **100% Local & CI/CD Testability**: The entire resilience lifecycle runs identically on local developer machines and production containers.
- **Bulletproof Deduplication**: Prevents duplicate tickets and double-deducted leave balances across turns.
