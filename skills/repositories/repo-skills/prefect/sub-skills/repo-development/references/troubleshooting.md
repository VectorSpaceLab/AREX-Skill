# Repo Development Troubleshooting

Use this reference when a Prefect repository change fails validation, touches generated artifacts, crosses package boundaries, or seems blocked by environment/service assumptions.

## Missing `uv`, `just`, or Node Tools

Symptoms:

- `uv: command not found`
- `just: command not found`
- UI-v2 hooks fail because `nvm`, `node`, or `npm` is unavailable

Response:

- Prefer installing or enabling the missing tool rather than switching to `pip` or ad-hoc Python invocations.
- For Python commands, use `uv run ...` and `uv sync`; do not use `pip install` or `uv pip` for repo dependency management.
- For UI-v2, follow `ui-v2/AGENTS.md`: use `nvm`, then npm scripts from `ui-v2/`.
- If the task does not touch UI-v2, do not run UI-v2 npm checks just because pre-commit has a UI hook.

## Dependency and Lockfile Drift

Symptoms:

- `uv-lock` modifies `uv.lock`.
- `prefect-client` build fails after root dependency changes.
- CI reports dependency mismatch between `pyproject.toml` and `client/pyproject.toml`.

Response:

1. Determine whether the dependency is server-only, full Prefect, or client-visible.
2. If client-visible, mirror the dependency constraint in `client/pyproject.toml`.
3. Regenerate or update `uv.lock` with `uv lock` or the pre-commit hook.
4. Re-run focused tests and `bash client/build_client.sh` when the client package boundary is involved.

Do not add broad optional extras or dev dependencies to fix one missing runtime import unless the source package actually requires them.

## `prefect-client` Import Failures

Symptoms:

- Import succeeds in `prefect` but fails in `prefect-client`.
- Build fails after adding an import to client-side code.
- A client schema or orchestration module unexpectedly imports server/database code.

Response:

- Remove server-only imports from `src/prefect/client/` and code shipped in the client package.
- Keep client schemas separate from server schemas; mirror compatible fields deliberately.
- Check `client/AGENTS.md` for files stripped by `build_client.sh`.
- Run the focused client tests first, then local client build reproduction if needed.

## Generated Docs or Schema Staleness

Symptoms:

- Docs/API/CLI reference files differ after pre-commit.
- Settings type/schema tests fail after adding a setting.
- `prefect.yaml` validation tests fail after deployment config changes.
- UI-v2 type generation changes after server API/schema edits.

Response:

- Regenerate from the appropriate source of truth; do not hand-edit generated files.
- For settings, update tests and run settings generators.
- For docs, obey `docs/AGENTS.md`: generated directories are not directly edited, except hand-authored event API docs.
- For UI-v2 service types, run UI service sync only when server API/schema changes affect UI consumers.

## AGENTS Scope Conflicts

Symptoms:

- Root guidance says one thing, but a component-specific `AGENTS.md` adds a stricter rule.
- Tests fail due to component-specific fixture or architecture assumptions.
- Code review flags an import or output style that seemed acceptable globally.

Response:

- The nearest scoped `AGENTS.md` wins for files under its tree.
- Apply all relevant ancestor instructions unless a deeper file refines them.
- For cross-area changes, follow each touched area's instructions independently.
- When rules conflict with the user request, ask for clarification rather than silently violating maintainer guidance.

## Async Tests and Settings Contexts

Symptoms:

- Async tests intermittently fail due to loop scope, background tasks, or delayed events.
- Settings changes do not appear to take effect.
- Event or log assertions count setup events instead of action events.

Response:

- Prefer existing async fixtures and test harness utilities rather than creating custom event loops.
- Use `temporary_settings()` with string keys or env-var names for new tests.
- Check `pyproject.toml` pytest config: async mode is automatic and default fixture loop scope is session-level.
- Use `retry_asserts` for async event propagation.
- Reset event assertion clients after fixture setup when asserting only on action-produced events.

## Database Isolation and Service Requirements

Symptoms:

- Tests pass alone but fail with residual database rows.
- SQLite passes but PostgreSQL fails, or vice versa.
- Local tests fail because Postgres, Redis, Docker, or Kubernetes is unavailable.

Response:

- Add `@pytest.mark.clear_db` only when the test depends on an empty database. Audit with `--no-clear-db` when possible.
- Keep SQLite and PostgreSQL behavior aligned. Use database-specific query variants only when necessary and test both paths.
- Avoid service-backed tests for ordinary changes. Use skip/exclude options for Docker and Kubernetes unless the service behavior is under test.
- For Postgres-required checks, state the connection/service requirement explicitly before running.

## Server State-Transition Anti-Pattern

Symptoms:

- A test directly mutates flow-run state rows.
- A code path tries to skip orchestration rules for convenience.
- State metadata appears stale in emitted events.
- Completed state metadata or persisted results are lost across transitions.

Response:

- Route flow state changes through orchestration APIs or policies; do not bypass the server, even in tests.
- Remember that task state transitions are local engine behavior plus task-run events; do not copy task assumptions to flow orchestration.
- Persist observable run metadata before proposing the state that emits the event.
- Treat `force=True` as a minimal-policy path, not an all-rules bypass.
- For new `state_details` fields, account for Pydantic v2 explicit-null behavior in orchestration transforms.

## CLI JSON Output Failures

Symptoms:

- A `--json` command prints human-readable text before or after JSON.
- CLI tests fail due output formatting or error exits.

Response:

- Suppress diagnostics and prompts when JSON output is active.
- Use `rich` for human output and `exit_with_error` for error exits.
- Add or update targeted CLI tests for both human and JSON output when a command supports JSON.

## Docs Validation Failures

Symptoms:

- Broken relative links or links ending in `.mdx`.
- New page is not visible in navigation.
- Docs body starts with an extra H1.
- Generated docs were edited directly and overwritten.

Response:

- Use absolute docs-root links without `.mdx`.
- Add navigable pages to `docs/docs.json`; use `hidden: true` for unlisted pages.
- Start body content at `##` because frontmatter title renders H1.
- Move edits to the source generator or hand-authored page.
- Use `just links` and `just lint` for docs-specific checks.

## Integration and UI Boundary Failures

Symptoms:

- Integration tests import local core Prefect unexpectedly.
- A new integration changes release/version behavior incorrectly.
- UI-v2 code fails dark-mode, service-sync, or mock conventions.

Response:

- Work inside the integration package for integration-local commands. Use editable core Prefect only when developing a core interface consumed by that integration.
- Do not add new integrations without prior discussion.
- Keep credentials in blocks; never hardcode secrets in flows or integration tests.
- For UI-v2, follow the React-specific rules: semantic color tokens, MSW mocks, suspense query conventions, Storybook for new components, and npm validation scripts.

## Over-Broad or Destructive Validation

Symptoms:

- A command starts long-lived services unexpectedly.
- A release or publishing helper generated unrelated files.
- A full test/pre-commit run obscures the focused failure.

Response:

- Stop and narrow the command to the changed component.
- Treat release/publishing/Postgres/Docker/integration scripts as reference-only unless the task explicitly requires them.
- Record skipped broad checks and the reason in the handoff rather than hiding them.

## Quick Triage Checklist

1. Re-read the nearest `AGENTS.md` for every touched path.
2. Confirm whether the failure is source behavior, generated output, package-boundary drift, environment/tooling, or service prerequisites.
3. Run the smallest reproducing test or script.
4. Fix root cause, not generated symptoms.
5. Broaden validation only when the affected contract crosses components.
