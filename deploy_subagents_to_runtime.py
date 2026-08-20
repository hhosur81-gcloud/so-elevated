#!/usr/bin/env python3
"""Deploy dedicated sub-agents (WorkWeek, ITSM, Policy) to Vertex AI Agent Runtime (Reasoning Engine)."""

import os
import sys
import vertexai
from vertexai.preview import reasoning_engines

# Ensure source files are reachable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.agent_engine import ITSMAgentEngine, PolicyAgentEngine, WorkWeekAgentEngine

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "no-vibing-here")
LOCATION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
STAGING_BUCKET = f"gs://{PROJECT_ID}-agent-engine"

print(f"============================================================")
print(f"🚀 Deploying Dedicated Sub-Agents to Vertex AI Agent Runtime")
print(f"   Project:        {PROJECT_ID}")
print(f"   Location:       {LOCATION}")
print(f"   Staging Bucket: {STAGING_BUCKET}")
print(f"============================================================")

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)

requirements = [
    "google-cloud-aiplatform>=1.44.0",
    "google-genai>=0.1.1",
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

# 1. Deploy WorkWeek HCM Sub-Agent
print("\n[1/3] Deploying WorkWeek HCM Sub-Agent...")
ww_app = WorkWeekAgentEngine(project_id=PROJECT_ID, location=LOCATION)
ww_engine = reasoning_engines.ReasoningEngine.create(
    ww_app,
    requirements=requirements,
    extra_packages=["src", "knowledge"],
    display_name="so-elevated-workweek-subagent",
    description="Dedicated WorkWeek HCM Specialist Sub-Agent on Vertex AI Agent Runtime"
)
print(f"✅ WorkWeek Sub-Agent Deployed: {ww_engine.resource_name}")

# 2. Deploy ITSM Sub-Agent
print("\n[2/3] Deploying ITSM ServiceImmediately Sub-Agent...")
itsm_app = ITSMAgentEngine(project_id=PROJECT_ID, location=LOCATION)
itsm_engine = reasoning_engines.ReasoningEngine.create(
    itsm_app,
    requirements=requirements,
    extra_packages=["src", "knowledge"],
    display_name="so-elevated-itsm-subagent",
    description="Dedicated ServiceImmediately ITSM Specialist Sub-Agent on Vertex AI Agent Runtime"
)
print(f"✅ ITSM Sub-Agent Deployed: {itsm_engine.resource_name}")

# 3. Deploy Policy Specialist Sub-Agent
print("\n[3/3] Deploying Policy Grounding Sub-Agent...")
pol_app = PolicyAgentEngine(project_id=PROJECT_ID, location=LOCATION)
pol_engine = reasoning_engines.ReasoningEngine.create(
    pol_app,
    requirements=requirements,
    extra_packages=["src", "knowledge"],
    display_name="so-elevated-policy-subagent",
    description="Dedicated Policy Grounding Specialist Sub-Agent on Vertex AI Agent Runtime"
)
print(f"✅ Policy Sub-Agent Deployed: {pol_engine.resource_name}")

print("\n============================================================")
print("🎉 All Dedicated Sub-Agents Successfully Deployed on Agent Runtime!")
print(f"  • WorkWeek Sub-Agent: {ww_engine.resource_name}")
print(f"  • ITSM Sub-Agent:     {itsm_engine.resource_name}")
print(f"  • Policy Sub-Agent:   {pol_engine.resource_name}")
print("============================================================")
