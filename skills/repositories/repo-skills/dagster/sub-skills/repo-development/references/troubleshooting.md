# Repo Development Troubleshooting

Use this reference when repository-development commands fail or when an edit creates unclear validation scope. Prefer fixing the root cause and re-running the narrowest relevant command before escalating to broad suites.

## Install and Import Errors

**Symptom: `import dagster` or related package imports fail after setup**

- Confirm the developer environment was installed with the repository's setup target, not only a partial package install.
- Use `uv` for package installation and environment repair.
- If a package's command-line entry point or package metadata changed, reinstall that package from its package root with `uv pip install -e .`.
- Verify CLI surfaces with safe help/version checks such as `dagster --help`, `dagster-webserver --help`, or package-specific `--version` commands; do not start services as a smoke test.

**Symptom: editable package points at stale code**

- Reinstall the affected package editable from its package directory.
- Re-run `make ruff` after Python fixes.
- Run focused tests for the edited package path before broader checks.

**Symptom: setup fails around heavy optional wheels or platform-specific binaries**

- Keep the dependency set minimal for the changed package or workflow.
- For Apple silicon `grpcio` setup failures, use the repository's Apple-silicon grpcio wheel install target rather than changing unrelated dependency pins.
- Do not install broad integration extras unless the edited feature requires them.

## Optional Dependency Gaps

Optional integrations can fail imports when their extra dependencies are not installed. Before adding dependencies or changing code:

- Identify whether the edited path is core, webserver, GraphQL, Pipes, shared, docs, UI, or an integration library.
- Search `setup.py` files for the dependency source of truth.
- Keep optional imports lazy when the dependency is not required for core import or CLI startup.
- For CLI commands, lazy-load expensive or optional dependencies inside command functions when needed for startup performance or optional availability.
- If a focused test requires Docker, external credentials, cloud services, or network access, record the skip or ask the user before running it.

## Ruff, Pyright, and Test Failures

**Ruff fails after a Python edit**

- Run `make ruff` from the repository root.
- If it autofixes files, review the changes and re-run focused tests.
- Manually fix remaining line length, import ordering, docstring, unused import, or type-hint issues, then re-run `make ruff`.

**Pyright reports type errors**

- Use built-in generic annotations rather than legacy `typing` aliases.
- Prefer `@record` for immutable result/config data structures and add explicit field types.
- Add `TYPE_CHECKING` imports for type-only dependencies that would create runtime cycles.
- Avoid narrowing by exception-driven control flow when a direct mapping or `None` check is clearer.

**Pytest fails unexpectedly**

- Re-run the focused test with a full path from the repository root.
- Check whether the test requires Docker, external services, a persistent `DAGSTER_HOME`, or an optional integration extra.
- Do not fix unrelated failures; report them separately and keep changes scoped to the user's task.

## CLI, Config, and API Misuse While Editing

Repository edits often touch code that is also exposed via CLI or public API. Common pitfalls:

- A command works only after reinstall because entry points are resolved from installed metadata.
- A local `dagster` command can load an ephemeral instance unless `DAGSTER_HOME` is set, so schedule/sensor or instance state may not persist across commands.
- Config tests can fail because multiple YAML files or JSON config are merged differently; preserve existing command patterns in nearby tests.
- Public API additions may require `@public`, docs, and export decisions; do not add `__init__.py` exports unless requested or required by public API policy.
- GraphQL schema changes can require generated UI types before TypeScript checks make sense.

## UI Workflow Failures

**TypeScript or lint fails after a backend GraphQL schema change**

- Run `make generate-graphql` from `js_modules/` first.
- Wait for generation to complete, then run `yarn tsgo` and `yarn lint` from `js_modules/`.
- If generated files change, include them in the review and re-run relevant checks.

**Jest or UI build fails**

- Run from `js_modules/`, not the repository root.
- For `ui-components` changes, include `yarn build` after standard checks.
- Fix type or lint issues before assuming Jest failures are behavioral.
- Do not run a long-lived dev server as validation unless the user asks.

## Docs Workflow Failures

- Run docs commands from `docs/`.
- Use `yarn build-api-docs` when API documentation or generated API pages are affected.
- If a docs page embeds Python snippets or references changed APIs, pair docs validation with focused Python validation.
- Keep runtime skill or agent instructions self-contained; do not rely on local docs paths being present outside the repository.

## Git and Stack Mistakes

- If asked to push, pause and ask first; do not run `git push` directly.
- If asked to amend or manipulate a stack, inspect `gt log` before inferring branch relationships from raw git history.
- Avoid automatic `git commit --amend`; ask because it can hide the agent's changes in existing commit history.

## When to Escalate

Ask the user before proceeding when validation requires credentialed services, a networked integration, Docker-heavy suites, expensive full test runs, internal repositories that are not available, or mutation of an existing environment beyond normal editable reinstall.
