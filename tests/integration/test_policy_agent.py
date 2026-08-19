"""Integration tests for Policy Q&A Specialist Agent & Search Retrieval (ADR-0002, ADR-0008, ENG-0005)."""

import os
import unittest


class TestPolicyAgent(unittest.TestCase):
    """Test suite verifying policy question answering, deep-link citations, and ACL filtering."""

    def setUp(self):
        from src.agents.policy_agent import PolicyAgent
        self.policy_agent = PolicyAgent(policy_dir="fixtures/sample_policies")

    def test_policy_query_grounded_answer_with_citation(self):
        """Verify bereavement leave question returns factual answer with clickable citation."""
        query = "How many days of bereavement leave do I get for immediate family?"
        res = self.policy_agent.answer_policy_query(query, employee_role="Employee")

        self.assertTrue(res["success"])
        self.assertIn("5", res["answer"])
        self.assertIn("paid", res["answer"].lower())
        self.assertIn("https://intranet.company.com/policies/hr-2026-leave.pdf", res["citation_url"])
        self.assertIn("Section 3.2", res["citation_label"])

    def test_semantic_cache_hit_latency(self):
        """Verify second identical semantic query hits cache in < 50ms (ENG-0005)."""
        query = "What is the parental leave duration?"
        
        # Turn 1: Fresh retrieval
        res1 = self.policy_agent.answer_policy_query(query, employee_role="Employee")
        self.assertTrue(res1["success"])
        self.assertFalse(res1.get("cache_hit", False))

        # Turn 2: Cache hit
        res2 = self.policy_agent.answer_policy_query(query, employee_role="Employee")
        self.assertTrue(res2["success"])
        self.assertTrue(res2.get("cache_hit", False))
        self.assertTrue(res2["latency_ms"] < 50.0)

    def test_query_time_vector_acl_filtering(self):
        """Verify non-executive employee is blocked from accessing restricted executive policies."""
        query = "What are the executive severance multipliers?"
        
        # Non-executive role
        res_emp = self.policy_agent.answer_policy_query(query, employee_role="Employee")
        self.assertFalse(res_emp["has_policy_match"])
        self.assertIn("not covered in our current published company policies", res_emp["answer"])

        # Executive role
        res_exec = self.policy_agent.answer_policy_query(query, employee_role="Executive")
        self.assertTrue(res_exec["has_policy_match"])
        self.assertIn("12 months base salary", res_exec["answer"])

    def test_uncovered_topic_fallback(self):
        """Verify uncovered topic returns polite fallback message with zero hallucinations."""
        query = "Can I bring my pet iguana to the office cafeteria?"
        res = self.policy_agent.answer_policy_query(query, employee_role="Employee")

        self.assertFalse(res["has_policy_match"])
        self.assertIn("not covered in our current published company policies", res["answer"])


if __name__ == "__main__":
    unittest.main()
