# 01 — Project Scaffold, Domain Models & Signed JWT Auth

**What to build:** Common domain models (Employee Profile, PTO Balances, Leave Request, Incident Record, Policy Chunk), FileStore atomic persistence repository, and the cryptographic Signed JWT token generator/validator for origin verification.

**Blocked by:** None — can start immediately

**Status:** closed

- [x] Pydantic/dataclass domain schemas with Tolerant Reader pattern (`src/models/common.py`, `src/models/employee.py`, `src/models/ticket.py`, `src/models/session.py`).
- [x] Signed JWT utility generating and validating asymmetric ECDSA P-256 bearer tokens with claims (`sub`, `iss`, `aud`, `scopes`) and dynamic JWKS export (`src/config/security.py`).
- [x] Atomic FileStore repository with Linux kernel file locking (`src/repositories/filestore_repository.py`) and pristine JSON fixtures (`fixtures/seed_*.json`).
- [x] Comprehensive unit test suite with 100% pass rate (`tests/unit/test_domain_models.py`, `tests/unit/test_security_jwt.py`, `tests/unit/test_filestore_repository.py`).
