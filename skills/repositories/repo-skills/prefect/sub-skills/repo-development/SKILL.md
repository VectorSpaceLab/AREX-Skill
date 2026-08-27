---
name: repo-development
description: "Maintain Prefect itself safely: repo layout, scoped AGENTS rules,
  focused validation, generated artifacts, and package-boundary caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Prefect Repo Development

Use this sub-skill when the task is to change the Prefect repository itself rather than author user flows, operate deployments, call the API, or run the CLI as an end user.

## Route Here For

- Choosing source and test files for changes under `src/prefect/`, `tests/`, `docs/`, `client/`, `src/integrations/`, or `ui-v2/`.
- Applying scoped `AGENTS.md` rules, including the source/test mirror, client/server boundaries, docs generation rules, integration boundaries, and UI-v2 workflow.
- Selecting focused pytest, ruff, pre-commit, docs, generated-schema, or `prefect-client` validation commands before broader checks.
- Maintaining generated files such as settings types, schemas, CLI docs, OpenAPI docs, API references, examples, and integration docs.
- Creating issue repro scripts under `repros/` and avoiding maintainer anti-patterns such as bypassing server orchestration state transitions.

## Route Elsewhere

- Use `flow-task-authoring` for user-facing `@flow`, `@task`, states, futures, task runners, caching, and result behavior.
- Use `deployments-workers` for deployments, `prefect.yaml`, serve, workers, work pools, and run submission as a user workflow.
- Use `cli-server-operations` for operating the Prefect CLI, profiles, server startup/status, variables, artifacts, and diagnostics.
- Use `api-client-settings` for Python client usage, settings/profile APIs, schemas as a user, and the `prefect-client` package distinction.
- Use `events-blocks-assets` for events, automations, blocks, assets, variables, and concurrency primitives as user-facing features.

## Working Pattern

1. Read the nearest scoped `AGENTS.md` before editing; deeper files override broader files.
2. Map changed source paths to mirrored tests and component-specific invariants before writing code.
3. Keep behavior changes minimal, preserve public APIs unless explicitly approved, and update docs or generated artifacts when source-of-truth files change.
4. Run the most focused safe validation first, then broaden only when the change affects shared behavior, schemas, docs, client packaging, or CI selection.
5. Keep service-heavy, Docker, Postgres, integration, UI browser, and release/publish commands opt-in unless the task explicitly requires them.

## References

- Start with [repo-layout](references/repo-layout.md) for source/test mapping, scoped instructions, package boundaries, and maintainer caveats.
- Use [testing-and-validation](references/testing-and-validation.md) to choose focused pytest, lint, pre-commit, CI matrix, and repro-script checks.
- Use [generated-artifacts](references/generated-artifacts.md) when schemas, settings, docs, API references, examples, UI service types, or `prefect-client` metadata may be stale.
- Use [troubleshooting](references/troubleshooting.md) for missing tools, dependency drift, AGENTS conflicts, async test context failures, service requirements, and state-transition anti-patterns.

## Bundled Helper

Run `python scripts/select_prefect_tests.py --help` from this sub-skill directory to inspect a safe test-selection helper. It accepts changed paths and prints suggested validation commands without running tests, starting services, reading git history, or mutating files.
