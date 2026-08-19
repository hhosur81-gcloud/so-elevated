"""Integration tests for WorkWeek HCM MCP Server (ADR-0001, ADR-0006, ENG-0001, ENG-0002)."""

import os
import shutil
import tempfile
import unittest
from src.config.security import JWTManager
from src.repositories.filestore_repository import FileStoreRepository


class TestWorkWeekMCPServer(unittest.TestCase):
    """Test suite verifying WorkWeek MCP tools, JWT verification, and FileStore mutations."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.jwt_manager = JWTManager()
        self.repo = FileStoreRepository(base_path=self.temp_dir)

        # Seed employee EMP-1001
        self.repo.save_record("workweek/employees.json", "EMP-1001", {
            "employee_id": "EMP-1001",
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@enterprise.com",
            "department": "Engineering",
            "role": "Senior Cloud Engineer",
            "pto_balance_hours": 120.0,
            "sick_leave_hours": 40.0,
            "leave_requests": []
        })

        from src.mcp.workweek_server import WorkWeekMCPServer
        self.server = WorkWeekMCPServer(jwt_manager=self.jwt_manager, repository=self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_profile_with_valid_jwt(self):
        """Verify profile lookup succeeds with valid signed JWT."""
        token = self.jwt_manager.generate_delegated_token("EMP-1001", scopes=["hcm:read"])
        res = self.server.workweek_get_profile("EMP-1001", token)

        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["first_name"], "Jane")
        self.assertEqual(res["data"]["department"], "Engineering")

    def test_get_profile_rejects_unauthorized_token(self):
        """Verify profile lookup rejects token belonging to a different employee."""
        token = self.jwt_manager.generate_delegated_token("EMP-1002", scopes=["hcm:read"])
        res = self.server.workweek_get_profile("EMP-1001", token)

        self.assertFalse(res["success"])
        self.assertEqual(res["error_code"], "FORBIDDEN")

    def test_get_pto_balances(self):
        """Verify PTO balance query returns accrued hours."""
        token = self.jwt_manager.generate_delegated_token("EMP-1001", scopes=["hcm:read"])
        res = self.server.workweek_get_pto_balances("EMP-1001", token)

        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["pto_balance_hours"], 120.0)
        self.assertEqual(res["data"]["sick_leave_hours"], 40.0)

    def test_submit_leave_request_deducts_balance(self):
        """Verify leave booking updates balance and adds leave record."""
        token = self.jwt_manager.generate_delegated_token("EMP-1001", scopes=["hcm:write"])
        res = self.server.workweek_submit_leave_request(
            employee_id="EMP-1001",
            leave_type="PTO",
            start_date="2026-09-01",
            end_date="2026-09-03",
            hours=24.0,
            bearer_token=token,
            idempotency_key="req-12345"
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["status"], "CONFIRMED")
        self.assertEqual(res["data"]["remaining_pto_hours"], 96.0)

        # Verify in FileStore
        profile = self.repo.load_record("workweek/employees.json", "EMP-1001")
        self.assertEqual(profile["pto_balance_hours"], 96.0)
        self.assertEqual(len(profile["leave_requests"]), 1)

    def test_submit_leave_rejects_insufficient_balance(self):
        """Verify leave booking fails if requested hours exceed accrued balance."""
        token = self.jwt_manager.generate_delegated_token("EMP-1001", scopes=["hcm:write"])
        res = self.server.workweek_submit_leave_request(
            employee_id="EMP-1001",
            leave_type="PTO",
            start_date="2026-09-01",
            end_date="2026-09-30",
            hours=200.0,  # Only 120 available
            bearer_token=token
        )

        self.assertFalse(res["success"])
        self.assertEqual(res["error_code"], "INSUFFICIENT_BALANCE")

    def test_submit_leave_idempotency_deduplication(self):
        """Verify duplicate leave submissions with identical Idempotency-Key return cached response."""
        token = self.jwt_manager.generate_delegated_token("EMP-1001", scopes=["hcm:write"])
        res1 = self.server.workweek_submit_leave_request(
            employee_id="EMP-1001",
            leave_type="PTO",
            start_date="2026-09-01",
            end_date="2026-09-02",
            hours=16.0,
            bearer_token=token,
            idempotency_key="idemp-key-999"
        )
        self.assertTrue(res1["success"])
        self.assertEqual(res1["data"]["remaining_pto_hours"], 104.0)

        # Resend duplicate request
        res2 = self.server.workweek_submit_leave_request(
            employee_id="EMP-1001",
            leave_type="PTO",
            start_date="2026-09-01",
            end_date="2026-09-02",
            hours=16.0,
            bearer_token=token,
            idempotency_key="idemp-key-999"
        )
        self.assertTrue(res2["success"])
        self.assertEqual(res2["data"]["remaining_pto_hours"], 104.0)  # NOT deducted twice!

        profile = self.repo.load_record("workweek/employees.json", "EMP-1001")
        self.assertEqual(profile["pto_balance_hours"], 104.0)


if __name__ == "__main__":
    unittest.main()
