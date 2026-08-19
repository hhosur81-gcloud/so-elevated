"""Session State and Turn History Models (FR-5.1 to FR-5.5, ADR-0007, ADR-0009)."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.models.common import EnterpriseBaseModel


@dataclass
class ConversationTurn(EnterpriseBaseModel):
    """A single turn in the multi-agent conversational dialog."""
    turn_id: str
    user_input: str
    agent_response: str
    acting_agent: str
    tool_invoked: Optional[str] = None
    tool_payload: Optional[Dict[str, Any]] = None
    latency_ms: int = 0
    timestamp: Optional[str] = None


@dataclass
class PendingConfirmation(EnterpriseBaseModel):
    """Encapsulates a pending state mutation requiring employee approval (ADR-0007)."""
    action_type: str  # e.g., "SUBMIT_LEAVE", "CREATE_INCIDENT"
    target_system: str  # "WORKWEEK" or "SERVICEIMMEDIATELY"
    payload: Dict[str, Any]
    prompt_message: str
    created_at: str


@dataclass
class SessionState(EnterpriseBaseModel):
    """Active multi-turn session state for an authenticated employee."""
    session_id: str
    employee_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    pending_confirmation: Optional[PendingConfirmation] = None
    is_revoked: bool = False
    created_at: Optional[str] = None
    last_activity_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        clean = data.copy()
        if "turns" in clean and isinstance(clean["turns"], list):
            clean["turns"] = [
                ConversationTurn.from_dict(t) if isinstance(t, dict) else t
                for t in clean["turns"]
            ]
        if "pending_confirmation" in clean and isinstance(clean["pending_confirmation"], dict):
            clean["pending_confirmation"] = PendingConfirmation.from_dict(clean["pending_confirmation"])
        return super().from_dict(clean)
