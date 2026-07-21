---
name: prs-workflow
description: Use when creating, implementing, or critically reviewing a PRS in prs/ to apply the project's PRS structure, EARS requirements, statuses, and verification workflow.
---

# PRS Workflow

## Source of truth

For a new PRS, read these documents before drafting anything:

- `docs/architecture.md`
- `docs/decisions.md`
- `docs/local-development.md`
- `docs/learning.md`

The PRS must align with them. Do not invent product behavior when the request or these agreements do not establish it; identify the gap and ask a concise question.

## Location and name

Create exactly one file at:

```text
prs/{YYYYMMDD}-{description}/prs.md
```

- Use the local calendar date for `YYYYMMDD`.
- Use a lowercase ASCII kebab-case slug for `{description}`.
- Do not overwrite an existing `prs.md`; report the existing path instead.

## Required format

```markdown
# PRS: <Title>

## Status

Draft

## Purpose

<The user, business value, and expected outcome.>

## Requirements

- REQ-001: When <trigger>, the system shall <observable behavior>.

## Tasks

- [ ] T-001: Add a failing <layer> test proving REQ-001.
- [ ] T-002: Implement the smallest change that satisfies REQ-001.
- [ ] T-003: Run the specified verification.

## Acceptance Checks

- [ ] <Observable validation of the requirement.>

## Constraints

- <Relevant agreement from the four source documents.>
```

## EARS requirements

Every requirement is atomic, uniquely identified, testable, and uses one of these patterns:

- Ubiquitous: `The system shall <behavior>.`
- Event-driven: `When <trigger>, the system shall <behavior>.`
- State-driven: `While <state>, the system shall <behavior>.`
- Optional feature: `Where <feature applies>, the system shall <behavior>.`
- Unwanted behavior: `If <condition>, then the system shall <response>.`

Do not use vague verbs such as "support", "handle", "properly", or "as needed" without observable behavior.

## Status transitions

- `Draft`: authored and awaiting approval.
- `Approved`: authorized for implementation.
- `In Progress`: implementation has started.
- `In Review`: implementation and verification are ready for critical review.
- `Done`: review findings are resolved and required verification passes.

Only implement an `Approved` PRS. Approval must be explicit from the user or recorded project authority; continuing a conversation, starting a task, or a previous implementation attempt is not approval.

Only an implementer may move an approved PRS to `In Progress` or `In Review`. A reviewer does not modify the PRS; it reports findings for the implementer to resolve. Move a PRS to `Done` only after review findings are resolved and every required verification result is recorded. An implementer must not set `Done`.

## Implementation and review

- Start each requirement with its first failing test.
- Keep tasks ordered by dependency and map each task to one or more requirement IDs.
- Run the relevant checks documented in `docs/local-development.md`.
- Review the resulting diff against the PRS and all four agreements. Report bugs, regressions, agreement violations, missing EARS behavior, and missing tests before any summary.
- When an approved requirement explicitly requires an agreement-document update, treat that update as implementation scope. Do not modify an agreement merely to rationalize unapproved behavior.
