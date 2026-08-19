"""Application Settings and Configuration."""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Core application environment settings."""
    app_name: str = "So-Elevated HR Agentic Solution"
    version: str = "1.0.0"
    environment: str = os.getenv("APP_ENV", "development")
    gemini_model_primary: str = "gemini-3.7-flash"
    gemini_model_fallback_1: str = "gemini-3.6-flash"
    gemini_model_fallback_2: str = "gemini-3.0-flash"
    gemini_model_emergency: str = "gemini-2.5-flash"
    jwt_issuer: str = "so-elevated-hr-orchestrator"
    jwt_audience: str = "enterprise-mcp-mesh"
    jwt_ttl_seconds: int = 900  # 15 minutes (ADR-0009)
    filestore_base_path: str = os.getenv("FILESTORE_PATH", "data/filestore")


settings = Settings()
