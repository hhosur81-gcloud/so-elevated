# SEC-0001: Asymmetric Cloud KMS & Dynamic JWKS Key Lifecycle Management

## Context
To enforce zero-trust identity provenance without risking signing key compromise, the system requires an enterprise cryptographic key management protocol for signing and verifying delegated authorization JWTs.

## Decision
We standardize on asymmetric Cloud KMS keys (ECDSA P-256 / SHA-256) managed via Google Cloud KMS. The Primary Orchestrator signs JWT tokens using the Cloud KMS AsymmetricSign API, and the MCP servers verify tokens dynamically via a cached internal JSON Web Key Set (JWKS) endpoint. We enforce an automated 90-day key rotation schedule with a 30-day verification grace window where previous public keys remain valid for signature verification.

## Consequences
- **Security**: Eliminates the risk of private key leakage in application configuration or environment variables.
- **Zero-Downtime Rotation**: Downstream MCP servers dynamically discover newly rotated public keys via the JWKS endpoint without requiring server restarts.
- **Auditability**: All cryptographic signing operations are logged to Cloud KMS audit logs.
