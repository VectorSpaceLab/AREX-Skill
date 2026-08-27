# Repo Layout and Maintainer Boundaries

This reference is for agents changing Prefect itself. It distills repository evidence into maintainable routing and boundary rules; it is not user-facing Prefect runtime guidance.

## Repository Shape

| Area | Purpose | Usual validation owner |
| --- | --- | --- |
| `src/prefect/` | Core SDK, CLI, server, client, deployments, workers, events, settings, blocks, assets, utilities | Mirrored `tests/` paths plus component-specific tests |
| `tests/` | Python test suite mirroring `src/prefect/`; SQLite and PostgreSQL are both represented in CI | `uv run pytest ...` with focused paths |
| `client/` | Build configuration for the separate `prefect-client` package; source is copied from `src/prefect/` | `bash client/build_client.sh`, client smoke tests, dependency sync review |
| `docs/` | Mintlify docs, generated API/CLI/OpenAPI/example pages, contributor docs | `just docs`, `just links`, `just lint`, generation scripts as needed |
| `examples/` | Example flows that feed generated docs pages | `just generate-examples`, targeted example checks |
| `schemas/` | JSON schemas such as `prefect.yaml` and settings schema outputs | schema generation scripts and schema-focused tests |
| `scripts/` | Generation, release, CI utility, service, and verification helpers | Treat as source evidence; run only safe targeted scripts |
| `src/integrations/` | Separate PyPI packages such as `prefect-aws`, each with its own metadata, tests, and release tags | integration-local tests and docs generation from inside that package |
| `ui-v2/` | React/TypeScript UI migration replacing legacy Vue with minimal functional/visual change | UI-v2 npm checks; route deep UI coding to a UI-specific skill |
| `integration-tests/` | End-to-end tests requiring running services | Skip unless explicitly requested and services are available |
| `compat-tests/`, `load_testing/`, `benches/` | Compatibility, load, and benchmark suites | Opt-in only; usually too broad for routine code changes |

## Scoped Instruction Rules

- Always read the nearest `AGENTS.md` for every touched path. Root instructions apply repository-wide; deeper instructions under `src/prefect/`, `tests/`, `docs/`, `ui-v2/`, `src/integrations/`, `client/`, and component subdirectories override or refine them.
- `AGENTS.md` files are intentionally symlinked to `CLAUDE.md`; do not remove or desynchronize them.
- Keep source changes aligned with tests and docs in the same conceptual area. Do not use an adjacent component's instructions as permission to change unrelated behavior.
- Use single backticks in Python docstrings for inline code references; a local pre-commit hook rejects double backticks in Python files.

## Source/Test Mirror

Use the changed path to choose the first test target:

| Changed path | First tests to inspect or run |
| --- | --- |
| `src/prefect/flows.py`, `tasks.py`, engines, states, results, futures, task runners | `tests/test_flows.py`, `tests/test_tasks.py`, `tests/test_flow_engine.py`, `tests/test_task_engine.py`, `tests/engine/` |
| `src/prefect/client/` | `tests/client/`, client schema tests, affected top-level tests using clients |
| `src/prefect/server/api/` | `tests/server/api/` plus related model/orchestration tests |
| `src/prefect/server/database/` or migrations | `tests/server/database/` and both SQLite/PostgreSQL consideration |
| `src/prefect/server/models/` | `tests/server/models/` and API/orchestration tests for the resource |
| `src/prefect/server/orchestration/` | `tests/server/orchestration/` and state-transition policy tests |
| `src/prefect/cli/` | `tests/cli/`, especially matching command group files |
| `src/prefect/settings/` | `tests/test_settings.py`, settings schema/type generation checks |
| `src/prefect/events/` | `tests/events/`, `tests/events/client/`, and server-side event tests only when backend behavior changes |
| `src/prefect/deployments/`, `runner/`, `workers/` | `tests/deployment/`, `tests/runner/`, `tests/workers/`, deployment CLI tests |
| `src/prefect/blocks/`, `assets/`, `concurrency/` | `tests/blocks/`, `tests/assets/`, `tests/concurrency/` and related CLI tests |
| `src/prefect/utilities/schema_tools/` | `tests/utilities/schema_tools/` and schema hydration users |
| `docs/` | docs lint/link checks, generated-docs source validation, markdown-docs tests when examples change |
| `examples/` | generated examples docs and any matching example tests |
| `src/integrations/prefect-*/` | integration-local `tests/`; use integration package instructions |
| `ui-v2/` | UI-v2 npm tests/lint/build; route deep implementation to UI-specific guidance |

If no obvious mirror exists, search with `rg` for the symbol, route, CLI command, model, fixture, or setting name before choosing tests.

## Core Maintainer Invariants

- The server is the source of truth for flow state transitions. Flow state changes must go through the orchestration API or orchestration layer, including in tests. `force=True` still routes through `MinimalFlowPolicy`; it is not a full bypass.
- Task state transitions differ from flow transitions: task engines manage local `set_state` and emit `prefect.task_run.*` events. Do not assume task and flow state paths are interchangeable.
- Keep sync and async engine behavior aligned when changing `flow_engine.py`, `task_engine.py`, clients, or orchestration helpers.
- Persist run metadata that event subscribers need before calling `set_state()` for the transition that emits the event.
- Prefer real Prefect operations in tests. Mock external services and time-sensitive edges, not the core flow/deployment/server lifecycle being tested.
- Public APIs are anything without a leading underscore unless a more specific component instruction says otherwise. Avoid public API changes unless the task explicitly requires them.
- Use `get_logger()` or run-context loggers from `prefect.logging` for library logging; raw `logging.getLogger()` is reserved for logging internals or circular-import cases.

## Client Package Boundary

`prefect` and `prefect-client` are separate distributions. The `client/` directory packages a subset copied from `src/prefect/`, then strips server-only, CLI, deployment recipe/template, and testing code.

- If a dependency in root `pyproject.toml` affects client-side code, mirror it in `client/pyproject.toml`.
- Do not import `prefect.server.database`, `prefect.server.models`, or other server-only modules from `src/prefect/client/` or code that must survive the `prefect-client` build.
- All client methods live on orchestration submodules; both sync and async variants are expected.
- Client schemas are separate from server schemas. Keep shared protocol contracts deliberately mirrored rather than importing server-only schema packages.
- Reproduce local client package failures with `bash client/build_client.sh` only when the task touches client packaging or shared client imports.

## Server, CLI, Integration, and UI Boundaries

- Server endpoint work follows schema -> model -> route layering. Server/client schemas remain separate. Database queries and migrations must consider both SQLite and PostgreSQL.
- CLI commands are powered by Cyclopts. Use `rich` output, `exit_with_error` for error exits, and suppress human text when JSON output is active.
- Official integrations under `src/integrations/` are separate pre-1.0 packages. Use blocks for credentials, never hardcode secrets, and do not develop integration internals as if they were core `src/prefect/` modules.
- UI-v2 is a React/TypeScript app with its own npm workflow, design tokens, Storybook, MSW mocks, and dark-mode rules. Repo-level agents should route deep UI implementation to UI-specific guidance rather than applying Python repo habits.

## Issue Repro Scripts

When working on a GitHub issue:

1. Read the issue or PR context first if available.
2. Create one reproduction file named by issue number under `repros/`, such as `repros/1234.py`.
3. Add `repros/` to `.gitignore` if needed.
4. Reproduce the failure before fixing when feasible.
5. Do not delete repro scripts unless explicitly asked.

Keep repros deterministic and avoid external credentials, long-lived services, or destructive writes unless the issue specifically requires them.
