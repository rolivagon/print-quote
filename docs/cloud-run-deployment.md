# Cloud Run Deployment

This guide deploys the FastAPI application and built Vue SPA as the public `print-quote` Cloud Run service in GCP project `rodxdev-prod`. Cloud Build is invoked manually; a source-control trigger is intentionally not configured.

## Architecture

- Cloud Run runs one container that serves the Vue SPA and FastAPI API from the same service URL.
- The frontend calls the relative `/api` path in production, so no cross-origin configuration is required for normal browser use.
- Supabase continues to provide PostgreSQL and Auth. The backend connects through its PostgreSQL pooler using `DATABASE_URL`.
- Cloud Run obtains runtime configuration from Secret Manager. The container image never contains a database URL or Supabase service-role key.

## Prerequisites

- Access to `rolivagon@gmail.com` with permissions to administer `rodxdev-prod` and its billing account.
- A Supabase production project with its migrations applied and production email-confirmation contract configured.
- The Supabase PostgreSQL pooler connection URL, Supabase project URL, service-role key, publishable key, and project URL. Do not place sensitive values in shell history, source files, Cloud Build substitutions, or logs.
- Google Cloud CLI installed locally.

Authenticate and select the project before any bootstrap command:

```sh
gcloud auth login rolivagon@gmail.com
gcloud config set project rodxdev-prod
```

## One-Time Bootstrap

Enable required APIs and create the Artifact Registry repository:

```sh
gcloud services enable artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com secretmanager.googleapis.com
gcloud artifacts repositories create print-quote --repository-format=docker --location=us-central1
```

Create the dedicated deployment and runtime identities:

```sh
gcloud iam service-accounts create print-quote-deployer --display-name="Print Quote Cloud Build deployer"
gcloud iam service-accounts create print-quote-runtime --display-name="Print Quote Cloud Run runtime"
```

Grant the deployment identity the minimum roles it needs. The operator who submits builds must also be allowed to act as `print-quote-deployer`.

```sh
PROJECT_ID=rodxdev-prod
DEPLOYER=print-quote-deployer@$PROJECT_ID.iam.gserviceaccount.com
RUNTIME=print-quote-runtime@$PROJECT_ID.iam.gserviceaccount.com

gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$DEPLOYER" --role=roles/artifactregistry.writer
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$DEPLOYER" --role=roles/cloudbuild.builds.builder
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$DEPLOYER" --role=roles/run.admin
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$DEPLOYER" --role=roles/logging.logWriter
gcloud iam service-accounts add-iam-policy-binding "$RUNTIME" --member="serviceAccount:$DEPLOYER" --role=roles/iam.serviceAccountUser
gcloud iam service-accounts add-iam-policy-binding "$DEPLOYER" --member="user:rolivagon@gmail.com" --role=roles/iam.serviceAccountUser
```

## Secret Manager

Create exactly these runtime secrets:

```sh
gcloud secrets create print-quote-database-url --replication-policy=automatic
gcloud secrets create print-quote-supabase-url --replication-policy=automatic
gcloud secrets create print-quote-supabase-service-role-key --replication-policy=automatic
```

Add each value only from a secure terminal input or password manager integration. Never commit a secret value or paste it into Cloud Build logs. Grant the runtime identity access only to these secret resources:

```sh
for secret in print-quote-database-url print-quote-supabase-url print-quote-supabase-service-role-key; do
  gcloud secrets add-iam-policy-binding "$secret" --member="serviceAccount:$RUNTIME" --role=roles/secretmanager.secretAccessor
done
```

To add or rotate a secret version, stream one value through standard input. The command does not echo the value:

```sh
gcloud secrets versions add SECRET_NAME --data-file=-
```

Run it once for each secret and enter its value followed by end-of-file. The `DATABASE_URL` value must be the Supabase PostgreSQL pooler URL.

`SUPABASE_URL` is stored alongside the runtime credentials so Cloud Run resolves all backend Supabase configuration consistently. The frontend uses its own build-time `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`; both are public browser configuration, never service credentials.

## Manual Deployment

Run local checks first:

```sh
make fmt
make lint
make test
cd frontend && npm ci && npm run lint && npm run build
```

Submit the build with the Supabase URL and publishable key appropriate for the production browser client. These are public values, but avoid placing unrelated configuration in the build command.

```sh
gcloud builds submit \
  --project=rodxdev-prod \
  --config=cloudbuild.yaml \
  --service-account=projects/rodxdev-prod/serviceAccounts/print-quote-deployer@rodxdev-prod.iam.gserviceaccount.com \
  --substitutions=_VITE_SUPABASE_URL=SUPABASE_PROJECT_URL,_VITE_SUPABASE_PUBLISHABLE_KEY=SUPABASE_PUBLISHABLE_KEY
```

Cloud Build publishes the image to `us-central1-docker.pkg.dev/rodxdev-prod/print-quote/print-quote` and prints the Cloud Run URL, ready revision, and image identity. The service is public because application access control is enforced by Supabase Auth and the FastAPI API.

## Verify

Get the service URL and verify the SPA and readiness response. Cloud Run accepts traffic only after application startup has successfully connected to PostgreSQL:

```sh
SERVICE_URL=$(gcloud run services describe print-quote --project=rodxdev-prod --region=us-central1 --format='value(status.url)')
curl --fail --silent --show-error "$SERVICE_URL/"
curl --fail --silent --show-error "$SERVICE_URL/health"
```

Then manually verify sign-in, an authenticated `/api` request, role restrictions, and a quote workflow. Review Cloud Run logs and Supabase Auth logs without exposing credentials.

## Rollback

List revisions and route all traffic to the last known-good revision:

```sh
gcloud run revisions list --service=print-quote --project=rodxdev-prod --region=us-central1
gcloud run services update-traffic print-quote --project=rodxdev-prod --region=us-central1 --to-revisions=KNOWN_GOOD_REVISION=100
```

Verify `/` and `/health` again after traffic is updated. Rollback changes the running revision only; it does not modify Secret Manager versions or Supabase schema.
