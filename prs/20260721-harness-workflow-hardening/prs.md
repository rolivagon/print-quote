# PRS: Harness Workflow Hardening

## Status

Done

## Purpose

Make the reusable harness prevent unsafe operational commands, require explicit PRS approval, preserve agreement changes that an approved PRS requires, and provide a read-only release-readiness review.

## Requirements

- REQ-001: When the PRS implementer receives a PRS whose status is not `Approved`, the agent shall refuse implementation without changing the PRS status.
- REQ-002: When an approved PRS explicitly requires changes to one or more project agreement documents, the PRS implementer shall allow only those documented changes and shall not alter an agreement to justify unapproved behavior.
- REQ-003: When the PRS reviewer performs verification, the agent shall not invoke a command that formats, lints with automatic fixes, installs dependencies, deploys, or otherwise edits the workspace.
- REQ-004: When a harness agent performs operational work, the agent shall avoid commands that print secret values and shall use project-provided operational targets that keep credentials out of tool output.
- REQ-005: When the release verifier evaluates a change, the agent shall report blocking findings for a missing Git commit, an unapproved or incomplete PRS, unverified applicable checks, or secret exposure risks without deploying or changing files.
- REQ-006: When a user invokes the release-verification command, the harness shall delegate the review to the read-only release verifier.

## Tasks

- [x] T-001: Add the `safe-operations` skill with observable rules for secret-safe operational commands (`REQ-004`).
- [x] T-002: Update the PRS workflow and implementer instructions to require explicit approval and conditionally permit agreement updates (`REQ-001`, `REQ-002`).
- [x] T-003: Restrict the PRS reviewer to non-mutating verification and require it to report unavailable checks (`REQ-003`).
- [x] T-004: Add the read-only release verifier and its command (`REQ-005`, `REQ-006`).
- [x] T-005: Inspect all harness frontmatter and command references for valid names, matching files, and non-mutating permissions (`REQ-001`–`REQ-006`).

## Acceptance Checks

- [x] The implementer instruction refuses any status other than `Approved` and cannot advance a PRS to `Done`.
- [x] The implementer instruction permits agreement-document changes only when named by an approved PRS requirement.
- [x] The reviewer permission list does not allow `make lint*`, `npm run lint*`, or `npm run format*`.
- [x] The safe-operations skill prohibits environment and shell-tracing commands that expose secrets.
- [x] The release verifier is read-only, has no deployment permission, and identifies required release blockers.
- [x] The `verify-release` command refers to the release verifier.

## Constraints

- This change is limited to reusable files under `harness/` and its PRS record; it does not install or synchronize the harness into `.opencode/`.
- Do not place secrets, environment values, service-role credentials, passwords, or connection strings in the harness or PRS.
- Preserve the project PRS status model and test-first workflow.
- Agent and skill frontmatter must use valid OpenCode configuration fields.

## Verification Record

- `git diff --check` completed without whitespace errors. Because the repository has no commit and every file is untracked, this check cannot provide a conventional tracked-file diff.
- Inspected all updated harness files: agent permissions deny edits for reviewers and the release verifier; neither grants automatic linting, formatting, deployment, environment dumping, or database reset.
- Confirmed `harness/commands/verify-release.md` references `release-verifier`, and both `prs-workflow` and `safe-operations` skills exist with matching names.
- Independent PRS review found that test, build, and lint permissions could write ignored artifacts and that incomplete PRS checks were not explicitly blocking. Removed those permissions and made incomplete tasks, acceptance checks, and verification evidence release blockers.
- Follow-up independent review confirmed both findings are resolved and reported no new findings.
