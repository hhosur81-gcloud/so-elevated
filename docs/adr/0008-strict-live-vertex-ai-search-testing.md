# Strict Repository-Managed Open Knowledge Format (OKF) Policy Knowledge Testing & Validation

To guarantee zero discrepancy between test environments and production deployment, all Policy Q&A integration and end-to-end evaluation tests strictly validate policy answers directly against the canonical Open Knowledge Format (OKF) Markdown files in the repository (`knowledge/`), enforcing exact citation anchor resolution and failing fast if required policy concepts or schema frontmatters are missing.
