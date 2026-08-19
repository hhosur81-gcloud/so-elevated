"""ServiceImmediately ITSM Model Context Protocol (MCP) Server (ADR-0001, ADR-0010, SEC-0005, ENG-0002)."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from src.config.security import JWTManager
from src.repositories.filestore_repository import FileStoreRepository


class ServiceImmediatelyMCPServer:
    """Model Context Protocol (MCP) Enterprise Server for ServiceImmediately ITSM."""

    FILE_PATH = "serviceimmediately/tickets.json"
    IDEMPOTENCY_FILE = "serviceimmediately/idempotency_cache.json"

    VALID_TRANSITIONS = {
        "OPEN": ["IN_PROGRESS", "RESOLVED", "CLOSED"],
        "IN_PROGRESS": ["PENDING_CUSTOMER", "RESOLVED", "CLOSED"],
        "PENDING_CUSTOMER": ["IN_PROGRESS", "RESOLVED", "CLOSED"],
        "RESOLVED": ["IN_PROGRESS", "CLOSED"],
        "CLOSED": []  # Closed tickets cannot be directly reopened without new ticket
    }

    def __init__(self, jwt_manager: Optional[JWTManager] = None, repository: Optional[FileStoreRepository] = None):
        self.jwt_manager = jwt_manager or JWTManager()
        self.repo = repository or FileStoreRepository()

    def _verify_auth(self, bearer_token: str, required_scope: str) -> Optional[Dict[str, Any]]:
        """Verify token signature, expiry, and scope."""
        try:
            claims = self.jwt_manager.verify_token(bearer_token)
        except Exception as e:
            return {"success": False, "error_code": "UNAUTHORIZED", "error": f"Invalid token: {str(e)}"}

        if not self.jwt_manager.has_scope(claims, required_scope):
            return {"success": False, "error_code": "FORBIDDEN", "error": f"Missing required scope: {required_scope}"}

        return None

    def itsm_get_ticket(self, ticket_id: str, bearer_token: str) -> Dict[str, Any]:
        """MCP Tool: Fetch ticket details and timeline comments."""
        auth_err = self._verify_auth(bearer_token, "itsm:read")
        if auth_err:
            return auth_err

        ticket = self.repo.load_record(self.FILE_PATH, ticket_id)
        if not ticket:
            return {"success": False, "error_code": "NOT_FOUND", "error": f"Ticket {ticket_id} not found"}

        return {"success": True, "data": ticket}

    def itsm_create_incident(
        self,
        employee_id: str,
        category: str,
        priority: str,
        title: str,
        description: str,
        bearer_token: str,
        justification: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP Tool: Create an incident with Priority verification guardrail (ADR-0010)."""
        auth_err = self._verify_auth(bearer_token, "itsm:write")
        if auth_err:
            return auth_err

        if idempotency_key:
            cached = self.repo.load_record(self.IDEMPOTENCY_FILE, idempotency_key)
            if cached:
                return cached

        # ADR-0010: Priority Downgrade Guardrail
        assigned_priority = priority.upper()
        downgraded = False
        if assigned_priority == "P1":
            outage_keywords = ["outage", "production down", "critical system", "company-wide", "security breach", "sev1"]
            has_justification = justification and any(k in justification.lower() for k in outage_keywords)
            has_desc_outage = any(k in description.lower() for k in outage_keywords)
            
            if not (has_justification or has_desc_outage):
                assigned_priority = "P3"
                downgraded = True

        ticket_id = f"INC-{uuid.uuid4().hex[:5].upper()}"
        now_str = datetime.now(timezone.utc).isoformat()

        ticket_data = {
            "ticket_id": ticket_id,
            "employee_id": employee_id,
            "category": category,
            "priority": assigned_priority,
            "status": "OPEN",
            "title": title,
            "description": description,
            "created_at": now_str,
            "updated_at": now_str,
            "assigned_to": "IT-Support-L1",
            "comments": [],
            "idempotency_key": idempotency_key,
            "downgraded_from_p1": downgraded
        }

        self.repo.save_record(self.FILE_PATH, ticket_id, ticket_data)

        response = {"success": True, "data": ticket_data}
        if idempotency_key:
            self.repo.save_record(self.IDEMPOTENCY_FILE, idempotency_key, response)

        return response

    def itsm_post_comment(self, ticket_id: str, author: str, comment_text: str, bearer_token: str) -> Dict[str, Any]:
        """MCP Tool: Add a timeline comment to an existing ticket."""
        auth_err = self._verify_auth(bearer_token, "itsm:write")
        if auth_err:
            return auth_err

        ticket = self.repo.load_record(self.FILE_PATH, ticket_id)
        if not ticket:
            return {"success": False, "error_code": "NOT_FOUND", "error": f"Ticket {ticket_id} not found"}

        now_str = datetime.now(timezone.utc).isoformat()
        comment_entry = {
            "author": author,
            "timestamp": now_str,
            "text": comment_text
        }

        def mutate_ticket(data: Dict[str, Any]) -> Dict[str, Any]:
            data.setdefault("comments", []).append(comment_entry)
            data["updated_at"] = now_str
            return data

        updated = self.repo.update_record(self.FILE_PATH, ticket_id, mutate_ticket)
        return {"success": True, "data": updated}

    def itsm_update_status(self, ticket_id: str, new_status: str, bearer_token: str) -> Dict[str, Any]:
        """MCP Tool: Transition ticket lifecycle state."""
        auth_err = self._verify_auth(bearer_token, "itsm:write")
        if auth_err:
            return auth_err

        ticket = self.repo.load_record(self.FILE_PATH, ticket_id)
        if not ticket:
            return {"success": False, "error_code": "NOT_FOUND", "error": f"Ticket {ticket_id} not found"}

        current_status = ticket.get("status", "OPEN")
        allowed = self.VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            return {
                "success": False,
                "error_code": "INVALID_STATE_TRANSITION",
                "error": f"Cannot transition ticket from '{current_status}' to '{new_status}'"
            }

        now_str = datetime.now(timezone.utc).isoformat()

        def mutate_status(data: Dict[str, Any]) -> Dict[str, Any]:
            data["status"] = new_status
            data["updated_at"] = now_str
            return data

        updated = self.repo.update_record(self.FILE_PATH, ticket_id, mutate_status)
        return {"success": True, "data": updated}

    def itsm_create_security_incident(
        self,
        attacker_ip: str,
        finding_category: str,
        forensic_payload: Dict[str, Any],
        bearer_token: str
    ) -> Dict[str, Any]:
        """MCP Tool: Automated Priority 1 Security Incident Creation for CIRT (SEC-0005)."""
        auth_err = self._verify_auth(bearer_token, "itsm:security:write")
        if auth_err:
            return auth_err

        ticket_id = f"SEC-{uuid.uuid4().hex[:5].upper()}"
        now_str = datetime.now(timezone.utc).isoformat()

        sec_ticket = {
            "ticket_id": ticket_id,
            "employee_id": "security-sentinel-gateway",
            "category": "Cybersecurity / Threat Intelligence",
            "priority": "P1",
            "status": "OPEN",
            "title": f"Automated Security Alert: {finding_category} detected",
            "description": f"Model Armor intercepted high-confidence adversarial attack from IP: {attacker_ip}",
            "created_at": now_str,
            "updated_at": now_str,
            "assigned_to": "CIRT-ONCALL",
            "comments": [
                {
                    "author": "SecurityCommandCenter-Eventarc",
                    "timestamp": now_str,
                    "text": f"Forensic payload evidence: {forensic_payload}"
                }
            ]
        }

        self.repo.save_record(self.FILE_PATH, ticket_id, sec_ticket)
        return {"success": True, "data": sec_ticket}
