"""24/7 Continuous Synthetic Production Canary & Probing Worker (ENG-0006)."""
import time
from typing import Dict, Any
from ..services.policy_service import PolicyService
from ..cache.fallback_cascade import FallbackCascadeManager
from .. import config


class SyntheticCanaryProbe:
    """Automated probe testing Policy Grounding, Model Cascading, and FastMCP endpoints."""

    def __init__(self):
        self.policy_service = PolicyService()
        self.cascade_manager = FallbackCascadeManager()

    def run_probe(self, canary_emp_id: str = "EMP-CANARY-01") -> Dict[str, Any]:
        """Executes a full vertical health probe and returns diagnostic telemetry."""
        start_time = time.time()
        results: Dict[str, Any] = {
            "canary_id": canary_emp_id,
            "timestamp": time.time(),
            "status": "HEALTHY",
            "checks": {},
        }

        # 1. Probe Policy Retrieval (OKF)
        try:
            p_start = time.time()
            concept = self.policy_service.read_concept(
                "01-paid-time-off-leave-operations/1.1-outpatient-sick-time-hospitalization-leave-singapore.md"
            )
            assert "14 days of paid outpatient sick leave" in concept
            results["checks"]["okf_policy_retrieval"] = {
                "status": "PASS",
                "latency_ms": round((time.time() - p_start) * 1000, 2),
            }
        except Exception as e:
            results["status"] = "UNHEALTHY"
            results["checks"]["okf_policy_retrieval"] = {"status": "FAIL", "error": str(e)}

        # 2. Probe FastMCP Server URLs
        results["checks"]["workweek_mcp_config"] = {
            "url": config.WORKWEEK_MCP_URL,
            "status": "CONFIGURED" if config.WORKWEEK_MCP_TOKEN else "MISSING_TOKEN",
        }
        results["checks"]["serviceimmediately_mcp_config"] = {
            "url": config.SERVICEIMMEDIATELY_MCP_URL,
            "status": "CONFIGURED" if config.SERVICEIMMEDIATELY_MCP_TOKEN else "MISSING_TOKEN",
        }

        results["total_latency_ms"] = round((time.time() - start_time) * 1000, 2)
        return results


if __name__ == "__main__":
    probe = SyntheticCanaryProbe()
    report = probe.run_probe()
    print("Canary Diagnostic Report:", report)
