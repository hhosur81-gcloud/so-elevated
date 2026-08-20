#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PROJECT_ID="${1:-so-elevated}"
REGION="${2:-asia-south1}"

echo "=========================================================================="
echo " Deploying ADK Agent to Google Cloud Vertex AI Agent Runtime"
echo " Project: $PROJECT_ID"
echo " Region:  $REGION (Mumbai, India)"
echo " Model:   gemini-3.5-flash (Global endpoint)"
echo "=========================================================================="

.venv/bin/adk deploy agent_engine \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --display_name="Altostrat HR & IT Agentic Orchestrator" \
  --description="Tier-1 Enterprise HR & ITSM Assistant with OKF grounding and live FastMCP tools" \
  --extra_packages="knowledge" \
  agent

echo "=========================================================================="
echo " Deployment to Vertex AI Agent Runtime Complete!"
echo "=========================================================================="
