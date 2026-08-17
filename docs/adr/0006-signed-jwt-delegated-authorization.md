# Use Signed JWT Bearer Tokens for Delegated Authorization & Origin Verification

To satisfy FR-1.2 (Verification of Request Origin) and FR-3.1 (Delegated Authorization), all downstream API requests to WorkWeek and ServiceImmediately must include a cryptographically signed JWT bearer token containing claims for the acting employee ID (`sub`), the agent service origin (`iss`), and authorized operation scopes (`scopes`).
