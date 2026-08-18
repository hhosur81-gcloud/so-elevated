# SEC-0003: Full Customer Managed Encryption Keys (CMEK) Governance

## Context
To comply with regulatory standards (GDPR, HIPAA, SOC 2 Type II), enterprise data-at-rest across vector search stores, document repositories, and relational audit databases must be encrypted using keys owned and controlled by the customer.

## Decision
We mandate Customer Managed Encryption Keys (CMEK) backed by FIPS 140-2 Level 3 Cloud KMS Hardware Security Modules (HSMs) across all persistent layers:
1. **Vertex AI Search**: CMEK key encrypting document chunk indexes and vector embeddings.
2. **Cloud Storage**: CMEK key encrypting raw HR policy PDF/Markdown repositories (`gs://hr-policy-repo-prod`).
3. **Relational Database**: CMEK key encrypting PostgreSQL tablespaces for `employee_sessions`, `audit_logs`, and `pending_sync_tasks`.

## Consequences
- **Cryptographic Control**: The enterprise can instantly revoke key access in Cloud KMS to perform emergency cryptographic shredding of all project data.
- **Compliance Certification**: Satisfies strict banking, healthcare, and global enterprise data sovereignty mandates.
