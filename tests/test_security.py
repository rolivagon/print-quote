"""Tests for asymmetric Supabase access-token validation."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from jose import jwk, jwt

from quote.service.security import InvalidAccessToken, validate_supabase_access_token


@pytest.fixture
def supabase_token(monkeypatch):
    """Create an RS256 token backed by a mock Supabase JWKS entry."""
    url = "http://127.0.0.1:54321"
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_jwk = jwk.construct(public_pem, "RS256").to_dict()
    public_jwk["kid"] = "supabase-test-key"
    monkeypatch.setenv("SUPABASE_URL", url)
    monkeypatch.setattr("quote.service.security._jwks", lambda: {"keys": [public_jwk]})

    def create(expires_in: int = 300) -> str:
        return jwt.encode(
            {
                "sub": str(uuid4()),
                "aud": "authenticated",
                "iss": f"{url}/auth/v1",
                "exp": datetime.now(UTC) + timedelta(seconds=expires_in),
            },
            private_pem,
            algorithm="RS256",
            headers={"kid": "supabase-test-key"},
        )

    create.public_jwk = public_jwk
    return create


def test_valid_asymmetric_supabase_token_returns_claims(supabase_token):
    """Only an issuer-signed Supabase token with the required audience is accepted."""
    assert validate_supabase_access_token(supabase_token())["aud"] == "authenticated"


def test_es256_supabase_token_returns_claims(monkeypatch):
    """Supabase's local ES256 key can validate a browser session token."""
    url = "http://127.0.0.1:54321"
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_jwk = jwk.construct(public_pem, "ES256").to_dict()
    public_jwk["kid"] = "supabase-es256-key"
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": "authenticated",
            "iss": f"{url}/auth/v1",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        private_pem,
        algorithm="ES256",
        headers={"kid": "supabase-es256-key"},
    )
    monkeypatch.setenv("SUPABASE_URL", url)
    monkeypatch.setattr(
        "quote.service.security._get_jwks", lambda refresh=False: {"keys": [public_jwk]}
    )

    assert validate_supabase_access_token(token)["aud"] == "authenticated"


def test_jwks_is_refreshed_when_token_uses_a_new_key(supabase_token, monkeypatch):
    """A token issued after Supabase rotates signing keys retries with fresh JWKS once."""
    token = supabase_token()
    calls = []

    def get_jwks(refresh: bool = False):
        calls.append(refresh)
        return {"keys": [supabase_token.public_jwk]} if refresh else {"keys": []}

    monkeypatch.setattr("quote.service.security._get_jwks", get_jwks)

    assert validate_supabase_access_token(token)["aud"] == "authenticated"
    assert calls == [False, True]


@pytest.mark.parametrize("token", ["invalid.token.here", "not.a.valid.jwt"])
def test_malformed_token_is_rejected(token):
    """Malformed bearer values cannot authenticate."""
    with pytest.raises(InvalidAccessToken):
        validate_supabase_access_token(token)


def test_hs256_token_is_rejected(monkeypatch):
    """The former application-signed HS256 token format cannot authenticate."""
    monkeypatch.setenv("SUPABASE_URL", "http://127.0.0.1:54321")
    token = jwt.encode({"sub": str(uuid4())}, "legacy-secret", algorithm="HS256")

    with pytest.raises(InvalidAccessToken):
        validate_supabase_access_token(token)


def test_expired_supabase_token_is_rejected(supabase_token):
    """Expiry is validated instead of trusting the browser token."""
    with pytest.raises(InvalidAccessToken):
        validate_supabase_access_token(supabase_token(expires_in=-1))
