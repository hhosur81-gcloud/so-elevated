"""Unit tests verifying Deterministic Idempotency & Deduplication Engine (ENG-0002)."""
from pathlib import Path
from agent.services.idempotency_store import IdempotencyStore


def test_deterministic_hashing():
    """Verify exact same parameters generate identical hash keys."""
    params1 = {"leave_type": "Vacation", "days": 3, "start_date": "2026-09-01"}
    params2 = {"days": 3, "start_date": "2026-09-01", "leave_type": "Vacation"}  # Different key order

    key1 = IdempotencyStore.generate_key("session_123", "request_time_off", params1)
    key2 = IdempotencyStore.generate_key("session_123", "request_time_off", params2)

    assert key1 == key2  # Order-independent deterministic hash


def test_idempotency_store_lifecycle(tmp_path: Path):
    """Verify lock acquisition, completion caching, and duplicate interception."""
    db_file = tmp_path / "test_idempotency.db"
    store = IdempotencyStore(db_file)

    params = {"employee_id": "EMP1001", "days": 2.0, "leave_type": "Sick"}
    key = store.generate_key("sess_01", "request_time_off", params)

    # 1. First attempt: Acquires lock (NEW)
    status, payload = store.get_or_lock(key, "request_time_off", params)
    assert status == "NEW"
    assert payload is None

    # 2. Concurrent second attempt while in progress: Blocked (IN_PROGRESS)
    status2, payload2 = store.get_or_lock(key, "request_time_off", params)
    assert status2 == "IN_PROGRESS"

    # 3. First attempt succeeds: Mark COMPLETED
    receipt = {"receipt_id": "WW-8902", "status": "APPROVED", "days_deducted": 2.0}
    store.complete(key, receipt)

    # 4. Subsequent retry (e.g. user refreshed browser / replayed turn):
    # Returns cached response with 0 downstream execution
    status3, payload3 = store.get_or_lock(key, "request_time_off", params)
    assert status3 == "COMPLETED"
    assert payload3 == receipt
    assert payload3["receipt_id"] == "WW-8902"
