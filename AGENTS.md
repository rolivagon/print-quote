# Print Quote Agent Guide

## Setup and verification

- Use Python 3.11 and the root `.venv`: `make venv`, then `make deps`. The Makefile invokes `.venv/bin/*` and loads `.env.local` when present.
- Backend checks: `make fmt`, `make lint`, then `make test`. `make lint` fixes issues; `make all` recreates the environment before running that sequence.
- Run a focused backend test with `.venv/bin/pytest tests/test_api/test_quotes_digital.py -v` or append `::test_name`.
- Frontend commands run from `frontend/`. Install from its committed lockfile with `npm ci`; use `npm run lint`, `npm run format`, and `npm run build`. The latter runs `vue-tsc` before Vite; `make build-frontend` runs only Vite.

## Application boundaries

- The FastAPI application is `quote.api.main:app`; routers live in `src/quote/api/`. `make run` serves only the API on port 8000.
- Use `make dev` for the integrated app: API port 5001 plus Vite (5173 or next available). The frontend defaults to `http://localhost:5001/api` in development and `/api` in production; override with `VITE_API_URL` when needed. `make dev` first force-kills ports 5001, 5173, and 5174.
- Build the SPA before `make serve`: the API serves `frontend/dist` and provides the SPA fallback only when that directory exists.
- Keep pricing logic in `src/quote/pricing/`; API quote routes compose pricing strategies with SQL repositories. Use `Decimal` for monetary values.
- Persistent SQLModel entities are in `src/quote/repo/models/`; `supabase/migrations/` is the public-schema authority. Domain types and orchestration remain under `domain/` and `service/`.

## Data and tests

- PostgreSQL/Supabase is required at runtime. Set a PostgreSQL-compatible `DATABASE_URL` for the backend.
- `make db-reset` targets local Supabase and applies checked-in Supabase migrations; it does not invoke Alembic or credential-bearing seed scripts.
- Pure unit tests use in-memory repositories. API, Auth, RLS, reset, and migration checks run against local Supabase/PostgreSQL.
- Reuse `tests/conftest.py` fixtures and helpers. Add HTTP tests under `tests/test_api/` using `api_client` or `authorized_client`; use in-memory repositories for service-layer tests.

## Significant changes

- For a new feature or substantial refactor, create a PRS first with `/create-prs <description>`. The contract lives at `prs/{YYYYMMDD}-{description}/prs.md` and must be approved before implementation.
- Implement approved PRS files with `/implement-prs <path>`, following their EARS requirements and TDD-first tasks. Run the relevant formatting, linting, and test checks before moving the PRS to `In Review`.
- Critically review implementation with `/review-prs <path>`. Resolve review findings and required verification before marking the PRS `Done`.
- The four project agreements are `docs/architecture.md`, `docs/decisions.md`, `docs/local-development.md`, and `docs/learning.md`. They are the source of truth for new PRS work.
- Existing `openspec/` material is historical; do not use OpenSpec for new changes.
