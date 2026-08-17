# Strict Live Vertex AI Search Connection for Policy Retrieval

To guarantee zero discrepancy between test environments and production deployment, all Policy Q&A integration and end-to-end evaluation tests strictly connect to live Google Cloud Vertex AI Search datastores using authentic GCP project credentials, failing fast if the cloud datastore is unavailable.
