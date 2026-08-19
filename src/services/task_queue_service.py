"""Cloud Tasks / PubSub Asynchronous DLQ & Idempotent Worker (ENG-0002, ADR-0004)."""

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.repositories.filestore_repository import FileStoreRepository


class TaskQueueManager:
    """Manages asynchronous task dispatch, exponential backoff retries, and Dead Letter Queueing."""

    TASKS_FILE = "queue/tasks.json"
    DLQ_FILE = "queue/dead_letter_queue.json"
    IDEMPOTENCY_TABLE = "queue/idempotency_table.json"
    MAX_RETRIES = 5

    def __init__(self, repository: Optional[FileStoreRepository] = None):
        self.repo = repository or FileStoreRepository()

    def enqueue_task(
        self,
        queue_name: str,
        task_name: str,
        payload: Dict[str, Any],
        idempotency_key: str
    ) -> Dict[str, Any]:
        """Enqueue a background task with unique ID and Idempotency-Key."""
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        task_record = {
            "task_id": task_id,
            "queue_name": queue_name,
            "task_name": task_name,
            "payload": payload,
            "idempotency_key": idempotency_key,
            "status": "ENQUEUED",
            "attempt_count": 0,
            "max_retries": self.MAX_RETRIES,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        self.repo.save_record(self.TASKS_FILE, task_id, task_record)
        return task_record

    def process_task(self, task_id: str) -> Dict[str, Any]:
        """Worker execution loop with exponential retry handling and DLQ escalation."""
        task = self.repo.load_record(self.TASKS_FILE, task_id)
        if not task:
            return {"success": False, "error": f"Task {task_id} not found"}

        idemp_key = task["idempotency_key"]

        # Check Idempotency Table
        cached_result = self.repo.load_record(self.IDEMPOTENCY_TABLE, idemp_key)
        if cached_result and cached_result.get("status") == "COMPLETED":
            return {
                "success": True,
                "status": "COMPLETED",
                "is_duplicate_cached": True,
                "data": cached_result.get("output")
            }

        # Simulate execution
        payload = task.get("payload", {})
        is_failing = payload.get("simulate_network_503", False)

        task["attempt_count"] += 1
        now_str = datetime.now(timezone.utc).isoformat()
        task["updated_at"] = now_str

        if is_failing:
            if task["attempt_count"] >= self.MAX_RETRIES:
                # Exceeded max retries -> Move to Dead Letter Queue (DLQ)
                task["status"] = "DEAD_LETTERED"
                self.repo.save_record(self.TASKS_FILE, task_id, task)

                dlq_record = task.copy()
                dlq_record["dead_lettered_at"] = now_str
                dlq_record["alert"] = "P2 Cloud Monitoring Alert: Asynchronous task failed 5 retries. Escalated to on-call engineer."
                self.repo.save_record(self.DLQ_FILE, task_id, dlq_record)

                return {
                    "success": False,
                    "status": "DEAD_LETTERED",
                    "queue": "DLQ_hr-forward-recovery-dlq",
                    "alert": dlq_record["alert"],
                    "attempt_count": task["attempt_count"]
                }
            else:
                # Increment retry count
                task["status"] = "RETRYING"
                # Backoff: 2^(attempt-1) seconds
                task["next_retry_delay_sec"] = 2 ** (task["attempt_count"] - 1)
                self.repo.save_record(self.TASKS_FILE, task_id, task)

                return {
                    "success": False,
                    "status": "RETRYING",
                    "attempt_count": task["attempt_count"],
                    "next_retry_delay_sec": task["next_retry_delay_sec"]
                }

        # Successful execution
        task["status"] = "COMPLETED"
        self.repo.save_record(self.TASKS_FILE, task_id, task)

        # Cache completed execution in idempotency table
        output_data = {"processed_at": now_str, "result": "SYNC_SUCCESSFUL"}
        self.repo.save_record(self.IDEMPOTENCY_TABLE, idemp_key, {
            "idempotency_key": idemp_key,
            "status": "COMPLETED",
            "task_id": task_id,
            "output": output_data
        })

        return {
            "success": True,
            "status": "COMPLETED",
            "task_id": task_id,
            "data": output_data
        }
