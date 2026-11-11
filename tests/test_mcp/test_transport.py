"""MCP endpoint contracts that do not require a database."""

import uuid
from types import SimpleNamespace

import pytest

from quote.api.deps import get_current_user
from quote.api.main import app
from quote.domain.enums import UserRole

EXPECTED_TOOLS = {"list_clients", "list_papers", "list_finishes", "preview_quote", "create_quote"}


@pytest.fixture
def seller():
    user = SimpleNamespace(id=uuid.uuid4(), role=UserRole.VENDEDOR, is_active=True)
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.clear()


def test_mcp_without_bearer_token_is_rejected(raw_mcp_request):
    """Requests without a bearer token never reach the MCP server."""
    response = raw_mcp_request(token=None)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_mcp_with_invalid_token_is_rejected(raw_mcp_request, monkeypatch):
    """Tokens that fail Supabase validation are rejected with 401."""
    from quote.api import deps
    from quote.service.security import InvalidAccessToken

    def reject(_token):
        raise InvalidAccessToken("bad token")

    monkeypatch.setattr(deps, "validate_supabase_access_token", reject)

    response = raw_mcp_request(token="not-a-jwt")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_mcp_lists_quote_tools_for_authenticated_user(run_mcp, seller):
    """An authenticated client initializes the stateless server and lists the quote tools."""

    async def scenario(client):
        result = await client.list_tools()
        return {tool.name for tool in result.tools}

    assert run_mcp(scenario) == EXPECTED_TOOLS


def test_mcp_tool_validation_errors_are_tool_errors(run_mcp, seller):
    """Domain validation failures are reported as MCP tool errors."""

    async def scenario(client):
        return await client.call_tool("list_papers", {"print_type": "digital"})

    result = run_mcp(scenario)

    assert result.is_error
    assert "color_mode is required" in result.content[0].text


def test_mcp_is_not_captured_by_spa_fallback(raw_mcp_request, seller):
    """GET /mcp is served by the MCP transport, never by the SPA index."""
    response = raw_mcp_request(method="GET", token="token")

    assert response.status_code == 405
    assert response.headers["allow"] == "POST"
