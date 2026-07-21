# PRS: Manual Cloud Run deployment

**Status:** Done

## Purpose

Provide a repeatable, manually triggered Cloud Build deployment that builds the FastAPI application and its production Vue SPA into one public Cloud Run service in GCP project `rodxdev-prod`. Runtime secrets must be supplied by Secret Manager without committing their values, and the deployment process must be documented under `docs/`.

## Requirements

### Docker image build

1. **When** Cloud Build is manually started for the deployment, **the system shall** build one container image that contains the FastAPI application and the production-built Vue SPA.
2. **When** the deployed container receives a request for a production SPA route, **the system shall** serve the built SPA through the FastAPI application.
3. **When** the deployed container starts, **the system shall** use a PostgreSQL-compatible `DATABASE_URL` supplied at runtime.

### Secret handling

4. **When** the Cloud Run revision is created, **the system shall** obtain `DATABASE_URL` from a Secret Manager secret reference rather than from a value committed in deployment configuration, documentation, or the container image.
5. **Where** additional sensitive runtime settings are required for the application to operate, **the system shall** obtain each setting from a Secret Manager secret reference rather than a committed plaintext value.

### Manual Cloud Build deployment

6. **When** an authorized operator manually runs the documented Cloud Build deployment, **the system shall** deploy the image as one Cloud Run service in GCP project `rodxdev-prod`.
7. **When** that Cloud Run service is deployed, **the system shall** allow unauthenticated HTTP requests to its service URL.
8. **When** the Cloud Build deployment completes successfully, **the system shall** report the deployed Cloud Run service URL and image identity to the operator.

### Documentation and verification

9. **When** an operator follows the deployment documentation under `docs/`, **the documentation shall** identify the prerequisites, required non-secret configuration, Secret Manager secret-reference setup, manual Cloud Build invocation, and rollback procedure without containing secret values.
10. **When** the deployment verification is performed against the deployed service URL, **the system shall** return a successful response for the application entry route and a successful response for an API health or equivalent application-readiness endpoint.
11. **When** deployment configuration or documentation is reviewed, **the system shall not** contain plaintext secret values, service-role credentials, passwords, or database connection strings.

## TDD-first tasks

1. Add failing deployment-configuration tests that assert the image build includes the production SPA, the Cloud Run deployment targets `rodxdev-prod`, and unauthenticated access is configured.
2. Add failing static checks that assert sensitive runtime variables use Secret Manager references and reject plaintext secret values in deployment configuration and deployment documentation.
3. Implement the container build definition and manually invocable Cloud Build configuration until the deployment-configuration tests pass.
4. Implement the Secret Manager environment-variable references without adding secret values to version control; make the secret-handling checks pass.
5. Add the operator documentation under `docs/`, including invocation, prerequisites, secret-reference setup, verification, and rollback; make the documentation checks pass.
6. Run the built image locally or in the build environment and add/execute a failing-then-passing smoke check for the SPA entry route and readiness endpoint.
7. Run required formatting and linting before the final relevant test pass; review the resulting diff for accidental sensitive values.
8. Manually run Cloud Build in `rodxdev-prod`, perform the deployed-service acceptance checks, and record only non-sensitive identifiers and results in the implementation evidence.

## Acceptance checks

- A manual Cloud Build invocation builds and publishes the deployable image, then deploys exactly one public Cloud Run service in `rodxdev-prod`.
- The deployed service serves the built Vue SPA and FastAPI API from the same public service URL; production frontend API requests resolve through `/api`.
- The Cloud Run revision obtains `DATABASE_URL` and all other required sensitive runtime settings via Secret Manager references, with no values committed to the repository or included in the image.
- Documentation resides under `docs/` and enables an authorized operator to prepare secrets, invoke deployment, verify the service, and roll back without exposing secret material.
- Against the deployed public service URL, the application entry route and an API health/readiness endpoint return successful responses.
- Relevant deployment-configuration checks, backend formatting/linting/tests, and frontend lint/format/type-checked production build pass before the PRS is moved forward.

## Constraints

- This change is deployment and documentation scoped; it must not alter pricing, domain behavior, persistence schema, or browser business-data access boundaries.
- The application remains a FastAPI backend and Vue 3 SPA, with production SPA assets built before FastAPI serves the SPA fallback.
- PostgreSQL/Supabase remains required at runtime; SQLite is not a production fallback, and public-schema changes remain governed solely by checked-in Supabase migrations.
- Supabase Auth remains the credential and browser-session authority. Browser code may receive only publishable Supabase configuration; service-role credentials and all secret values must remain unavailable to browser code, commits, logs, and documentation.
- Use the repository's Python 3.11 `.venv`, frontend committed lockfile, existing fixtures/helpers, and Makefile targets for project operations and Cloud Run diagnostics when available.
- Implementation must follow TDD: introduce a failing test or check first, make it pass, then refactor without changing behavior. Keep changes minimal and avoid duplicate logic.
- Implementation remains limited to deployment artifacts, operational documentation, and the minimum runtime readiness behavior required for Cloud Run verification.

## Implementation Evidence

- `make fmt`, `make lint`, and `make test` passed: 208 passed, 17 skipped.
- `npm run lint` and `npm run build` passed; the existing frontend CSS and bundle-size warnings remain.
- `RUN_CONTAINER_SMOKE=1 .venv/bin/pytest tests/test_container_smoke.py -q` passed, building the production image and verifying PostgreSQL startup, `/`, `/quotes`, and `/health`.
- Cloud Build `9335c9e0-5551-47cc-9d80-a4c429564188` deployed image `us-central1-docker.pkg.dev/rodxdev-prod/print-quote/print-quote:9335c9e0-5551-47cc-9d80-a4c429564188` as revision `print-quote-00001-jmd`.
- The public service URL `https://print-quote-zzaehk46xa-uc.a.run.app` returned HTTP 200 for `/`, `/quotes`, and `/health`. The deployed revision references the three Secret Manager secrets and runs as `print-quote-runtime@rodxdev-prod.iam.gserviceaccount.com`.
