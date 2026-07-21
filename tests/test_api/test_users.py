"""Tests for UUID-backed application profiles and invitations."""

from uuid import uuid4

from fastapi.testclient import TestClient

from quote.api.deps import get_current_user
from quote.api.main import app
from quote.domain.enums import UserRole
from quote.service.supabase_admin import SupabaseAdminError


def test_admin_can_invite_user_without_a_password(
    authorized_client: TestClient, api_test_state, api_user_factory, monkeypatch
):
    """An invitation creates a profile without accepting a password field."""
    invited_user = api_user_factory(
        name="Invited User",
        email="invited@test.com",
        role=UserRole.VENDEDOR,
    )
    api_test_state.session.commit()
    monkeypatch.setattr("quote.api.users.invite_user", lambda email, name: invited_user.id)

    response = authorized_client.post(
        "/api/users/",
        json={"name": "Invited User", "email": "invited@test.com", "role": "admin"},
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(invited_user.id)
    assert response.json()["role"] == "admin"


def test_invitation_request_does_not_accept_a_password(authorized_client: TestClient):
    """Passwords are ignored by neither the browser nor the application API contract."""
    response = authorized_client.post(
        "/api/users/",
        json={
            "name": "No Password",
            "email": "no-password@test.com",
            "role": "vendedor",
            "password": "x",
        },
    )

    assert response.status_code == 422


def test_vendedor_cannot_invite_users(api_client: TestClient, api_user_factory):
    """Only administrative profiles can request Supabase invitations."""
    seller = api_user_factory(name="Seller", role=UserRole.VENDEDOR)
    app.dependency_overrides[get_current_user] = lambda: seller

    response = api_client.post(
        "/api/users/",
        json={"name": "Blocked Invite", "email": "blocked-invite@test.com", "role": "vendedor"},
    )

    assert response.status_code == 403


def test_current_profile_is_returned_by_uuid(authorized_client: TestClient, admin_user):
    """The profile identity returned by the API is the Auth-linked UUID."""
    response = authorized_client.get("/api/users/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(admin_user.id)


def test_administrator_can_update_profile_state(authorized_client: TestClient, admin_user):
    """Roles and active state remain application-profile fields."""
    response = authorized_client.patch(
        f"/api/users/{admin_user.id}", json={"is_active": False, "role": "vendedor"}
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["role"] == "vendedor"


def test_administrator_cannot_delete_own_profile(authorized_client: TestClient, admin_user):
    """The current authenticated profile cannot be soft-deleted by itself."""
    response = authorized_client.delete(f"/api/users/{admin_user.id}")

    assert response.status_code == 400


def test_super_admin_can_reset_user_password(api_client: TestClient, api_user_factory, monkeypatch):
    super_admin = api_user_factory(name="Super Admin", role=UserRole.SUPER_ADMIN)
    target = api_user_factory(name="Target User", role=UserRole.VENDEDOR)
    app.dependency_overrides[get_current_user] = lambda: super_admin
    api_client.headers = {"Authorization": "Bearer test-supabase-token"}
    submitted_password = "Updated-password-123"
    updated: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "quote.api.users.reset_password_user",
        lambda user_id, password: updated.append((str(user_id), password)),
    )

    response = api_client.post(
        f"/api/users/{target.id}/password/", json={"password": submitted_password}
    )

    assert response.status_code == 204
    assert updated == [(str(target.id), submitted_password)]
    assert submitted_password not in response.text


def test_admin_cannot_reset_user_password(authorized_client: TestClient, admin_user):
    submitted_password = "Updated-password-123"

    response = authorized_client.post(
        f"/api/users/{admin_user.id}/password/", json={"password": submitted_password}
    )

    assert response.status_code == 403
    assert submitted_password not in response.text


def test_password_validation_error_does_not_return_password(
    api_client: TestClient, api_user_factory
):
    super_admin = api_user_factory(name="Super Admin", role=UserRole.SUPER_ADMIN)
    target = api_user_factory(name="Target User", role=UserRole.VENDEDOR)
    app.dependency_overrides[get_current_user] = lambda: super_admin
    api_client.headers = {"Authorization": "Bearer test-supabase-token"}
    submitted_password = "too-short"

    response = api_client.post(
        f"/api/users/{target.id}/password/", json={"password": submitted_password}
    )

    assert response.status_code == 422
    assert submitted_password not in response.text


def test_reset_password_rejects_unknown_target(api_client: TestClient, api_user_factory):
    super_admin = api_user_factory(name="Super Admin", role=UserRole.SUPER_ADMIN)
    app.dependency_overrides[get_current_user] = lambda: super_admin
    api_client.headers = {"Authorization": "Bearer test-supabase-token"}
    target_id = uuid4()
    submitted_password = "Updated-password-123"

    response = api_client.post(
        f"/api/users/{target_id}/password/", json={"password": submitted_password}
    )

    assert response.status_code == 404
    assert submitted_password not in response.text


def test_reset_password_hides_supabase_failure(
    api_client: TestClient, api_user_factory, monkeypatch
):
    super_admin = api_user_factory(name="Super Admin", role=UserRole.SUPER_ADMIN)
    target = api_user_factory(name="Target User", role=UserRole.VENDEDOR)
    app.dependency_overrides[get_current_user] = lambda: super_admin
    api_client.headers = {"Authorization": "Bearer test-supabase-token"}
    submitted_password = "Updated-password-123"

    def fail_reset(*_) -> None:
        raise SupabaseAdminError("upstream failure")

    monkeypatch.setattr("quote.api.users.reset_password_user", fail_reset)

    response = api_client.post(
        f"/api/users/{target.id}/password/", json={"password": submitted_password}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Password update failed"}
    assert submitted_password not in response.text
