"""Vertex AI Gemini ADK Agent Engine with Live FastMCP Tool Calling & Google Cloud Trace."""

import os
import time
import uuid
import logging
from typing import Any, Dict, List, Optional

import vertexai
from vertexai.preview import reasoning_engines
from google import genai
from google.genai import types

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

from src.agents.itsm_agent import ITSMAgent
from src.agents.policy_agent import PolicyAgent
from src.agents.workweek_agent import WorkWeekAgent
from src.config.settings import settings
from src.repositories.filestore_repository import FileStoreRepository

logger = logging.getLogger("gemini_adk_service")

ORCHESTRATOR_ENGINE_ID = os.getenv(
    "ADK_ORCHESTRATOR_RESOURCE",
    "projects/136598345275/locations/us-central1/reasoningEngines/7730773457276764160",
)


class GeminiADKService:
    """Enterprise Vertex AI Gemini Agent with Dynamic FastMCP Tool Calling & OpenTelemetry Cloud Trace."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        model_name: Optional[str] = None,
        workweek_agent: Optional[WorkWeekAgent] = None,
        itsm_agent: Optional[ITSMAgent] = None,
        policy_agent: Optional[PolicyAgent] = None,
    ):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "no-vibing-here")
        self.location = location or os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
        self.model_name = model_name or settings.gemini_model_primary

        self.repo = FileStoreRepository()
        self.workweek_agent = workweek_agent or WorkWeekAgent(repository=self.repo)
        self.itsm_agent = itsm_agent or ITSMAgent(repository=self.repo)
        self.policy_agent = policy_agent or PolicyAgent()

        # Initialize OpenTelemetry Google Cloud Trace Provider
        self._init_cloud_trace()

        # Initialize Vertex AI Reasoning Engine for Remote Native ADK Execution
        try:
            vertexai.init(project=self.project_id, location=self.location)
            self.remote_orchestrator = reasoning_engines.ReasoningEngine(ORCHESTRATOR_ENGINE_ID)
            logger.info(f"Connected to remote Vertex AI Reasoning Engine: {ORCHESTRATOR_ENGINE_ID}")
        except Exception as e:
            logger.warning(f"Could not connect to remote Reasoning Engine: {e}")
            self.remote_orchestrator = None

        # Initialize Vertex AI GenAI Client fallback
        try:
            self.client = genai.Client(vertexai=True, project=self.project_id, location=self.location)
            self.is_connected = True
        except Exception as e:
            logger.warning(f"Vertex AI Client initialization warning: {e}")
            self.client = None
            self.is_connected = False

    def _init_cloud_trace(self):
        """Initialize Google Cloud Trace span exporter."""
        try:
            self.provider = TracerProvider()
            exporter = CloudTraceSpanExporter(project_id=self.project_id)
            self.provider.add_span_processor(SimpleSpanProcessor(exporter))
            trace.set_tracer_provider(self.provider)
            self.tracer = trace.get_tracer("so-elevated-gemini-adk")
        except Exception as e:
            logger.warning(f"Could not initialize CloudTraceSpanExporter: {e}")
            self.provider = None
            self.tracer = trace.get_tracer("local-adk-tracer")

    def query(
        self,
        user_message: str,
        employee_id: str = "EMP-436",
        session_id: Optional[str] = None,
        employee_role: str = "Employee",
    ) -> Dict[str, Any]:
        """Execute conversational turn through Gemini with dynamic FastMCP tool execution & Cloud Trace."""
        start_time = time.perf_counter()
        tools_called: List[str] = []

        # 1. Define real FastMCP tool wrappers bound to current employee context
        def get_leave_balances() -> Dict[str, Any]:
            """Fetch current remaining vacation and sick leave balances for the authenticated employee."""
            with self.tracer.start_as_current_span("fastmcp.workweek.get_balances") as span:
                span.set_attribute("employee.id", employee_id)
                span.set_attribute("mcp.tool", "get_balances")
                tools_called.append("workweek_get_balances")
                res = self.workweek_agent.get_balances(employee_id)
                span.set_attribute("response.success", str(res.get("success", True)))
                return res

        def get_open_tickets() -> Dict[str, Any]:
            """Look up open IT support and facilities incidents/tickets for the employee."""
            with self.tracer.start_as_current_span("fastmcp.itsm.get_tickets") as span:
                span.set_attribute("employee.id", employee_id)
                span.set_attribute("mcp.tool", "get_tickets")
                tools_called.append("itsm_get_tickets")
                res = self.itsm_agent.lookup_tickets(user_message="", employee_id=employee_id)
                return res

        def create_support_ticket(category: str, priority: str, short_description: str, details: str = "") -> Dict[str, Any]:
            """Create a new IT support incident, hardware request, loaner laptop order, or facilities ticket."""
            with self.tracer.start_as_current_span("fastmcp.itsm.create_ticket") as span:
                span.set_attribute("employee.id", employee_id)
                span.set_attribute("mcp.tool", "create_ticket")
                span.set_attribute("ticket.category", category)
                span.set_attribute("ticket.priority", priority)
                tools_called.append("itsm_create_ticket")
                res = self.itsm_agent.create_ticket(
                    user_message=short_description,
                    employee_id=employee_id
                )
                return res

        def search_company_policies(policy_query: str) -> Dict[str, Any]:
            """Search 161 OKF enterprise policies for bereavement, travel expenses, allowances, and benefits."""
            with self.tracer.start_as_current_span("rag.policy_search") as span:
                span.set_attribute("employee.id", employee_id)
                span.set_attribute("policy.query", policy_query)
                tools_called.append("policy_search")
                res = self.policy_agent.answer_policy_query(policy_query, employee_role=employee_role)
                return res

        tools = [
            get_leave_balances,
            get_open_tickets,
            create_support_ticket,
            search_company_policies,
        ]

        system_instruction = f"""You are the So-Elevated Enterprise HR & IT Virtual Assistant for employee {employee_id} (Role: {employee_role}).

Operational Rules:
1. Always invoke available FastMCP tools to fetch ground-truth information (leave balances, support tickets, company policies).
2. For leave balance questions, call `get_leave_balances()`.
3. For open support tickets inquiries (e.g. 'list my tickets', 'open tickets'), call `get_open_tickets()`.
4. For hardware, laptop, keyboard, mouse, or IT requests, call `create_support_ticket()`.
5. For policy inquiries (bereavement, travel, allowances, expenses), call `search_company_policies()`.
6. When citing company policies, preserve policy names and citation links.
7. Be concise, professional, and helpful."""

        # Start Root Cloud Trace Span
        with self.tracer.start_as_current_span("gemini.adk.chat_turn") as root_span:
            root_span.set_attribute("gemini.model", self.model_name)
            root_span.set_attribute("user.id", employee_id)
            root_span.set_attribute("user.message", user_message)

            # Route first to native Vertex AI Reasoning Engine if online
            if self.remote_orchestrator:
                try:
                    with self.tracer.start_as_current_span("vertexai.reasoning_engine.query") as engine_span:
                        engine_span.set_attribute("engine.resource_name", ORCHESTRATOR_ENGINE_ID)
                        engine_span.set_attribute("user.id", employee_id)

                        formatted_prompt = f"[Authenticated Employee ID: {employee_id}, Role: {employee_role}]\nUser Request: {user_message}"
                        remote_resp = self.remote_orchestrator.query(input=formatted_prompt)
                        
                        raw_out = remote_resp.get("output", "") if isinstance(remote_resp, dict) else remote_resp
                        if isinstance(raw_out, list):
                            text_parts = [b.get("text", "") for b in raw_out if isinstance(b, dict) and "text" in b]
                            resp_text = "\n".join(text_parts) if text_parts else str(raw_out)
                        else:
                            resp_text = str(raw_out)

                        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                        root_span.set_attribute("execution.latency_ms", elapsed_ms)
                        root_span.set_attribute("engine.type", "native_adk_reasoning_engine")

                        # Infer acting agent
                        msg_lower = user_message.lower()
                        if any(k in msg_lower for k in ["leave", "pto", "vacation", "sick", "balance", "off"]):
                            acting_agent = "workweek_agent"
                        elif any(k in msg_lower for k in ["ticket", "laptop", "keyboard", "mouse", "support", "incident", "issue"]):
                            acting_agent = "itsm_agent"
                        elif any(k in msg_lower for k in ["policy", "bereavement", "expense", "travel", "allowance", "handbook"]):
                            acting_agent = "policy_agent"
                        else:
                            acting_agent = "orchestrator"

                        if self.provider:
                            self.provider.force_flush()

                        return {
                            "success": True,
                            "response": resp_text.strip(),
                            "acting_agent": acting_agent,
                            "tools_called": [f"adk_reasoning_engine_{acting_agent}"],
                            "latency_ms": elapsed_ms,
                            "trace_id": format(root_span.get_span_context().trace_id, "032x"),
                            "requires_confirmation": False
                        }
                except Exception as remote_err:
                    logger.warning(f"Remote Reasoning Engine query failed, falling back to direct GenAI: {remote_err}")
                    root_span.record_exception(remote_err)

            # Direct fallback via GenAI SDK
            try:
                active_model = "gemini-2.5-flash"
                chat = self.client.chats.create(
                    model=active_model,
                    config=types.GenerateContentConfig(
                        tools=tools,
                        system_instruction=system_instruction,
                        temperature=0.2,
                    )
                )
                response = chat.send_message(user_message)
                resp_text = response.text or ""

                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                root_span.set_attribute("execution.latency_ms", elapsed_ms)
                root_span.set_attribute("tools.called", ",".join(tools_called))

                if any("workweek" in t for t in tools_called):
                    acting_agent = "workweek_agent"
                elif any("itsm" in t for t in tools_called):
                    acting_agent = "itsm_agent"
                elif any("policy" in t for t in tools_called):
                    acting_agent = "policy_agent"
                else:
                    acting_agent = "orchestrator"

                if self.provider:
                    self.provider.force_flush()

                return {
                    "success": True,
                    "response": resp_text.strip(),
                    "acting_agent": acting_agent,
                    "tools_called": tools_called,
                    "latency_ms": elapsed_ms,
                    "trace_id": format(root_span.get_span_context().trace_id, "032x"),
                    "requires_confirmation": False
                }

            except Exception as ex:
                logger.error(f"Gemini ADK execution error: {ex}")
                root_span.record_exception(ex)
                if self.provider:
                    self.provider.force_flush()
                raise ex
