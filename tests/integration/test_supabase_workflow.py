"""Supabase workflow and frontend-secret integration checks."""

import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_SUPABASE_INTEGRATION") != "1",
    reason="requires local Supabase; run through make test-supabase",
)


def test_supabase_target_propagates_forced_pytest_failure():
    """The documented integration target must return a non-zero exit status on failure."""
    workspace = Path(__file__).parents[2]
    result = subprocess.run(
        [
            "make",
            "test-supabase-existing",
            "SUPABASE_TEST_TARGETS=tests/test_database_config.py::test_does_not_exist",
        ],
        cwd=workspace,
        env=os.environ,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0


def test_frontend_build_excludes_privileged_supabase_sentinel():
    """Only publishable Supabase configuration may be emitted in browser assets."""
    workspace = Path(__file__).parents[2]
    frontend = workspace / "frontend"
    sentinel = "supabase-service-role-must-not-reach-browser"
    environment = os.environ | {
        "VITE_SUPABASE_URL": "http://127.0.0.1:54321",
        "VITE_SUPABASE_PUBLISHABLE_KEY": "publishable-test-key",
        "VITE_SUPABASE_SERVICE_ROLE_KEY": sentinel,
    }

    subprocess.run(["npm", "run", "build"], cwd=frontend, env=environment, check=True)

    assert all(
        sentinel not in asset.read_text(errors="ignore")
        for asset in (frontend / "dist").rglob("*")
        if asset.is_file()
    )
