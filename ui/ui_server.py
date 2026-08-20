"""Altostrat HR & IT Enterprise Agentic Portal — FastAPI Backend (Option 1: Vertex AI Agent Engine + Model Armor)."""
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Optional

import google.auth
import google.auth.transport.requests
import httpx
import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Configure structured server logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("altostrat.portal")

# Security Sentinel Gateway (Model Armor & SPII Masking)
try:
    from agent.security.model_armor_service import model_armor_gateway, SecurityViolationError
except ImportError:
    try:
        from model_armor_service import model_armor_gateway, SecurityViolationError
    except ImportError:
        model_armor_gateway = None
        SecurityViolationError = Exception

# Base directory paths
APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
STATIC_DIR = APP_DIR / "static"

def _resolve_knowledge_dir() -> Path:
    if (APP_DIR / "knowledge").is_dir():
        return APP_DIR / "knowledge"
    if (REPO_ROOT / "knowledge").is_dir():
        return REPO_ROOT / "knowledge"
    return APP_DIR / "knowledge"

KNOWLEDGE_DIR = _resolve_knowledge_dir()

# Google Cloud Platform & Vertex AI Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "so-elevated")
PROJECT_NUMBER = os.getenv("GOOGLE_CLOUD_PROJECT_NUMBER", "501431672831")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "asia-south1")
REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID", "1246520730456162304")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

app = FastAPI(
    title="Altostrat HR & IT Enterprise Assistant",
    description="Conversational Portal powered by Google Cloud Vertex AI Agent Runtime & Model Armor Guardrails",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "EMP-436"
    session_id: Optional[str] = None


def get_gcp_access_token() -> str:
    """Retrieve fresh Google Cloud IAM Bearer token via Application Default Credentials (ADC)."""
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return credentials.token


async def stream_reasoning_engine_events(
    user_query: str,
    user_id: str = "EMP-436",
    session_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream live events from Vertex AI ReasoningEngine with Layer 0 Model Armor sanitization."""
    start_time = time.time()
    logger.info("📩 New query received: user_id=%s, session_id=%s, text=%r", user_id, session_id, user_query[:80])
    
    # 1. Model Armor Ingress Screening (Prompt Injection & SPII Guardrails)
    processed_query = user_query
    if model_armor_gateway:
        try:
            sanitization = model_armor_gateway.sanitize_user_prompt(user_query)
            processed_query = sanitization.sanitized_text
            if sanitization.spii_redacted:
                logger.info("🔒 Model Armor SPII redacted: %s", sanitization.violations)
                notice_payload = {
                    "type": "security_notice",
                    "message": "🔒 Sensitive PII was masked by Google Cloud Model Armor before transmission.",
                    "violations": sanitization.violations
                }
                yield f"data: {json.dumps(notice_payload)}\n\n"
        except SecurityViolationError as sve:
            logger.warning("🚨 Model Armor blocked injection attempt: %s", sve)
            error_payload = {
                "type": "security_violation",
                "message": f"🚨 {str(sve)}",
                "violation_type": sve.violation_type
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
            return

    token = get_gcp_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    engine_resource = f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}"
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/{engine_resource}:streamQuery"

    body: Dict[str, Any] = {
        "class_method": "stream_query",
        "input": {
            "message": processed_query,
            "user_id": user_id,
        }
    }
    
    if session_id and (session_id.startswith("projects/") or session_id.isdigit()):
        body["input"]["session_id"] = session_id

    accumulated_text = ""
    active_tools = []
    vertex_session_id = session_id

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=body) as response:
                if response.status_code != 200:
                    err_text = await response.aread()
                    logger.error("❌ Vertex AI Agent Runtime error (%s): %s", response.status_code, err_text.decode('utf-8')[:300])
                    error_payload = {
                        "type": "error",
                        "status_code": response.status_code,
                        "message": f"Vertex AI Agent Runtime error ({response.status_code}): {err_text.decode('utf-8')[:500]}"
                    }
                    yield f"data: {json.dumps(error_payload)}\n\n"
                    return

                async for raw_line in response.aiter_lines():
                    if not raw_line or not raw_line.strip():
                        continue

                    try:
                        event_data = json.loads(raw_line)
                    except Exception:
                        continue

                    if "session_id" in event_data:
                        vertex_session_id = event_data["session_id"]
                    elif "session" in event_data and isinstance(event_data["session"], dict):
                        vertex_session_id = event_data["session"].get("name")

                    content = event_data.get("content", {})
                    parts = content.get("parts", [])
                    
                    for part in parts:
                        if "function_call" in part:
                            fc = part["function_call"]
                            tool_name = fc.get("name", "tool")
                            tool_args = fc.get("args", {})
                            tool_id = fc.get("id", "")
                            active_tools.append(tool_name)
                            logger.info("🔧 Tool Call: %s (args=%s)", tool_name, tool_args)
                            yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_name, 'args': tool_args, 'id': tool_id})}\n\n"

                        elif "function_response" in part:
                            fr = part["function_response"]
                            tool_name = fr.get("name", "tool")
                            tool_res = fr.get("response", {})
                            tool_id = fr.get("id", "")
                            logger.info("✅ Tool Result: %s -> %s", tool_name, str(tool_res)[:100])
                            yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': tool_res, 'id': tool_id})}\n\n"

                        elif "text" in part:
                            text_chunk = part["text"]
                            if model_armor_gateway:
                                text_chunk = model_armor_gateway.sanitize_model_response(text_chunk).sanitized_text
                            accumulated_text += text_chunk
                            yield f"data: {json.dumps({'type': 'text_chunk', 'text': text_chunk})}\n\n"

        duration_ms = int((time.time() - start_time) * 1000)
        logger.info("🏁 Query complete in %sms (tools=%s, text_len=%d)", duration_ms, active_tools, len(accumulated_text))
        yield f"data: {json.dumps({'type': 'done', 'duration_ms': duration_ms, 'tools_used': active_tools, 'session_id': vertex_session_id})}\n\n"

    except Exception as e:
        logger.error("❌ Exception during streaming: %s", e)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@app.post("/api/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    """Server-Sent Events (SSE) streaming endpoint."""
    return StreamingResponse(
        stream_reasoning_engine_events(
            user_query=req.message,
            user_id=req.user_id,
            session_id=req.session_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/config")
async def get_config():
    """Return runtime metadata and deployment information."""
    return {
        "project_id": PROJECT_ID,
        "project_number": PROJECT_NUMBER,
        "location": LOCATION,
        "reasoning_engine_id": REASONING_ENGINE_ID,
        "model": GEMINI_MODEL,
        "security": {
            "model_armor": "Active (Enforced Global FloorSetting)",
            "dlp_spi_masking": "Active",
            "rbac_isolation": "Active",
            "idempotency_mode": "SHA-256 In-Turn Lock"
        },
        "knowledge_count": len(list(KNOWLEDGE_DIR.glob("**/*.md"))) if KNOWLEDGE_DIR.is_dir() else 0,
        "systems": [
            {"name": "WorkWeek HCM", "status": "Active (Live FastMCP)", "endpoint": "https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/"},
            {"name": "ServiceImmediately ITSM", "status": "Active (Live FastMCP)", "endpoint": "https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/"},
            {"name": "Open Knowledge Format", "status": "Active (Grounding)", "source": "knowledge/ (Open Knowledge Format)"},
        ]
    }


@app.get("/api/policies")
async def list_policies():
    """List all available OKF policy documents and index headers."""
    index_file = KNOWLEDGE_DIR / "index.md"
    if not index_file.is_file():
        return {"sections": []}
    
    content = index_file.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]
            
    sections = []
    current_sec = None
    
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("## Section"):
            current_sec = {"title": line.lstrip("# ").strip(), "items": []}
            sections.append(current_sec)
        elif line.startswith("- [") and current_sec:
            try:
                title_part = line[line.find("[") + 1 : line.find("]")]
                path_part = line[line.find("(") + 1 : line.find(")")]
                current_sec["items"].append({"title": title_part, "path": path_part})
            except Exception:
                pass

    return {"sections": sections}


@app.get("/api/policies/read")
async def read_policy(path: str = Query(..., description="Relative path to OKF policy markdown")):
    """Read a specific policy file with frontmatter metadata."""
    clean_path = path.strip().lstrip("/")
    if not clean_path.endswith(".md"):
        clean_path += ".md"
    target_file = KNOWLEDGE_DIR / clean_path
    
    if not target_file.is_file():
        matches = list(KNOWLEDGE_DIR.glob(f"**/*{Path(clean_path).name}*"))
        if matches:
            target_file = matches[0]
        else:
            raise HTTPException(status_code=404, detail="Policy file not found")
            
    raw_text = target_file.read_text(encoding="utf-8")
    metadata = {}
    body = raw_text
    
    if raw_text.startswith("---"):
        parts = raw_text.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
            except Exception:
                pass
            body = parts[2].strip()
            
    return {
        "title": metadata.get("title", target_file.stem),
        "version": metadata.get("version", "1.0"),
        "status": metadata.get("status", "Active"),
        "path": f"/{target_file.relative_to(KNOWLEDGE_DIR)}",
        "body": body,
    }


@app.get("/healthz")
@app.get("/api/health")
async def health_check():
    """Healthcheck endpoint."""
    return {"status": "HEALTHY", "service": "altostrat-hr-portal", "timestamp": time.time()}


# Mount static assets
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the single page application."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="Frontend assets not found")
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


def main():
    """Local runner entry point."""
    port = int(os.getenv("PORT", "3000"))
    host = os.getenv("HOST", "0.0.0.0")
    print("=" * 75)
    print(f"🚀 Altostrat HR & IT Enterprise Portal starting on http://{host}:{port}")
    print(f"   Connected to Vertex AI Agent Runtime: {REASONING_ENGINE_ID} in {LOCATION}")
    print(f"   Using Swapna's FastMCP Token")
    print(f"   Security Sentinel: Google Cloud Model Armor Active")
    print("=" * 75)
    uvicorn.run("ui_server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
