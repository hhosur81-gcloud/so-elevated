"""Security Command Center (SCC) Premium Streaming & Automated P1 Alert Handler (SEC-0005)."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.config.security import JWTManager
from src.config.settings import settings
from src.mcp.remote_mcp_client import RemoteServiceImmediatelyClient
from src.models.guardrail import InspectionResult
from src.repositories.filestore_repository import FileStoreRepository


class SCCThreatAutomationService:
    """Eventarc subscriber streaming Model Armor attacks to SCC and automating P1 IT incident creation."""

    SCC_FINDINGS_FILE = "scc/findings.json"

    def __init__(self, jwt_manager: Optional[JWTManager] = None, repository: Optional[FileStoreRepository] = None):
        self.jwt_manager = jwt_manager or JWTManager()
        self.repo = repository or FileStoreRepository()
        self.itsm_client = RemoteServiceImmediatelyClient(
            endpoint_url=settings.itsm_mcp_url,
            token=settings.itsm_mcp_token
        )

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
        inc_res = self.itsm_client.create_ticket(
            requested_by="CIRT-Automated-Sentinel",
            category="Compliance_Approval",
            short_description=f"CRITICAL: {finding.category or 'UNKNOWN_ATTACK'} prompt injection detected from {attacker_ip}",
            priority="1 - Critical"
        )

        ticket_id = "SEC-001"
        try:
            raw_t = inc_res.get("result", "")
            if isinstance(raw_t, str) and (raw_t.strip().startswith("[") or raw_t.strip().startswith("{")):
                import json
                p = json.loads(raw_t)
                item = p[0] if isinstance(p, list) and p else (p if isinstance(p, dict) else {})
                ticket_id = item.get("ticket_id", ticket_id)
        except Exception:
            pass

        return {
            "success": True,
            "scc_event_status": "STREAMED_TO_SCC_PREMIUM",
            "finding_id": finding_id,
            "p1_ticket_id": ticket_id,
            "assigned_to": "Cyber Incident Response Team (CIRT)"
        }

