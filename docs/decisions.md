# Decisions

## Architecture and data

- Use the existing layered architecture: domain, pricing, repository, service, and API.
- Keep pricing calculations in `src/quote/pricing/`; use `Decimal` for every monetary value.
- Store persistent SQLModel entities in `src/quote/repo/models/`; manage public-schema changes only with checked-in Supabase migrations.
- Supabase Auth is the sole credential and access-token authority. Profiles use the Auth UUID and retain roles and active state in PostgreSQL.
- Keep public-table RLS deny-by-default. Browser code receives only publishable Supabase configuration and accesses business data through FastAPI.
- Do not introduce compatibility behavior without a concrete persisted-data, shipped-behavior, or external-consumer need.

## Development and quality

- Use Python 3.11 and the root `.venv` for backend tooling.
- Implement behavior test-first: add the first failing test, make it pass, then refactor without changing behavior.
- Reuse existing fixtures and helpers instead of duplicating test setup.
- Run formatting, linting, and relevant tests before considering work complete.
- Frontend dependency installation uses its committed lockfile with `npm ci`.

## Change workflow

- Every feature or substantial refactor starts with an approved PRS in `prs/{YYYYMMDD}-{description}/prs.md`.
- A PRS is the implementation contract. Its EARS requirements, acceptance checks, and documented constraints guide implementation and review.
- An approved PRS is implemented with TDD, critically reviewed against the agreed documents, and then moved through its declared status.
- Existing `openspec/` material is historical and is not required for new work.
