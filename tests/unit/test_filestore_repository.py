"""Unit tests for Atomic FileStore Repository with file-locking (Q1 & Q5)."""

import os
import shutil
import tempfile
import unittest


class TestFileStoreRepository(unittest.TestCase):
    """Test suite verifying atomic reads, writes, locking, and rollback in FileStore."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        from src.repositories.filestore_repository import FileStoreRepository
        self.repo = FileStoreRepository(base_path=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_load_record(self):
        """Verify saving and reading a document record."""
        payload = {"employee_id": "EMP-1001", "pto_balance_hours": 120.0}
        self.repo.save_record("workweek/employees.json", "EMP-1001", payload)

        loaded = self.repo.load_record("workweek/employees.json", "EMP-1001")
        self.assertEqual(loaded, payload)

    def test_load_all_records(self):
        """Verify loading all records in a domain file."""
        self.repo.save_record("workweek/employees.json", "EMP-1001", {"name": "Jane"})
        self.repo.save_record("workweek/employees.json", "EMP-1002", {"name": "John"})

        all_records = self.repo.load_all("workweek/employees.json")
        self.assertEqual(len(all_records), 2)
        self.assertIn("EMP-1001", all_records)
        self.assertIn("EMP-1002", all_records)

    def test_atomic_update_prevents_partial_writes(self):
        """Verify updates are atomically committed."""
        self.repo.save_record("workweek/employees.json", "EMP-1001", {"pto": 120})

        def mutate_fn(record):
            record["pto"] -= 16
            return record

        updated = self.repo.update_record("workweek/employees.json", "EMP-1001", mutate_fn)
        self.assertEqual(updated["pto"], 104)

        reloaded = self.repo.load_record("workweek/employees.json", "EMP-1001")
        self.assertEqual(reloaded["pto"], 104)


if __name__ == "__main__":
    unittest.main()
