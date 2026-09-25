# Print Quote

Print quote calculations for digital, offset, and plotter printing plus packing services.
Backend is FastAPI, frontend is Vue 3 + Vite, database is PostgreSQL via Supabase.

## Stack

- Backend: Python 3.11, FastAPI app at `quote.api.main:app`, routers in `src/quote/api/`, pricing strategies in `src/quote/pricing/`, SQLModel entities in `src/quote/repo/models/`, monetary values as `Decimal`.
- Frontend: Vue 3 + Vite in `frontend/`, Supabase client in `frontend/src/config/supabase.ts`, API base in `frontend/src/config/api.ts`.
- Database authority: `supabase/migrations/` (public schema). No Alembic. No SQLite fallback at runtime.
- Tooling: root `.venv`, Ruff, pytest, Supabase CLI, npm from committed `frontend/package-lock.json`.

## Prerequisites

- Python 3.11
- Node.js + npm (use `npm ci` in `frontend/`, never `npm install` for setup)
- Supabase CLI + Docker (required for local Supabase stack and DB-backed tests)
- A PostgreSQL-compatible `DATABASE_URL` for any backend runtime command

## Backend quickstart (agent path)

```bash
make venv
make deps
cp .env.example .env.local
make fmt
make lint
make test
```

Focused checks:

```bash
make test-unit
.venv/bin/pytest tests/test_api/test_quotes_digital.py -v
```

`make lint` applies Ruff fixes. `make all` recreates the venv and runs fmt + lint + test. The Makefile invokes `.venv/bin/*` and auto-loads `.env.local` when present.

## Local Supabase + DB-backed tests

```bash
make db-reset
make test-supabase
```

- `make db-reset` starts local Supabase and applies checked-in `supabase/migrations/`.
- `make test-supabase` resets the DB then runs `tests/integration` + `tests/test_api` with `RUN_SUPABASE_INTEGRATION=1`, `DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres`, `SUPABASE_URL=http://127.0.0.1:54321`.
- `make test-supabase-existing` reruns the same suite without resetting.
- Pure unit tests use in-memory repositories and need no database.

Create or reset the first admin:

```bash
make bootstrap-admin-local
```

This resolves the local service-role credential from `supabase status` without writing it to `.env.local`. Direct `make bootstrap-admin` requires `SUPABASE_BOOTSTRAP_EMAIL` and `SUPABASE_BOOTSTRAP_PASSWORD` in the environment.

## Run the app

```bash
make run
make dev
make build-frontend && make serve
```

- `make run`: API only on port 8000 (`make run PORT=8080` to override).
- `make dev`: API on 5001 plus Vite on 5173 or next available port. It force-kills 5001, 5173, and 5174 first. Frontend proxies `/api` to `http://localhost:5001` and `/supabase` to `http://127.0.0.1:54321` (see `frontend/vite.config.ts`).
- `make serve`: production mode. Build the SPA first; the API serves `frontend/dist` and its SPA fallback only when that directory exists.

## Frontend

Run from `frontend/`:

```bash
npm ci
npm run lint
npm run format
npm run build
```

`npm run build` runs `vue-tsc` before Vite. `make build-frontend` from the repo root runs only Vite. In development the frontend defaults to `http://localhost:5001/api`; in production to `/api`. Override with `VITE_API_URL`.

## Environment variables

Copy `.env.example` to `.env.local`. Every key in `.env.example` is consumed by code; no unused keys are kept.

| Variable | Used by | Notes |
|---|---|---|
| `DATABASE_URL` | `src/quote/repo/database.py` | PostgreSQL only, required at runtime |
| `SUPABASE_URL` | `src/quote/service/security.py`, `supabase_admin.py` | Local default `http://127.0.0.1:54321` |
| `CORS_ORIGINS` | `src/quote/api/main.py` | Comma-separated browser origins |
| `FRONTEND_DIST` | `src/quote/api/main.py` | Defaults to `frontend/dist` |
| `SUPABASE_SERVICE_ROLE_KEY` | `src/quote/service/supabase_admin.py` | Backend/scripts only, never expose to frontend |
| `SUPABASE_BOOTSTRAP_EMAIL` / `SUPABASE_BOOTSTRAP_PASSWORD` | `scripts/bootstrap_admin.py` | Environment only, never commit or log |
| `LEGACY_DATABASE_URL` | `scripts/migrate_legacy_users.py` | Run via `make migrate-legacy` |
| `VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY` | `frontend/src/config/supabase.ts` | Publishable, required for build |
| `VITE_API_URL` | `frontend/src/config/api.ts` | Defaults to `/api` if unset |

## Tests

- `make test`: backend suite excluding `tests/test_api`.
- `make test-unit`: database-free pricing, domain, service, and token tests.
- `make test-supabase`: full Supabase-backed API, Auth, RLS, reset, and migration checks.
- HTTP tests live under `tests/test_api/` and reuse `api_client` / `authorized_client` from `tests/conftest.py`. Service-layer tests use in-memory repositories.

## Layout

```text
src/quote/
├── api/        # FastAPI app (main.py) and routers (quotes, clients, papers, finishes, fixed_products, users, auth)
├── domain/     # Business models and enums
├── pricing/    # Pricing strategies per print type
├── repo/       # SQL repositories + models/ entities
└── service/    # Orchestration and Supabase admin helpers
supabase/migrations/  # Public-schema authority
scripts/              # bootstrap_admin.py, migrate_legacy_users.py, load_*_data.py
tests/test_api/       # HTTP tests
tests/integration/    # Supabase-backed workflow/schema checks
frontend/src/         # Vue app, config/api.ts, config/supabase.ts
```

## Project agreements

Source of truth for new work:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/decisions.md`
- `docs/local-development.md`
- `docs/learning.md`

For a new feature or substantial refactor, create a PRS first (`prs/{YYYYMMDD}-{description}/prs.md`) and follow the create → implement → review flow. `openspec/` is historical; do not use it for new changes.
