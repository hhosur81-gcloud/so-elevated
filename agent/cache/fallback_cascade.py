"""Multi-Tier Gemini Flash Fallback Cascade Manager (ENG-0005)."""
import logging
from typing import Callable, List, Optional, Any

logger = logging.getLogger(__name__)

# 3-Tier model hierarchy according to available live models
MODEL_CASCADE_TIERS: List[str] = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
]


class FallbackCascadeManager:
    """Orchestrates multi-tier model cascading upon 429 quota spikes or transient 503 errors."""

    def __init__(self, tiers: Optional[List[str]] = None):
        self.tiers = tiers or MODEL_CASCADE_TIERS

    def execute_with_fallback(self, call_fn: Callable[[str], Any]) -> Any:
        """Executes a model call across the fallback tiers until success or all tiers exhausted."""
        last_error = None
        for tier_model in self.tiers:
            try:
                logger.info(f"Attempting model execution on tier: {tier_model}")
                return call_fn(tier_model)
            except Exception as e:
                err_str = str(e)
                logger.warning(f"Tier {tier_model} encountered failure: {err_str}")
                last_error = e
                # If it's a rate limit (429) or transient error (503/500), cascade to next tier
                if any(code in err_str for code in ["429", "503", "500", "ResourceExhausted", "UNAVAILABLE"]):
                    continue
                else:
                    # Non-transient errors (e.g. client validation) fail immediately
                    raise e

        raise RuntimeError(f"All fallback model tiers exhausted. Last error: {last_error}")
