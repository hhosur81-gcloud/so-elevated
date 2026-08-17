# Multi-Stage Hybrid Guardrails Pipeline for Safety & SPII

To guarantee the strict <300ms latency ceiling (NFR-2.1) while maintaining 100% prompt injection and toxic output defense (FR-1.3), we implement a hybrid safety interceptor: fast local regex & Presidio pattern redaction for SPII (<20ms) combined with a targeted LLM safety classifier for prompt injection and topic boundaries.
