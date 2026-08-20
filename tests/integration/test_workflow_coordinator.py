"""Integration tests for Cross-System Workflow Coordination & Forward Recovery (ADR-0004, UC-2.1, UC-2.2, UC-2.3)."""

import os
import shutil
import tempfile
import unittest
from src.config.security import JWTManager
from src.repositories.filestore_repository import FileStoreRepository


class TestWorkflowCoordinator(unittest.TestCase):
    """Test suite verifying cross-system workflows across Policy, WorkWeek, and ITSM."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.jwt_manager = JWTManager()
        self.repo = FileStoreRepository(base_path=self.temp_dir)

        # Seed employee Jane Doe
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

        from src.services.workflow_service import CrossSystemWorkflowCoordinator
        self.coordinator = CrossSystemWorkflowCoordinator(
            jwt_manager=self.jwt_manager,
            repository=self.repo,
            policy_dir="fixtures/sample_policies"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_uc21_equipment_procurement_workflow(self):
        """Verify UC-2.1: Policy check -> WorkWeek verify -> ServiceImmediately ticket creation."""
        res = self.coordinator.execute_equipment_procurement(
            employee_id="EMP-436",
            item_requested="Dual 27-inch 4K Monitors"
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["workflow_type"], "UC-2.1_EQUIPMENT_PROCUREMENT")
        self.assertTrue(res["ticket_id"].startswith("INC"))
        self.assertEqual(res["assigned_to"], "Service Desk")

    def test_uc22_medical_leave_coordination(self):
        """Verify UC-2.2: Policy check -> WorkWeek LOA booking -> ServiceImmediately IT routing."""
        res = self.coordinator.execute_medical_leave_coordination(
            employee_id="EMP-436",
            start_date="2026-09-01",
            end_date="2026-09-14",
            hours=80.0
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["workflow_type"], "UC-2.2_MEDICAL_LEAVE")
        self.assertTrue(res["leave_request_id"].startswith("LOA-"))
        self.assertTrue(res["it_routing_ticket_id"].startswith("INC"))


    def test_forward_recovery_on_downstream_failure(self):
        """Verify forward recovery creates compensation alert on downstream failure (ADR-0004)."""
        from unittest.mock import patch
        with patch.object(self.coordinator.workweek_client, "request_time_off", return_value={"success": False, "error": "Downstream timeout"}):
            res = self.coordinator.execute_medical_leave_coordination(
                employee_id="EMP-436",
                start_date="2026-09-01",
                end_date="2026-09-14",
                hours=80.0
            )

            self.assertFalse(res["success"])
            self.assertEqual(res["error_code"], "FORWARD_RECOVERY_TRIGGERED")
            self.assertIn("support assistance", res["recovery_guidance"].lower())



if __name__ == "__main__":
    unittest.main()
