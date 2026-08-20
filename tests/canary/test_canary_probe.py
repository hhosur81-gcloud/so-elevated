"""Canary test suite for continuous synthetic production probing (ENG-0006)."""
from agent.canary.synthetic_probe import SyntheticCanaryProbe


def test_synthetic_canary_execution():
    """Verify synthetic canary probe runs diagnostic checks without errors."""
    probe = SyntheticCanaryProbe()
    report = probe.run_probe("EMP-CANARY-01")

    assert report["canary_id"] == "EMP-CANARY-01"
    assert report["status"] == "HEALTHY"
    assert "okf_policy_retrieval" in report["checks"]
    assert report["checks"]["okf_policy_retrieval"]["status"] == "PASS"
    assert report["total_latency_ms"] >= 0.0
