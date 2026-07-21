"""Supabase access-token verification."""

import json
import os
from functools import lru_cache
from typing import Any
from urllib.request import urlopen

from jose import JWTError, jwt


class InvalidAccessToken(ValueError):
    """Raised when a bearer token is not an authentic Supabase access token."""


def _supabase_url() -> str:
    url = os.getenv("SUPABASE_URL")
    if not url:
        raise InvalidAccessToken("SUPABASE_URL is not configured")
    return url.rstrip("/")


@lru_cache(maxsize=1)
def _jwks() -> dict[str, Any]:
    with urlopen(f"{_supabase_url()}/auth/v1/.well-known/jwks.json", timeout=5) as response:
        return json.load(response)


def _get_jwks(refresh: bool = False) -> dict[str, Any]:
    if refresh:
        _jwks.cache_clear()
    return _jwks()


def validate_supabase_access_token(token: str) -> dict[str, Any]:
    """Validate signature, issuer, audience, expiry, and UUID subject of a Supabase JWT."""
    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        if algorithm not in {"RS256", "ES256"}:
            raise InvalidAccessToken("Unsupported token algorithm")

        jwks = _get_jwks()
        if header.get("kid") not in {key.get("kid") for key in jwks.get("keys", [])}:
            # Supabase can rotate signing keys without restarting this API process.
            jwks = _get_jwks(refresh=True)

        return jwt.decode(
            token,
            jwks,
            algorithms=[algorithm],
            audience="authenticated",
            issuer=f"{_supabase_url()}/auth/v1",
        )
    except (JWTError, OSError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidAccessToken("Invalid Supabase access token") from exc
