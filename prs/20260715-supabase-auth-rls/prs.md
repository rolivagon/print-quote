# PRS: Supabase Auth, UUID Identity, and RLS Migration

## Status

In Review

## Purpose

Replace the custom credential and token system with Supabase Auth, migrate application identities and ownership references to Auth-linked UUIDs, require PostgreSQL/Supabase, and protect the public schema with deny-by-default RLS while preserving FastAPI as the sole business-data API. Establish Supabase migrations and reproducible Makefile workflows as the schema and environment contract for local development, CI, and production.

## Requirements

### Runtime and authentication boundary

- REQ-001: When the backend starts without `DATABASE_URL`, the system shall reject startup with a clear configuration error.
- REQ-002: When the backend starts with a `DATABASE_URL` that is not PostgreSQL-compatible, the system shall reject startup with a clear configuration error.
- REQ-003: When a protected API request is authenticated, the system shall accept only a valid Supabase access token as authentication evidence.
- REQ-004: When a protected API request contains an invalid, expired, malformed, or unverifiable access token, the system shall respond with HTTP 401.
- REQ-005: When a valid Supabase access token identifies a subject with no linked application profile, the system shall deny access.
- REQ-006: When a valid Supabase access token identifies a subject whose linked application profile is inactive, the system shall deny access.
- REQ-007: When an authenticated request requires authorization, the system shall determine the user's role from the active database profile linked to the token subject UUID rather than from client-supplied or token profile metadata.
- REQ-008: When a client attempts to authenticate through the former custom password or HS256-token contract, the system shall not authenticate the client or issue a legacy application token.

### Signup and browser session behavior

- REQ-009: When public email/password signup succeeds, the system shall create exactly one application profile linked to the new Auth subject UUID with the default `vendedor` role.
- REQ-010: When signup occurs in production, the system shall require email confirmation before the new user can establish an authenticated application session.
- REQ-011: When signup occurs in the documented local or test environment, the system shall allow the user to establish a session without external email delivery.
- REQ-012: When a user has an unexpired browser session and reloads the application, the system shall restore the authenticated session without requesting credentials again.
- REQ-013: When a browser session has a refreshable expired access token, the system shall obtain a new valid access token and continue authenticated API access without requesting credentials again.
- REQ-014: When a signed-in user logs out, the system shall terminate and remove the local session so subsequent protected API requests are not authenticated by that session.
- REQ-015: When login, signup, refresh, logout, or an error occurs, the system shall prevent plaintext passwords from appearing in browser console output, backend logs, API responses, test artifacts, or other application diagnostics.

### Administration and legacy transition

- REQ-016: When an authorized administrator invites a user through the application UI or API, the system shall create an invitation linked to an application profile without accepting or assigning an administrator-defined password. The operational first-administrator bootstrap is governed separately by `prs/20260720-bootstrap-admin-password/prs.md`.
- REQ-017: When a non-administrator attempts to invite a user, the system shall deny the operation.
- REQ-018: When an existing bcrypt-backed user is migrated, the system shall provision or invite the user in Supabase and require the user to set or reset credentials before authenticating.
- REQ-019: When legacy users are migrated, the system shall not copy a bcrypt hash or other existing password-derived credential into Supabase Auth, application profiles, migration output, or logs.
- REQ-020: When an existing user is migrated, the system shall retain that user's existing application role and active state in the linked UUID profile.
- REQ-021: When legacy identities and references are migrated, the system shall preserve every existing quote seller and client creator association with the same application user.
- REQ-022: When the migration/bootstrap workflow is rerun against an already migrated database, the system shall complete without duplicate Auth identities, duplicate profiles, duplicate invitations, or changed ownership.
- REQ-023: When a fresh environment has no administrator, the system shall provide a documented bootstrap workflow that creates the first administrator from environment-only credentials without embedding, printing, logging, seeding, or committing a password, access token, service-role credential, or other secret.

### UUID integrity and data access

- REQ-024: When a profile exists, the system shall use the same UUID for its application identity and linked `auth.users` subject.
- REQ-025: When a quote seller or client creator is stored or returned, the system shall use a UUID reference that resolves to an existing application profile.
- REQ-026: When a write supplies a seller or creator UUID that has no corresponding application profile, the system shall reject the write without persisting partial data.
- REQ-027: When the fresh public application schema is inspected, the system shall have row-level security enabled on every application table.
- REQ-028: When the public schema is accessed directly with Supabase anonymous credentials, the system shall deny application-table reads and writes.
- REQ-029: When the public schema is accessed directly with ordinary Supabase authenticated credentials, the system shall deny application-table reads and writes.
- REQ-030: When an authorized user performs a supported business operation through FastAPI, the system shall retain the required backend database access and enforce the user's profile status, role, and ownership rules.
- REQ-031: When frontend assets, browser configuration, network traffic, and build output are inspected, the system shall not expose a privileged database or Supabase service-role credential.

### Schema, reset, and workflow authority

- REQ-032: When the documented fresh-reset Makefile target runs against local Supabase, the system shall recreate the complete public schema, Auth-linked profile behavior, UUID references, and RLS protections without invoking Alembic.
- REQ-033: When the fresh-reset workflow is run repeatedly from an empty local environment, the system shall produce the same documented non-secret seed identities, roles, ownership relationships, and business data.
- REQ-034: When a future public-schema change is created or a fresh schema is rebuilt, the system shall apply `supabase/migrations` as the sole source of public-schema changes and shall not invoke an active Alembic workflow.
- REQ-035: When the documented Supabase integration Makefile target runs in local development or CI, the system shall execute API, Auth, RLS, and migration integration checks against Supabase/PostgreSQL and report failure with a non-zero exit status.
- REQ-036: When pure unit tests run, the system shall not require a running database.
- REQ-037: When implementation is review-ready, the system shall provide architecture, decisions, and local-development agreements that describe Supabase Auth, PostgreSQL-only runtime, UUID identity, deny-by-default RLS, Supabase migration authority, and the current reset/test workflows without retaining conflicting SQLite, custom-auth, or Alembic guidance.

## Tasks

Tasks are ordered. For every requirement, add the stated failing check first, observe the failure, implement only enough behavior to pass, and then refactor while keeping the check green.

- [x] T-001: Add failing startup tests for absent and non-PostgreSQL `DATABASE_URL` (`REQ-001`, `REQ-002`).
- [x] T-002: Implement PostgreSQL-only runtime configuration (`REQ-001`, `REQ-002`).
- [x] T-003: Add failing API tests for Supabase tokens, missing/inactive profiles, database-backed roles, and rejected legacy authentication (`REQ-003`–`REQ-008`).
- [x] T-004: Replace custom bcrypt/HS256 authentication with Supabase token validation and profile-backed authorization (`REQ-003`–`REQ-008`).
- [x] T-005: Add failing Supabase integration tests for signup profiles and environment-specific email confirmation (`REQ-009`–`REQ-011`).
- [x] T-006: Implement public Supabase signup and automatic UUID-linked `vendedor` profile creation (`REQ-009`–`REQ-011`).
- [x] T-007: Add failing frontend tests for session restoration, token refresh, logout, and credential confidentiality (`REQ-012`–`REQ-015`).
- [x] T-008: Integrate `supabase-js` with the frontend auth store and replace the registration mock (`REQ-012`–`REQ-015`).
- [x] T-009: Add failing API and frontend tests for administrator invitations and non-administrator denial (`REQ-016`, `REQ-017`).
- [x] T-010: Replace administrator-defined passwords with Supabase invitations (`REQ-016`, `REQ-017`).
- [x] T-011: Add failing migration tests for credential reset, hash exclusion, role/state preservation, and ownership preservation (`REQ-018`–`REQ-021`).
- [x] T-012: Implement the legacy-user transition to Auth-linked UUID profiles and UUID ownership references (`REQ-018`–`REQ-021`, `REQ-024`, `REQ-025`).
- [x] T-013: Add failing repeat-run and fresh-environment tests for idempotent migration and administrator bootstrap (`REQ-022`, `REQ-023`).
- [x] T-014: Implement secure, idempotent migration and administrator bootstrap commands (`REQ-022`, `REQ-023`).
- [x] T-015: Add failing schema and transactional tests for profile UUIDs, ownership UUIDs, referential rejection, and rollback (`REQ-024`–`REQ-026`).
- [x] T-016: Implement UUID constraints and transactional ownership validation (`REQ-024`–`REQ-026`).
- [x] T-017: Add failing schema and direct-access tests that enumerate application tables and exercise anonymous and authenticated credentials (`REQ-027`–`REQ-029`).
- [x] T-018: Enable deny-by-default RLS on every application table (`REQ-027`–`REQ-029`).
- [x] T-019: Add failing end-to-end tests for permitted and forbidden FastAPI operations through the privileged backend path (`REQ-030`).
- [x] T-020: Configure backend database access without weakening application authorization (`REQ-030`).
- [x] T-021: Add a failing frontend build/configuration scan using sentinel privileged credentials (`REQ-031`).
- [x] T-022: Restrict frontend configuration to publishable Supabase values (`REQ-031`).
- [x] T-023: Add failing clean-reset and repeat-reset tests for the complete schema, Auth behavior, RLS, deterministic seed data, and absence of Alembic execution (`REQ-032`–`REQ-034`).
- [x] T-024: Establish `supabase/migrations` as schema authority and retire active Alembic/reset workflows (`REQ-032`–`REQ-034`).
- [x] T-025: Add a failing harness test for the local/CI Supabase integration target and its failure propagation (`REQ-035`).
- [x] T-026: Implement the Makefile integration target for API, Auth, RLS, and migration checks (`REQ-035`).
- [x] T-027: Add a failing isolation check for the pure unit-test subset with database services stopped (`REQ-036`).
- [x] T-028: Separate pure unit tests from Supabase-backed integration tests (`REQ-036`).
- [x] T-029: Add a failing agreement-consistency check for superseded SQLite, Alembic, custom-auth, and integer-identity guidance (`REQ-037`).
- [x] T-030: Update architecture, decisions, and local-development agreements after executable behavior is green (`REQ-037`).
- [x] T-031: Run `make fmt`, `make lint`, `make test`, the Supabase integration target, and frontend lint, format, and build checks (all requirements).
- [x] T-032: Review the implementation against every requirement and the four project agreements before moving the PRS to `In Review` (all requirements).

## Acceptance Checks

- [x] Startup tests prove missing and non-PostgreSQL `DATABASE_URL` are rejected (`REQ-001`, `REQ-002`).
- [x] Protected-route tests prove valid Supabase-token access, 401 for invalid tokens, missing/inactive-profile denial, database-backed role authority, and legacy-auth rejection (`REQ-003`–`REQ-008`).
- [x] Local/CI and production-mode Auth tests prove signup profile defaults, confirmation behavior, persistence, refresh, and logout (`REQ-009`–`REQ-014`).
- [x] Sentinel-secret tests and artifact inspection prove passwords, hashes, and privileged credentials are not exposed (`REQ-015`, `REQ-019`, `REQ-023`, `REQ-031`).
- [x] Admin invitation tests prove admin-only invitations and the absence of admin-defined passwords (`REQ-016`, `REQ-017`).
- [x] Migration tests prove required credential reset, role/active-state preservation, ownership preservation, and repeatable idempotence (`REQ-018`–`REQ-022`).
- [x] Bootstrap tests prove the first administrator is created securely and repeat runs create no duplicate identities, profiles, or invitations (`REQ-022`, `REQ-023`).
- [x] Schema and API tests prove Auth-linked UUID profiles, UUID seller/creator references, referential rejection, and transaction safety (`REQ-024`–`REQ-026`).
- [x] Direct Supabase tests enumerate every application table and prove RLS is enabled and both anonymous and ordinary authenticated access are denied (`REQ-027`–`REQ-029`).
- [x] FastAPI end-to-end tests prove permitted business operations still work and forbidden operations remain denied through the privileged backend path (`REQ-030`).
- [x] The fresh-reset target succeeds from an empty local Supabase instance twice, recreates the complete schema and deterministic seed state, and does not invoke Alembic (`REQ-032`–`REQ-034`).
- [x] The Supabase integration Makefile target passes locally and in CI, and a forced test failure returns a non-zero status (`REQ-035`).
- [x] The pure unit-test subset passes with database services stopped (`REQ-036`).
- [x] Updated agreements contain no conflicting SQLite runtime, Alembic authority, custom-auth, integer-identity, or database-free API/integration-test guidance (`REQ-037`).
- [x] Backend verification passes in order: `make fmt`, `make lint`, `make test`.
- [x] The documented Supabase integration Makefile target passes.
- [x] Frontend verification passes from `frontend/`: `npm run lint`, `npm run format`, `npm run build`.
- [x] Final review maps passing evidence to `REQ-001` through `REQ-037` and confirms no undocumented secrets or unrelated changes.

## Constraints

- Supabase Auth is the sole authentication authority; custom bcrypt verification, application-issued HS256 authentication, and credentials in `public.users` must not remain active.
- FastAPI remains the sole business-data API. Browser clients must not gain direct application-table access.
- The frontend may receive only publishable Supabase configuration; service-role, privileged database, and signing credentials must remain backend-only.
- PostgreSQL/Supabase is required at runtime in local development and production; there is no runtime SQLite fallback.
- Pure unit tests may avoid a database. API, integration, Auth, RLS, reset, and migration tests must use local Supabase/PostgreSQL in development and CI.
- `supabase/migrations` is the sole authority for future public-schema changes. Conflicting Alembic migration/reset workflows must be removed or clearly retired from active use.
- Existing user roles, active states, quote seller ownership, and client creator ownership must survive migration; legacy password hashes must not.
- Production requires email confirmation. Local and test environments disable it through deterministic checked-in configuration, not ad hoc manual steps.
- Setup, reset, bootstrap, and integration operations must be exposed through Makefile targets. Documentation must not contain secret values.
- Preserve the established domain, pricing, repository, service, and API boundaries. Pricing remains in `src/quote/pricing/` and monetary values remain `Decimal`.
- Reuse shared views, fixtures, and helpers; do not duplicate preview views or repeated test/setup logic.
- Use Python 3.11 and the root `.venv` for backend tooling. Install frontend dependencies with the committed lockfile via `npm ci`.
- Implement each requirement test-first and keep requirements observable; implementation choices not fixed by this PRS remain open to the implementer.
- This PRS intentionally supersedes the current agreement statements that prescribe SQLite runtime fallback, Alembic schema authority, and SQLite-backed API tests; the implementation must update those agreements before review readiness.

## Verification Record

2026-08-12:

- Passed: `make fmt`, `make lint`, `make test` (226 passed, 22 skipped), and `make test-unit` (117 passed).
- Passed: `make test-supabase` (125 passed, 1 skipped, 1 xfailed). These runs exercise Supabase signup/token validation, database-profile authorization, RLS, migration, legacy transition, bootstrap-admin idempotence, forced integration-target failure propagation, frontend build secret-sentinel scanning, HTTP API suite against PostgreSQL, and end-to-end real-token authorization for clients, quotes, and catalog endpoints.
- Passed from `frontend/`: `npm run lint`, `npm run format`, and `npm run build`. The build reports existing CSS-minification and chunk-size warnings but exits successfully.
- Remediation & review gap completed: Added end-to-end real-token authorization coverage across quotes and catalog endpoints in `test_fastapi_enforces_quote_ownership_and_admin_catalog_authorization_with_real_tokens`. Moved PRS to `In Review`.
