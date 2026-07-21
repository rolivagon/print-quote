"""Tests for the Supabase-only authentication boundary."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt


def test_legacy_login_endpoint_does_not_issue_a_token(api_client: TestClient):
    """The former password endpoint is not an authentication contract."""
    response = api_client.post("/api/auth/login", data={"username": "x", "password": "y"})

    assert response.status_code == 405


@pytest.mark.parametrize("token", ["invalid_token", "not.a.valid.jwt"])
def test_protected_endpoint_rejects_invalid_supabase_token(api_client: TestClient, token: str):
    """Malformed bearer values always produce HTTP 401."""
    api_client.headers = {"Authorization": f"Bearer {token}"}

    assert api_client.get("/api/users/me").status_code == 401


def test_protected_endpoint_rejects_expired_supabase_token(api_client: TestClient, monkeypatch):
    """A JWT signed with the local Supabase secret still requires a valid expiry."""
    url = "http://127.0.0.1:54321"
    secret = "test-supabase-jwt-secret"
    monkeypatch.setenv("SUPABASE_URL", url)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", secret)
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": "authenticated",
            "iss": f"{url}/auth/v1",
            "exp": datetime.now(UTC) - timedelta(seconds=1),
        },
        secret,
        algorithm="HS256",
    )
    api_client.headers = {"Authorization": f"Bearer {token}"}

    assert api_client.get("/api/users/me").status_code == 401
