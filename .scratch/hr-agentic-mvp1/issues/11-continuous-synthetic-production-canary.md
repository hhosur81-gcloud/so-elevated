# 11 — 24/7 Continuous Synthetic Production Canary & Dual-Region HA Probes

**What to build:** Automated Cloud Scheduler synthetic canary worker executing end-to-end multi-turn dialogs every 5 minutes against `EMP-CANARY-01`, streaming availability SLAs to Cloud Monitoring with Global Load Balancer health-check endpoints for dual-region failover (SEC-0004, ENG-0006).

**Blocked by:** 08 — End-to-End Evaluation Suite & Performance Benchmark

**Status:** ready-for-agent

- [ ] Cloud Scheduler job triggering headless canary probe container every 5 minutes.
- [ ] Synthetic probe script executing Policy Q&A -> WorkWeek balance query -> ServiceImmediately test incident create & resolve against `EMP-CANARY-01`.
- [ ] Export synthetic transaction latency and success/failure metrics to Google Cloud Monitoring.
- [ ] Health check endpoint (`/healthz`) reporting deep subsystem readiness for Global Load Balancer multi-region failover (<60s RTO).
- [ ] Automated alerting policy paging on-call upon 2 consecutive synthetic probe failures.
