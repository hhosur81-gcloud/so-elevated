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
    workweek_mcp_url: str = os.getenv("WORKWEEK_MCP_URL", "https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/")
    workweek_mcp_token: str = os.getenv("WORKWEEK_MCP_TOKEN", "mcp_fZFYPQVV1fAkmOYz4Lal8OVc9ltyLmfHiO4BZGCm-Tw")
    itsm_mcp_url: str = os.getenv("ITSM_MCP_URL", "https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/")
    itsm_mcp_token: str = os.getenv("ITSM_MCP_TOKEN", "mcp_iimWc8kxBKZR5m8hSgy_0tYy22fURzCR7Tn3KWsAOag")

    def get_workweek_token(self, employee_id: str = None) -> str:
        """Resolve tenant-specific WorkWeek FastMCP token."""
        tokens = {
            "EMP-436": os.getenv("WORKWEEK_MCP_TOKEN_EMP_436", "mcp_fZFYPQVV1fAkmOYz4Lal8OVc9ltyLmfHiO4BZGCm-Tw"),
            "EMP-477": os.getenv("WORKWEEK_MCP_TOKEN_EMP_477", "mcp_hleEvQkByz82OySU1A7CoX0-Jk4nyfxzMFujS-YDTLQ"),
        }
        if employee_id and employee_id in tokens:
            return tokens[employee_id]
        return self.workweek_mcp_token

    def get_itsm_token(self, employee_id: str = None) -> str:
        """Resolve tenant-specific ServiceImmediately FastMCP token."""
        tokens = {
            "EMP-436": os.getenv("ITSM_MCP_TOKEN_EMP_436", "mcp_iimWc8kxBKZR5m8hSgy_0tYy22fURzCR7Tn3KWsAOag"),
            "EMP-477": os.getenv("ITSM_MCP_TOKEN_EMP_477", "mcp_hleEvQkByz82OySU1A7CoX0-Jk4nyfxzMFujS-YDTLQ"),
        }
        if employee_id and employee_id in tokens:
            return tokens[employee_id]
        return self.itsm_mcp_token


settings = Settings()

