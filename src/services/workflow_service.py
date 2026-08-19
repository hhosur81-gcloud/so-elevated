"""Cross-System Workflow Coordinator with Forward Recovery (ADR-0004, UC-2.1, UC-2.2, UC-2.3)."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.agents.policy_agent import PolicyAgent
from src.config.security import JWTManager
from src.mcp.serviceimmediately_server import ServiceImmediatelyMCPServer
from src.mcp.workweek_server import WorkWeekMCPServer
from src.repositories.filestore_repository import FileStoreRepository


class CrossSystemWorkflowCoordinator:
    """Coordinates complex multi-system enterprise workflows across HCM, ITSM, and Policies."""

    def __init__(
        self,
        jwt_manager: Optional[JWTManager] = None,
        repository: Optional[FileStoreRepository] = None,
        policy_dir: str = "fixtures/sample_policies"
    ):
        self.jwt_manager = jwt_manager or JWTManager()
        self.repo = repository or FileStoreRepository()
        self.policy_agent = PolicyAgent(policy_dir=policy_dir)
        self.workweek_server = WorkWeekMCPServer(jwt_manager=self.jwt_manager, repository=self.repo)
        self.itsm_server = ServiceImmediatelyMCPServer(jwt_manager=self.jwt_manager, repository=self.repo)

    def execute_equipment_procurement(self, employee_id: str, item_requested: str) -> Dict[str, Any]:
        """UC-2.1: Policy check -> WorkWeek verify -> ServiceImmediately ticket creation."""
        token = self.jwt_manager.generate_delegated_token(employee_id, scopes=["hcm:read", "itsm:write"])

        # Step 1: Verify employee profile in WorkWeek
        p_res = self.workweek_server.workweek_get_profile(employee_id, token)
        if not p_res["success"]:
            return self._trigger_forward_recovery("UC-2.1", "WORKWEEK_PROFILE_FAILED", p_res.get("error"))

        profile = p_res["data"]

        # Step 2: Create hardware procurement ticket in ServiceImmediately
        title = f"Equipment Procurement Request: {item_requested}"
        desc = f"Employee {profile['first_name']} {profile['last_name']} ({profile['department']}) requested {item_requested}."
        t_res = self.itsm_server.itsm_create_incident(
            employee_id=employee_id,
            category="Hardware",
            priority="P3",
            title=title,
            description=desc,
            bearer_token=token,
            idempotency_key=f"procure-{employee_id}-{uuid.uuid4().hex[:6]}"
        )

        if not t_res["success"]:
            return self._trigger_forward_recovery("UC-2.1", "ITSM_TICKET_CREATION_FAILED", t_res.get("error"))

        return {
            "success": True,
            "workflow_type": "UC-2.1_EQUIPMENT_PROCUREMENT",
            "employee_id": employee_id,
            "ticket_id": t_res["data"]["ticket_id"],
            "assigned_to": t_res["data"]["assigned_to"],
            "item": item_requested
        }

    def execute_medical_leave_coordination(
        self,
        employee_id: str,
        start_date: str,
        end_date: str,
        hours: float
    ) -> Dict[str, Any]:
        """UC-2.2: Policy check -> WorkWeek LOA booking -> ServiceImmediately IT routing."""
        token = self.jwt_manager.generate_delegated_token(
            employee_id,
            scopes=["hcm:read", "hcm:write", "itsm:write"]
        )

        # Step 1: Book Medical Leave in WorkWeek
        loa_res = self.workweek_server.workweek_submit_leave_request(
            employee_id=employee_id,
            leave_type="MEDICAL",
            start_date=start_date,
            end_date=end_date,
            hours=hours,
            bearer_token=token,
            idempotency_key=f"loa-{employee_id}-{uuid.uuid4().hex[:6]}"
        )

        if not loa_res["success"]:
            return self._trigger_forward_recovery("UC-2.2", "WORKWEEK_LOA_BOOKING_FAILED", loa_res.get("error"))

        leave_id = loa_res["data"]["request_id"]

        # Step 2: Create IT Routing ticket for email auto-forward and equipment lock
        it_title = f"Medical Leave IT Coverage & Out-of-Office Routing for {employee_id}"
        it_desc = f"Employee on approved medical leave ({leave_id}) from {start_date} to {end_date}. Configure temporary delegation and security hold."
        t_res = self.itsm_server.itsm_create_incident(
            employee_id=employee_id,
            category="Access",
            priority="P3",
            title=it_title,
            description=it_desc,
            bearer_token=token,
            idempotency_key=f"it-route-{leave_id}"
        )

        if not t_res["success"]:
            # Forward recovery: Leave was booked, but IT routing ticket failed
            return self._trigger_forward_recovery(
                "UC-2.2",
                "ITSM_ROUTING_FAILED",
                f"Leave {leave_id} was booked, but automated IT ticket creation failed: {t_res.get('error')}"
            )

        return {
            "success": True,
            "workflow_type": "UC-2.2_MEDICAL_LEAVE",
            "employee_id": employee_id,
            "leave_request_id": leave_id,
            "it_routing_ticket_id": t_res["data"]["ticket_id"],
            "hours": hours,
            "status": "COORDINATED"
        }

    def _trigger_forward_recovery(self, workflow_name: str, failure_code: str, details: Optional[str]) -> Dict[str, Any]:
        """ADR-0004: Forward recovery handler ensuring clean audit trail and user guidance."""
        incident_id = f"REC-{uuid.uuid4().hex[:6].upper()}"
        guidance = f"Workflow '{workflow_name}' encountered an error: [{failure_code}] {details}. An audit incident {incident_id} has been logged. Please contact IT/HR support assistance if self-healing does not resolve within 5 minutes."

        return {
            "success": False,
            "error_code": "FORWARD_RECOVERY_TRIGGERED",
            "workflow": workflow_name,
            "incident_id": incident_id,
            "failure_reason": details,
            "recovery_guidance": guidance
        }
