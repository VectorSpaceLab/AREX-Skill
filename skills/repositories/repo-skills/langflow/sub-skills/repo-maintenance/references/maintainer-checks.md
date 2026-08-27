# Maintainer Checks

This reference covers repo-wide Langflow maintenance tasks that are not primarily component design, backend implementation, frontend UI work, executor usage, SDK integration, or production deployment.

## Repository Shape

Langflow is a Python and TypeScript monorepo with these maintenance surfaces:

- Root `langflow` package: top-level metadata, workspace membership, bundle dependencies, app launcher, and release version.
- `langflow-base`: FastAPI app, services, graph execution, component framework, migrations, backend tests, and most runtime dependencies.
- `lfx`: lightweight executor CLI, extension system, flow runner/server, pytest plugin, and bundle API surface.
- `langflow-sdk`: Python REST SDK and test helpers.
- Frontend: React/Vite UI served during development by Vite and copied into the backend static frontend for packaged runs.
- Bundles: workspace packages such as `lfx-arxiv`, `lfx-docling`, `lfx-duckduckgo`, and `lfx-ibm` with extension manifests and `lfx` dependency pins.

Supported maintenance prerequisites are Python `>=3.10,<3.15`, `uv`, Node.js `>=20.19.0`, npm `>=10.9`, and `make`.

## Setup and Clean Runs

Start from the narrowest setup that matches the task:

```bash
make check_tools
make init
make backend
make frontend
make run_cli
make run_clic
```

Use `make init` for a full development setup. It installs backend dependencies, installs frontend dependencies, and installs pre-commit hooks. Use `make run_cli` for a packaged-style local run that builds the frontend and starts Langflow through the CLI. Use `make run_clic` when frontend build artifacts or caches look stale because it cleans frontend build outputs first.

For hot-reload development, run `make backend` and `make frontend` in separate terminals. `make backend` runs the FastAPI app on port `7860`; `make frontend` runs Vite on port `3000`.

## Python Workspace and Package Sync

Use `uv run` for Python commands from the repository so the workspace environment, lockfile, and package metadata are respected:

```bash
uv run pytest path/to/test.py -q
uv run python -m py_compile path/to/file.py
uv run ruff check path/to/package
```

When running tests from a sub-package, sync that package's dev group first. The root sync may not install package-local test dependencies such as fake Redis, package-specific pytest plugins, or optional integration helpers:

```bash
uv sync --group dev --package langflow-base
cd src/lfx && uv sync --dev
cd src/sdk && uv sync --dev
```

If `langflow --help` or a CLI import fails because `openai` is absent, install or select the development environment that includes the current CLI import dependencies. PyTorch/transformer execution is optional and out of scope for ordinary maintenance checks unless a task explicitly targets local model execution.

## Generated Artifacts

Treat generated artifacts as reproducible outputs. Regenerate, review the diff, and validate; do not hand-edit generated outputs as a shortcut.

Component index:

```bash
make build_component_index
```

Use this when built-in component files or bundle availability changed and the prebuilt component index needs to match source. During component development, `LFX_DEV=1 make backend` dynamically loads components and avoids needing an index rebuild for every edit. For a targeted dynamic load, use `LFX_DEV=openai,mistral make backend` with the relevant module names.

Frontend static bundle:

```bash
make build_frontend
make clean_frontend_build
make run_clic
```

`make build_frontend` builds `src/frontend` and copies the build output into the backend static frontend directory. `make clean_frontend_build` clears frontend build outputs without clearing all dependencies. `make run_clic` is the end-to-end clean frontend rebuild path.

Lockfiles and dependency pins:

```bash
uv lock --no-upgrade
make lock
make lock_base
make lock_langflow
```

Use lock targets only when dependency metadata changed or a release workflow expects updated lockfiles. Review package marker preservation, optional extras, and workspace source entries after lock or version changes.

## Version and Package Updates

For normal release-line version bumps, prefer the root target:

```bash
make patch v=1.10.2
```

This updates the root `langflow` version, derives the `langflow-base` version from the release line, updates the frontend package version, and runs related package update helpers. After a version bump, check at least:

```bash
rg -n 'version = "|"version":|langflow-base|lfx>=' pyproject.toml src/backend/base/pyproject.toml src/lfx/pyproject.toml src/sdk/pyproject.toml src/frontend/package.json src/bundles/*/pyproject.toml
uv lock --no-upgrade
```

Important package invariants:

- Root `langflow` depends on `langflow-base[complete]` and bundled `lfx-*` extension packages.
- `langflow-base` depends on `lfx` and carries backend runtime dependencies.
- `lfx` depends on `langflow-sdk` for CLI/remote workflows.
- Bundle packages should keep an `lfx` runtime floor that admits the current release line, including `.devN` nightlies, and caps the next major line.
- Nightly helpers intentionally use exact canonical pre-release pins for `lfx` and `langflow-sdk`; do not mix canonical and `-nightly` names unless following the release automation.

For a risky version edit, inspect the resulting metadata rather than trusting a string replacement. Confirm that PEP 440 versions are valid, extras such as `[complete]` are preserved, bundle dependency markers remain inside the bundle marker blocks, and root workspace sources still point at workspace packages. If a change depends on CI release helpers, describe the invariant being preserved in the handoff instead of hand-editing around it.

Do not run publish targets such as `make publish`, `make lfx_publish`, or `make sdk_publish` unless the user explicitly asks and credentials/release state are ready.

## Alembic and Database Migrations

Use root targets for migration lifecycle tasks:

```bash
make alembic-revision message="Add table"
make alembic-check
make alembic-upgrade
make alembic-current
make alembic-history
make alembic-downgrade
make alembic-stamp revision=<revision>
```

Guardrails:

- Prefer expand/migrate/contract style changes for live data safety.
- Avoid destructive schema changes without data migration and rollback notes.
- Keep generated migration files deterministic and review any auto-generated drop/rename operations carefully.
- Run focused migration tests for migration validators, execution, and special data backfills before broad unit tests.
- Do not run upgrade/downgrade against a user's real database without backup and explicit approval.

Useful focused checks:

```bash
uv run pytest src/backend/tests/unit/alembic/test_migration_validator.py -q
uv run pytest src/backend/tests/unit/alembic/test_migration_execution.py -q
uv run pytest src/backend/tests/unit/alembic/test_existing_migrations.py -q
```

## Extension Migration and Bundle API Guards

The extension system has CI-style static guards for `lfx` extension loading, bundle manifests, route trust, and migration tables. This sub-skill distills the invariants future agents must preserve; if a task needs an executable guard beyond the bundled deprecated-import checker, copy or adapt the needed logic into this skill tree before instructing another agent to run it.

Key invariants:

- Bare component class migration entries must map to exactly one bundle folder unless registered as ambiguous.
- Migration table entries and ambiguous bare-name markers are append-only; do not remove or mutate published entries.
- Runtime extension routes under `/api/v1/extensions/**` must not expose install/uninstall/registry mutation operations.
- Changes to the public bundle API surface require a changelog entry in the bundle API contract.

For provider extraction into standalone bundles, do not perform a mechanical port from this sub-skill alone. Route component and bundle authoring details to `../component-development/SKILL.md`, preserve the extension migration invariants listed here, and require a dry-run/review workflow before any tree mutation.

## Documentation and API Examples

Use docs targets for Docusaurus maintenance:

```bash
make docs
make docs_build
make docs_serve
```

Docs run on port `3030` by default. If the Vite frontend is also running, choose a non-conflicting docs port:

```bash
make docs docs_port=3031
```

API examples can be checked syntactically without requiring a live server:

```bash
make api_examples_local_syntax suites=python,javascript,curl
```

Only run live API example execution when a local Langflow server is intentionally running and the examples do not require external credentials:

```bash
make api_examples_local suites=python
```

## Pull Request Hygiene

Before handoff, summarize:

- The touched surface and why the chosen tests are sufficient.
- Commands run and whether they were focused, package-level, or broad.
- Skipped checks and the reason: missing Node modules, missing dev extras, credentials, database, network, GPU, or time.
- Generated files reviewed and whether diffs were produced by a generator.
- Version or migration invariants checked explicitly.

Contribution metadata expectations: target the active release branch rather than `main`, use semantic PR/commit titles, and reference issues when relevant.
