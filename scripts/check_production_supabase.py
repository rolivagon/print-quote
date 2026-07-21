"""Read-only production Supabase schema and RLS verification."""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

APPLICATION_TABLES = {
    "users",
    "legacy_user_migrations",
    "clients",
    "papers",
    "finishes",
    "base_measurements",
    "paper_pricing",
    "finish_pricing",
    "quotes",
    "quote_items",
    "quote_item_finishes",
    "fixed_products",
    "fixed_product_quantity_ranges",
}


def main() -> None:
    """Confirm production schema and browser-role RLS without modifying data."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    engine = create_engine(database_url, pool_pre_ping=True)
    stage = "schema"
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(text("set transaction read only"))
                tables = connection.execute(
                    text(
                        "select tablename, rowsecurity from pg_tables "
                        "where schemaname = 'public' and tablename = any(:tables)"
                    ),
                    {"tables": list(APPLICATION_TABLES)},
                ).all()
                discovered_tables = {row.tablename for row in tables}
                missing_tables = sorted(APPLICATION_TABLES - discovered_tables)
                tables_without_rls = sorted(row.tablename for row in tables if not row.rowsecurity)
                if missing_tables or tables_without_rls:
                    problems = []
                    if missing_tables:
                        problems.append(f"missing tables: {', '.join(missing_tables)}")
                    if tables_without_rls:
                        problems.append(f"RLS disabled: {', '.join(tables_without_rls)}")
                    raise RuntimeError("; ".join(problems))

                stage = "RLS permissions"
                for role in ("anon", "authenticated"):
                    connection.execute(text(f"set local role {role}"))
                    for table in APPLICATION_TABLES:
                        try:
                            rows = connection.execute(
                                text(f"select 1 from public.{table} limit 1")
                            ).all()
                        except SQLAlchemyError:
                            continue
                        if rows:
                            raise RuntimeError(f"RLS exposes {table} rows to {role}")
            finally:
                transaction.rollback()
    except OperationalError:
        raise SystemExit("Production Supabase check could not connect") from None
    except RuntimeError as exc:
        raise SystemExit(
            f"Production Supabase {stage} check failed without modifying data: {exc}"
        ) from None
    except SQLAlchemyError:
        raise SystemExit(
            f"Production Supabase {stage} check failed without modifying data"
        ) from None
    finally:
        engine.dispose()

    print("Production Supabase schema and RLS checks passed")


if __name__ == "__main__":
    main()
