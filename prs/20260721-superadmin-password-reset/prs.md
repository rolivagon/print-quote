# Superadmin Password Reset

**Status:** Done

## Purpose

Allow a `SUPER_ADMIN` to directly set a new password for a user from the user list, without exposing or retaining that password. The browser submits the selected password once through an authenticated API request, and the backend updates the target user's Supabase Auth credential.

## Requirements

1. **When** an authenticated user with the `SUPER_ADMIN` role views the user list, **the system shall** provide an action that opens a password-reset modal for each user.
2. **When** an authenticated user without the `SUPER_ADMIN` role views the user list, **the system shall not** provide an action to open a password-reset modal.
3. **When** a `SUPER_ADMIN` opens the password-reset modal, **the system shall** present fields for a new password and its confirmation before enabling submission.
4. **When** the new-password and confirmation values do not match, **the system shall** prevent submission and indicate that they must match.
5. **When** a `SUPER_ADMIN` confirms matching password values, **the browser shall** send the new password exactly once in an authenticated request to the password-reset API for the selected user.
6. **When** a `SUPER_ADMIN` cancels or closes the password-reset modal, **the system shall** discard the entered password values and shall not send a password-reset request.
7. **When** the password-reset API receives a request from an authenticated `SUPER_ADMIN` for an existing target user, **the system shall** update that target user's Supabase Auth password and return a success result without returning the password.
8. **When** the password-reset API receives a request from an authenticated user whose role is not `SUPER_ADMIN`, **the system shall** reject the request and shall not change the target user's password.
9. **When** the password-reset API receives a request for a target user that cannot be updated, **the system shall** return a failure result without returning the submitted password.
10. **The system shall not** persist, return, log, or otherwise expose a password submitted through the password-reset flow.

## TDD-First Tasks

1. Add failing backend API tests using the established Supabase-backed fixtures and dependency overrides that verify successful `SUPER_ADMIN` reset, non-superadmin rejection, and failure responses do not contain the submitted password.
2. Add the minimal backend behavior to authorize the caller independently of the UI and update the target Auth user through the Supabase Admin API; make the backend tests pass.
3. Add failing frontend tests for superadmin action visibility, modal open/cancel behavior, confirmation mismatch validation, one authenticated submission on confirmation, and hiding the action from other roles.
4. Implement the minimal user-list action and modal behavior to make the frontend tests pass, ensuring entered values are cleared when the modal closes.
5. Refactor only after all tests pass, preserving behavior and avoiding duplicated view or test setup.
6. Run backend formatting, linting, and relevant Supabase-backed tests; run frontend linting, formatting, and TypeScript-inclusive build.

## Acceptance Checks

- A `SUPER_ADMIN` can open the modal from the user list, enter matching values, and receives a successful completion indication after one authenticated request.
- A mismatched confirmation cannot be submitted, and cancelling or closing the modal makes no request and removes entered values.
- A non-superadmin neither sees the user-list action nor can reset a password by calling the API directly.
- A successful reset changes the target user's Supabase Auth password, while no password is included in API responses, stored in application data, or emitted in logs.
- An unavailable or invalid target produces a failure indication without disclosing the submitted password.

## Constraints

- Supabase Auth remains the sole credential authority; use its Admin API server-side to update the target Auth user's password.
- The browser must use the authenticated FastAPI API; it must not receive a Supabase service-role credential or directly access business data.
- Backend authorization is mandatory and must not depend on whether the frontend hides the action.
- No public-schema migration or password persistence is permitted for this change.
- API/Auth tests must run against local Supabase/PostgreSQL and reuse existing test fixtures and dependency overrides; frontend verification must include the TypeScript-aware build.
- Use the root Python 3.11 `.venv` and project Makefile checks for backend work, and the committed frontend lockfile for frontend dependencies.
- Do not place passwords, environment values, service-role credentials, or legacy password hashes in source, logs, PRS material, commits, or frontend code.

## Implementation Evidence

- `make test-supabase SUPABASE_TEST_TARGETS=tests/test_api/test_users.py` passed: 11 tests, including superadmin authorization, failure handling, and password-redaction responses.
- The local Supabase integration test proved that a password set through the Admin API authenticates successfully.
- `npm run test`, `npm run lint`, and `npm run build` passed; the existing CSS and bundle-size warnings remain.
- Cloud Build `9d3e611c-c01a-4611-92f9-3ddee541b84e` deployed revision `print-quote-00002-p7h`. The public service returned HTTP 200 for `/` and `/health`; an unauthenticated password-reset request returned HTTP 401.
