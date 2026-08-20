"""Automated Cloud Build & Cloud Run deployment script for Altostrat HR Portal."""
import io
import json
import os
import sys
import tarfile
import time
from pathlib import Path
import google.auth
import google.auth.transport.requests
import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
UI_DIR = REPO_ROOT / "ui"

PROJECT_ID = "so-elevated"
PROJECT_NUMBER = "501431672831"
REGION = "asia-south1"
SERVICE_NAME = "altostrat-hr-portal"
IMAGE_TAG = f"{REGION}-docker.pkg.dev/{PROJECT_ID}/cloud-run-apps/{SERVICE_NAME}:latest"
STAGING_BUCKET = f"{PROJECT_ID}-cloudbuild-staging"
SOURCE_OBJECT = f"sources/{SERVICE_NAME}-{int(time.time())}.tar.gz"

def get_auth_headers():
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return {"Authorization": f"Bearer {credentials.token}"}

def create_source_tarball() -> bytes:
    print(f"📦 Packaging source files from {UI_DIR}...")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for root, dirs, files in os.walk(UI_DIR):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".pytest_cache", ".venv")]
            for file in files:
                if file.endswith((".pyc", ".pyo")):
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(UI_DIR)
                tar.add(file_path, arcname=str(rel_path))
    buf.seek(0)
    data = buf.read()
    print(f"   Archive size: {len(data) / 1024:.1f} KB")
    return data

def upload_source_to_gcs(data: bytes):
    headers = get_auth_headers()
    headers["Content-Type"] = "application/gzip"
    upload_url = f"https://storage.googleapis.com/upload/storage/v1/b/{STAGING_BUCKET}/o?uploadType=media&name={SOURCE_OBJECT}"
    print(f"⬆️  Uploading source archive to gs://{STAGING_BUCKET}/{SOURCE_OBJECT}...")
    resp = httpx.post(upload_url, headers=headers, content=data, timeout=60.0)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"GCS Upload failed: {resp.status_code} {resp.text}")
    print("   Upload complete!")

def trigger_cloud_build() -> str:
    headers = get_auth_headers()
    headers["Content-Type"] = "application/json"
    build_url = f"https://cloudbuild.googleapis.com/v1/projects/{PROJECT_ID}/builds"
    
    build_config = {
        "source": {
            "storageSource": {
                "bucket": STAGING_BUCKET,
                "object": SOURCE_OBJECT,
            }
        },
        "steps": [
            {
                "name": "gcr.io/cloud-builders/docker",
                "args": ["build", "-t", IMAGE_TAG, "."],
            },
            {
                "name": "gcr.io/cloud-builders/docker",
                "args": ["push", IMAGE_TAG],
            }
        ],
        "images": [IMAGE_TAG],
        "options": {
            "logging": "LEGACY",
        }
    }
    
    print(f"🔨 Submitting Cloud Build for image {IMAGE_TAG}...")
    resp = httpx.post(build_url, headers=headers, json=build_config, timeout=60.0)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Cloud Build submission failed: {resp.status_code} {resp.text}")
    
    build_data = resp.json()
    build_id = build_data.get("metadata", {}).get("build", {}).get("id") or build_data.get("id")
    print(f"   Build ID: {build_id}")
    return build_id

def wait_for_build(build_id: str):
    headers = get_auth_headers()
    status_url = f"https://cloudbuild.googleapis.com/v1/projects/{PROJECT_ID}/builds/{build_id}"
    print("⏳ Building container image in Google Cloud...")
    
    while True:
        resp = httpx.get(status_url, headers=headers, timeout=30.0)
        if resp.status_code != 200:
            print(f"Warning: Could not fetch build status ({resp.status_code})")
            time.sleep(5)
            continue
            
        data = resp.json()
        status = data.get("status")
        print(f"   Build status: {status}")
        
        if status == "SUCCESS":
            print("✅ Container build and push succeeded!")
            break
        elif status in ("FAILURE", "INTERNAL_ERROR", "TIMEOUT", "CANCELLED"):
            raise RuntimeError(f"Cloud Build failed with status: {status}")
            
        time.sleep(8)

def deploy_to_cloud_run() -> str:
    headers = get_auth_headers()
    headers["Content-Type"] = "application/json"
    
    get_url = f"https://run.googleapis.com/v2/projects/{PROJECT_ID}/locations/{REGION}/services/{SERVICE_NAME}"
    r_get = httpx.get(get_url, headers=headers, timeout=30.0)
    
    service_payload = {
        "template": {
            "containers": [
                {
                    "image": IMAGE_TAG,
                    "env": [
                        {"name": "GOOGLE_CLOUD_PROJECT", "value": PROJECT_ID},
                        {"name": "GOOGLE_CLOUD_LOCATION", "value": REGION},
                        {"name": "REASONING_ENGINE_ID", "value": "1246520730456162304"},
                        {"name": "GEMINI_MODEL", "value": "gemini-2.5-flash"},
                        {"name": "GOOGLE_GENAI_USE_VERTEXAI", "value": "true"},
                    ],
                    "resources": {
                        "limits": {
                            "cpu": "1000m",
                            "memory": "512Mi"
                        }
                    },
                    "ports": [
                        {"containerPort": 8080}
                    ]
                }
            ],
            "scaling": {
                "minInstanceCount": 0,
                "maxInstanceCount": 10
            }
        }
    }
    
    if r_get.status_code == 200:
        print(f"🔄 Updating existing Cloud Run service '{SERVICE_NAME}'...")
        patch_url = f"https://run.googleapis.com/v2/projects/{PROJECT_ID}/locations/{REGION}/services/{SERVICE_NAME}?updateMask=template"
        r = httpx.patch(patch_url, headers=headers, json=service_payload, timeout=60.0)
    else:
        print(f"🚀 Creating new Cloud Run service '{SERVICE_NAME}'...")
        post_url = f"https://run.googleapis.com/v2/projects/{PROJECT_ID}/locations/{REGION}/services?serviceId={SERVICE_NAME}"
        r = httpx.post(post_url, headers=headers, json=service_payload, timeout=60.0)
        
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Cloud Run deployment failed: {r.status_code} {r.text}")
        
    op_name = r.json().get("name")
    print(f"   Operation: {op_name}")
    
    print("⏳ Waiting for Cloud Run service readiness...")
    service_uri = None
    for i in range(30):
        time.sleep(6)
        svc_resp = httpx.get(get_url, headers=headers, timeout=30.0)
        if svc_resp.status_code == 200:
            svc_data = svc_resp.json()
            uri = svc_data.get("uri")
            conditions = svc_data.get("terminalCondition", {})
            state = conditions.get("state")
            print(f"   [Check {i+1}] State: {state}, URI: {uri}")
            if uri and state == "CONDITION_SUCCEEDED":
                print(f"✅ Cloud Run Service Ready at: {uri}")
                service_uri = uri
                break
            elif state == "CONDITION_FAILED":
                msg = conditions.get("message", "")
                raise RuntimeError(f"Cloud Run service failed: {msg}")
    
    if not service_uri:
        svc_data = httpx.get(get_url, headers=headers, timeout=30.0).json()
        service_uri = svc_data.get("uri", f"https://{SERVICE_NAME}-xxxx.a.run.app")
    
    return service_uri

def allow_unauthenticated_access():
    """Configure IAM policy on Cloud Run to allow allUsers unauthenticated invocation."""
    print("🔓 Granting unauthenticated public access (allUsers -> roles/run.invoker)...")
    headers = get_auth_headers()
    headers["Content-Type"] = "application/json"
    iam_url = f"https://run.googleapis.com/v2/projects/{PROJECT_ID}/locations/{REGION}/services/{SERVICE_NAME}:setIamPolicy"
    iam_policy = {
        "policy": {
            "bindings": [
                {
                    "role": "roles/run.invoker",
                    "members": ["allUsers"]
                }
            ]
        }
    }
    resp = httpx.post(iam_url, headers=headers, json=iam_policy, timeout=30.0)
    if resp.status_code == 200:
        print("✅ Unauthenticated public access granted to allUsers successfully!")
    else:
        print(f"⚠️ IAM policy response: {resp.status_code} {resp.text}")

def main():
    print("=" * 75)
    print(f"🚀 Deploying Altostrat HR Portal to Google Cloud Run ({REGION})")
    print("=" * 75)
    tar_data = create_source_tarball()
    upload_source_to_gcs(tar_data)
    build_id = trigger_cloud_build()
    wait_for_build(build_id)
    service_uri = deploy_to_cloud_run()
    allow_unauthenticated_access()
    print("=" * 75)
    print(f"🎉 DEPLOYMENT COMPLETE! Live Cloud Run URL:")
    print(f"   👉 {service_uri}")
    print("=" * 75)

if __name__ == "__main__":
    main()
