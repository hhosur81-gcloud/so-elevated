# 05 — Policy Q&A Specialist Agent & Open Knowledge Format (OKF) Grounding

<<<<<<< HEAD
**What to build:** Dedicated Policy Q&A Agent grounding responses against repository-resident Open Knowledge Format (OKF) policy files (`knowledge/`) (ADR-0002, ADR-0008) holding approved HR policy documents, returning deep-link citations and strict zero-hallucination fallback.
=======
**What to build:** Dedicated Policy Q&A Agent grounding responses against live Vertex AI Search datastore (ADR-0008) holding approved HR policy documents, returning deep-link citations, Redis semantic vector caching (<50ms, ENG-0005), and strict zero-hallucination fallback.
>>>>>>> ced5c7f (feat(ticket-05): implement Policy Q&A Agent with grounded citations, semantic caching, and query-time ACL filtering)

**Blocked by:** 01 — Project Scaffold, Domain Models & Signed JWT Auth, 02 — Security Sentinel Interceptor

**Status:** closed

<<<<<<< HEAD
- [ ] Open Knowledge Format (OKF) policy bundle parser and retrieval connector with YAML frontmatter inspection.
- [ ] Formats policy answers with clickable citations ([Document Title#Section](url)).
- [ ] Returns explicit fallback message when topic is not covered in company policy.
- [ ] Grounding evaluation benchmark demonstrating >= 95% accuracy and 0% hallucinations against canonical OKF policy bundle.
=======
- [x] Policy Search datastore retrieval connector with query-time vector ACL filtering (`src/repositories/search_repository.py`).
- [x] Redis Vector Semantic Cache simulation delivering <50ms cached responses (`src/services/semantic_cache_service.py`).
- [x] Policy Q&A Agent formatting grounded policy answers with deep-link citations (`src/agents/policy_agent.py`).
- [x] Zero-hallucination fallback when query is not covered in company policy documents.
- [x] Integration test suite verifying grounded citations, caching, and ACL gates (`tests/integration/test_policy_agent.py`).
>>>>>>> ced5c7f (feat(ticket-05): implement Policy Q&A Agent with grounded citations, semantic caching, and query-time ACL filtering)
