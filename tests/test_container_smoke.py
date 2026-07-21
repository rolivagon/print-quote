"""Opt-in smoke test for the production container image."""

import os
import shutil
import socket
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "print-quote:container-smoke"
NETWORK = "print-quote-smoke"
DATABASE_CONTAINER = "print-quote-smoke-db"
APPLICATION_CONTAINER = "print-quote-smoke-app"


def _run(*args: str) -> None:
    subprocess.run(args, check=True, cwd=ROOT)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _get(url: str) -> bytes:
    with urlopen(url, timeout=1) as response:
        return response.read()


@pytest.mark.skipif(
    os.getenv("RUN_CONTAINER_SMOKE") != "1" or shutil.which("docker") is None,
    reason="set RUN_CONTAINER_SMOKE=1 with Docker available to run the production image smoke test",
)
def test_production_container_serves_spa_and_readiness() -> None:
    port = _free_port()
    _run("docker", "build", "--tag", IMAGE, ".")
    _run("docker", "network", "create", NETWORK)
    _run(
        "docker",
        "run",
        "--detach",
        "--name",
        DATABASE_CONTAINER,
        "--network",
        NETWORK,
        "--env",
        "POSTGRES_PASSWORD=postgres",
        "postgres:16-alpine",
    )

    try:
        for _ in range(30):
            database_ready = (
                subprocess.run(
                    ["docker", "exec", DATABASE_CONTAINER, "pg_isready", "-U", "postgres"],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                ).returncode
                == 0
            )
            if database_ready:
                break
            time.sleep(1)
        else:
            pytest.fail("PostgreSQL container did not become ready")

        _run(
            "docker",
            "run",
            "--detach",
            "--name",
            APPLICATION_CONTAINER,
            "--network",
            NETWORK,
            "--publish",
            f"{port}:8080",
            "--env",
            "DATABASE_URL=postgresql://postgres:postgres@print-quote-smoke-db:5432/postgres",
            "--env",
            "SUPABASE_URL=https://example.supabase.co",
            IMAGE,
        )

        for _ in range(30):
            try:
                if _get(f"http://127.0.0.1:{port}/health") == b'{"status":"ok"}':
                    break
            except OSError:
                time.sleep(1)
        else:
            pytest.fail("Application container did not become ready")

        assert b'<div id="app"></div>' in _get(f"http://127.0.0.1:{port}/")
        assert b'<div id="app"></div>' in _get(f"http://127.0.0.1:{port}/quotes")
        assert _get(f"http://127.0.0.1:{port}/images/logo/logo.png").startswith(b"\x89PNG")
    finally:
        subprocess.run(["docker", "rm", "--force", APPLICATION_CONTAINER], check=False)
        subprocess.run(["docker", "rm", "--force", DATABASE_CONTAINER], check=False)
        subprocess.run(["docker", "network", "rm", NETWORK], check=False)
