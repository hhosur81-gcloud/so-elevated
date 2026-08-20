"""Vertex AI Agent Engine / Reasoning Engine Module for So-Elevated HR Assistant."""

import os
import sys
from typing import Any, Dict, List, Optional

# Ensure path is configured
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.agents.orchestrator_agent import PrimaryHROrchestrator
from src.config.settings import settings
from src.services.canary_service import ContinuousSyntheticCanary


class SoElevatedHRAgentEngine:
    """Vertex AI Managed Agent Engine / Reasoning Engine entrypoint.
    
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
        """Processes a single conversational turn in the Vertex AI Agent Engine runtime.
        
        Args:
            message: The user's prompt or action.
            employee_id: Authenticated employee identifier.
            session_id: Session identifier for 15m TTL context.
            
        Returns:
            Dict containing response text, success status, and turn metadata.
        """
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
