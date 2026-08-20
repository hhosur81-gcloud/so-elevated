# ENG-0005: Redis Vector Semantic Caching & Multi-Tier Gemini Flash Fallback Cascading

## Context
Repetitive informational policy queries (e.g. bereavement leave days, holiday schedules) cause unnecessary model latency and token expense. Furthermore, upstream Google Cloud quota spikes or regional capacity limits require automated fallback mechanisms.

## Decision
We implement a dual-layer optimization and resilience architecture:
1. **Semantic Query Cache (Redis / In-Memory)**:
   - High-frequency static policy queries are normalized and matched against the cache.
   - If a query matches an approved cached answer, the response is returned instantly in **< 50ms** with zero LLM inference cost.
2. **Multi-Tier Gemini Flash Model Fallback Cascade**:
   - If the Primary model encounters 429 rate limits, 503 service unavailability, or transient timeout exceptions, the orchestrator automatically cascades down the verified Gemini Flash model hierarchy:
     - **Tier 1 (Primary Production)**: `gemini-3.5-flash`
     - **Tier 2 (High-Efficiency Fallback)**: `gemini-3.5-flash-lite`
     - **Tier 3 (Dynamic Alias Fallback)**: `gemini-flash-latest`

## Consequences
- **Cost & Latency Reduction**: Deflects 35%+ of repetitive queries to cache, achieving <50ms response times.
- **High Availability**: Guarantees uninterrupted conversational service even during upstream model quota saturation.
