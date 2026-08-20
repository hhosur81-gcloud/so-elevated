"""Unit tests verifying Idempotent Key generation and Forward Recovery Tasks (ENG-0002)."""
from agent.services.workflow_service import WorkflowService


def test_idempotency_key_generation():
    """Verify unique UUIDv4 generation with custom prefixes."""
    key1 = WorkflowService.generate_idempotency_key("leave")
    key2 = WorkflowService.generate_idempotency_key("leave")
    
    assert key1.startswith("leave-")
    assert key2.startswith("leave-")
    assert key1 != key2


def test_medical_leave_sync_task_structure():
    """Verify forward recovery sync task payload complies with queue schema."""
    task = WorkflowService.build_medical_leave_sync_task(
        employee_id="EMP1001",
        start_date="2026-08-24",
        end_date="2026-08-28",
        leave_type="Outpatient Sick",
        days=5.0,
    )
    assert task.workflow_name == "UC-2.2-Medical-Leave"
    assert task.target_system == "ServiceImmediately_ITSM"
    assert task.action_type == "create_ticket"
    assert task.status == "PENDING"
    assert task.retry_count == 0
    assert task.max_retries == 5
    assert task.idempotency_key.startswith("itsm-med-")
    assert task.payload["requested_by"] == "EMP1001"
