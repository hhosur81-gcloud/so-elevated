"""Unit tests verifying Semantic Cache and Fallback Cascade (ENG-0005)."""
import time
from agent.cache.semantic_cache import SemanticPolicyCache
from agent.cache.fallback_cascade import FallbackCascadeManager


def test_semantic_cache_hit_and_miss():
    """Verify exact/normalized cache lookup and expiration."""
    cache = SemanticPolicyCache(ttl_seconds=2)
    
    query = "How many sick days in Singapore?"
    response = "Up to 14 days of paid outpatient sick leave."
    
    # Initial miss
    assert cache.get(query) is None
    
    # Store and hit with different whitespace/casing
    cache.set(query, response)
    assert cache.get("  how many SICK days in Singapore? ") == response
    
    # Expiration test
    time.sleep(2.1)
    assert cache.get(query) is None


def test_fallback_cascade_tier_success():
    """Verify fallback cascade succeeds on first tier when healthy."""
    manager = FallbackCascadeManager(["tier-1", "tier-2"])
    executed_tiers = []

    def mock_call(model_name: str):
        executed_tiers.append(model_name)
        return f"Result from {model_name}"

    result = manager.execute_with_fallback(mock_call)
    assert result == "Result from tier-1"
    assert executed_tiers == ["tier-1"]


def test_fallback_cascade_on_quota_error():
    """Verify fallback cascades to Tier 2 when Tier 1 throws 429 quota exception."""
    manager = FallbackCascadeManager(["gemini-3.5-flash", "gemini-3.5-flash-lite"])
    executed_tiers = []

    def mock_call(model_name: str):
        executed_tiers.append(model_name)
        if model_name == "gemini-3.5-flash":
            raise RuntimeError("429 ResourceExhausted: Quota exceeded for model")
        return f"Success from {model_name}"

    result = manager.execute_with_fallback(mock_call)
    assert result == "Success from gemini-3.5-flash-lite"
    assert executed_tiers == ["gemini-3.5-flash", "gemini-3.5-flash-lite"]
