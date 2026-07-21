# Bootstrap Administrator Password

**Status:** Done

## Purpose

Provide an operational, idempotent Supabase bootstrap command that creates or repairs an administrator Auth identity and profile using environment-only credentials. The command supports local and production initial setup and administrator password reset without exposing the password.

## Requirements

1. **When** the bootstrap command is run with `SUPABASE_BOOTSTRAP_EMAIL` and `SUPABASE_BOOTSTRAP_PASSWORD` set and no Auth user exists for that email, **the system shall** create a confirmed Supabase Auth user for that email whose password can successfully authenticate with Supabase.
2. **When** the bootstrap command is run with both bootstrap environment variables set and an Auth user already exists for that email, **the system shall** set that user's password to the supplied environment value so that Supabase password authentication succeeds with the new value.
3. **When** the bootstrap command completes for the configured email, **the system shall** ensure a linked `public.users` profile exists for that Auth user's UUID, is active, and has the `SUPER_ADMIN` role.
4. **When** the bootstrap command is run repeatedly with the same configured environment values, **the system shall** complete successfully and leave exactly one Auth user and one linked active `SUPER_ADMIN` profile for the configured email.
5. **When** the bootstrap command is run without either required bootstrap environment variable, **the system shall** fail with an actionable message that identifies the missing variable name and shall not create or modify an Auth user or profile.
6. **When** the bootstrap command writes console output or reports an error, **the system shall** not include the value of `SUPABASE_BOOTSTRAP_PASSWORD`.
7. **When** an operator invokes the documented Makefile bootstrap target, **the system shall** execute the password-bootstrap operation using backend-only service-role access; browser-delivered code shall not receive or use service-role credentials.
8. **When** the local-development documentation describes administrator bootstrap, **the documentation shall** replace the invitation-only contract with the environment-only password-bootstrap contract, name the required environment-variable keys, and state that the password value must never be embedded, logged, seeded, committed, or documented.
9. **When** this PRS describes authentication bootstrap behavior, **it shall** state that Supabase Auth remains the credential authority and that `public.users` retains only the linked profile's role and active state.

## TDD-First Tasks

1. Add a failing local-Supabase integration test proving the Makefile-backed bootstrap operation creates a confirmed user, creates or repairs its active `SUPER_ADMIN` profile, and allows password sign-in with the configured environment value.
2. Add failing integration tests for an existing Auth user, an existing incomplete or inactive profile, repeated invocation, and missing required environment variables.
3. Add a failing integration test that captures command output for both success and failure paths and proves the configured password value is absent.
4. Implement the smallest backend-only operational bootstrap behavior needed to satisfy the failing tests, using service-role access only outside browser-delivered code.
5. Add the Makefile target that invokes the operation without echoing the password.
6. Update `docs/local-development.md` and this PRS's authentication-bootstrap documentation to replace the invitation-only policy with the environment-only password-bootstrap contract and its secrecy rules; do not include a password value.
7. Refactor only after tests pass, preserving observable behavior and avoiding duplicated setup or credential-handling logic.

## Acceptance Checks

- Local Supabase integration tests demonstrate password sign-in after both initial creation and reset of an existing Auth user.
- Local Supabase integration tests demonstrate a linked, active `SUPER_ADMIN` profile exists after creation, profile repair, and repeated execution.
- Local Supabase integration tests demonstrate repeated execution is successful and does not duplicate the Auth identity or profile.
- Tests demonstrate missing required variables make no identity or profile changes and produce an actionable variable-name-only error.
- Captured command output contains no configured password value on success or failure.
- The Makefile target performs the operation without requiring service-role credentials in frontend or browser-delivered configuration.
- `docs/local-development.md` documents the environment-only password-bootstrap flow and explicitly prohibits embedding, logging, seeding, committing, or documenting the password value.
- Run `make fmt`, `make lint`, and the relevant `make test-supabase` checks successfully.

## Constraints

- Supabase Auth is the sole authority for credentials and access tokens; the linked PostgreSQL profile retains role and active state.
- PostgreSQL/Supabase is required; Auth and integration coverage must run against local Supabase/PostgreSQL rather than SQLite or an in-memory substitute.
- Keep public-table RLS deny-by-default and do not expose a service-role credential to browser code.
- Public-schema changes, if required, must be managed only through checked-in Supabase migrations; do not use Alembic.
- Use Python 3.11 and the root `.venv` for backend tooling. Reuse existing fixtures and helpers where applicable.
- Treat `SUPABASE_BOOTSTRAP_PASSWORD` solely as an environment-provided secret: never embed, log, seed, commit, or document its value.
- Follow test-first implementation: first failing test, minimal passing behavior, then refactor without changing behavior.
