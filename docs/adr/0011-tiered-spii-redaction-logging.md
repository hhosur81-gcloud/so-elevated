# Tiered SPII Redaction for Self-View vs. Persistent Logs

To support legitimate self-service profile queries (UC-1.2) while maintaining 100% compliance with FR-1.4, the system implements tiered visibility: unmasked contact data is rendered in the immediate ephemeral UI response to the authenticated employee, while the Output Security Interceptor strictly redacts all SPII (addresses, phone numbers, SSNs) prior to writing to persistent disk logs, stdout, or audit stores.
