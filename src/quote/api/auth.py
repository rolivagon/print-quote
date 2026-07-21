"""Authentication routes.

Supabase Auth owns credential entry, login, refresh, and logout. The API
intentionally exposes no password or token-issuing endpoint.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])
