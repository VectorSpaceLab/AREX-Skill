---
name: repo-development
description: "Use when a coding agent edits the Dagster OSS repository itself:
  package lookup, Python/UI/docs validation, coding conventions, mandatory ruff,
  safe test selection, CLI entry point reinstall notes, and git or stack
  constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Repo Development

Use this sub-skill when changing the Dagster OSS monorepo rather than using Dagster as an application framework. It routes future agents to the repo-specific development workflow, package map, validation commands, style rules, and safety constraints needed for edits in this checkout.

## Route First

- Use this sub-skill for locating Dagster packages, choosing validation commands after repo edits, applying Python style conventions, docs checks, UI checks, or repository contribution workflow rules.
- Route public `dagster` CLI usage and user-project local development to `../cli-local-development/SKILL.md` if that sub-skill exists.
- Route GraphQL API and webserver runtime behavior to `../graphql-and-webserver/SKILL.md` if that sub-skill exists.
- Route deployment operations, production instances, and daemon/run-launcher behavior to `../deployment-operations/SKILL.md` if that sub-skill exists.
- Do not use this sub-skill for broad integration-library internals, Dagster Cloud, release automation, Buildkite deep internals, or UI implementation details beyond validation workflow routing.

## Start Here

1. Identify changed paths and package ownership before editing; package paths and validation commands differ across core Python, libraries, webserver, GraphQL, Pipes, docs, and UI workspaces.
2. After every Python file edit, run `make ruff` from the repository root before considering the task complete.
3. Use `uv` for Python package management; if command-line entry points change in a `setup.py` or package metadata, reinstall the affected package with `uv pip install -e .` from that package root.
4. For UI or GraphQL schema changes, run UI checks from `js_modules/`; schema changes require `make generate-graphql` before `yarn tsgo` or `yarn lint`.
5. Prefer focused tests that match changed files before broad suites; avoid credentialed, networked, Docker-heavy, or expensive tests unless the user explicitly asks.
6. Never push directly with `git push`; ask first. When stack metadata matters, inspect with `gt log` before manual git inference.

## References

- [Repo development workflows](references/workflows.md) for package locations, command selection, Python/UI/docs validation, style conventions, test strategy, and git constraints.
- [Troubleshooting](references/troubleshooting.md) for install/import failures, optional dependency gaps, CLI/API misuse while developing the repo, UI/docs validation failures, and workflow-specific recovery steps.
- [Validation command selector](scripts/select_validation_commands.py) for a safe helper that suggests commands from changed paths without executing them.

## Safety Notes

- Treat `make ruff` as mandatory after Python edits even if the changed file is small or generated.
- Do not search Python code under `.tox` directories; they are temporary environments and can mislead package ownership or dependency conclusions.
- Search package dependencies in `setup.py` files as the source of truth for this repo.
- Do not run broad native examples, Docker-backed tests, or external-service integrations as routine validation without confirming scope and cost with the user.
