"""Unit tests for dedicated WorkWeekAgent and ITSMAgent specialist sub-agents (ADK Pattern)."""

import tempfile
import unittest
from src.agents.itsm_agent import ITSMAgent
from src.agents.workweek_agent import WorkWeekAgent
from src.repositories.filestore_repository import FileStoreRepository


class TestDedicatedAgents(unittest.TestCase):
    """Test suite verifying modular specialist agent contracts."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo = FileStoreRepository(base_path=self.temp_dir)
        self.workweek_agent = WorkWeekAgent(repository=self.repo)
        self.itsm_agent = ITSMAgent(repository=self.repo)

    def test_workweek_natural_dates_parsing(self):
        """Verify multi-format natural language date parsing."""
        d1 = self.workweek_agent.parse_natural_dates("I need PTO on 2026-09-16")
        self.assertEqual(d1, ["2026-09-16"])

        d2 = self.workweek_agent.parse_natural_dates("taking off 16 sep to 18 sep")
        self.assertEqual(d2, ["2026-09-16", "2026-09-18"])

        d3 = self.workweek_agent.parse_natural_dates("starting 16th september")
        self.assertEqual(d3, ["2026-09-16"])

    def test_workweek_duration_parsing(self):
        """Verify hours, days, and weeks duration conversions."""
        h1, s1 = self.workweek_agent.parse_duration("16 hours from 16 sep")
        self.assertEqual(h1, 16.0)
        self.assertEqual(s1, 2)

        h2, s2 = self.workweek_agent.parse_duration("3 days from 16 sep")
        self.assertEqual(h2, 24.0)
        self.assertEqual(s2, 3)

        h3, s3 = self.workweek_agent.parse_duration("2 weeks from 16 sep 2026")
        self.assertEqual(h3, 80.0)
        self.assertEqual(s3, 14)

    def test_workweek_process_leave_intent_missing_details(self):
        """Verify elicitation prompt when details are omitted."""
        res = self.workweek_agent.process_leave_intent("I want to request PTO", "EMP-436")
        self.assertFalse(res["requires_confirmation"])
        self.assertIn("How many hours or days", res["response"])

    def test_workweek_process_leave_intent_full_details(self):
        """Verify confirmation gate generation when all parameters are resolved."""
        res = self.workweek_agent.process_leave_intent("2 weeks from 16 sep 2026", "EMP-436")
        self.assertTrue(res["requires_confirmation"])
        self.assertIn("80.0 hours of PTO from 2026-09-16 to 2026-09-29", res["response"])
        self.assertEqual(res["pending_confirmation"].payload["hours"], 80.0)

    def test_itsm_category_classification(self):
        """Verify accurate categorization across Hardware, Access, Compliance, and Operations."""
        self.assertEqual(self.itsm_agent.classify_category("my laptop screen is broken"), "Hardware")
        self.assertEqual(self.itsm_agent.classify_category("cannot connect to vpn"), "Access_Network")
        self.assertEqual(self.itsm_agent.classify_category("approval for vendor gift over $500"), "Compliance_Approval")
        self.assertEqual(self.itsm_agent.classify_category("question about onboarding benefits"), "HR_Operations")

    def test_itsm_priority_downgrade_guardrail(self):
        """Verify ADR-0010 priority downgrade without active major outage."""
        # Case A: Requesting P1 for laptop -> Downgraded to P3
        p_code, p_label, notice = self.itsm_agent.evaluate_priority("need loaner macbook with priority 1 critical")
        self.assertEqual(p_code, "P3")
        self.assertEqual(p_label, "3 - Moderate")
        self.assertIn("ADR-0010", notice)

        # Case B: Requesting P1 during major production outage -> Retained P1
        p_code2, p_label2, notice2 = self.itsm_agent.evaluate_priority("major outage production down sev1")
        self.assertEqual(p_code2, "P1")
        self.assertEqual(p_label2, "1 - Critical")
        self.assertEqual(notice2, "")


if __name__ == "__main__":
    unittest.main()
