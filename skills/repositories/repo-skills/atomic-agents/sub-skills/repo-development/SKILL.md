---
name: repo-development
description: "Work safely inside the Atomic Agents monorepo: tests, docs,
  packaging, CI, and release-adjacent maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Repo Development

Use this subskill when the task is to modify this checkout, run focused tests, update docs, inspect packaging, or reason about maintainer workflow and release behavior.

## Read first

- `references/development.md` for the monorepo layout, commands, and maintenance conventions.
- `references/docs-generation.md` for maintainer-only docs and `llms.txt` bundle generation context.
- `references/troubleshooting.md` for local dev, packaging, docs, and release failures.
- `scripts/check_repo_layout.py` for a safe local layout / version smoke check.

## Owns

- The monorepo's package and workspace layout.
- Safe local development commands and focused verification choices.
- Docs, lint, type, and test guidance for the checkout itself.
- Release-adjacent awareness when a task needs to understand the maintainer path.

## Does not own

- End-user agent-building recipes; use `../agent-core/SKILL.md`.
- Tool / CLI / Forge workflows; use `../tooling-and-forge/SKILL.md`.
- MCP connectors; use `../mcp-integrations/SKILL.md`.
- Example adaptation; use `../example-workflows/SKILL.md`.

## Common triggers

- "How do I run the tests for this repo?"
- "Where is the package boundary or workspace layout?"
- "How do I format or lint a change?"
- "How do I inspect the docs or release setup?"
- "What should I check before editing this monorepo?"
