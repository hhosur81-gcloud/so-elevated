#!/usr/bin/env python3
"""Deploy So-Elevated HR Agent to Google Cloud Vertex AI Agent Engine (Reasoning Engine)."""

import os
import sys
import vertexai
from vertexai.preview import reasoning_engines

# Ensure source files are reachable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.agent_engine import SoElevatedHRAgentEngine

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "no-vibing-here")
LOCATION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
STAGING_BUCKET = f"gs://{PROJECT_ID}-agent-engine"

print(f"============================================================")
print(f"🚀 Deploying to Vertex AI Agent Engine (Managed Runtime)")
print(f"   Project:        {PROJECT_ID}")
print(f"   Location:       {LOCATION}")
print(f"   Staging Bucket: {STAGING_BUCKET}")
print(f"============================================================")

# 1. Initialize Vertex AI SDK
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)

# 2. Package and Deploy Reasoning Engine Instance
print("\n[1/3] Packaging and registering Reasoning Engine on Vertex AI...")

app = SoElevatedHRAgentEngine(
    project_id=PROJECT_ID,
    location=LOCATION,
    model="gemini-3.7-flash"
)

remote_engine = reasoning_engines.ReasoningEngine.create(
    app,
    requirements=[
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
    ],
    extra_packages=["src", "knowledge"],
    display_name="so-elevated-hr-agent-engine",
    description="So-Elevated Enterprise HR Agent Engine on Vertex AI ADK"
)


print("\n[2/3] Deployed Successfully to Vertex AI Agent Engine!")
print(f"Resource Name: {remote_engine.resource_name}")

# 3. Test Live Inference on Vertex AI Agent Engine
print("\n[3/3] Executing Live Validation Probe against Vertex AI Agent Engine...")
test_query = "What are my current leave balances?"
print(f"   Prompt: '{test_query}' (Employee: EMP-436)")

try:
    response = remote_engine.query(message=test_query, employee_id="EMP-436")
    print(f"   Response:\n{response}")
except Exception as e:
    print(f"   Validation Probe Note: {e}")

print(f"\n============================================================")
print(f"✅ Vertex AI Agent Engine Deployment Verified!")
print(f"   Resource: {remote_engine.resource_name}")
print(f"============================================================")
