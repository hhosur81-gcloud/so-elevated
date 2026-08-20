"""FastAPI Production Server for So-Elevated Enterprise HR Assistant on Google Cloud Run."""

import os
import re
import sys
import time
import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("server")

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.agents.orchestrator_agent import PrimaryHROrchestrator
from src.config.settings import settings
from src.services.canary_service import ContinuousSyntheticCanary
from src.services.gemini_adk_service import GeminiADKService

app = FastAPI(
    title="So-Elevated Enterprise HR Agentic Solution",
    description="Multi-agent HR/IT virtual assistant on Vertex AI ADK and FastMCP",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Canary (which encapsulates Orchestrator) & Gemini ADK Engine
canary = ContinuousSyntheticCanary(policy_dir="knowledge")
orchestrator = canary.orchestrator
gemini_adk = GeminiADKService(
    workweek_agent=orchestrator.workweek_agent,
    itsm_agent=orchestrator.itsm_agent,
    policy_agent=orchestrator.policy_agent
)


class ChatRequest(BaseModel):
    message: str = Field(..., example="What are my current leave balances?")
    employee_id: str = Field("EMP-436", example="EMP-436")
    session_id: Optional[str] = Field(None, example="web-session-1")


class ResetRequest(BaseModel):
    employee_id: str = Field("EMP-436")
    session_id: str = Field("web-session-1")


@app.get("/api/health")
@app.get("/healthz")
async def health_check():
    """Deep Liveness & Dual-Region Readiness Probe for Cloud Load Balancer."""
    status = canary.get_health_status()
    status["project_id"] = os.getenv("GOOGLE_CLOUD_PROJECT", "no-vibing-here")
    status["region"] = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    status["model"] = settings.gemini_model_primary
    status["mcp_target"] = settings.workweek_mcp_url
    status["adk_connected"] = gemini_adk.is_connected
    return status



@app.post("/api/chat")
async def process_chat(req: ChatRequest):
    """Execute conversational turn across Model Armor, Gemini ADK Tool Calling, and FastMCP."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    session_id = req.session_id or f"sess-{req.employee_id}"
    
    # 1. Layer 0 Security Sentinel Gate (Model Armor)
    inspection = orchestrator.guardrail.inspect_inbound_prompt(req.message, employee_id=req.employee_id)
    if not inspection.is_valid:
        return orchestrator._format_result({
            "success": False,
            "error_code": "SECURITY_BLOCKED",
            "response": inspection.sanitized_text,
            "category": inspection.category,
            "requires_confirmation": False
        }, acting_agent="security_sentinel")

    # 2. Check if currently inside a pending confirmation gate or multi-turn PTO booking flow
    session = orchestrator._get_or_create_session(session_id, req.employee_id)
    lowered = req.message.lower().strip()
    
    was_awaiting_pto = False
    if session.turns:
        last_tool = getattr(session.turns[-1], "tool_invoked", "")
        if last_tool in ["prompt_pto_details", "enter_confirmation_gate"]:
            was_awaiting_pto = True

    is_pto_booking_intent = (
        was_awaiting_pto
        or bool(session.pending_confirmation)
        or bool(re.search(r"\b(request|book|take|apply\s+for|schedule)\s+(?:an?\s+)?(?:[\w\-]+\s+)?\b(pto|vacation|time\s*off|leave)\b", lowered))
        or (bool(re.search(r"\b(pto|vacation|time\s*off|annual\s+leave)\b", lowered)) and any(w in lowered for w in ["request", "book", "take", "apply", "schedule", "submit", "want", "need"]))
    )

    if is_pto_booking_intent and not ("balance" in lowered or "policy" in lowered or "rules" in lowered or "can i" in lowered):
        return orchestrator.process_turn(session_id=session_id, employee_id=req.employee_id, user_message=req.message)

    # 3. Check for greeting / capabilities intent
    is_greeting = bool(re.search(r"\b(hello|hi|hey|good\s*(morning|afternoon|evening)|howdy|greetings|help|help\s*me|who\s*are\s*you|what\s*(else\s*)?can\s*you\s*(do|help\s*with)|what\s*(else\s*)?do\s*you\s*do|what\s*are\s*your\s*capabilities|what\s*services\s*do\s*you\s*offer|what\s*can\s*i\s*ask|capabilities|features|menu)\b", lowered))
    if is_greeting:
        return orchestrator.process_turn(session_id=session_id, employee_id=req.employee_id, user_message=req.message)

    # 4. Invoke Vertex AI Gemini ADK with dynamic FastMCP Function Calling & Cloud Trace
    if gemini_adk.is_connected:
        try:
            profile = orchestrator.repo.load_record("workweek/employees.json", req.employee_id)
            emp_role = "Executive" if profile and profile.get("role") in ["VP of Engineering", "Executive", "VP"] else "Employee"
            adk_res = gemini_adk.query(
                user_message=req.message,
                employee_id=req.employee_id,
                session_id=session_id,
                employee_role=emp_role
            )
            return orchestrator._format_result(adk_res, acting_agent=adk_res.get("acting_agent", "orchestrator"))
        except Exception as e:
            logger.warning(f"Gemini ADK execution fallback: {e}")

    # 5. Fallback to in-process Orchestrator
    try:
        res = orchestrator.process_turn(
            session_id=session_id,
            employee_id=req.employee_id,
            user_message=req.message
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
async def reset_session(req: ResetRequest):
    """Explicitly purge session context from memory."""
    try:
        res = orchestrator.process_turn(
            session_id=req.session_id,
            employee_id=req.employee_id,
            user_message="reset session"
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_system_status():
    """Return subsystem architecture and FastMCP connectivity status."""
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "model": settings.gemini_model_primary,
        "knowledge_corpus": "161 Open Knowledge Format (OKF) Policy Sections",
        "live_fastmcp_endpoints": {
            "workweek_hcm": settings.workweek_mcp_url,
            "serviceimmediately_itsm": settings.itsm_mcp_url
        }
    }


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve Google Material Responsive Web Chat UI."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>So-Elevated Enterprise HR Assistant</title>
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto+Mono:wght@400;500&family=Roboto:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --google-blue: #1a73e8;
      --google-blue-dark: #1557b0;
      --google-blue-light: #e8f0fe;
      --google-green: #137333;
      --google-green-light: #e6f4ea;
      --google-yellow: #f9ab00;
      --google-red: #d93025;
      --google-gray-50: #f8f9fa;
      --google-gray-100: #f1f3f4;
      --google-gray-200: #e8eaed;
      --google-gray-700: #5f6368;
      --google-gray-900: #202124;
      --surface: #ffffff;
      --shadow-elevation: 0 4px 16px rgba(0,0,0,0.08);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Google Sans', 'Roboto', sans-serif;
      background: #f0f4f9;
      color: var(--google-gray-900);
      height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: var(--surface);
      border-bottom: 1px solid var(--google-gray-200);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-icon {
      font-size: 24px;
      background: var(--google-blue-light);
      color: var(--google-blue);
      padding: 6px 10px;
      border-radius: 8px;
    }
    .brand-title h1 {
      font-size: 18px;
      font-weight: 500;
      color: var(--google-gray-900);
    }
    .brand-title p {
      font-size: 12px;
      color: var(--google-gray-700);
    }
    .controls {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    select, button {
      font-family: 'Google Sans', sans-serif;
      font-size: 13px;
      padding: 8px 14px;
      border-radius: 20px;
      border: 1px solid var(--google-gray-200);
      background: var(--surface);
      outline: none;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    select:hover, button:hover {
      border-color: var(--google-blue);
    }
    .btn-reset {
      color: var(--google-gray-700);
    }
    .badge-live {
      background: var(--google-green-light);
      color: var(--google-green);
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 12px;
      letter-spacing: 0.5px;
    }
    main {
      flex: 1;
      max-width: 960px;
      width: 100%;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      padding: 16px;
      overflow: hidden;
    }
    .chat-window {
      flex: 1;
      background: var(--surface);
      border-radius: 16px;
      border: 1px solid var(--google-gray-200);
      box-shadow: var(--shadow-elevation);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .messages-container {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .message {
      display: flex;
      gap: 12px;
      max-width: 80%;
      line-height: 1.5;
      font-size: 14px;
      animation: fadeIn 0.2s ease;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
    .message.user {
      align-self: flex-end;
      flex-direction: row-reverse;
    }
    .message.assistant {
      align-self: flex-start;
    }
    .avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      flex-shrink: 0;
    }
    .message.user .avatar {
      background: var(--google-blue);
      color: #fff;
    }
    .message.assistant .avatar {
      background: var(--google-gray-100);
      border: 1px solid var(--google-gray-200);
    }
    .bubble {
      padding: 12px 18px;
      border-radius: 18px;
      word-break: break-word;
      white-space: pre-wrap;
    }
    .message.user .bubble {
      background: var(--google-blue);
      color: #ffffff;
      border-bottom-right-radius: 4px;
    }
    .message.assistant .bubble {
      background: var(--google-gray-50);
      color: var(--google-gray-900);
      border: 1px solid var(--google-gray-200);
      border-bottom-left-radius: 4px;
    }
    .agent-header {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 6px;
    }
    .agent-badge-tag {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.3px;
    }
    .badge-workweek_agent {
      background: #e6f4ea;
      color: #137333;
      border: 1px solid #ceead6;
    }
    .badge-itsm_agent {
      background: #f3e8fd;
      color: #7627bb;
      border: 1px solid #e1cbf9;
    }
    .badge-policy_agent {
      background: #fef7e0;
      color: #b06000;
      border: 1px solid #fdd663;
    }
    .badge-orchestrator {
      background: #e8f0fe;
      color: #1a73e8;
      border: 1px solid #aecbfa;
    }
    .badge-security_sentinel {
      background: #fce8e6;
      color: #c5221f;
      border: 1px solid #f5c2c7;
    }
    .badge-system-error {
      background: #fce8e6;
      color: #c5221f;
      border: 1px solid #f5c2c7;
    }
    .badge-live {
      background: var(--google-green-light);
      color: var(--google-green);
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 12px;
      letter-spacing: 0.5px;
      transition: all 0.3s ease;
    }
    .badge-offline {
      background: #fce8e6;
      color: #c5221f;
      border: 1px solid #f5c2c7;
    }
    .badge-reconnecting {
      background: #fef7e0;
      color: #b06000;
      border: 1px solid #fdd663;
    }
    .retry-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin-top: 8px;
      background: #ffffff;
      color: var(--google-blue);
      border: 1px solid var(--google-blue);
      padding: 5px 12px;
      border-radius: 14px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }
    .retry-btn:hover {
      background: var(--google-blue-light);
    }
    .bubble a {
      color: var(--google-blue);
      text-decoration: underline;
      font-weight: 500;
    }
    .quick-chips {
      padding: 8px 16px;
      background: var(--surface);
      border-top: 1px solid var(--google-gray-100);
      display: flex;
      gap: 8px;
      overflow-x: auto;
      white-space: nowrap;
    }
    .chip {
      background: var(--google-gray-100);
      color: var(--google-gray-700);
      padding: 6px 12px;
      border-radius: 14px;
      font-size: 12px;
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.15s;
    }
    .chip:hover {
      background: var(--google-blue-light);
      color: var(--google-blue);
      border-color: var(--google-blue);
    }
    .input-area {
      padding: 16px;
      background: var(--surface);
      border-top: 1px solid var(--google-gray-200);
      display: flex;
      gap: 12px;
      align-items: center;
    }
    .input-area input {
      flex: 1;
      padding: 12px 18px;
      border-radius: 24px;
      border: 1px solid var(--google-gray-200);
      background: var(--google-gray-50);
      font-size: 14px;
      outline: none;
      transition: all 0.2s;
    }
    .input-area input:focus {
      background: #ffffff;
      border-color: var(--google-blue);
      box-shadow: 0 0 0 2px rgba(26,115,232,0.15);
    }
    .btn-send {
      background: var(--google-blue);
      color: #ffffff;
      border: none;
      padding: 10px 20px;
      border-radius: 20px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .btn-send:hover {
      background: var(--google-blue-dark);
    }
    .spinner {
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255,255,255,0.3);
      border-radius: 50%;
      border-top-color: #fff;
      animation: spin 0.6s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-icon">🤖</div>
      <div class="brand-title">
        <h1>So-Elevated Enterprise HR Assistant</h1>
        <p>Vertex AI ADK • Model Armor • FastMCP Streamable HTTP</p>
      </div>
    </div>
    <div class="controls">
      <span id="connBadge" class="badge-live">● LIVE GCP CLOUD RUN</span>
      <select id="personaSelector" onchange="switchPersona()">
        <option value="EMP-436">Skhadkikar (EMP-436) [Live SaaS]</option>
        <option value="EMP-477">Harshahosur (EMP-477) [Live SaaS]</option>
        <option value="EMP-1001">Jane Doe (EMP-1001) [Engineer]</option>
        <option value="EMP-1002">John Smith (EMP-1002) [Sales]</option>
        <option value="EMP-1004">Maria Chen (EMP-1004) [DPO]</option>
        <option value="EMP-1005">Marcus Vance (EMP-1005) [VP Exec]</option>
      </select>
      <button class="btn-reset" onclick="resetSession()">Clear Context</button>
    </div>
  </header>

  <main>
    <div class="chat-window">
      <div class="messages-container" id="messages">
        <div class="message assistant">
          <div class="avatar">🤖</div>
          <div class="bubble">
            <div class="agent-header"><span class="agent-badge-tag badge-orchestrator">👑 HR Supervisor</span></div>
            <div class="bubble-text">Hello! I am your Enterprise HR & IT Assistant powered by Google Cloud Vertex AI and FastMCP. How may I assist you today with policy grounding, time-off balances, or support tickets?</div>
          </div>
        </div>
      </div>

      <div class="quick-chips">
        <button class="chip" onclick="sendChip('What are my current leave balances?')">🌴 Check Leave Balances</button>
        <button class="chip" onclick="sendChip('List my open support tickets')">🎟️ List My Tickets</button>
        <button class="chip" onclick="sendChip('What is the policy for bereavement leave in Singapore?')">📖 Bereavement Policy</button>
        <button class="chip" onclick="sendChip('Can I expense a $1000 gift card for a vendor?')">🎁 Gift Card Compliance</button>
        <button class="chip" onclick="sendChip('I want to request PTO')">📅 Request PTO</button>
      </div>

      <div class="input-area">
        <input type="text" id="userInput" placeholder="Ask a policy question or enter a request..." onkeydown="if(event.key==='Enter') sendMessage()" />
        <button class="btn-send" id="sendBtn" onclick="sendMessage()">Send</button>
      </div>
    </div>
  </main>

  <script>
    let currentEmpId = "EMP-436";
    let sessionId = "session-" + Math.random().toString(36).substring(7);

    // Live Heartbeat Probe to monitor Cloud Run connection
    async function checkHealth() {
      const badge = document.getElementById("connBadge");
      try {
        const res = await fetch("/api/health", { cache: "no-store" });
        if (res.ok) {
          badge.className = "badge-live";
          badge.innerText = "● LIVE GCP CLOUD RUN";
        } else {
          badge.className = "badge-live badge-reconnecting";
          badge.innerText = "● SERVICE DEGRADATION";
        }
      } catch (e) {
        badge.className = "badge-live badge-offline";
        badge.innerText = "● NETWORK OFFLINE";
      }
    }
    setInterval(checkHealth, 15000);
    window.addEventListener("online", checkHealth);
    window.addEventListener("offline", checkHealth);

    function switchPersona() {
      currentEmpId = document.getElementById("personaSelector").value;
      sessionId = "session-" + currentEmpId + "-" + Math.random().toString(36).substring(7);
      appendMessage("assistant", "Switched active identity to " + currentEmpId + ". Session context re-initialized.", {
        acting_agent: "orchestrator",
        agent_badge: "👑 HR Supervisor"
      });
    }

    function sendChip(text) {
      document.getElementById("userInput").value = text;
      sendMessage();
    }

    function appendMessage(role, text, agentData, failedMsgText = null) {
      const container = document.getElementById("messages");
      const msgDiv = document.createElement("div");
      msgDiv.className = "message " + role;
      
      const avatar = document.createElement("div");
      avatar.className = "avatar";
      avatar.innerText = role === "user" ? "👤" : (agentData && agentData.acting_agent === "system_error" ? "⚠️" : "🤖");
      
      const bubble = document.createElement("div");
      bubble.className = "bubble";

      if (role === "assistant" && agentData && agentData.agent_badge) {
        const agentHeader = document.createElement("div");
        agentHeader.className = "agent-header";
        const agentTag = document.createElement("span");
        agentTag.className = "agent-badge-tag badge-" + (agentData.acting_agent || "orchestrator");
        agentTag.innerText = agentData.agent_badge;
        agentHeader.appendChild(agentTag);
        bubble.appendChild(agentHeader);
      }
      
      const textDiv = document.createElement("div");
      textDiv.className = "bubble-text";
      
      // Auto linkify URLs
      const linkified = text.replace(/\[(.*?)\]\((https?:[^\)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
      textDiv.innerHTML = linkified;
      bubble.appendChild(textDiv);

      if (failedMsgText) {
        const retryBtn = document.createElement("button");
        retryBtn.className = "retry-btn";
        retryBtn.innerHTML = "🔄 Click to Retry";
        retryBtn.onclick = () => {
          document.getElementById("userInput").value = failedMsgText;
          sendMessage();
        };
        bubble.appendChild(retryBtn);
      }
      
      msgDiv.appendChild(avatar);
      msgDiv.appendChild(bubble);
      container.appendChild(msgDiv);
      container.scrollTop = container.scrollHeight;
    }

    async function fetchWithRetry(url, options, retries = 1, delay = 1000) {
      for (let attempt = 0; attempt <= retries; attempt++) {
        try {
          return await fetch(url, options);
        } catch (err) {
          if (attempt < retries) {
            await new Promise(r => setTimeout(r, delay));
            continue;
          }
          throw err;
        }
      }
    }

    async function sendMessage() {
      const input = document.getElementById("userInput");
      const btn = document.getElementById("sendBtn");
      const msg = input.value.trim();
      if (!msg) return;

      appendMessage("user", msg);
      input.value = "";
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span>';

      try {
        const resp = await fetchWithRetry("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: msg,
            employee_id: currentEmpId,
            session_id: sessionId
          })
        });

        if (!resp.ok) {
          let errorDetail = "Server returned status " + resp.status;
          try {
            const errJson = await resp.json();
            if (errJson.detail) errorDetail = errJson.detail;
          } catch (_) {}
          appendMessage("assistant", "Server Error (" + resp.status + "): " + errorDetail, {
            acting_agent: "system_error",
            agent_badge: "⚠️ Service Notice"
          }, msg);
          return;
        }

        const data = await resp.json();
        if (data.response) {
          appendMessage("assistant", data.response, {
            acting_agent: data.acting_agent,
            agent_name: data.agent_name,
            agent_badge: data.agent_badge
          });
        } else {
          appendMessage("assistant", "Received unexpected response format from agent router.", {
            acting_agent: "system_error",
            agent_badge: "⚠️ Notice"
          }, msg);
        }
      } catch (err) {
        const isOffline = !navigator.onLine;
        const errMsg = isOffline 
          ? "Network connection is currently offline. Please check your internet or VPN connection."
          : "Temporary network interruption (" + err.message + "). The server could not be reached.";
        appendMessage("assistant", errMsg, {
          acting_agent: "system_error",
          agent_badge: "⚠️ Network Interruption"
        }, msg);
      } finally {
        btn.disabled = false;
        btn.innerText = "Send";
        input.focus();
      }
    }

    async function resetSession() {
      try {
        const resp = await fetchWithRetry("/api/reset", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            employee_id: currentEmpId,
            session_id: sessionId
          })
        });
        appendMessage("assistant", "Session context has been reset. How may I assist you today?", {
          acting_agent: "orchestrator",
          agent_badge: "👑 HR Supervisor"
        });
      } catch(err) {
        appendMessage("assistant", "Failed to reset session: " + err.message, {
          acting_agent: "system_error",
          agent_badge: "⚠️ Connection Notice"
        });
      }
    }
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
