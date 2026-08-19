"""Integration tests for Cloud Tasks Asynchronous DLQ & Idempotent Worker (ENG-0002, ADR-0004)."""

import os
import shutil
import tempfile
import unittest
from src.repositories.filestore_repository import FileStoreRepository


class TestCloudTasksDLQ(unittest.TestCase):
    """Test suite verifying async task queuing, exponential retries, idempotency, and DLQ routing."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo = FileStoreRepository(base_path=self.temp_dir)
        from src.services.task_queue_service import TaskQueueManager
        self.queue = TaskQueueManager(repository=self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_enqueue_and_process_task_idempotently(self):
        """Verify task execution commits once and caches idempotency key."""
        idemp_key = "idemp-async-001"
        payload = {"employee_id": "EMP-1001", "action": "SYNC_PROFILE"}

        task = self.queue.enqueue_task(
            queue_name="hr-forward-recovery-queue",
            task_name="sync_employee_profile",
            payload=payload,
            idempotency_key=idemp_key
        )
        self.assertEqual(task["status"], "ENQUEUED")

        # Process task
        result = self.queue.process_task(task["task_id"])
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "COMPLETED")

        # Reprocess with same idempotency key -> returns cached result
        res2 = self.queue.process_task(task["task_id"])
        self.assertTrue(res2["success"])
        self.assertTrue(res2.get("is_duplicate_cached", False))

    def test_transient_failure_and_dlq_routing_after_5_retries(self):
        """Verify task failing 5 times is routed to Dead Letter Queue (DLQ) (ENG-0002)."""
        task = self.queue.enqueue_task(
            queue_name="hr-forward-recovery-queue",
            task_name="failing_external_api_call",
            payload={"simulate_network_503": True},
            idempotency_key="idemp-failing-999"
        )

        # Simulate 5 failed retry attempts
        for attempt in range(1, 6):
            res = self.queue.process_task(task["task_id"])
            if attempt < 5:
                self.assertFalse(res["success"])
                self.assertEqual(res["status"], "RETRYING")
                self.assertEqual(res["attempt_count"], attempt)
            else:
                # 5th attempt -> Routed to DLQ
                self.assertFalse(res["success"])
                self.assertEqual(res["status"], "DEAD_LETTERED")
                self.assertIn("DLQ", res["queue"])
                self.assertIn("P2 Cloud Monitoring Alert", res["alert"])


if __name__ == "__main__":
    unittest.main()
