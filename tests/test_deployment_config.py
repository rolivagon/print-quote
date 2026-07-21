"""Static contracts for the Cloud Run deployment artifacts."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_docker_image_builds_the_production_spa() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "npm ci" in dockerfile
    assert "npm run build" in dockerfile
    assert "frontend/dist" in dockerfile
    assert "FRONTEND_DIST=/app/frontend/dist" in dockerfile
    assert "uvicorn quote.api.main:app" in dockerfile


def test_cloud_build_deploys_public_service_to_configured_project() -> None:
    cloudbuild = (ROOT / "cloudbuild.yaml").read_text()

    assert "--project=rodxdev-prod" in cloudbuild
    assert "--allow-unauthenticated" in cloudbuild
    assert "      - print-quote" in cloudbuild


def test_cloud_run_uses_secret_manager_references() -> None:
    cloudbuild = (ROOT / "cloudbuild.yaml").read_text()

    assert "DATABASE_URL=print-quote-database-url:latest" in cloudbuild
    assert "SUPABASE_URL=print-quote-supabase-url:latest" in cloudbuild
    assert "SUPABASE_SERVICE_ROLE_KEY=print-quote-supabase-service-role-key:latest" in cloudbuild


def test_deployment_artifacts_do_not_contain_runtime_secret_values() -> None:
    artifacts = [
        ROOT / "Dockerfile",
        ROOT / "cloudbuild.yaml",
        ROOT / "docs" / "cloud-run-deployment.md",
    ]

    for artifact in artifacts:
        assert not re.search(r"postgres(?:ql(?:\+[a-z0-9_]+)?)?://", artifact.read_text())


def test_sensitive_runtime_variables_are_only_mapped_from_secret_manager() -> None:
    cloudbuild = (ROOT / "cloudbuild.yaml").read_text()
    sensitive_assignment = re.compile(
        r"(?<!VITE_)(?:DATABASE_URL|SUPABASE_URL|SUPABASE_SERVICE_ROLE_KEY)="
    )
    sensitive_lines = [
        line.strip() for line in cloudbuild.splitlines() if sensitive_assignment.search(line)
    ]

    assert sensitive_lines == [
        "- --set-secrets=DATABASE_URL=print-quote-database-url:latest,SUPABASE_URL=print-quote-supabase-url:latest,SUPABASE_SERVICE_ROLE_KEY=print-quote-supabase-service-role-key:latest"
    ]


def test_deployment_documentation_covers_manual_deployment_and_rollback() -> None:
    documentation = (ROOT / "docs" / "cloud-run-deployment.md").read_text()

    assert "gcloud builds submit" in documentation
    assert "Rollback" in documentation
    assert "Secret Manager" in documentation
