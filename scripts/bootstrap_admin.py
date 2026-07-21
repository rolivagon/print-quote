"""Create or repair a password-authenticated administrator through Supabase Auth.

Set SUPABASE_BOOTSTRAP_EMAIL and SUPABASE_BOOTSTRAP_PASSWORD in the environment.
This command never stores, prints, or derives the supplied password.
"""

import os

from quote.domain.enums import UserRole
from quote.repo.database import SessionLocal, configure_database
from quote.repo.models import User
from quote.repo.sql_repo import SQLUserRepository
from quote.service.supabase_admin import SupabaseAdminError, provision_password_user


def main() -> None:
    """Idempotently provision the configured administrator Auth user and profile."""
    email = os.getenv("SUPABASE_BOOTSTRAP_EMAIL")
    if not email:
        raise SystemExit("SUPABASE_BOOTSTRAP_EMAIL is required")
    password = os.getenv("SUPABASE_BOOTSTRAP_PASSWORD")
    if not password:
        raise SystemExit("SUPABASE_BOOTSTRAP_PASSWORD is required")

    configure_database()
    with SessionLocal() as session:
        users = SQLUserRepository(session)
        try:
            subject = provision_password_user(email, password, "Administrator")
        except SupabaseAdminError as exc:
            raise SystemExit(f"Unable to provision Supabase administrator: {exc}") from exc
        profile = users.get_by_id(subject, include_deleted=True)
        if profile is None:
            profile = User(id=subject, name="Administrator", email=email, role=UserRole.SUPER_ADMIN)
            session.add(profile)
            session.flush()
        profile.deleted_at = None
        users.update(profile.id, role=UserRole.SUPER_ADMIN, is_active=True, commit=False)
        session.commit()


if __name__ == "__main__":
    main()
