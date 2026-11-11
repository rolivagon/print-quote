"""Helpers to talk to the mounted MCP endpoint through the real application lifespan."""

from collections.abc import Awaitable, Callable
from typing import Any

import anyio
import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from quote.api import main
from quote.repo.models import SQLModel

MCP_URL = "http://testserver/mcp"


@pytest.fixture(scope="session")
def engine():
    """In-memory engine shared across threads: MCP runs synchronous tools in a worker thread."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


class _Connection:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *_: object) -> None:
        return None


class _Engine:
    def connect(self) -> _Connection:
        return _Connection()


def _http_client(token: str | None) -> httpx2.AsyncClient:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx2.AsyncClient(
        transport=httpx2.ASGITransport(app=main.app), base_url="http://testserver", headers=headers
    )


@pytest.fixture
def run_mcp(monkeypatch) -> Callable[..., Any]:
    """Run `scenario(client)` against /mcp inside the application lifespan.

    The database connectivity check is replaced so transport tests stay database-free;
    data-backed tests override `get_db` like the API fixtures do.
    """
    monkeypatch.setattr(main, "configure_database", lambda: _Engine())

    def run(scenario: Callable[[Client], Awaitable[Any]], token: str | None = "token") -> Any:
        async def main_task() -> Any:
            async with main.lifespan(main.app):
                async with _http_client(token) as http_client:
                    transport = streamable_http_client(MCP_URL, http_client=http_client)
                    async with Client(transport) as client:
                        return await scenario(client)

        return anyio.run(main_task)

    return run


@pytest.fixture
def raw_mcp_request(monkeypatch) -> Callable[..., httpx2.Response]:
    """Send one raw HTTP request to /mcp inside the application lifespan."""
    monkeypatch.setattr(main, "configure_database", lambda: _Engine())

    def send(method: str = "POST", token: str | None = None) -> httpx2.Response:
        async def main_task() -> httpx2.Response:
            async with main.lifespan(main.app):
                async with _http_client(token) as http_client:
                    return await http_client.request(
                        method,
                        "/mcp",
                        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                        headers={"Accept": "application/json, text/event-stream"},
                    )

        return anyio.run(main_task)

    return send
