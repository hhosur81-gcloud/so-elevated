# 05 — Policy Q&A Specialist Agent & Open Knowledge Format (OKF) Grounding

**What to build:** Dedicated Policy Q&A Agent grounding responses against repository-resident Open Knowledge Format (OKF) policy files (`knowledge/`) (ADR-0002, ADR-0008) holding approved HR policy documents, returning deep-link citations and strict zero-hallucination fallback.

**Blocked by:** 01 — Project Scaffold, Domain Models & Signed JWT Auth, 02 — Security Sentinel Interceptor

**Status:** ready-for-agent

- [ ] Open Knowledge Format (OKF) policy bundle parser and retrieval connector with YAML frontmatter inspection.
- [ ] Formats policy answers with clickable citations ([Document Title#Section](url)).
- [ ] Returns explicit fallback message when topic is not covered in company policy.
- [ ] Grounding evaluation benchmark demonstrating >= 95% accuracy and 0% hallucinations against canonical OKF policy bundle.
