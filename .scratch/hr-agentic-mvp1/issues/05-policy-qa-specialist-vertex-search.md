# 05 — Policy Q&A Specialist Agent & Live Vertex AI Search Grounding

**What to build:** Dedicated Policy Q&A Agent grounding responses against live Vertex AI Search datastore (ADR-0008) holding approved HR policy documents, returning deep-link citations and strict zero-hallucination fallback.

**Blocked by:** 01 — Project Scaffold, Domain Models & Signed JWT Auth, 02 — Security Sentinel Interceptor

**Status:** ready-for-agent

- [ ] Live Vertex AI Search datastore retrieval connector with authentic GCP project credentials.
- [ ] Formats policy answers with clickable citations ([Document Title#Section](url)).
- [ ] Returns explicit fallback message when topic is not covered in company policy.
- [ ] Grounding evaluation benchmark demonstrating >= 95% accuracy and 0% hallucinations against live datastore.
