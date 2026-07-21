"""Transition legacy SQLite/PostgreSQL identities to Supabase Auth UUID profiles.

The command reads only identity, role, active-state, and ownership columns from
the legacy database. Password hashes are intentionally neither selected nor
written. Set LEGACY_DATABASE_URL and run ``make migrate-legacy``.
"""

import os
from collections.abc import Iterable
from typing import Any

from sqlalchemy import create_engine, text

from quote.domain.enums import UserRole
from quote.repo.database import SessionLocal, configure_database
from quote.repo.sql_repo import SQLUserRepository
from quote.service.supabase_admin import invite_user


def _rows(connection, statement: str) -> Iterable[dict[str, Any]]:
    """Return mappings without selecting legacy credential columns."""
    return (dict(row) for row in connection.execute(text(statement)).mappings())


def _role(value: str) -> UserRole:
    """Normalize historic enum names and current enum values."""
    return UserRole(value.lower())


def _user_id(session, legacy_user: dict[str, Any]) -> str:
    """Return the existing or newly invited Auth profile UUID for one legacy user."""
    mapped = session.execute(
        text("select user_id from public.legacy_user_migrations where legacy_user_id = :id"),
        {"id": legacy_user["id"]},
    ).scalar_one_or_none()
    if mapped is not None:
        return str(mapped)

    users = SQLUserRepository(session)
    profile = users.get_by_email(legacy_user["email"], include_deleted=True)
    if profile is None:
        profile = users.get_by_id(invite_user(legacy_user["email"], legacy_user["name"]))
    if profile is None:
        raise RuntimeError("Supabase did not create the invited application profile")

    users.update(
        profile.id,
        role=_role(legacy_user["role"]),
        is_active=bool(legacy_user["is_active"]),
        commit=False,
    )
    session.execute(
        text(
            "insert into public.legacy_user_migrations (legacy_user_id, user_id) "
            "values (:legacy_id, :user_id) on conflict (legacy_user_id) do nothing"
        ),
        {"legacy_id": legacy_user["id"], "user_id": str(profile.id)},
    )
    return str(profile.id)


def _copy_clients(session, clients: Iterable[dict[str, Any]], user_ids: dict[int, str]) -> None:
    """Copy clients while replacing the legacy creator ID with the Auth UUID."""
    statement = text(
        "insert into public.clients "
        "(id, client_type, email, phone, address, tax_id, first_name, last_name, company_name, "
        "created_at, updated_at, deleted_at, created_by_id) "
        "values (:id, :client_type, :email, :phone, :address, :tax_id, :first_name, :last_name, "
        ":company_name, :created_at, :updated_at, :deleted_at, :created_by_id) "
        "on conflict (id) do nothing"
    )
    for client in clients:
        legacy_creator_id = client["created_by_id"]
        if legacy_creator_id is not None and legacy_creator_id not in user_ids:
            raise RuntimeError("Legacy client creator has no migrated user mapping")
        client["created_by_id"] = user_ids.get(legacy_creator_id)
        session.execute(statement, client)


def _copy_quotes(session, quotes: Iterable[dict[str, Any]], user_ids: dict[int, str]) -> None:
    """Copy quote headers while replacing the legacy seller ID with the Auth UUID."""
    statement = text(
        "insert into public.quotes "
        "(id, quote_number, status, seller_id, client_id, subtotal, tax, total, created_at, updated_at, sent_at) "
        "values (:id, :quote_number, :status, :seller_id, :client_id, :subtotal, :tax, :total, "
        ":created_at, :updated_at, :sent_at) on conflict (id) do nothing"
    )
    for quote in quotes:
        quote["seller_id"] = user_ids[quote["seller_id"]]
        session.execute(statement, quote)


def _advance_identity_sequences(session) -> None:
    """Keep generated integer IDs above migrated client and quote IDs."""
    for table in ("clients", "quotes"):
        session.execute(
            text(
                "select setval(pg_get_serial_sequence(:table_name, 'id'), "
                "coalesce((select max(id) from public." + table + "), 1), true)"
            ),
            {"table_name": f"public.{table}"},
        )


def main() -> None:
    """Run the legacy identity and ownership transition once or repeatedly."""
    legacy_url = os.getenv("LEGACY_DATABASE_URL")
    if not legacy_url:
        raise SystemExit("LEGACY_DATABASE_URL is required")

    configure_database()
    source = create_engine(legacy_url)
    try:
        with source.connect() as legacy_connection, SessionLocal() as session:
            legacy_users = list(
                _rows(
                    legacy_connection,
                    "select id, name, email, role, is_active from users order by id",
                )
            )
            user_ids = {user["id"]: _user_id(session, user) for user in legacy_users}
            _copy_clients(
                session,
                _rows(
                    legacy_connection,
                    "select id, client_type, email, phone, address, tax_id, first_name, last_name, "
                    "company_name, created_at, updated_at, deleted_at, created_by_id from clients",
                ),
                user_ids,
            )
            _copy_quotes(
                session,
                _rows(
                    legacy_connection,
                    "select id, quote_number, status, seller_id, client_id, subtotal, tax, total, "
                    "created_at, updated_at, sent_at from quotes",
                ),
                user_ids,
            )
            _advance_identity_sequences(session)
            session.commit()
    finally:
        source.dispose()


if __name__ == "__main__":
    main()
