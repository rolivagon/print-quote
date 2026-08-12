"""Supabase migration and RLS integration checks.

These tests run only through ``make test-supabase`` against local Supabase.
"""

import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import uuid
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import sessionmaker

from quote.api.main import app
from quote.domain.enums import PlotterBillingMetric
from quote.repo.models import Finish, FinishPricing, Paper, PaperPricing, PlotterPricing
from quote.service.supabase_admin import reset_password_user

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
import load_plotter_data as plotter_loader  # noqa: E402
from load_digital_data import _catalog  # noqa: E402
from load_plotter_data import _catalog as plotter_catalog  # noqa: E402
from load_plotter_data import load_plotter_data  # noqa: E402

APPLICATION_TABLES = {
    "users",
    "legacy_user_migrations",
    "clients",
    "papers",
    "finishes",
    "base_measurements",
    "paper_pricing",
    "finish_pricing",
    "plotter_pricing",
    "quotes",
    "quote_items",
    "quote_item_finishes",
    "fixed_products",
    "fixed_product_quantity_ranges",
}

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_SUPABASE_INTEGRATION") != "1",
    reason="requires local Supabase; run through make test-supabase",
)


def test_migration_creates_auth_linked_profiles_and_enables_rls():
    """All application tables must be present and deny direct browser access by policy."""
    database_url = os.environ["DATABASE_URL"]
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "select tablename, rowsecurity from pg_tables "
                    "where schemaname = 'public' and tablename = any(:tables)"
                ),
                {"tables": list(APPLICATION_TABLES)},
            ).all()
            assert {row.tablename for row in rows} == APPLICATION_TABLES
            assert all(row.rowsecurity for row in rows)

            profile_fk = connection.execute(
                text(
                    "select 1 from pg_constraint where conrelid = 'public.users'::regclass "
                    "and confrelid = 'auth.users'::regclass"
                )
            ).scalar()
            assert profile_fk == 1

            policies = connection.execute(
                text("select count(*) from pg_policies where schemaname = 'public'")
            ).scalar_one()
            assert policies == 0
    finally:
        engine.dispose()


def test_reset_creates_deterministic_credential_free_seed_state():
    """Reset creates the documented roles and ownership without a usable password."""
    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        with engine.connect() as connection:
            profiles = connection.execute(
                text(
                    "select email, role from public.users where email like 'seed-%' order by email"
                )
            ).all()
            ownership = connection.execute(
                text(
                    "select c.created_by_id, q.seller_id from public.clients c "
                    "join public.quotes q on q.client_id = c.id where c.id = 1000"
                )
            ).one()
            passwords = connection.execute(
                text(
                    "select count(*) from auth.users where email like 'seed-%' "
                    "and encrypted_password is not null"
                )
            ).scalar_one()
        assert profiles == [
            ("seed-admin@example.com", "ADMIN"),
            ("seed-seller@example.com", "VENDEDOR"),
        ]
        assert str(ownership[0]) == str(ownership[1]) == "00000000-0000-0000-0000-000000000002"
        assert passwords == 0
    finally:
        engine.dispose()


def test_digital_data_loader_is_additive_and_idempotent():
    """The operational loader creates missing canonical data without overwriting rows."""
    workspace = Path(__file__).parents[2]
    catalog = _catalog().records
    source_papers = {paper.id: paper for paper in catalog if isinstance(paper, Paper)}
    source_finishes = {finish.id: finish for finish in catalog if isinstance(finish, Finish)}
    expected_papers = {
        paper.name: (paper.weight, paper.description, paper.is_active)
        for paper in source_papers.values()
    }
    expected_finishes = {
        finish.name: (finish.description, finish.is_active) for finish in source_finishes.values()
    }
    expected_paper_pricing = {
        (
            source_papers[price.paper_id].name,
            price.print_type.name,
            price.color_mode.name if price.color_mode else None,
            price.min_quantity,
            price.max_quantity,
        ): price.unit_price
        for price in catalog
        if isinstance(price, PaperPricing)
    }
    expected_finish_pricing = {
        (
            source_finishes[price.finish_id].name,
            price.print_type.name,
            price.unit.name,
            price.min_quantity,
            price.max_quantity,
        ): price.unit_price
        for price in catalog
        if isinstance(price, FinishPricing)
    }
    expected_papers["Couche 130g BTE y Opaco"] = (999, "Production paper", True)
    expected_finishes["Corte Guillotina"] = ("Production finish", True)
    expected_paper_pricing[("Couche 130g BTE y Opaco", "DIGITAL", "C4_4", 1, 5)] = Decimal("9999")
    expected_finish_pricing[("Corte Guillotina", "DIGITAL", "PER_ITEM", 1, 5)] = Decimal("1234")
    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        with engine.begin() as connection:
            paper_id = connection.execute(
                text(
                    "insert into public.papers (name, weight, description) "
                    "values ('Couche 130g BTE y Opaco', 999, 'Production paper') returning id"
                )
            ).scalar_one()
            connection.execute(
                text(
                    "insert into public.paper_pricing "
                    "(paper_id, print_type, color_mode, min_quantity, max_quantity, unit_price) "
                    "values (:paper_id, 'DIGITAL', 'C4_4', 1, 5, 9999)"
                ),
                {"paper_id": paper_id},
            )
            finish_id = connection.execute(
                text(
                    "insert into public.finishes (name, description) "
                    "values ('Corte Guillotina', 'Production finish') returning id"
                )
            ).scalar_one()
            connection.execute(
                text(
                    "insert into public.finish_pricing "
                    "(finish_id, print_type, unit, min_quantity, max_quantity, unit_price) "
                    "values (:finish_id, 'DIGITAL', 'PER_ITEM', 1, 5, 1234)"
                ),
                {"finish_id": finish_id},
            )

        processes = [
            subprocess.Popen(
                ["make", "load-digital-data"],
                cwd=workspace,
                env=os.environ,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for _ in range(2)
        ]
        for process in processes:
            _, stderr = process.communicate()
            assert process.returncode == 0, stderr.decode()

        with engine.connect() as connection:
            counts = connection.execute(
                text(
                    "select (select count(*) from public.papers), "
                    "(select count(*) from public.finishes), "
                    "(select count(*) from public.paper_pricing), "
                    "(select count(*) from public.finish_pricing)"
                )
            ).one()
            paper_rows = connection.execute(
                text("select name, weight, description, is_active from public.papers")
            ).all()
            finish_rows = connection.execute(
                text("select name, description, is_active from public.finishes")
            ).all()
            paper_pricing_rows = connection.execute(
                text(
                    "select p.name, pp.print_type::text, pp.color_mode::text, pp.min_quantity, "
                    "pp.max_quantity, pp.unit_price from public.paper_pricing pp "
                    "join public.papers p on p.id = pp.paper_id"
                )
            ).all()
            finish_pricing_rows = connection.execute(
                text(
                    "select f.name, fp.print_type::text, fp.unit::text, fp.min_quantity, "
                    "fp.max_quantity, fp.unit_price from public.finish_pricing fp "
                    "join public.finishes f on f.id = fp.finish_id"
                )
            ).all()
            papers = {
                name: (weight, description, is_active)
                for name, weight, description, is_active in paper_rows
            }
            finishes = {
                name: (description, is_active) for name, description, is_active in finish_rows
            }
            paper_pricing = {tuple(row[:-1]): row[-1] for row in paper_pricing_rows}
            finish_pricing = {tuple(row[:-1]): row[-1] for row in finish_pricing_rows}

        assert all(papers[name] == value for name, value in expected_papers.items())
        assert all(finishes[name] == value for name, value in expected_finishes.items())
        assert all(paper_pricing[key] == value for key, value in expected_paper_pricing.items())
        assert all(finish_pricing[key] == value for key, value in expected_finish_pricing.items())
    finally:
        engine.dispose()


@pytest.fixture
def postgres_connection():
    """Provide a PostgreSQL transaction that is always rolled back after the test."""
    engine = create_engine(os.environ["DATABASE_URL"])
    connection = engine.connect()
    transaction = connection.begin()
    try:
        yield connection
    finally:
        transaction.rollback()
        connection.close()
        engine.dispose()


def _plotter_counts(connection):
    return connection.execute(
        text(
            "select (select count(*) from public.papers), "
            "(select count(*) from public.finishes), "
            "(select count(*) from public.plotter_pricing)"
        )
    ).one()


@pytest.mark.parametrize("owner_table", ["papers", "finishes"])
def test_plotter_exclude_constraints_reject_overlapping_ranges_per_metric(
    postgres_connection, owner_table: str
):
    """PostgreSQL EXCLUDE constraints allow another metric but reject overlapping ranges."""
    owner_id = postgres_connection.execute(
        text(f"insert into public.{owner_table} (name, weight) values (:name, 1) returning id")
        if owner_table == "papers"
        else text(f"insert into public.{owner_table} (name) values (:name) returning id"),
        {"name": f"plotter-overlap-{uuid.uuid4().hex}"},
    ).scalar_one()
    owner_column = "paper_id" if owner_table == "papers" else "finish_id"
    insert = text(
        f"insert into public.plotter_pricing ({owner_column}, billing_metric, minimum, maximum, unit_price) "
        "values (:owner_id, :metric, :minimum, :maximum, 1000)"
    )
    postgres_connection.execute(
        insert,
        {"owner_id": owner_id, "metric": "SQM", "minimum": 1, "maximum": 5},
    )
    with pytest.raises(IntegrityError):
        with postgres_connection.begin_nested():
            postgres_connection.execute(
                insert,
                {"owner_id": owner_id, "metric": "SQM", "minimum": 4, "maximum": 10},
            )
    postgres_connection.execute(
        insert,
        {"owner_id": owner_id, "metric": "JOB_QUANTITY", "minimum": 4, "maximum": 10},
    )


def test_plotter_data_loader_is_idempotent_and_preserves_digital_offset_rates(postgres_connection):
    """Two loads add one Plotter catalog and leave Digital and Offset rates unchanged."""
    session_factory = sessionmaker(
        bind=postgres_connection, join_transaction_mode="create_savepoint"
    )
    paper_id = postgres_connection.execute(
        text("insert into public.papers (name, weight) values (:name, 100) returning id"),
        {"name": f"catalog-preservation-{uuid.uuid4().hex}"},
    ).scalar_one()
    finish_id = postgres_connection.execute(
        text("insert into public.finishes (name) values (:name) returning id"),
        {"name": f"catalog-preservation-{uuid.uuid4().hex}"},
    ).scalar_one()
    postgres_connection.execute(
        text(
            "insert into public.paper_pricing "
            "(paper_id, print_type, color_mode, min_quantity, max_quantity, unit_price) values "
            "(:paper_id, 'DIGITAL', 'C4_4', 1, 1, 777), "
            "(:paper_id, 'OFFSET', 'C4_0', 2, 2, 888)"
        ),
        {"paper_id": paper_id},
    )
    postgres_connection.execute(
        text(
            "insert into public.finish_pricing "
            "(finish_id, print_type, unit, min_quantity, max_quantity, unit_price) values "
            "(:finish_id, 'DIGITAL', 'PER_ITEM', 1, 1, 999), "
            "(:finish_id, 'OFFSET', 'JOB', 2, 2, 111)"
        ),
        {"finish_id": finish_id},
    )
    preserved_before = postgres_connection.execute(
        text(
            "select 'paper', print_type::text, color_mode::text, min_quantity, max_quantity, unit_price "
            "from public.paper_pricing where paper_id = :paper_id union all "
            "select 'finish', print_type::text, unit::text, min_quantity, max_quantity, unit_price "
            "from public.finish_pricing where finish_id = :finish_id"
        ),
        {"paper_id": paper_id, "finish_id": finish_id},
    ).all()
    counts_before = _plotter_counts(postgres_connection)

    with session_factory.begin() as session:
        load_plotter_data(session)
    counts_after_first_load = _plotter_counts(postgres_connection)
    with session_factory.begin() as session:
        load_plotter_data(session)
    counts_after_second_load = _plotter_counts(postgres_connection)

    preserved_after = postgres_connection.execute(
        text(
            "select 'paper', print_type::text, color_mode::text, min_quantity, max_quantity, unit_price "
            "from public.paper_pricing where paper_id = :paper_id union all "
            "select 'finish', print_type::text, unit::text, min_quantity, max_quantity, unit_price "
            "from public.finish_pricing where finish_id = :finish_id"
        ),
        {"paper_id": paper_id, "finish_id": finish_id},
    ).all()
    duplicate_rates = postgres_connection.execute(
        text(
            "select 1 from public.plotter_pricing group by paper_id, finish_id, billing_metric, minimum, maximum "
            "having count(*) > 1"
        )
    ).all()
    assert counts_after_first_load[0] >= counts_before[0]
    assert counts_after_first_load[1] >= counts_before[1]
    assert counts_after_first_load[2] >= counts_before[2]
    assert counts_after_second_load == counts_after_first_load
    assert preserved_after == preserved_before
    assert duplicate_rates == []
    source = plotter_catalog().records
    expected_rate_count = len([record for record in source if isinstance(record, PlotterPricing)])
    source_names = [record.name for record in source if isinstance(record, Paper | Finish)]
    catalog_rate_count = postgres_connection.execute(
        text(
            "select count(*) from public.plotter_pricing pp "
            "left join public.papers p on p.id = pp.paper_id "
            "left join public.finishes f on f.id = pp.finish_id "
            "where coalesce(p.name, f.name) = any(:names)"
        ),
        {"names": source_names},
    ).scalar_one()
    assert catalog_rate_count >= expected_rate_count


def test_plotter_loader_public_entrypoint_rolls_back_partial_catalog_on_conflict(
    postgres_connection, monkeypatch
):
    """The no-session entrypoint rolls back every catalog insertion after a persisted conflict."""
    session_factory = sessionmaker(
        bind=postgres_connection, join_transaction_mode="create_savepoint"
    )
    monkeypatch.setattr(plotter_loader, "SessionLocal", session_factory)
    paper_id = postgres_connection.execute(
        text("select id from public.papers where name = 'SINTÉTICO' order by id limit 1")
    ).scalar()
    if paper_id is not None:
        postgres_connection.execute(
            text("delete from public.plotter_pricing where paper_id = :paper_id"),
            {"paper_id": paper_id},
        )

    setup_session = session_factory()
    try:
        if paper_id is None:
            paper = Paper(name="SINTÉTICO", weight=1)
            setup_session.add(paper)
            setup_session.flush()
            paper_id = paper.id
        setup_session.add(
            PlotterPricing(
                paper_id=paper_id,
                billing_metric=PlotterBillingMetric.SQM,
                minimum=Decimal("1"),
                maximum=Decimal("5"),
                unit_price=Decimal("1"),
            )
        )
        setup_session.commit()
    finally:
        setup_session.close()

    counts_before = _plotter_counts(postgres_connection)
    with pytest.raises(ValueError, match="Plotter rate conflict"):
        plotter_loader.load_plotter_data()
    assert _plotter_counts(postgres_connection) == counts_before


@pytest.mark.parametrize("role", ["anon", "authenticated"])
def test_direct_browser_roles_cannot_read_application_tables(role: str):
    """RLS denies every application table to Supabase browser roles."""
    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        for table in APPLICATION_TABLES:
            with engine.begin() as connection:
                connection.execute(text(f"set local role {role}"))
                with pytest.raises(DBAPIError):
                    connection.execute(text(f"select 1 from public.{table} limit 1"))
    finally:
        engine.dispose()


def _local_publishable_key() -> str:
    """Read the local publishable key without printing or persisting it."""
    result = subprocess.run(
        ["supabase", "status", "-o", "env"],
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"^(?:ANON_KEY|PUBLISHABLE_KEY)=(.+)$", result.stdout, re.MULTILINE)
    if match is None:
        raise RuntimeError("Supabase publishable key was not available")
    return match.group(1).strip().strip('"')


def _local_supabase_value(name: str) -> str:
    """Read one local CLI environment value without writing it to disk or logs."""
    result = subprocess.run(
        ["supabase", "status", "-o", "env"],
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(rf"^{name}=(.+)$", result.stdout, re.MULTILINE)
    if match is None:
        raise RuntimeError(f"Supabase {name} was not available")
    return match.group(1).strip().strip('"')


def test_supabase_admin_password_reset_changes_auth_password(monkeypatch):
    base_url = os.environ["SUPABASE_URL"]
    email, user_id, _ = _signup_user(base_url)
    new_password = "replacement-password-123"
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", _local_supabase_value("SERVICE_ROLE_KEY"))

    reset_password_user(uuid.UUID(user_id), new_password)

    request = Request(
        f"{base_url}/auth/v1/token?grant_type=password",
        data=json.dumps({"email": email, "password": new_password}).encode(),
        headers={"apikey": _local_publishable_key(), "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request) as response:
        payload = json.load(response)

    assert payload["access_token"]


def _signup_user(base_url: str) -> tuple[str, str, str]:
    """Create a local Auth user and return its email, UUID, and access token."""
    email = f"integration-{uuid.uuid4().hex}@example.com"
    payload = json.dumps(
        {
            "email": email,
            "password": "integration-password-123",
            "data": {"name": "Integration User"},
        }
    ).encode()
    request = Request(
        f"{base_url}/auth/v1/signup",
        data=payload,
        headers={"apikey": _local_publishable_key(), "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=2) as response:
                payload = json.load(response)
            break
        except (OSError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(1)
    return email, payload["user"]["id"], payload["access_token"]


def _request_with_retry(request: Request):
    """Wait for local PostgREST while its container settles after reset."""
    for attempt in range(3):
        try:
            return urlopen(request, timeout=2)
        except OSError:
            if attempt == 2:
                raise
            time.sleep(1)


def test_supabase_token_authenticates_fastapi_profile():
    """A real Supabase session token resolves the UUID-linked API profile."""
    base_url = os.environ["SUPABASE_URL"].rstrip("/")
    email, subject, session = _signup_user(base_url)

    with TestClient(app) as client:
        response = client.get("/api/users/me", headers={"Authorization": f"Bearer {session}"})

    assert response.status_code == 200
    assert response.json()["email"] == email
    assert response.json()["id"] == subject
    assert response.json()["role"] == "vendedor"

    for authorization in (None, f"Bearer {session}"):
        headers = {
            "apikey": _local_publishable_key(),
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        if authorization:
            headers["Authorization"] = authorization
        for table in APPLICATION_TABLES:
            read = Request(
                f"{base_url}/rest/v1/{table}?select=*",
                headers=headers,
                method="GET",
            )
            try:
                with _request_with_retry(read) as response:
                    assert json.load(response) == []
            except HTTPError as error:
                assert error.code in {401, 403}

            write = Request(
                f"{base_url}/rest/v1/{table}",
                data=b"{}",
                headers=headers,
                method="POST",
            )
            with pytest.raises(HTTPError) as error:
                _request_with_retry(write)
            assert error.value.code in {401, 403}


def test_fastapi_uses_the_active_database_profile_for_authorization():
    """Changing profile activity or role after token issue changes API authorization."""
    base_url = os.environ["SUPABASE_URL"].rstrip("/")
    email, _, session = _signup_user(base_url)
    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        with engine.begin() as connection:
            connection.execute(
                text("update public.users set is_active = false where email = :email"),
                {"email": email},
            )
        with TestClient(app) as client:
            assert (
                client.get(
                    "/api/users/me", headers={"Authorization": f"Bearer {session}"}
                ).status_code
                == 403
            )

        with engine.begin() as connection:
            connection.execute(
                text(
                    "update public.users set is_active = true, role = 'VENDEDOR' where email = :email"
                ),
                {"email": email},
            )
        with TestClient(app) as client:
            assert (
                client.get(
                    "/api/users/", headers={"Authorization": f"Bearer {session}"}
                ).status_code
                == 403
            )

        with engine.begin() as connection:
            connection.execute(
                text("update public.users set role = 'ADMIN' where email = :email"),
                {"email": email},
            )
        with TestClient(app) as client:
            assert (
                client.get(
                    "/api/users/", headers={"Authorization": f"Bearer {session}"}
                ).status_code
                == 200
            )
    finally:
        engine.dispose()


def test_fastapi_denies_a_token_without_a_profile():
    """A valid Supabase subject without a public profile cannot use protected endpoints."""
    base_url = os.environ["SUPABASE_URL"].rstrip("/")
    email, _, session = _signup_user(base_url)
    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        with engine.begin() as connection:
            connection.execute(
                text("delete from public.users where email = :email"), {"email": email}
            )
        with TestClient(app) as client:
            assert (
                client.get(
                    "/api/users/me", headers={"Authorization": f"Bearer {session}"}
                ).status_code
                == 401
            )
    finally:
        engine.dispose()


def test_fastapi_enforces_client_ownership_with_real_tokens():
    """FastAPI writes with the profile UUID and rejects a different seller."""
    base_url = os.environ["SUPABASE_URL"].rstrip("/")
    _, owner_id, owner_token = _signup_user(base_url)
    _, _, other_token = _signup_user(base_url)
    tax_id = f"76.{uuid.uuid4().int % 10_000_000:07d}-4"
    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/clients/",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"client_type": "company", "tax_id": tax_id, "company_name": "Ownership Test"},
            )
            assert created.status_code == 201
            client_id = created.json()["id"]
            assert (
                client.get(
                    f"/api/clients/{client_id}", headers={"Authorization": f"Bearer {owner_token}"}
                ).status_code
                == 200
            )
            assert (
                client.get(
                    f"/api/clients/{client_id}", headers={"Authorization": f"Bearer {other_token}"}
                ).status_code
                == 403
            )
        with engine.connect() as connection:
            assert connection.execute(
                text("select created_by_id from public.clients where id = :id"), {"id": client_id}
            ).scalar_one() == uuid.UUID(owner_id)
    finally:
        engine.dispose()


def test_invalid_profile_uuid_write_rolls_back_without_a_client():
    """Foreign keys reject a non-profile creator without leaving a partial row."""
    engine = create_engine(os.environ["DATABASE_URL"])
    tax_id = f"76.{uuid.uuid4().int % 10_000_000:07d}-8"
    try:
        with engine.connect() as connection:
            before = connection.execute(text("select count(*) from public.clients")).scalar_one()
        with pytest.raises(DBAPIError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "insert into public.clients (client_type, tax_id, company_name, created_by_id) "
                        "values ('COMPANY', :tax_id, 'Invalid owner', :owner_id)"
                    ),
                    {"tax_id": tax_id, "owner_id": str(uuid.uuid4())},
                )
        with engine.connect() as connection:
            assert (
                connection.execute(text("select count(*) from public.clients")).scalar_one()
                == before
            )
    finally:
        engine.dispose()


def test_legacy_transition_is_idempotent():
    """Legacy identity mappings and ownership copy exactly once across repeated runs."""
    workspace = Path(__file__).parents[2]
    suffix = uuid.uuid4().hex
    legacy_user_id = uuid.uuid4().int % 1_000_000_000
    legacy_client_id = legacy_user_id + 1
    legacy_quote_id = legacy_user_id + 2
    with TemporaryDirectory() as directory:
        database_path = Path(directory) / "legacy.db"
        with sqlite3.connect(database_path) as legacy:
            legacy.executescript(
                f"""
                create table users (id integer primary key, name text, email text, role text, is_active boolean);
                create table clients (
                  id integer primary key, client_type text, email text, phone text, address text, tax_id text,
                  first_name text, last_name text, company_name text, created_at text, updated_at text,
                  deleted_at text, created_by_id integer
                );
                create table quotes (
                  id integer primary key, quote_number text, status text, seller_id integer, client_id integer,
                  subtotal numeric, tax numeric, total numeric, created_at text, updated_at text, sent_at text
                );
                insert into users values
                  ({legacy_user_id}, 'Legacy Admin', 'legacy-admin-{suffix}@example.com', 'ADMIN', 1),
                  ({legacy_user_id + 1}, 'Legacy Seller', 'legacy-seller-{suffix}@example.com', 'VENDEDOR', 1),
                  ({legacy_user_id + 2}, 'Inactive Seller', 'legacy-inactive-{suffix}@example.com', 'VENDEDOR', 0);
                insert into clients values
                  ({legacy_client_id}, 'COMPANY', null, null, null, '76.{uuid.uuid4().int % 10_000_000:07d}-3', null, null, 'Legacy Company',
                   '2026-01-01', null, null, {legacy_user_id + 1});
                insert into quotes values
                  ({legacy_quote_id}, 'LEGACY-{suffix}', 'DRAFT', {legacy_user_id + 1}, {legacy_client_id}, 0, 0, 0, '2026-01-01', null, null);
                """
            )
        environment = os.environ | {
            "LEGACY_DATABASE_URL": f"sqlite:///{database_path}",
            "SUPABASE_SERVICE_ROLE_KEY": _local_supabase_value("SERVICE_ROLE_KEY"),
        }
        command = [str(workspace / ".venv/bin/python"), "scripts/migrate_legacy_users.py"]
        engine = create_engine(os.environ["DATABASE_URL"])
        try:
            with engine.connect() as connection:
                before = connection.execute(
                    text(
                        "select (select count(*) from public.legacy_user_migrations), "
                        "(select count(*) from public.clients), (select count(*) from public.quotes)"
                    )
                ).one()
            for _ in range(2):
                subprocess.run(
                    command, cwd=workspace, env=environment, check=True, capture_output=True
                )
            with engine.connect() as connection:
                counts = connection.execute(
                    text(
                        "select (select count(*) from public.legacy_user_migrations), "
                        "(select count(*) from public.clients), (select count(*) from public.quotes)"
                    )
                ).one()
            assert counts == (before[0] + 3, before[1] + 1, before[2] + 1)
        finally:
            engine.dispose()


def test_bootstrap_admin_password_is_idempotent_and_allows_sign_in():
    """Repeated password bootstrap creates one active super-admin profile."""
    workspace = Path(__file__).parents[2]
    email = f"bootstrap-{uuid.uuid4().hex}@example.com"
    password = f"Bootstrap-{uuid.uuid4().hex}"
    environment = os.environ | {
        "SUPABASE_BOOTSTRAP_EMAIL": email,
        "SUPABASE_BOOTSTRAP_PASSWORD": password,
        "SUPABASE_SERVICE_ROLE_KEY": _local_supabase_value("SERVICE_ROLE_KEY"),
    }
    command = [str(workspace / ".venv/bin/python"), "scripts/bootstrap_admin.py"]

    for _ in range(2):
        result = subprocess.run(
            command, cwd=workspace, env=environment, check=True, capture_output=True
        )
        assert password not in result.stdout.decode()
        assert password not in result.stderr.decode()

    login_request = Request(
        f"{os.environ['SUPABASE_URL']}/auth/v1/token?grant_type=password",
        data=json.dumps({"email": email, "password": password}).encode(),
        headers={"apikey": _local_publishable_key(), "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(login_request, timeout=2) as response:
        assert json.load(response)["access_token"]

    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        with engine.connect() as connection:
            profile = connection.execute(
                text(
                    "select u.role, u.is_active, u.id = a.id, a.encrypted_password is not null "
                    "from public.users u join auth.users a on a.id = u.id "
                    "where u.email = :email"
                ),
                {"email": email},
            ).one()
            count = connection.execute(
                text("select count(*) from public.users where email = :email"), {"email": email}
            ).scalar_one()
            assert profile == ("SUPER_ADMIN", True, True, True)
            assert count == 1
    finally:
        engine.dispose()


def test_bootstrap_admin_password_requires_both_environment_variables():
    """Missing bootstrap variables fail without disclosing a configured password."""
    workspace = Path(__file__).parents[2]
    password = f"Bootstrap-{uuid.uuid4().hex}"
    environment = os.environ | {
        "SUPABASE_BOOTSTRAP_EMAIL": f"missing-{uuid.uuid4().hex}@example.com",
        "SUPABASE_BOOTSTRAP_PASSWORD": password,
        "SUPABASE_SERVICE_ROLE_KEY": _local_supabase_value("SERVICE_ROLE_KEY"),
    }
    environment.pop("SUPABASE_BOOTSTRAP_PASSWORD")
    result = subprocess.run(
        [str(workspace / ".venv/bin/python"), "scripts/bootstrap_admin.py"],
        cwd=workspace,
        env=environment,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "SUPABASE_BOOTSTRAP_PASSWORD is required" in result.stderr.decode()
    assert password not in result.stdout.decode()
    assert password not in result.stderr.decode()


def test_bootstrap_admin_password_repairs_an_inactive_non_admin_profile():
    """Password bootstrap restores an existing administrator profile's access."""
    workspace = Path(__file__).parents[2]
    email = f"repair-{uuid.uuid4().hex}@example.com"
    environment = os.environ | {
        "SUPABASE_BOOTSTRAP_EMAIL": email,
        "SUPABASE_BOOTSTRAP_PASSWORD": f"Bootstrap-{uuid.uuid4().hex}",
        "SUPABASE_SERVICE_ROLE_KEY": _local_supabase_value("SERVICE_ROLE_KEY"),
    }
    command = [str(workspace / ".venv/bin/python"), "scripts/bootstrap_admin.py"]
    subprocess.run(command, cwd=workspace, env=environment, check=True, capture_output=True)

    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "update public.users set role = 'VENDEDOR', is_active = false where email = :email"
                ),
                {"email": email},
            )
        subprocess.run(command, cwd=workspace, env=environment, check=True, capture_output=True)
        with engine.connect() as connection:
            profile = connection.execute(
                text("select role, is_active from public.users where email = :email"),
                {"email": email},
            ).one()
        assert profile == ("SUPER_ADMIN", True)
    finally:
        engine.dispose()
