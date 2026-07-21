---
name: safe-operations
description: Use when running Supabase, Cloud Run, deployment, environment, credential, or diagnostic commands to prevent secrets from appearing in tool output.
---

# Safe Operations

## Secret-safe execution

- Treat every command's stdout, stderr, agent transcript, exported session, logs, and pasted output as potentially persistent and visible.
- Never run `supabase status -o env`, `env`, `printenv`, `set`, `export -p`, commands that print `.env*` files, or shell tracing such as `set -x` when secrets may be present.
- Never display, copy, serialize, or inspect secret values from `DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, bootstrap-password variables, access tokens, JWT secrets, cloud credentials, or S3 credentials.
- Use documented Makefile targets for project operations and Cloud Run diagnostics when they exist. A target may load a secret internally, but its output must not print the secret.
- Do not source an environment file into a command whose output, arguments, or tracing can reveal values. Do not use a shell command to diagnose a missing value by printing its contents.

## Operational boundaries

- Before database reset, migration, bootstrap, deployment, or production data loading, identify the target environment and the exact documented target to use.
- Do not deploy or mutate an environment as part of diagnosis or review. Report the required operator action instead.
- If an operation needs a credential that is not already provided safely by the environment or an existing target, stop and state the missing variable name without requesting or printing its value.
- If a transcript may already contain a secret, stop using that value, identify the credential by name only, and recommend rotation or revocation.

## Verification output

- Report command names, exit statuses, test counts, non-sensitive resource identifiers, and redacted configuration keys only.
- Never claim a deployment, migration, or security check passed without command output or a documented non-sensitive record.
