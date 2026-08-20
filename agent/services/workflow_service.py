"""Cross-System Workflow Service with In-Process Retries & Idempotency (ENG-0002, ENG-0003)."""
import json
import logging
import uuid
from typing import Any, Callable, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from ..models.session import SyncTaskPayload
    from .idempotency_store import IdempotencyStore
except (ImportError, ValueError):
    from models.session import SyncTaskPayload
    from services.idempotency_store import IdempotencyStore

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service layer orchestrating cross-system workflows with in-process resilience."""

    @staticmethod
    def generate_idempotency_key(prefix: str = "req") -> str:
        """Generate a unique idempotency key with custom prefix."""
        return f"{prefix}-{uuid.uuid4()}"

    @staticmethod
    def generate_deterministic_key(session_id: str, action: str, params: Dict[str, Any]) -> str:
        """Generate a deterministic SHA-256 idempotency key."""
        return IdempotencyStore.generate_key(session_id, action, params)

    @staticmethod
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        reraise=True,
    )
    def execute_with_fast_retry(call_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Executes a downstream tool call with fast in-turn retry (up to 2 attempts)."""
        return call_fn(*args, **kwargs)

    @staticmethod
    def build_medical_leave_sync_task(
        employee_id: str,
        start_date: str,
        end_date: str,
        leave_type: str,
        days: float,
        reason: str = "Medical Leave of Absence Out-of-Office Routing"
    ) -> SyncTaskPayload:
        """Construct a task payload for auxiliary ITSM out-of-office ticket creation."""
        idempotency_key = WorkflowService.generate_idempotency_key("itsm-med")
        return SyncTaskPayload(
            idempotency_key=idempotency_key,
            workflow_name="UC-2.2-Medical-Leave",
            target_system="ServiceImmediately_ITSM",
            action_type="create_ticket",
            payload={
                "requested_by": employee_id,
                "category": "HR Service Desk",
                "short_description": f"{reason} ({start_date} to {end_date})",
                "priority": "3 - Medium",
                "assignment_group": "HR Operations",
            },
        )
