"""Backend-only Supabase Auth administration client."""

import json
import os
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID


class SupabaseAdminError(RuntimeError):
    """Raised when Supabase Auth administration fails."""


def _admin_request(path: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call the backend-only Supabase Auth admin API without exposing request data."""
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not service_key:
        raise SupabaseAdminError("Supabase admin credentials are not configured")

    request = Request(
        f"{url.rstrip('/')}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urlopen(request, timeout=10) as response:
            data: dict[str, Any] = json.load(response)
            return data
    except HTTPError as exc:
        raise SupabaseAdminError(
            f"Supabase Auth administration failed with HTTP {exc.code}"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise SupabaseAdminError("Supabase Auth administration failed") from exc


def invite_user(email: str, name: str) -> UUID:
    """Invite a user without accepting or storing a password in the application."""
    data = _admin_request("/auth/v1/invite", "POST", {"email": email, "data": {"name": name}})

    try:
        return UUID(data["id"])
    except (KeyError, ValueError) as exc:
        raise SupabaseAdminError("Supabase invitation returned no user identity") from exc


def provision_password_user(email: str, password: str, name: str) -> UUID:
    """Create or reset a confirmed Auth user without storing its password locally."""
    users = _admin_request("/auth/v1/admin/users?page=1&per_page=1000", "GET").get("users", [])
    user_id = next((user.get("id") for user in users if user.get("email") == email), None)
    payload = {"password": password, "email_confirm": True, "user_metadata": {"name": name}}
    if user_id is None:
        data = _admin_request("/auth/v1/admin/users", "POST", {"email": email, **payload})
        user_id = data.get("id")
    else:
        _admin_request(f"/auth/v1/admin/users/{user_id}", "PUT", payload)

    try:
        return UUID(user_id)
    except (TypeError, ValueError) as exc:
        raise SupabaseAdminError("Supabase Auth administration returned no user identity") from exc


def reset_password_user(user_id: UUID, password: str) -> None:
    """Update an existing Auth password without retaining its value."""
    _admin_request(f"/auth/v1/admin/users/{user_id}", "PUT", {"password": password})
