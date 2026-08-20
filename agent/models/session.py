"""Session and Asynchronous Task Models (ENG-0001, ENG-0002, ENG-0004)."""
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import Field
from .workweek import TolerantBaseModel


class SyncTaskPayload(TolerantBaseModel):
    """Asynchronous forward recovery task payload for Cloud Tasks / PubSub DLQ (ENG-0002)."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    idempotency_key: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_name: str
    target_system: str
    action_type: str
    payload: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 5
    created_at: float = Field(default_factory=time.time)
    last_attempt_at: Optional[float] = None
    status: str = "PENDING"  # PENDING, COMPLETED, FAILED, DLQ
    error_message: Optional[str] = None


class AuditLogEntry(TolerantBaseModel):
    """Immutable audit trail record for compliance and debugging."""
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    employee_id: str
    action: str
    target_system: str
    status: str  # SUCCESS, FAILED, REVERTED
    details: Dict[str, Any] = Field(default_factory=dict)


class SessionState(TolerantBaseModel):
    """Conversational session state model."""
    session_id: str
    employee_id: Optional[str] = None
    authenticated: bool = False
    pending_confirmation_action: Optional[Dict[str, Any]] = None
    last_activity: float = Field(default_factory=time.time)
    audit_trail: List[AuditLogEntry] = Field(default_factory=list)
    pending_sync_tasks: List[SyncTaskPayload] = Field(default_factory=list)
