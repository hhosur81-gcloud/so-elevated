# Explicit Human Confirmation Gate on State Mutations

To prevent accidental data corruption and enforce enterprise safety standards, the Primary Orchestrator and specialized sub-agents must require explicit user confirmation before executing state-changing write operations (Leave of Absence booking, contact info updates, incident status closure). Read queries and ticket comments execute directly without confirmation.
