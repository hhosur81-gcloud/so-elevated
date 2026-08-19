"""Integration tests for Continuous Synthetic Canary & Dual-Region Health Probes (SEC-0004, ENG-0006)."""

import os
import shutil
import tempfile
import unittest
from src.config.security import JWTManager
from src.repositories.filestore_repository import FileStoreRepository


class TestSyntheticCanary(unittest.TestCase):
    """Test suite verifying 24/7 continuous canaries on EMP-CANARY-01 and /healthz endpoint."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.jwt_manager = JWTManager()
        self.repo = FileStoreRepository(base_path=self.temp_dir)

        # Seed EMP-CANARY-01
        self.repo.save_record("workweek/employees.json", "EMP-CANARY-01", {
            "employee_id": "EMP-CANARY-01",
            "first_name": "Synthetic",
            "last_name": "Canary",
            "email": "synthetic.canary@enterprise.com",
            "department": "Engineering",
            "role": "Reliability Canary",
            "pto_balance_hours": 200.0,
            "sick_leave_hours": 40.0,
            "leave_requests": []
        })

        from src.services.canary_service import ContinuousSyntheticCanary
        self.canary = ContinuousSyntheticCanary(
            jwt_manager=self.jwt_manager,
            repository=self.repo,
            policy_dir="fixtures/sample_policies"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_deep_health_check_endpoint(self):
        """Verify /healthz returns deep subsystem readiness for Global Load Balancer (SEC-0004)."""
        health = self.canary.get_health_status()

        self.assertEqual(health["status"], "HEALTHY")
        self.assertIn("us-central1", health["region"])
        self.assertEqual(health["components"]["model_armor"], "OK")
        self.assertEqual(health["components"]["policy_search"], "OK")
        self.assertEqual(health["components"]["workweek_mcp"], "OK")
        self.assertEqual(health["components"]["itsm_mcp"], "OK")
        self.assertEqual(health["components"]["filestore"], "OK")

    def test_synthetic_canary_probe_execution(self):
        """Verify synthetic probe executes full 3-step transaction and exports SLA metrics (ENG-0006)."""
        probe_res = self.canary.run_synthetic_probe()

        self.assertTrue(probe_res["success"])
        self.assertEqual(probe_res["canary_id"], "EMP-CANARY-01")
        self.assertEqual(probe_res["steps_completed"], 3)
        self.assertTrue(probe_res["total_latency_ms"] < 2500.0)

        # Verify metrics written to monitoring store
        metrics = self.repo.load_all("monitoring/canary_metrics.json")
        self.assertTrue(len(metrics) >= 1)


if __name__ == "__main__":
    unittest.main()
