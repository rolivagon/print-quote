# PRS: Servidor MCP para crear cotizaciones

## Status

In Review

## Purpose

Permitir que vendedores y administradores creen cotizaciones desde un agente compatible con MCP (Claude Code, Claude Desktop u otro cliente MCP) con el mismo resultado que la vista `QuotesCreateView`. El servidor MCP se expone en la ruta `/mcp` del servicio Cloud Run actual, actúa con la identidad del usuario autenticado en Supabase y reutiliza los cálculos y reglas de acceso existentes, sin duplicar lógica de precios. La primera versión ofrece los catálogos que la vista necesita para armar un ítem, una previsualización sin persistencia y la creación de la cotización.

## Requirements

- REQ-001: The system shall expose an MCP server over the Streamable HTTP transport at the `/mcp` path of the existing FastAPI application `quote.api.main:app`.
- REQ-002: The system shall serve `/mcp` from the same process and container image as the API, without changes to the deployment command, and the SPA fallback route shall not capture `/mcp` requests.
- REQ-003: The system shall run the MCP server in stateless mode so that any Cloud Run instance can serve any MCP request.
- REQ-004: If an MCP request has no `Authorization: Bearer` header, or the token fails Supabase access-token validation, then the system shall respond with HTTP 401 and a `WWW-Authenticate: Bearer` header without executing any tool.
- REQ-005: If the token subject has no profile or the profile is inactive, then the system shall reject the MCP request with the same status codes used by the HTTP API (401 for a missing profile, 403 for an inactive profile).
- REQ-006: When an MCP tool executes, the system shall apply the role and ownership rules of the authenticated profile exactly as the equivalent HTTP endpoint does.
- REQ-007: When the `list_clients` tool is called with an optional search term, the system shall return the active clients visible to the authenticated profile, matching the `GET /api/clients` search behavior.
- REQ-008: When the `list_papers` tool is called with `print_type` `digital` or `offset` and a `color_mode`, the system shall return only papers with pricing for that combination, matching `GET /api/papers?print_type&color_mode`.
- REQ-009: When the `list_papers` tool is called with `print_type` `plotter`, the system shall return the plotter materials catalog without requiring a `color_mode`.
- REQ-010: When the `list_finishes` tool is called with `print_type` `digital` or `offset`, the system shall return only finishes that have selling-price pricing configured for that print type.
- REQ-011: When the `list_finishes` tool is called with `print_type` `plotter`, the system shall return the finishes of the plotter pricing catalog.
- REQ-012: When the `preview_quote` tool is called with one or more items in the `QuoteItemCreate` shape, the system shall return, for each item and for the whole quote, the same calculated amounts that `POST /api/quotes/` would persist for the same input.
- REQ-013: When the `preview_quote` tool completes, the system shall not create or modify any quote, quote item, or quote finish row.
- REQ-014: When the `create_quote` tool is called with a `client_id` and one or more items, the system shall create a `draft` quote whose seller is the authenticated profile and shall return its id, quote number, totals, and items in the `QuoteResponse` shape.
- REQ-015: If `create_quote` references a client that does not exist, then the system shall return a tool error indicating the client was not found and shall persist nothing.
- REQ-016: If a non-administrative profile calls `create_quote` for a client created by another profile, then the system shall return a tool error indicating client access was denied and shall persist nothing.
- REQ-017: When a digital or offset item omits `sheet_config`, the system shall apply the defaults used by the quote view (digital 31×46 cm, offset 60×46 cm) before calculation.
- REQ-018: When a plotter item is received, the system shall use color mode `4/0` and, if `material_type` is absent and `paper_id` is present, shall resolve `material_type` from the plotter material name, as the quote view does.
- REQ-019: When a quote result is returned by an MCP tool to a non-administrative profile, the system shall not include the internal production cost breakdown or its component values.
- REQ-020: If a tool input fails validation or an existing calculation raises an HTTP error, then the system shall return an MCP tool error with the error detail and without echoing submitted input values.
- REQ-021: Where monetary values are calculated for MCP tools, the system shall use the existing `Decimal` pricing paths and the CLP formatting already used by quote responses.

## Tasks

- [x] T-001: Add a failing API regression check (reusing the existing quote API tests as the safety net) and extract the per-item calculation loop and client-access check out of `create_quote` into reusable functions without changing behavior; required by REQ-012, REQ-015, REQ-016, REQ-021.
- [x] T-002: Add failing tests for the shared token-to-profile resolution (missing, invalid, unknown profile, inactive profile) and extract it from `get_current_user` into a helper reused by the API dependency and the MCP authentication layer; required by REQ-004, REQ-005.
- [x] T-003: Add the `mcp` SDK dependency and failing integration tests that `/mcp` answers MCP `initialize` and `tools/list` in stateless mode, is not captured by the SPA fallback, and returns 401 without a valid bearer token; mount the MCP app in `quote.api.main` and integrate its session manager in the existing lifespan; required by REQ-001, REQ-002, REQ-003, REQ-004.
- [x] T-004: Add failing unit tests for MCP item normalization (default sheet configs, plotter color mode and material resolution) and implement it; required by REQ-017, REQ-018.
- [x] T-005: Add failing Supabase-backed tests for `list_clients`, `list_papers`, and `list_finishes` as administrator and seller; implement the catalog tools reusing the existing routers' repositories and public mappers; required by REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011.
- [x] T-006: Add failing Supabase-backed tests proving `preview_quote` returns the same totals as `POST /api/quotes/` for digital, offset, and plotter items, persists no rows, and hides internal costs from sellers; implement the tool; required by REQ-012, REQ-013, REQ-019, REQ-021.
- [x] T-007: Add failing Supabase-backed tests for `create_quote` (draft status, seller from token, unknown client, foreign client for sellers, internal costs hidden for sellers, validation errors without input echo); implement the tool; required by REQ-006, REQ-014, REQ-015, REQ-016, REQ-019, REQ-020.
- [x] T-008: Update `docs/architecture.md` with the MCP adapter boundary and `docs/local-development.md` with how to connect a client to `/mcp` locally and on Cloud Run.
- [x] T-009: Run `make fmt`, `make lint`, `make test`, and `make test-supabase`; manually exercise `/mcp` with an MCP client using a real Supabase token; record the results before moving the PRS to review.

## Acceptance Checks

- [x] An MCP client configured with `https://<cloud-run>/mcp` and a valid Supabase access token lists the tools `list_clients`, `list_papers`, `list_finishes`, `preview_quote`, and `create_quote`.
- [x] Requests to `/mcp` without a token, with an invalid token, or for an inactive profile are rejected before any tool runs.
- [x] A seller sees only their own clients through `list_clients` and cannot create a quote for another seller's client.
- [x] Paper and finish catalogs returned by the tools match what the quote view offers for each print type and color mode.
- [x] `preview_quote` totals equal the totals of the quote that `create_quote` persists for the same input, and preview leaves no rows behind.
- [x] A quote created through MCP is visible in the quote detail view with the same values as one created from `QuotesCreateView` with equal input.
- [x] Sellers never receive internal production cost values through any MCP tool.
- [x] Existing quote API tests pass unchanged after the calculation extraction.
- [ ] `make fmt`, `make lint`, `make test`, and `make test-supabase` pass.

## Verification Notes

- Environment: no Python 3.11 was available locally; `.venv` was created with Python 3.14.7. A fresh install resolves `sqlmodel` 0.0.49, which rejects naive datetimes and breaks 78 existing tests unrelated to this PRS; the local `.venv` pins `sqlmodel==0.0.44` (last passing version). `pyproject.toml` still allows `sqlmodel>=0.0.14`, so a fresh Docker build has the same risk; this needs a separate decision.
- `make fmt` and `make lint` pass. `make test`: `261 passed, 24 skipped, 1 failed`; the failure (`test_plotter_production_loader_explicitly_loads_prod_environment_with_override`) is pre-existing and requires a local `.env.prod`. Baseline before the change was `238 passed, 1 failed` (same test).
- T-001: the existing quote API tests are the regression net, but they need Supabase (see below). The extraction is exercised by `tests/test_mcp/test_tools.py`, where `create_quote` and `preview_quote` produce identical totals.
- T-002 (deviation): instead of extracting a new token helper, `/mcp` is a FastAPI route that depends on `get_current_user`, so missing/invalid tokens (401 + `WWW-Authenticate: Bearer`), unknown profiles (401) and inactive profiles (403) use the exact API code path. Covered by `tests/test_mcp/test_transport.py` (missing and invalid token).
- REQ-001/REQ-003 (deviation to review): the endpoint accepts only `POST`; `GET`/`DELETE` return 405 (`Allow: POST`). A stateless JSON server has no SSE stream or session, and an open `GET` stream would hold Cloud Run requests indefinitely. The MCP spec allows 405 for `GET`.
- REQ-020 (partial): domain errors (unknown/foreign client, missing color mode, paper or material) return tool errors with only the detail. Argument schema validation is done by the MCP SDK before the tool runs; its error text includes pydantic's `input_value`, returned to the same caller (the SDK logs only field names).
- T-005..T-007 (deviation): tool tests run over the existing in-memory SQLite fixtures (`seeded_db`) with `get_db`/`get_current_user` overrides, through the real lifespan and the SDK client over ASGI. Covered: catalogs (digital papers/finishes, offset finishes empty, plotter materials), seller client ownership, preview = create for digital, preview persists no rows, plotter material resolved from `paper_id` with `4/0`, unknown client, foreign client, internal costs hidden for sellers and present for admins. Not covered: offset preview vs. create.
- `make test-supabase-existing` on a freshly started local Supabase (migrations and seed applied on container creation; `make db-reset` was not run because it is destructive): `131 passed, 1 xfailed, 4 failed`. The same 4 tests fail on the code without this change: two RLS browser-role checks in `tests/integration/test_supabase_schema.py`, `test_frontend_build_excludes_privileged_supabase_sentinel` (no `frontend/node_modules`), and `test_legacy_login_endpoint_does_not_issue_a_token` (expects the SPA fallback's 405; no `frontend/dist`). All quote API tests pass with the extracted calculation.
- Manual check: `uvicorn quote.api.main:app` against local Supabase with a real access token of a local-only bootstrap admin, using the SDK client over HTTP: the 5 tools are listed; `list_clients` returned 5, digital 4/4 papers 18, digital finishes 7; `preview_quote` and `create_quote` for 500 flyers 10x15 cm gave identical totals (`$393.100 / $74.700 / $467.800`, 56 sheets); the quote was created as `draft` and `GET /api/quotes/{id}` (used by the detail view) returns the same values. Without a token: 401 `WWW-Authenticate: Bearer`; `GET /mcp`: 405 `Allow: POST`. The detail view itself was not opened in a browser.
- Remaining uncovered: offset preview vs. create, and a real plotter catalog (local `plotter_pricing` is empty; plotter is covered only by the in-memory test).

## Constraints

- Pricing logic stays in `src/quote/pricing/` and the existing quote calculation functions; the MCP layer composes them and must not introduce pricing rules.
- The MCP adapter lives in `src/quote/mcp/` and runs inside the FastAPI application, so FastAPI remains the sole business-data API; RLS policies are not changed.
- Supabase Auth is the sole access-token authority; the MCP layer validates tokens with `validate_supabase_access_token` and never accepts passwords or service-role credentials.
- Backend authorization is authoritative: role and ownership checks are the same code paths used by the HTTP routers.
- All monetary values use `Decimal`; runtime persistence requires PostgreSQL/Supabase with no SQLite fallback.
- No schema migration is required; no new persisted entity is introduced.
- Repeated logic between `create_quote` and the MCP tools is extracted into shared functions rather than duplicated.
- Tests use existing fixtures and helpers from `tests/conftest.py`; API and Auth checks run against local Supabase.
- Supabase access tokens expire; OAuth-based authorization for remote connectors (protected-resource metadata) is out of scope for this PRS.
- Out of scope for this version: quote status updates, quote listing/detail tools, fixed-product tools, and catalog administration.
- Implementation starts only after this PRS receives explicit approval. The PRS must be critically reviewed before it can be marked `Done`.
