"""Operational contract tests for the Plotter catalog Makefile targets."""

import subprocess
from pathlib import Path


def test_plotter_production_loader_explicitly_loads_prod_environment_with_override():
    workspace = Path(__file__).parents[1]
    result = subprocess.run(
        ["make", "-n", "load-plotter-data-prod"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "set -a && . ./.env.prod && set +a &&" in result.stdout
    assert "-e load-plotter-data" in result.stdout
