---
name: maintenance
description: "Run Honcho repo tests, type checks, release hygiene checks, and
  maintenance scripts."
metadata:
  disco-role: operating
disable-model-invocation: true
license: AGPL 3.0
---

# Maintenance

Use this sub-skill when the task is about repo-level development, testing,
static checks, release hygiene, or maintenance scripts.

## What this route covers

- Python test execution and test selection.
- Type checking and formatting commands.
- TypeScript SDK validation and monorepo test routing.
- Repo-maintained helper scripts.
- Versioning and release-alignment workflows.
- Safety checks around auth, sessions, and runtime invariants.

## What it does not cover

- Local API deployment or worker startup.
- SDK usage from an application.
- CLI operator workflows.

Use `sub-skills/self-hosting/` for runtime setup, `sub-skills/integrations/` for
SDK and REST usage, and `sub-skills/cli-operations/` for terminal inspection.

## Read first

- `../../references/development-and-testing.md`
- `../../references/troubleshooting.md`
- `references/testing-and-release.md`
- `references/troubleshooting.md`
- `scripts/native_test_selector.py`

## Typical questions this route should answer

- What test command should I run for this change?
- How do I validate the Python or TypeScript SDK?
- How do I run static checks before a release?
- Which repo scripts matter for maintenance?
- What safety rules should I keep in mind when touching auth or DB code?

## Practical workflow

1. Identify the affected surface: API, SDK, CLI, tests, or release metadata.
2. Choose the smallest safe validation command that covers the change.
3. Escalate to broader test or type-check commands only when needed.
4. Keep the Python and TypeScript package versions aligned when a release is
   involved.
5. Use the bundled selector script to enumerate the likely checks when unsure.

## Decision points

- Use `uv run pytest tests/` for broad Python coverage.
- Use a targeted `pytest` path when only one area changed.
- Use `uv run pytest tests/ -k typescript` for TypeScript SDK tests.
- Use `cd sdks/typescript && bun run tsc --noEmit` for direct TS type checking.
- Use `uv run ruff check src/` and `uv run basedpyright` for static quality.

## Troubleshooting focus

This route owns problems such as:

- test selection is too broad or too narrow,
- a script behaves differently than the docs imply,
- release versions drift between API and SDK packages,
- static checks fail after an API or schema change,
- auth or session policy changes break a route policy test,
- test runs depend on unavailable live-provider credentials.

## Helpful bundled script

`scripts/native_test_selector.py` prints a maintenance-friendly test matrix and
safe command suggestions. Use it when you need a quick map of which checks are
worth running.

## Good handoff phrases

- "Which tests should I run for this change?"
- "How do I verify the TypeScript SDK?"
- "How do I check the release surface?"
- "Which script should I use for this maintenance task?"
- "What static checks matter here?"
