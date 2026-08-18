# SEC-0002: Strict VPC Service Controls (VPC-SC) Perimeter Enforcement

## Context
Enterprise CISO standards mandate strict data perimeter isolation to prevent Server-Side Request Forgery (SSRF), unauthorized API egress, and employee PII exfiltration to untrusted networks.

## Decision
We enforce a strict Google Cloud VPC Service Controls (VPC-SC) service perimeter encompassing all core project resources: Vertex AI Search (Discovery Engine), Google Cloud Model Armor, Cloud Storage policy buckets, Cloud Run orchestrator and MCP server instances, and Cloud KMS keys. Egress from the perimeter is strictly limited to authorized enterprise Service Bridges and Private Google Access (PGA).

## Consequences
- **Data Exfiltration Prevention**: Blocks any compromised container or prompt injection attack from transmitting sensitive HR data to external IP addresses or unauthorized cloud buckets.
- **Zero-Trust Network Isolation**: All inter-service traffic stays on the private Google Cloud backbone without traversing the public internet.
