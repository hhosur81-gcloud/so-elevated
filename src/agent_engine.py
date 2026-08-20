"""Vertex AI Agent Engine / Reasoning Engine Module for So-Elevated HR Assistant & Dedicated Sub-Agents."""

import os
import sys
from typing import Any, Dict, List, Optional

# Ensure path is configured
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.agents.itsm_agent import ITSMAgent
from src.agents.orchestrator_agent import PrimaryHROrchestrator
from src.agents.policy_agent import PolicyAgent
from src.agents.workweek_agent import WorkWeekAgent
from src.config.settings import settings
from src.repositories.filestore_repository import FileStoreRepository
from src.services.canary_service import ContinuousSyntheticCanary


class SoElevatedHRAgentEngine:
    """Root Vertex AI Managed Agent Engine / Reasoning Engine entrypoint.
    
    Adheres to Vertex AI Reasoning Engine lifecycle standard (set_up, query, stream_query).
    """

    def __init__(
        self,
        project_id: str = "no-vibing-here",
        location: str = "us-central1",
        model: str = "gemini-3.7-flash"
    ):
        self.project_id = project_id
        self.location = location
        self.model = model
        self.orchestrator: Optional[PrimaryHROrchestrator] = None
        self.canary: Optional[ContinuousSyntheticCanary] = None

    def set_up(self):
        """Initializes agents, policy knowledge base, and FastMCP connectors upon runtime startup."""
        policy_dir = "knowledge" if os.path.exists("knowledge") else "fixtures/sample_policies"
        self.canary = ContinuousSyntheticCanary(policy_dir=policy_dir)
        self.orchestrator = self.canary.orchestrator

    def query(
        self,
        message: str,
        employee_id: str = "EMP-436",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Processes a conversational turn through the root orchestrator and specialist sub-agents."""
        if self.orchestrator is None:
            self.set_up()

        sess_id = session_id or f"agent-engine-sess-{employee_id}"
        return self.orchestrator.process_turn(
            session_id=sess_id,
            employee_id=employee_id,
            user_message=message
        )

    def reset_session(self, employee_id: str, session_id: str) -> Dict[str, Any]:
        """Explicitly purges conversational session context from Agent Engine memory."""
        if self.orchestrator is None:
            self.set_up()
        return self.orchestrator.process_turn(
            session_id=session_id,
            employee_id=employee_id,
            user_message="reset session"
        )

    def health_check(self) -> Dict[str, Any]:
        """Returns deep subsystem health and readiness metrics."""
        if self.canary is None:
            self.set_up()
        status = self.canary.get_health_status()
        status["runtime"] = "Vertex AI Agent Engine (Managed Reasoning Engine)"
        status["project_id"] = self.project_id
        status["location"] = self.location
        status["model"] = self.model
        return status


class WorkWeekAgentEngine:
    """Dedicated Vertex AI Reasoning Engine runtime for WorkWeek HCM Agent."""

    def __init__(self, project_id: str = "no-vibing-here", location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.agent: Optional[WorkWeekAgent] = None

    def set_up(self):
        self.agent = WorkWeekAgent(repository=FileStoreRepository())

    def query(self, message: str, employee_id: str = "EMP-436") -> Dict[str, Any]:
        """Process HCM time-off and leave balance queries."""
        if self.agent is None:
            self.set_up()
        lowered = message.lower().strip()
        if "balance" in lowered:
            return self.agent.get_balances(employee_id)
        return self.agent.process_leave_intent(message, employee_id)

    def execute_leave(self, employee_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute state mutation to live WorkWeek server."""
        if self.agent is None:
            self.set_up()
        return self.agent.execute_confirmed_leave(employee_id, payload)


class ITSMAgentEngine:
    """Dedicated Vertex AI Reasoning Engine runtime for ITSM ServiceImmediately Agent."""

    def __init__(self, project_id: str = "no-vibing-here", location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.agent: Optional[ITSMAgent] = None

    def set_up(self):
        self.agent = ITSMAgent(repository=FileStoreRepository())

    def query(self, message: str, employee_id: str = "EMP-436", policy_guidance: str = "") -> Dict[str, Any]:
        """Process ITSM ticketing and support operations."""
        if self.agent is None:
            self.set_up()
        lowered = message.lower().strip()
        if "ticket" in lowered and any(w in lowered for w in ["list", "show", "my", "open", "view", "track", "status"]):
            return self.agent.lookup_tickets(message, employee_id)
        return self.agent.create_ticket(message, employee_id, policy_guidance=policy_guidance)


class PolicyAgentEngine:
    """Dedicated Vertex AI Reasoning Engine runtime for Policy Specialist Agent."""

    def __init__(self, project_id: str = "no-vibing-here", location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.agent: Optional[PolicyAgent] = None

    def set_up(self):
        policy_dir = "knowledge" if os.path.exists("knowledge") else "fixtures/sample_policies"
        self.agent = PolicyAgent(policy_dir=policy_dir)

    def query(self, message: str, employee_role: str = "Employee") -> Dict[str, Any]:
        """Process policy Q&A query with citation grounding."""
        if self.agent is None:
            self.set_up()
        return self.agent.answer_policy_query(message, employee_role=employee_role)
