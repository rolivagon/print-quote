# Local Development

## Backend setup

1. Create the environment with `make venv`.
2. Install backend dependencies with `make deps`.
3. Run the backend test suite with `make test`.

The Makefile runs Python tooling through `.venv/bin/*` and loads `.env.local` when present. Runtime commands require a PostgreSQL-compatible `DATABASE_URL`; no SQLite fallback exists. Run API tests through `make test-supabase` (or its `test-supabase-existing` variant after a reset); pure checks can run directly with `.venv/bin/pytest`.

## Backend verification

Run these checks in order:

```bash
make fmt
make lint
make test
```

Run `make test-unit` when validating the database-free pricing, domain, service, and token subset. API, Auth, RLS, reset, and migration checks belong to `make test-supabase`.

`make lint` applies Ruff fixes. `make all` recreates the environment and runs the full backend sequence.

## Frontend

Install frontend dependencies from `frontend/` with `npm ci`. Use these commands from that directory:

```bash
npm run lint
npm run format
npm run build
```

`npm run build` runs `vue-tsc` before Vite. `make build-frontend` only runs Vite.

## Running the application

- `make run` starts only the API on port 8000 by default.
- `make dev` starts the API on port 5001 and Vite on port 5173 or the next available port. It clears ports 5001, 5173, and 5174 first.
- Build the frontend before `make serve`; the API serves `frontend/dist` only when it exists.

## Databases

- Supabase/PostgreSQL is the required runtime database in local development and production.
- Pure unit tests use in-memory repositories and need no database service. API, Auth, RLS, reset, and migration tests require local Supabase/PostgreSQL.
- `make db-reset` rebuilds local Supabase from `supabase/migrations/`; it does not invoke Alembic. Run `make test-supabase` for Supabase-backed integration checks.
- To create or reset the first administrator, set `SUPABASE_BOOTSTRAP_EMAIL` and `SUPABASE_BOOTSTRAP_PASSWORD` in the runtime environment and run `make bootstrap-admin`. The command creates or updates the Supabase Auth password and ensures an active `SUPER_ADMIN` profile. Never embed, log, seed, commit, or document the password value.
- For the running local Supabase stack, use `make bootstrap-admin-local` with those same bootstrap variables. It resolves the local service-role credential from `supabase status` without writing it to `.env.local`.
- To transition a legacy SQLite or PostgreSQL database, set `LEGACY_DATABASE_URL` and run `make migrate-legacy`. It reads identity, role, active-state, and ownership columns only; it never reads or copies password hashes.
- `supabase/config.toml` disables confirmation for local/test. Production deployments must apply the checked-in `supabase/config.production.toml` contract, which requires email confirmation.
- The Makefile includes `.env.local`. When running the additive digital catalog loader against an explicitly loaded production environment, use `set -a && . ./.env.prod && set +a && make -e load-digital-data` so the production `DATABASE_URL` takes precedence over local configuration.
