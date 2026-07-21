# Load Canonical Digital Data

**Status:** Done

## Purpose

Provide a repeatable, additive operational command that loads the canonical digital papers, finishes, and associated pricing into the PostgreSQL/Supabase database selected by `DATABASE_URL`. It must be safe to run against production data: records and prices already present must not be changed, and only missing canonical data may be created.

## Requirements

1. **When** the digital-data loader is invoked with a PostgreSQL-compatible `DATABASE_URL` that contains none of the canonical digital papers, finishes, or pricing records, **the system shall** create each canonical digital paper, finish, and associated price in that database.
2. **When** a canonical digital paper already exists in the target database, **the system shall** leave its persisted attributes unchanged.
3. **When** a canonical finish already exists in the target database, **the system shall** leave its persisted attributes unchanged.
4. **When** a canonical price already exists in the target database, **the system shall** leave its persisted monetary value and associated persisted attributes unchanged.
5. **When** the target database contains only a subset of the canonical digital papers, finishes, or prices, **the system shall** add every missing canonical record without changing any existing record.
6. **When** the loader is invoked more than once against the same target database, **the system shall** produce the same persisted digital papers, finishes, and prices after each invocation as after the first successful invocation.
7. **When** a developer invokes the documented Makefile target for the loader, **the system shall** execute the loader using the `DATABASE_URL` environment configuration.
8. **When** the integration suite runs against local Supabase after a database reset, **the system shall** verify the first loader invocation creates the canonical digital papers, finishes, and prices.
9. **When** the integration suite invokes the loader a second time against that same local Supabase database, **the system shall** verify that record counts and all pre-existing paper, finish, and price values are unchanged.

## TDD-first tasks

1. Add a failing Supabase-backed integration test that invokes the loader against a reset local database and asserts the complete canonical digital catalog and pricing data are present.
2. Add a failing integration test that captures the loaded records, invokes the loader again, and asserts that no duplicate records are created and all captured values are unchanged.
3. Add a failing integration test with pre-existing production-like paper, finish, and price rows and assert that the loader adds only missing canonical rows without updating those existing rows.
4. Implement the additive loader and its canonical data definition until the tests pass, keeping monetary values as `Decimal`.
5. Add the Makefile target that runs the loader through the project virtual environment and passes through `DATABASE_URL`.
6. Run formatting and linting, then rerun the relevant local-Supabase integration tests.

## Acceptance checks

- After `make db-reset`, the loader Makefile target succeeds with local Supabase/PostgreSQL configured through `DATABASE_URL`.
- The local-Supabase integration test proves all canonical digital papers, finishes, and their prices are created on the first invocation.
- The same test proves a second invocation creates no duplicates and preserves all previously persisted attributes and monetary values.
- The pre-existing-row test proves existing paper, finish, and price data is never overwritten while missing canonical data is added.
- `make fmt`, `make lint`, and the relevant `make test-supabase` checks pass.

## Constraints

- PostgreSQL/Supabase is required; use `DATABASE_URL` and provide no SQLite fallback.
- Public-schema changes, if required, must be managed only through checked-in Supabase migrations; Alembic must not be used.
- The loader must be additive and idempotent: it must not update or delete existing production rows or prices.
- Store persistent entities in the repository model layer, retain pricing logic in `pricing/`, and use `Decimal` for monetary values.
- Tests that exercise persistence must run against local Supabase/PostgreSQL and reuse established fixtures and helpers where applicable.
- Implement test-first; run formatting and linting before the final relevant test pass.
- Use the root `.venv` through Makefile targets for backend tooling, keep environment values in `.env.local`, and do not expose them in this PRS.
- Prefer the smallest correct change and avoid duplicated loader or test setup logic.
