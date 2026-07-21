# Architecture

## System boundaries

- The application is a FastAPI backend in `src/quote/` and a Vue 3 SPA in `frontend/`.
- The API entry point is `quote.api.main:app`; HTTP routers belong in `src/quote/api/`.
- The frontend calls `http://localhost:5001/api` in development and `/api` in production, unless `VITE_API_URL` overrides it.

## Backend layers

- `domain/` contains domain types and business orchestration contracts.
- `pricing/` contains pricing strategies. All pricing logic belongs here and monetary values use `Decimal`.
- `repo/` contains repository abstractions and SQL persistence. Persistent SQLModel entities belong in `repo/models/`.
- `service/` coordinates use cases and domain behavior.
- `api/` composes services, pricing strategies, and SQL repositories; it must not contain pricing rules.

## Persistence

- PostgreSQL/Supabase is required at runtime. `DATABASE_URL` must be PostgreSQL-compatible; SQLite has no runtime fallback.
- `supabase/migrations/` is the sole authority for public-schema changes. Alembic is retired and must not be used by reset or deployment workflows.
- Application identities are UUIDs shared with `auth.users`. Quote sellers and client creators reference those UUID profiles.
- Row-level security is enabled on every public application table with no browser-access policies. FastAPI is the sole business-data API and enforces profile status, role, and ownership.

## Frontend

- The frontend is a Vue 3 application using TypeScript, Vue Router, Pinia, Tailwind, and Vite.
- Reuse the established views and components rather than duplicating preview-specific implementations.
- Production SPA assets must be built before the API can serve the SPA fallback.

## Testing boundaries

- Service tests use in-memory repositories where appropriate.
- Pure domain/service tests use in-memory repositories. API, Auth, RLS, reset, and migration checks run against local Supabase/PostgreSQL.
- Tests must be added at the layer that owns the behavior.
