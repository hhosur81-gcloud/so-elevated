"""Security Command Center (SCC) Premium Streaming & Automated P1 Alert Handler (SEC-0005)."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.config.security import JWTManager
from src.mcp.serviceimmediately_server import ServiceImmediatelyMCPServer
from src.models.guardrail import InspectionResult
from src.repositories.filestore_repository import FileStoreRepository


class SCCThreatAutomationService:
    """Eventarc subscriber streaming Model Armor attacks to SCC and automating P1 IT incident creation."""

    SCC_FINDINGS_FILE = "scc/findings.json"

    def __init__(self, jwt_manager: Optional[JWTManager] = None, repository: Optional[FileStoreRepository] = None):
        self.jwt_manager = jwt_manager or JWTManager()
        self.repo = repository or FileStoreRepository()
        self.itsm_server = ServiceImmediatelyMCPServer(jwt_manager=self.jwt_manager, repository=self.repo)

    def handle_security_finding(
        self,
        finding: InspectionResult,
        attacker_ip: str,
        raw_prompt: str
    ) -> Dict[str, Any]:
        """Stream event to SCC Premium and create automated P1 Security Incident."""
        finding_id = finding.finding_id or f"scc-{uuid.uuid4().hex[:8]}"
        now_str = datetime.now(timezone.utc).isoformat()

        # 1. Stream finding to SCC Premium
        scc_payload = {
            "finding_id": finding_id,
            "category": finding.category,
            "severity": "CRITICAL",
            "state": "ACTIVE",
            "source_properties": {
                "attacker_ip": attacker_ip,
                "risk_score": finding.risk_score,
                "sanitized_action": finding.action,
                "raw_prompt_hash": str(hash(raw_prompt))
            },
            "event_time": now_str
        }
        self.repo.save_record(self.SCC_FINDINGS_FILE, finding_id, scc_payload)

        # 2. Automatically create P1 incident in ServiceImmediately for CIRT
        token = self.jwt_manager.generate_delegated_token("system-admin", scopes=["itsm:security:write"])
        inc_res = self.itsm_server.itsm_create_security_incident(
            attacker_ip=attacker_ip,
            finding_category=finding.category or "UNKNOWN_ATTACK",
            forensic_payload={"raw_prompt": raw_prompt, "risk_score": finding.risk_score},
            bearer_token=token
        )

        ticket_id = inc_res["data"]["ticket_id"]
        assigned_to = inc_res["data"]["assigned_to"]

        return {
            "success": True,
            "scc_event_status": "STREAMED_TO_SCC_PREMIUM",
            "finding_id": finding_id,
            "p1_ticket_id": ticket_id,
            "assigned_to": assigned_to
        }
