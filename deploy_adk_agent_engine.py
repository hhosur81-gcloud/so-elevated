#!/usr/bin/env python3
"""Deploy Native Vertex AI ADK LangchainAgents with OpenInference Tracing to Agent Platform."""

import os
import sys
import vertexai
from vertexai.preview import reasoning_engines

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
print(f"🚀 Deploying Native Vertex AI ADK Agents with Full Tracing")
print(f"   Project:        {PROJECT_ID}")
print(f"   Location:       {LOCATION}")
print(f"   Staging Bucket: {STAGING_BUCKET}")
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

# Tool Definitions
def get_leave_balances(employee_id: str = "EMP-436") -> str:
    """Fetch current remaining vacation and sick leave balances for an employee from WorkWeek HCM."""
    res = workweek_agent.get_balances(employee_id)
    return str(res.get("response", res))

def lookup_support_tickets(employee_id: str = "EMP-436") -> str:
    """Look up open IT support and facilities tickets for an employee from ServiceImmediately."""
    res = itsm_agent.lookup_tickets(user_message="", employee_id=employee_id)
    return str(res.get("response", res))

def create_support_ticket(short_description: str, employee_id: str = "EMP-436") -> str:
    """Create a new IT support incident, hardware request, loaner laptop order, or facilities ticket."""
    res = itsm_agent.create_ticket(user_message=short_description, employee_id=employee_id)
    return str(res.get("response", res))

def search_company_policies(policy_query: str, employee_role: str = "Employee") -> str:
    """Search 161 OKF enterprise policies for bereavement, travel expenses, allowances, and benefits with exact citation links."""
    res = policy_agent.answer_policy_query(policy_query, employee_role=employee_role)
    ans = res.get("answer", "")
    if res.get("citation_label") and res.get("citation_url"):
        ans += f"\n\nSource: [{res['citation_label']}]({res['citation_url']})"
    return ans

requirements = [
    "google-cloud-aiplatform[langchain,reasoningengine]>=1.44.0",
    "langchain-google-vertexai>=2.0.0",
    "langchain-google-genai>=2.0.0",
    "langchain>=0.3.0",
    "openinference-instrumentation-langchain>=0.1.50",
    "pydantic>=2.6.0",
    "cryptography>=42.0.0",
    "pyjwt>=2.8.0",
    "pyyaml>=6.0.1",
    "requests>=2.31.0",
    "opentelemetry-api>=1.24.0",
    "opentelemetry-sdk>=1.24.0",
    "opentelemetry-exporter-gcp-trace>=1.7.0",
    "google-cloud-logging>=3.8.0"
]

# 1. Deploy Policy Sub-Agent (ADK)
print("\n[1/4] Deploying Policy ADK Sub-Agent...")
policy_adk = reasoning_engines.LangchainAgent(
    model="gemini-2.5-flash",
    tools=[search_company_policies],
    system_instruction="You are the So-Elevated Enterprise Policy Specialist Agent. Search company policies to provide grounded answers with exact citation URLs.",
    enable_tracing=True
)

remote_policy = reasoning_engines.ReasoningEngine.create(
    policy_adk,
    requirements=requirements,
    extra_packages=["src", "knowledge"],
    display_name="so-elevated-policy-subagent",
    description="So-Elevated Policy Specialist ADK Agent with native Agent Platform tracing"
)
print(f"✅ Policy Sub-Agent Deployed: {remote_policy.resource_name}")

# 2. Deploy WorkWeek HCM Sub-Agent (ADK)
print("\n[2/4] Deploying WorkWeek HCM ADK Sub-Agent...")
workweek_adk = reasoning_engines.LangchainAgent(
    model="gemini-2.5-flash",
    tools=[get_leave_balances],
    system_instruction="You are the WorkWeek HCM Specialist Agent. Use tools to check leave balances.",
    enable_tracing=True
)

remote_workweek = reasoning_engines.ReasoningEngine.create(
    workweek_adk,
    requirements=requirements,
    extra_packages=["src", "knowledge"],
    display_name="so-elevated-workweek-subagent",
    description="So-Elevated WorkWeek HCM ADK Agent with native Agent Platform tracing"
)
print(f"✅ WorkWeek Sub-Agent Deployed: {remote_workweek.resource_name}")

# 3. Deploy ITSM Sub-Agent (ADK)
print("\n[3/4] Deploying ITSM ServiceImmediately ADK Sub-Agent...")
itsm_adk = reasoning_engines.LangchainAgent(
    model="gemini-2.5-flash",
    tools=[lookup_support_tickets, create_support_ticket],
    system_instruction="You are the ServiceImmediately ITSM Specialist Agent. Use tools to look up and create support tickets.",
    enable_tracing=True
)

remote_itsm = reasoning_engines.ReasoningEngine.create(
    itsm_adk,
    requirements=requirements,
    extra_packages=["src", "knowledge"],
    display_name="so-elevated-itsm-subagent",
    description="So-Elevated ITSM ADK Agent with native Agent Platform tracing"
)
print(f"✅ ITSM Sub-Agent Deployed: {remote_itsm.resource_name}")

# 4. Deploy Master Orchestrator (ADK)
print("\n[4/4] Deploying Master HR Orchestrator ADK Agent...")
orchestrator_adk = reasoning_engines.LangchainAgent(
    model="gemini-2.5-flash",
    tools=[get_leave_balances, lookup_support_tickets, create_support_ticket, search_company_policies],
    system_instruction="You are the So-Elevated Enterprise HR & IT Virtual Assistant. Coordinate HCM, ITSM, and Policy inquiries using live tools.",
    enable_tracing=True
)

remote_orchestrator = reasoning_engines.ReasoningEngine.create(
    orchestrator_adk,
    requirements=requirements,
    extra_packages=["src", "knowledge"],
    display_name="so-elevated-hr-agent-engine",
    description="So-Elevated Master HR Orchestrator ADK Agent with native Agent Platform tracing"
)
print(f"✅ Master Orchestrator Deployed: {remote_orchestrator.resource_name}")

print("\n" + "=" * 60)
print("🎉 ALL 4 ADK AGENTS DEPLOYED TO VERTEX AI AGENT PLATFORM WITH FULL TRACING!")
print(f"Policy:       {remote_policy.resource_name}")
print(f"WorkWeek:     {remote_workweek.resource_name}")
print(f"ITSM:         {remote_itsm.resource_name}")
print(f"Orchestrator: {remote_orchestrator.resource_name}")
print("=" * 60)
