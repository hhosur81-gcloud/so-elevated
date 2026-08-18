# SEC-0005: Real-Time SCC Threat Streaming & Automated Security Incident Response

## Context
When Google Cloud Model Armor detects and blocks high-severity adversarial attacks (such as prompt injections, jailbreaks, or cross-tenant data harvesting probes), the enterprise Security Operations Center (SOC) must be notified in real time.

## Decision
We implement an automated threat response pipeline:
1. **Eventarc Threat Stream**: Model Armor security violation events emit structured event payloads (`google.cloud.modelarmor.finding.v1`) to Google Cloud Eventarc.
2. **Security Command Center (SCC) Premium**: Events are ingested in real time into SCC as high-priority security findings.
3. **Automated Incident Creation**: For high-confidence adversarial injection attacks, an automated Cloud Function creates a **Priority 1 Security Incident** in ServiceImmediately assigned directly to the Cyber Incident Response Team (CIRT) with sanitized attacker payload evidence.

## Consequences
- **Rapid SOC Response**: Eliminates manual log scraping; security teams are alerted within seconds of active adversarial attacks.
- **Automated Evidence Capture**: Pre-populates ticketing and SIEM systems with complete forensic traces.
