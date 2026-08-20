FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend & static frontend
COPY . /app/ui
COPY ../knowledge /app/knowledge

EXPOSE 8080

CMD ["python", "/app/ui/ui_server.py"]
