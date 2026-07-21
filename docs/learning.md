# Learning

## Working agreements

- Prefer the smallest correct change and share repeated logic in a common location.
- Inspect existing code and patterns before introducing a new abstraction.
- Keep code in one function unless a composable or reusable unit makes the design clearer.
- Do not duplicate a full view to implement a preview; reuse the main view implementation.

## Verification lessons

- Formatting and linting can change files, so run them before the final test pass and review their diff.
- API tests should use repository fixtures and dependency overrides from `tests/conftest.py`, not a developer's local database.
- Frontend builds include TypeScript checking; a Vite-only build is insufficient when type safety is relevant.

## Operational lessons

- Use Makefile targets for project operations, including Cloud Run diagnostics when those targets exist.
- Keep environment values in `.env.local`; do not expose or copy them into documentation, PRS files, or commits.
- Record a new learning here only after it has affected an implementation, review, incident, or verification result.
- Supabase Auth owns credentials and browser sessions. Never log passwords, copy legacy password hashes, or expose a service-role credential in frontend code.
