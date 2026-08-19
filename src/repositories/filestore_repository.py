"""Atomic FileStore Repository with Linux kernel file locking (fcntl.flock) (Q1 & Q5)."""

import fcntl
import json
import os
import tempfile
from typing import Any, Callable, Dict, Optional
from src.config.settings import settings


class FileStoreRepository:
    """Atomic, thread-safe, and process-safe FileStore data persistence."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or settings.filestore_base_path
        os.makedirs(self.base_path, exist_ok=True)

    def _get_full_path(self, relative_file_path: str) -> str:
        """Resolve full filesystem path for a relative FileStore path."""
        full_path = os.path.join(self.base_path, relative_file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return full_path

    def load_all(self, relative_file_path: str) -> Dict[str, Any]:
        """Load all JSON records from a file with shared read-lock."""
        full_path = self._get_full_path(relative_file_path)
        if not os.path.exists(full_path):
            return {}

        with open(full_path, "r", encoding="utf-8") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_SH)
                content = f.read()
                return json.loads(content) if content.strip() else {}
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def load_record(self, relative_file_path: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Load a single record by primary key ID."""
        data = self.load_all(relative_file_path)
        return data.get(record_id)

    def save_record(self, relative_file_path: str, record_id: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or overwrite a record atomically using write-and-replace with exclusive lock."""
        full_path = self._get_full_path(relative_file_path)
        dir_name = os.path.dirname(full_path)

        # Lock file
        lock_file_path = f"{full_path}.lock"
        with open(lock_file_path, "w") as lock_f:
            fcntl.flock(lock_f, fcntl.LOCK_EX)
            try:
                current_data = {}
                if os.path.exists(full_path):
                    with open(full_path, "r", encoding="utf-8") as read_f:
                        c = read_f.read()
                        current_data = json.loads(c) if c.strip() else {}

                current_data[record_id] = record_data

                # Write to temp file in same directory
                with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tmp_f:
                    json.dump(current_data, tmp_f, indent=2)
                    tmp_name = tmp_f.name

                # Atomic replace
                os.replace(tmp_name, full_path)
                return record_data
            finally:
                fcntl.flock(lock_f, fcntl.LOCK_UN)

    def update_record(
        self,
        relative_file_path: str,
        record_id: str,
        mutate_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Atomically mutate an existing record within an exclusive write lock."""
        full_path = self._get_full_path(relative_file_path)
        dir_name = os.path.dirname(full_path)

        lock_file_path = f"{full_path}.lock"
        with open(lock_file_path, "w") as lock_f:
            fcntl.flock(lock_f, fcntl.LOCK_EX)
            try:
                current_data = {}
                if os.path.exists(full_path):
                    with open(full_path, "r", encoding="utf-8") as read_f:
                        c = read_f.read()
                        current_data = json.loads(c) if c.strip() else {}

                if record_id not in current_data:
                    raise KeyError(f"Record with ID '{record_id}' not found in {relative_file_path}")

                updated_record = mutate_fn(current_data[record_id])
                current_data[record_id] = updated_record

                with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tmp_f:
                    json.dump(current_data, tmp_f, indent=2)
                    tmp_name = tmp_f.name

                os.replace(tmp_name, full_path)
                return updated_record
            finally:
                fcntl.flock(lock_f, fcntl.LOCK_UN)
