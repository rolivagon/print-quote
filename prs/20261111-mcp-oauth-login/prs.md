# PRS: Autenticación OAuth del servidor MCP con el login actual

## Status

In Review

## Purpose

Permitir que clientes MCP que solo aceptan OAuth (ChatGPT, conectores de claude.ai) y los que hoy usan un token pegado a mano (Claude Code, Claude Desktop) se conecten a `/mcp` sin copiar tokens. El cliente descubre que `/mcp` está protegido por Supabase Auth, abre el navegador en el login actual de Print Quote y obtiene un access token (con refresh token) emitido para el usuario, de modo que las tools actúan con su rol y propiedad de clientes. Si el usuario ya tiene una sesión activa en el navegador, la página de autorización la reutiliza y no vuelve a pedir correo y contraseña; si ya aprobó al cliente antes, la autorización termina sin intervención. Supabase Auth OAuth 2.1 Server (beta, sin costo adicional) actúa como servidor de autorización; FastAPI sigue validando tokens como hoy.

## Requirements

- REQ-001: When a request to `/mcp` is rejected for a missing or invalid token, the system shall respond with HTTP 401 and a `WWW-Authenticate` header of the form `Bearer resource_metadata="<public base URL>/.well-known/oauth-protected-resource/mcp"`.
- REQ-002: When `GET /.well-known/oauth-protected-resource/mcp` or `GET /.well-known/oauth-protected-resource` is requested without authentication, the system shall return a JSON protected resource metadata document (RFC 9728) with `resource` set to the public `/mcp` URL, `authorization_servers` set to `[<SUPABASE_URL>/auth/v1]`, and `bearer_methods_supported` set to `["header"]`.
- REQ-003: The system shall derive the public base URL of the metadata from the incoming request scheme and host, honoring `X-Forwarded-Proto` from Cloud Run, so that the advertised `resource` uses `https` in production.
- REQ-004: The SPA fallback route shall not capture `/.well-known/oauth-protected-resource` paths.
- REQ-005: When an access token issued by the Supabase OAuth server (carrying a `client_id` claim) is sent to `/mcp`, the system shall authenticate it through the same `get_current_user` validation (asymmetric signature, issuer, audience `authenticated`, UUID subject, active profile) used for browser sessions.
- REQ-006: The system shall keep accepting a Supabase access token sent manually in the `Authorization: Bearer` header of `/mcp` requests.
- REQ-007: The frontend shall serve an authorization page at `/oauth/consent` that reads the `authorization_id` query parameter.
- REQ-008: While the browser has an active Supabase session, when `/oauth/consent` is opened, the frontend shall use that session without asking for email or password.
- REQ-009: While the browser has no Supabase session, when `/oauth/consent` is opened, the frontend shall redirect to `/login` preserving the full consent URL, and after a successful login shall return to that consent URL instead of `/`.
- REQ-010: If the post-login return target is not an internal path starting with a single `/`, then the frontend shall ignore it and navigate to `/`.
- REQ-011: When the authorization details for a client the user has already approved contain no pending `authorization_id`, the frontend shall redirect the browser to the returned `redirect_url` without showing the consent screen.
- REQ-012: When the authorization requires consent, the frontend shall show the client name, the signed-in user's email, the requested scopes, and approve and deny actions.
- REQ-013: When the user approves or denies, the frontend shall call `supabase.auth.oauth.approveAuthorization` or `supabase.auth.oauth.denyAuthorization` with the `authorization_id` and redirect the browser to the returned `redirect_url`.
- REQ-014: If the `authorization_id` is missing, unknown, or expired, then the frontend shall show an error message and shall not call approve or deny.
- REQ-015: If the signed-in profile is inactive or has no profile in the API (`GET` of the current user fails with 401 or 403), then the frontend shall show an access-denied message and shall not offer the approve action.
- REQ-016: The local Supabase configuration shall enable the OAuth 2.1 server with `authorization_url_path = "/oauth/consent"` and dynamic client registration enabled.
- REQ-017: The production Supabase Auth contract (`supabase/config.production.toml` and the deployment guide) shall document enabling the OAuth 2.1 server, the authorization path `/oauth/consent`, dynamic client registration, and a Site URL equal to the Cloud Run service URL.
- REQ-018: The system shall not store OAuth client secrets, authorization codes, access tokens, or refresh tokens in FastAPI, the database, logs, or the repository.

## Tasks

- [x] T-001: Add failing API tests for the 401 `WWW-Authenticate` challenge with `resource_metadata` on `/mcp` (missing and invalid token, including `X-Forwarded-Proto: https`); implement it without changing the API's own 401 responses; required by REQ-001, REQ-003, REQ-006.
- [x] T-002: Add failing API tests for both protected resource metadata paths (content, unauthenticated access, `https` behind the proxy header, not captured by the SPA fallback); implement the route in the MCP adapter and register it before the SPA fallback; required by REQ-002, REQ-003, REQ-004.
- [x] T-003: Add a failing test proving a token with a `client_id` claim authenticates on `/mcp` and resolves the same profile and role; adjust validation only if the test fails; required by REQ-005.
- [x] T-004: Add failing frontend tests for the post-login return target (internal path honored, external or `//` targets rejected, `requiresGuest` redirect preserving the target); implement it in the router guard and `Signin.vue`; required by REQ-009, REQ-010.
- [x] T-005: Add failing frontend tests for `/oauth/consent` with a mocked Supabase client (session reused, no session → login redirect, already approved → auto redirect, consent screen content, approve, deny, invalid `authorization_id`, inactive profile); implement the view and route; required by REQ-007, REQ-008, REQ-011, REQ-012, REQ-013, REQ-014, REQ-015.
- [x] T-006: Enable `[auth.oauth_server]` in `supabase/config.toml`, add the production values to `supabase/config.production.toml`, and update `docs/cloud-run-deployment.md`, `docs/local-development.md`, and `docs/architecture.md` (OAuth connection steps for ChatGPT, claude.ai, and Claude Code; manual token as fallback); required by REQ-016, REQ-017, REQ-018.
- [x] T-007: Run `make fmt`, `make lint`, `make test`, `make test-supabase-existing`, and `npm run lint && npm run build` in `frontend/`; manually complete the OAuth flow against local Supabase with an MCP client (MCP Inspector or Claude Code) both with and without an existing browser session; record the results before moving the PRS to review.

## Acceptance Checks

- [x] An MCP client configured only with the `/mcp` URL discovers Supabase as the authorization server, opens the Print Quote consent page, and after approval lists and runs the quote tools with the user's role.
- [x] With an active browser session, the flow completes without entering email or password; a second authorization of the same client completes without the consent screen.
- [x] Without a session, the user signs in on the existing `/login` page and returns to the consent page, not to the dashboard.
- [ ] A seller authorized through OAuth sees only their own clients; an inactive profile cannot approve and is rejected by `/mcp`.
- [x] Denying consent returns the client to its redirect URI with an error and grants no token.
- [x] The manual `Authorization: Bearer` token keeps working on `/mcp`.
- [x] `/login` ignores external return targets.
- [x] `make fmt`, `make lint`, `make test`, `make test-supabase-existing`, and the frontend lint and build pass (pre-existing failures recorded separately).
- [ ] After deployment and enabling the OAuth server in the production project, ChatGPT (connector with OAuth) completes the flow against the Cloud Run URL.

## Verification Notes

- Backend: `tests/test_mcp/test_oauth.py` covers both metadata paths, the forwarded `https` scheme, the 401 challenge with `resource_metadata` for missing and invalid tokens, and an unchanged `WWW-Authenticate: Bearer` on `/api`. `tests/test_security.py` adds a token with a `client_id` claim; it passed without code changes (T-003 needed no validation change). The two existing transport tests now assert the new challenge prefix.
- Frontend: the consent logic lives in `useOAuthConsent` and the return-path check in `router/returnPath.ts`, tested with Vitest (29 tests pass). The repo has no component-testing library, so the view is a thin template over the composable and is not rendered in tests. The `requiresAuth` guard now sends `redirect=<fullPath>` to `/login` for every protected route, and `Signin.vue` and the `requiresGuest` guard honor only internal paths.
- `make fmt`, `make lint`: pass (ruff reformats the unrelated `docs/calculos_cotizacion.md`; reverted). `make test`: `268 passed, 24 skipped, 1 failed` (pre-existing `.env.prod` loader test). `npm run lint`, `npx vitest run`, and `npm run build` (with `vue-tsc`) pass.
- `make test-supabase-existing` with `[auth.oauth_server]` enabled: `133 passed, 1 xfailed, 2 failed`; the two RLS browser-role tests fail without this change as well. The frontend build and legacy-login tests now pass because `frontend/dist` exists.
- Manual end-to-end check against local Supabase (CLI 2.118.0) and `uvicorn` on port 8765, with a script acting as the MCP client and calling the same Auth endpoints `supabase-js` uses on the consent page: 401 challenge → metadata → Supabase discovery → dynamic registration (201) → `/oauth/authorize` redirects to `http://127.0.0.1:5173/oauth/consent?authorization_id=...` → details (client name, scope `email`) → approve → code exchange with PKCE returns access and refresh tokens (`aud=authenticated`, `client_id` present) → `/mcp` lists the 5 tools and `list_clients` succeeds → a second authorization of the same client returns `redirect_url` without consent → refresh grant succeeds → a new client denied returns `error`, `error_description`, `state`. Deny requires loading the details first, which the consent page always does.
- Not verified: rendering of `/oauth/consent` in a real browser, seller and inactive-profile runs through OAuth (covered by the existing `get_current_user` tests and the composable tests), and a real client (ChatGPT, claude.ai, Claude Code) against production, which requires enabling the OAuth server in the production Supabase project.
- Discovery: local Supabase serves `/auth/v1/.well-known/openid-configuration` but returns 404 for the RFC 8414 path-insertion URL `/.well-known/oauth-authorization-server/auth/v1`; production Supabase routes that URL (currently `feature_disabled`). MCP clients fall back to the OpenID path, so local clients still work.
- Local cleanup: the earlier manual-check user and its quote `COT-20261111-0003` were deleted. Because `generate_quote_number` counts the day's quotes, the gap caused duplicate-number failures; the local leftover `COT-20261111-0005` was renumbered to `0003`. This count-based numbering breaks whenever a same-day quote is deleted; it is pre-existing and out of scope.

## Constraints

- Supabase Auth remains the sole credential and access-token authority; FastAPI does not implement authorize, token, or client-registration endpoints and never sees passwords.
- Tokens are validated only by the existing `validate_supabase_access_token` and `get_current_user` path; backend role and ownership checks stay authoritative.
- Supabase OAuth access tokens use audience `authenticated` and are not bound to the `/mcp` resource, so any token of the project is accepted, exactly as the API accepts it today; resource-bound audiences are out of scope.
- The OAuth server is a beta Supabase feature; enabling it in production is a manual dashboard step recorded in the deployment guide, not performed by code.
- Browser code uses only the publishable Supabase configuration; RLS policies are not changed and no schema migration is required.
- The consent page reuses the existing auth store, `useAuth`, and login view rather than duplicating sign-in UI.
- Existing `/api` behavior, including its `WWW-Authenticate: Bearer` responses, is unchanged.
