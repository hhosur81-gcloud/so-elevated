FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0
ENV GOOGLE_CLOUD_PROJECT=so-elevated
ENV GOOGLE_CLOUD_LOCATION=asia-south1
ENV REASONING_ENGINE_ID=1246520730456162304
ENV GEMINI_MODEL=gemini-2.5-flash
ENV GOOGLE_GENAI_USE_VERTEXAI=true

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application files
COPY . /app

EXPOSE 8080

CMD ["uvicorn", "ui_server:app", "--host", "0.0.0.0", "--port", "8080"]
