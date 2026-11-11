"""OAuth discovery contracts that let MCP clients find the Supabase authorization server."""

import pytest
from fastapi.testclient import TestClient

from quote.api.main import app

SUPABASE_URL = "https://project.supabase.co"
METADATA_URL = "http://testserver/.well-known/oauth-protected-resource/mcp"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", SUPABASE_URL)
    return TestClient(app)


@pytest.mark.parametrize(
    "path", ["/.well-known/oauth-protected-resource/mcp", "/.well-known/oauth-protected-resource"]
)
def test_protected_resource_metadata_points_to_supabase(client, path):
    """Both discovery paths describe /mcp and its Supabase authorization server without auth."""
    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "resource": "http://testserver/mcp",
        "authorization_servers": [f"{SUPABASE_URL}/auth/v1"],
        "bearer_methods_supported": ["header"],
        "resource_name": "Print Quote",
    }


def test_protected_resource_metadata_uses_forwarded_https(client):
    """Behind Cloud Run the advertised resource uses the public https scheme."""
    response = client.get(
        "/.well-known/oauth-protected-resource/mcp", headers={"X-Forwarded-Proto": "https"}
    )

    assert response.json()["resource"] == "https://testserver/mcp"


def test_mcp_without_token_advertises_resource_metadata(client):
    """The 401 challenge tells MCP clients where to start the OAuth flow."""
    response = client.post("/mcp", json={})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == f'Bearer resource_metadata="{METADATA_URL}"'


def test_mcp_with_invalid_token_advertises_https_resource_metadata(client, monkeypatch):
    """Rejected tokens get the same challenge, with the public scheme behind the proxy."""
    from quote.api import deps
    from quote.service.security import InvalidAccessToken

    def reject(_token):
        raise InvalidAccessToken("bad token")

    monkeypatch.setattr(deps, "validate_supabase_access_token", reject)

    response = client.post(
        "/mcp",
        json={},
        headers={"Authorization": "Bearer not-a-jwt", "X-Forwarded-Proto": "https"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == (
        'Bearer resource_metadata="https://testserver/.well-known/oauth-protected-resource/mcp"'
    )


def test_api_challenge_is_unchanged(client):
    """Only /mcp advertises OAuth metadata; the API keeps its plain bearer challenge."""
    response = client.get("/api/users/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
