#!/usr/bin/env bash
# Deploy So-Elevated HR Assistant to Google Cloud Run
set -euo pipefail

PROJECT_ID="${1:-no-vibing-here}"
REGION="${2:-us-central1}"
SERVICE_NAME="so-elevated-hr-agent"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "============================================================"
echo "🚀 Deploying So-Elevated HR Assistant to Google Cloud Run"
echo "   Project: ${PROJECT_ID}"
echo "   Region:  ${REGION}"
echo "   Image:   ${IMAGE_TAG}"
echo "============================================================"

# 1. Enable required GCP APIs
echo "[1/4] Enabling required GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  --project "${PROJECT_ID}"

# 2. Build Container Image via Cloud Build
echo "[2/4] Building container image via Google Cloud Build..."
gcloud builds submit \
  --project "${PROJECT_ID}" \
  --tag "${IMAGE_TAG}" \
  .

# 3. Deploy to Cloud Run
echo "[3/4] Deploying to Cloud Run service '${SERVICE_NAME}'..."
gcloud run deploy "${SERVICE_NAME}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --image "${IMAGE_TAG}" \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GEMINI_MODEL=gemini-3.7-flash,GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_CLOUD_REGION=${REGION},WORKWEEK_MCP_URL=https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/,WORKWEEK_MCP_TOKEN=mcp_fZFYPQVV1fAkmOYz4Lal8OVc9ltyLmfHiO4BZGCm-Tw,WORKWEEK_MCP_TOKEN_EMP_477=mcp_hleEvQkByz82OySU1A7CoX0-Jk4nyfxzMFujS-YDTLQ,ITSM_MCP_URL=https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/,ITSM_MCP_TOKEN=mcp_iimWc8kxBKZR5m8hSgy_0tYy22fURzCR7Tn3KWsAOag,ITSM_MCP_TOKEN_EMP_477=mcp_hleEvQkByz82OySU1A7CoX0-Jk4nyfxzMFujS-YDTLQ"

# 4. Verify deployment and fetch live URL
echo "[4/4] Verifying deployment..."
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --project "${PROJECT_ID}" --region "${REGION}" --format='value(status.url)')

echo "============================================================"
echo "✅ Deployment Successful!"
echo "🌐 Live Application URL: ${SERVICE_URL}"
echo "============================================================"
