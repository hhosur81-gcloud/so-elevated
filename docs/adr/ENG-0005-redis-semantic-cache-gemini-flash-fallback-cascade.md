# ENG-0005: Redis Vector Semantic Caching & Multi-Tier Gemini Flash Fallback Cascading

## Context
Repetitive informational policy queries (e.g. bereavement leave days, holiday schedules) cause unnecessary model latency and token expense. Furthermore, upstream Google Cloud quota spikes or regional capacity limits require automated fallback mechanisms.

## Decision
We implement a dual-layer optimization and resilience architecture:
1. **Redis Vector Semantic Cache**: High-frequency static policy queries are embedded and matched against a Redis Vector store. If a query matches an approved cached answer with cosine similarity $\ge 0.96$, the answer is returned instantly in **< 50ms** with zero LLM inference cost.
2. **4-Tier Gemini Flash Model Fallback Cascade**: If the Primary model encounters 429 rate limits, 503 service unavailability, or timeout exceptions, the orchestrator automatically cascades down the model hierarchy:
   - **Tier 1 (Primary)**: `gemini-3.7-flash`
   - **Tier 2 (Fallback 1)**: `gemini-3.6-flash`
   - **Tier 3 (Fallback 2)**: `gemini-3.0-flash`
   - **Tier 4 (Emergency Fallback)**: `gemini-2.5-flash`

## Consequences
- **Cost & Latency Reduction**: Deflects 35%+ of LLM queries to cache, achieving <50ms response times.
- **High Availability**: Guarantees uninterrupted conversational service even during upstream model quota saturation.
