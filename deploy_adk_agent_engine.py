#!/usr/bin/env python3
"""Deploy Native Google ADK (google-adk) LlmAgents with AdkApp to Vertex AI Agent Platform."""

import os
import sys
import vertexai
from vertexai.preview import reasoning_engines
from google.adk.agents import LlmAgent

# Ensure source files are reachable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.agents.itsm_agent import ITSMAgent
from src.agents.policy_agent import PolicyAgent
from src.agents.workweek_agent import WorkWeekAgent
from src.repositories.filestore_repository import FileStoreRepository

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "no-vibing-here")
LOCATION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
STAGING_BUCKET = f"gs://{PROJECT_ID}-agent-engine"

print("=" * 60)
print(f"🚀 Deploying Native Google ADK Agents (Framework: google-adk)")
print(f"   Project:        {PROJECT_ID}")
print(f"   Location:       {LOCATION}")
print(f"   Staging Bucket: {STAGING_BUCKET}")
print(f"   Prefix:         group6-adk")
print("=" * 60)

# Initialize Vertex AI SDK
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)

repo = FileStoreRepository()
workweek_agent = WorkWeekAgent(repository=repo)
itsm_agent = ITSMAgent(repository=repo)
policy_agent = PolicyAgent(policy_dir="knowledge" if os.path.exists("knowledge") else "fixtures/sample_policies")

# Tool Definitions returning dicts
def get_leave_balances(employee_id: str = "EMP-436") -> dict:
    """Fetch current remaining vacation and sick leave balances for an employee from WorkWeek HCM."""
    try:
        res = workweek_agent.get_balances(employee_id)
        if isinstance(res, dict):
            return res
        return {"response": str(res)}
    except Exception as e:
        return {"error": str(e)}

def lookup_support_tickets(employee_id: str = "EMP-436") -> dict:
    """Look up open IT support and facilities tickets for an employee from ServiceImmediately."""
    try:
        res = itsm_agent.lookup_tickets(user_message="", employee_id=employee_id)
        if isinstance(res, dict):
            return res
        return {"response": str(res)}
    except Exception as e:
        return {"error": str(e)}

def create_support_ticket(short_description: str, employee_id: str = "EMP-436") -> dict:
    """Create a new IT support incident, hardware request, loaner laptop order, or facilities ticket."""
    try:
        res = itsm_agent.create_ticket(user_message=short_description, employee_id=employee_id)
        if isinstance(res, dict):
            return res
        return {"response": str(res)}
    except Exception as e:
        return {"error": str(e)}

def search_company_policies(policy_query: str, employee_role: str = "Employee") -> dict:
    """Search 161 OKF enterprise policies for bereavement, travel expenses, allowances, and benefits with exact citation links."""
    try:
        res = policy_agent.answer_policy_query(policy_query, employee_role=employee_role)
        if isinstance(res, dict):
            return res
        return {"answer": str(res)}
    except Exception as e:
        return {"error": str(e)}

requirements = [
    "google-adk>=2.4.0",
    "google-genai>=2.11.0",
    "google-cloud-aiplatform>=1.44.0",
    "pydantic>=2.6.0",
    "requests>=2.31.0",
    "pyyaml>=6.0.1",
    "authlib>=1.3.0",
    "joserfc>=0.9.0",
    "opentelemetry-api>=1.24.0",
    "opentelemetry-sdk>=1.24.0",
    "opentelemetry-exporter-gcp-trace>=1.7.0",
    "google-cloud-logging>=3.8.0"
]

env_vars = {
    "GOOGLE_GENAI_USE_VERTEXAI": "true",
    "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
    "GOOGLE_CLOUD_LOCATION": LOCATION,
    "GOOGLE_CLOUD_REGION": LOCATION,
    "WORKWEEK_MCP_URL": os.getenv("WORKWEEK_MCP_URL", "https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/"),
    "WORKWEEK_MCP_TOKEN": os.getenv("WORKWEEK_MCP_TOKEN", "mcp_fZFYPQVV1fAkmOYz4Lal8OVc9ltyLmfHiO4BZGCm-Tw"),
    "WORKWEEK_MCP_TOKEN_EMP_477": os.getenv("WORKWEEK_MCP_TOKEN_EMP_477", "mcp_hleEvQkByz82OySU1A7CoX0-Jk4nyfxzMFujS-YDTLQ"),
    "ITSM_MCP_URL": os.getenv("ITSM_MCP_URL", "https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/"),
    "ITSM_MCP_TOKEN": os.getenv("ITSM_MCP_TOKEN", "mcp_iimWc8kxBKZR5m8hSgy_0tYy22fURzCR7Tn3KWsAOag"),
    "ITSM_MCP_TOKEN_EMP_477": os.getenv("ITSM_MCP_TOKEN_EMP_477", "mcp_hleEvQkByz82OySU1A7CoX0-Jk4nyfxzMFujS-YDTLQ"),
}

# 1. Deploy Policy Sub-Agent (ADK)
print("\n[1/4] Deploying Policy ADK Sub-Agent (google-adk)...")
policy_adk_agent = LlmAgent(
    name="policy_specialist",
    model="gemini-2.5-flash",
    instruction="You are the So-Elevated Enterprise Policy Specialist Agent. Search company policies to provide grounded answers with exact citation URLs.",
    tools=[search_company_policies],
)
policy_app = reasoning_engines.AdkApp(
    agent=policy_adk_agent,
    enable_tracing=True,
    env_vars=env_vars,
)

remote_policy = reasoning_engines.ReasoningEngine.create(
    policy_app,
    requirements=requirements,
    extra_packages=["src", "knowledge"],
    display_name="group6-adk-policy-subagent",
    description="Group6 Policy Specialist ADK Agent with native google-adk framework and Agent Platform tracing"
)
print(f"✅ Policy Sub-Agent Deployed: {remote_policy.resource_name}")

# 2. Deploy WorkWeek HCM Sub-Agent (ADK)
print("\n[2/4] Deploying WorkWeek HCM ADK Sub-Agent (google-adk)...")
workweek_adk_agent = LlmAgent(
    name="workweek_specialist",
    model="gemini-2.5-flash",
    instruction="You are the WorkWeek HCM Specialist Agent. Use tools to check leave balances.",
    tools=[get_leave_balances],
)
workweek_app = reasoning_engines.AdkApp(
    agent=workweek_adk_agent,
    enable_tracing=True,
    env_vars=env_vars,
)

remote_workweek = reasoning_engines.ReasoningEngine.create(
    workweek_app,
    requirements=requirements,
    extra_packages=["src", "knowledge"],
    display_name="group6-adk-workweek-subagent",
    description="Group6 WorkWeek HCM ADK Agent with native google-adk framework and Agent Platform tracing"
)
print(f"✅ WorkWeek Sub-Agent Deployed: {remote_workweek.resource_name}")

# 3. Deploy ITSM Sub-Agent (ADK)
print("\n[3/4] Deploying ITSM ServiceImmediately ADK Sub-Agent (google-adk)...")
itsm_adk_agent = LlmAgent(
    name="itsm_specialist",
    model="gemini-2.5-flash",
    instruction="You are the ServiceImmediately ITSM Specialist Agent. Use tools to look up and create support tickets.",
    tools=[lookup_support_tickets, create_support_ticket],
)
itsm_app = reasoning_engines.AdkApp(
    agent=itsm_adk_agent,
    enable_tracing=True,
    env_vars=env_vars,
)

remote_itsm = reasoning_engines.ReasoningEngine.create(
    itsm_app,
    requirements=requirements,
    extra_packages=["src", "knowledge"],
    display_name="group6-adk-itsm-subagent",
    description="Group6 ITSM ADK Agent with native google-adk framework and Agent Platform tracing"
)
print(f"✅ ITSM Sub-Agent Deployed: {remote_itsm.resource_name}")

# 4. Deploy Master Orchestrator (ADK)
print("\n[4/4] Deploying Master HR Orchestrator ADK Agent (google-adk)...")
orchestrator_adk_agent = LlmAgent(
    name="hr_orchestrator",
    model="gemini-2.5-flash",
    instruction="You are the So-Elevated Enterprise HR & IT Virtual Assistant. Coordinate HCM, ITSM, and Policy inquiries using live tools.",
    tools=[get_leave_balances, lookup_support_tickets, create_support_ticket, search_company_policies],
)
orchestrator_app = reasoning_engines.AdkApp(
    agent=orchestrator_adk_agent,
    enable_tracing=True,
    env_vars=env_vars,
)

remote_orchestrator = reasoning_engines.ReasoningEngine.create(
    orchestrator_app,
    requirements=requirements,
    extra_packages=["src", "knowledge"],
    display_name="group6-adk-hr-agent-engine",
    description="Group6 Master HR Orchestrator ADK Agent with native google-adk framework and Agent Platform tracing"
)
print(f"✅ Master Orchestrator Deployed: {remote_orchestrator.resource_name}")

print("\n" + "=" * 60)
print("🎉 ALL 4 ADK AGENTS DEPLOYED TO VERTEX AI AGENT PLATFORM AS google-adk!")
print(f"Policy:       {remote_policy.resource_name}")
print(f"WorkWeek:     {remote_workweek.resource_name}")
print(f"ITSM:         {remote_itsm.resource_name}")
print(f"Orchestrator: {remote_orchestrator.resource_name}")
print("=" * 60)
