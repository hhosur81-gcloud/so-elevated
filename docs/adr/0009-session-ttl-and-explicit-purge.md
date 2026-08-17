# Session Expiry via Explicit Reset Prompts and 15-Minute Idle TTL

To fulfill FR-2.2 and FR-1.5 while preventing stale or orphaned multi-turn conversation contexts, the Vertex ADK session manager implements a dual purge mechanism: immediate purging upon user exit prompts ("reset", "clear", "log out") and an automated 15-minute idle Time-To-Live (TTL).
