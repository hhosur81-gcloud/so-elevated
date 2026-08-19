# 11 — 24/7 Continuous Synthetic Production Canary & Dual-Region HA Probes

**What to build:** Automated Cloud Scheduler synthetic canary worker executing end-to-end multi-turn dialogs every 5 minutes against `EMP-CANARY-01`, streaming availability SLAs to Cloud Monitoring with Global Load Balancer health-check endpoints for dual-region failover (SEC-0004, ENG-0006).

**Blocked by:** 08 — End-to-End Evaluation Suite & Performance Benchmark

**Status:** closed

- [x] Continuous Synthetic Canary executing 3-step transactions against `EMP-CANARY-01` (`src/services/canary_service.py`).
- [x] Synthetic probe script executing Policy Q&A -> WorkWeek balance query -> ServiceImmediately test incident create & resolve.
- [x] Export synthetic transaction latency and success/failure metrics to monitoring dataset.
- [x] Deep health check endpoint (`/healthz`) reporting subsystem readiness for Global Cloud Load Balancer (<60s RTO, SEC-0004).
- [x] Integration test suite verifying canary transactions and `/healthz` endpoint (`tests/integration/test_synthetic_canary.py`).
