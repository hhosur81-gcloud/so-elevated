# SEC-0004: Dual-Region Active-Passive High Availability & Disaster Recovery (HA/DR)

## Context
To guarantee business continuity and satisfy the CTO mandate for 99.99% service availability during regional cloud infrastructure disruptions, the system requires a multi-region failover architecture.

## Decision
We implement a Dual-Region Active-Passive Architecture:
- **Primary Region**: `us-central1` (Hosting Cloud Run orchestrator, Model Armor, and Vertex AI Search datastore).
- **Secondary Region**: `us-east4` (Warm standby replicas of Cloud Run services and cross-region replicated Cloud Storage policy buckets).
- **Failover Routing**: Google Cloud Global HTTPS Load Balancer with automated health-check probing triggers seamless regional failover in `< 60 seconds` (Recovery Time Objective RTO < 60s, Recovery Point Objective RPO = 0 for read-only policies).

## Consequences
- **High Availability**: Guarantees uninterrupted Tier-1 employee self-service even during a full primary region outage.
- **Cost Efficiency**: Active-Passive warm standby on Cloud Run incurs zero idle compute cost due to serverless scale-to-zero capabilities.
