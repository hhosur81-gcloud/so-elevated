# Production Dockerfile for So-Elevated Enterprise HR Assistant on Google Cloud Run
FROM python:3.11-slim

WORKDIR /app

# Prevent Python from buffering stdout/stderr and writing bytecode
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    APP_ENV=production \
    GOOGLE_GENAI_USE_VERTEXAI=true \
    GOOGLE_CLOUD_LOCATION=us-central1 \
    GOOGLE_CLOUD_REGION=us-central1 \
    WORKWEEK_MCP_URL=https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/ \
    WORKWEEK_MCP_TOKEN=mcp_fZFYPQVV1fAkmOYz4Lal8OVc9ltyLmfHiO4BZGCm-Tw \
    WORKWEEK_MCP_TOKEN_EMP_477=mcp_hleEvQkByz82OySU1A7CoX0-Jk4nyfxzMFujS-YDTLQ \
    ITSM_MCP_URL=https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/ \
    ITSM_MCP_TOKEN=mcp_iimWc8kxBKZR5m8hSgy_0tYy22fURzCR7Tn3KWsAOag \
    ITSM_MCP_TOKEN_EMP_477=mcp_hleEvQkByz82OySU1A7CoX0-Jk4nyfxzMFujS-YDTLQ

# Install dependencies via pip
ARG CACHE_BUST=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code, knowledge base, and configuration
COPY . .

EXPOSE 8080

# Run FastAPI app with Uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
