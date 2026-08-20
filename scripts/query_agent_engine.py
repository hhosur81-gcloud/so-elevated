#!/usr/bin/env python3
"""Interactive Client to query Vertex AI Agent Engine (Reasoning Engine) in Google Cloud."""

import json
import os
import subprocess
import sys
import urllib.request

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "no-vibing-here")
LOCATION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")


def get_gcloud_token():
    """Retrieve active gcloud access token."""
    res = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True)
    return res.stdout.strip()


def list_reasoning_engines():
    """List all deployed Reasoning Engines in the project."""
    token = get_gcloud_token()
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def query_reasoning_engine(engine_id: str, message: str, employee_id: str = "EMP-436"):
    """Send conversational query to Vertex AI Reasoning Engine instance."""
    token = get_gcloud_token()
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{engine_id}:query"
    payload = {
        "input": {
            "message": message,
            "employee_id": employee_id
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


if __name__ == "__main__":
    print(f"============================================================")
    print(f"🤖 Vertex AI Agent Engine Inspector ({PROJECT_ID} / {LOCATION})")
    print(f"============================================================")
    
    engines = list_reasoning_engines()
    print("Active Reasoning Engines:", json.dumps(engines, indent=2))
