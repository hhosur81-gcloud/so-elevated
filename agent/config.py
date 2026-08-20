"""Configuration settings for the HR Agentic Solution (Option 1: Native Vertex AI IAM)."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent

# Load environment variables from .env in agent package or repo root
load_dotenv(PACKAGE_DIR / ".env")
load_dotenv(REPO_ROOT / ".env")

# Ensure native Vertex AI mode is enforced on Google Cloud
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT", "so-elevated")
os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "asia-south1")

# Cleanse external API keys so calls never route to AI Studio
for key in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
    if key in os.environ:
        os.environ.pop(key, None)

# Google Cloud Platform Target Configuration
GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "so-elevated")
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "asia-south1")  # Mumbai, India

# Persistent ADK & Storage directory (.adk/)
ADK_STORAGE_DIR = REPO_ROOT / ".adk" if (REPO_ROOT / ".adk").exists() else PACKAGE_DIR / ".adk"
ADK_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# SQLite Session & Idempotency Database Paths (Local Mode)
SQLITE_SESSION_DB_PATH = ADK_STORAGE_DIR / "sessions.db"
SQLITE_SESSION_DB_URI = f"sqlite+aiosqlite:///{SQLITE_SESSION_DB_PATH}"
IDEMPOTENCY_DB_PATH = ADK_STORAGE_DIR / "idempotency.db"

# Knowledge base directory resolution
def _resolve_knowledge_dir() -> Path:
    explicit = os.getenv("KNOWLEDGE_DIR")
    if explicit and Path(explicit).is_dir():
        return Path(explicit)
    if (PACKAGE_DIR / "knowledge").is_dir():
        return PACKAGE_DIR / "knowledge"
    if (REPO_ROOT / "knowledge").is_dir():
        return REPO_ROOT / "knowledge"
    if Path("/app/knowledge").is_dir():
        return Path("/app/knowledge")
    return REPO_ROOT / "knowledge"

KNOWLEDGE_DIR = _resolve_knowledge_dir()

# Gemini Model identifier (gemini-2.5-flash on Vertex AI in asia-south1)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Live FastMCP Server URLs and Hardcoded Swapna Token
WORKWEEK_MCP_URL = os.getenv(
    "WORKWEEK_MCP_URL",
    "https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/"
)
WORKWEEK_MCP_TOKEN = os.getenv(
    "WORKWEEK_MCP_TOKEN",
    "mcp_fZFYPQVV1fAkmOYz4Lal8OVc9ltyLmfHiO4BZGCm-Tw"
)

SERVICEIMMEDIATELY_MCP_URL = os.getenv(
    "SERVICEIMMEDIATELY_MCP_URL",
    "https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/"
)
SERVICEIMMEDIATELY_MCP_TOKEN = os.getenv(
    "SERVICEIMMEDIATELY_MCP_TOKEN",
    "mcp_fZFYPQVV1fAkmOYz4Lal8OVc9ltyLmfHiO4BZGCm-Tw"
)
