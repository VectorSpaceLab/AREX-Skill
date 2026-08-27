# Repo Development Workflows

This reference is for agents editing the Dagster OSS monorepo. It condenses repository-maintainer instructions into self-contained command and style guidance. Commands are shown relative to the repository root unless a step explicitly changes directories.

## Package Lookup

Check package ownership before editing, testing, or reinstalling. Important selected packages:

| Package | Path | Notes |
| --- | --- | --- |
| `dagster` | `python_modules/dagster` | Core framework and core tests under `dagster_tests/`. |
| `dagster-graphql` | `python_modules/dagster-graphql` | GraphQL layer used by webserver and clients. |
| `dagster-webserver` | `python_modules/dagster-webserver` | Webserver package and CLI entry point. |
| `dagster-pipes` | `python_modules/dagster-pipes` | Pipes external-process support. |
| `dagster-shared` | `python_modules/libraries/dagster-shared` | Shared utilities used by multiple packages. |
| `dagster-test` | `python_modules/dagster-test` | Test support package. |
| `automation` | `python_modules/automation` | Repo automation helpers. |
| `dagit` | `python_modules/dagit` | Legacy UI package name retained in the tree. |
| Integration libraries | `python_modules/libraries/<package-name>` | Many optional integrations live here; avoid broad scope unless requested. |
| UI workspaces | `js_modules/` | React/TypeScript app and shared UI packages. |
| Docs site | `docs/` and `docs/docs/` | Docusaurus docs and examples. |

Dependency lookup rule: search `setup.py` files for Python package dependencies. Avoid treating temporary envs, generated caches, or lockfiles as the source of truth for package ownership.

## Environment Setup

For a full developer setup, the repo expects:

```bash
uv venv --python 3.13
make dev_install
```

Activate the environment according to the user's shell before running repo commands. Dagster supports Python 3.10 or higher. Node.js 20 or newer and `yarn` are required for UI and docs work. On Apple silicon, if `grpcio` wheel installation fails during setup, use the repository's M1/M2/M3 grpcio wheel install target instead of the default developer install target.

Use `uv`, not `pip`, for package management. If command-line entry points or package metadata change, reinstall the affected package from that package root:

```bash
uv pip install -e .
```

## Python Edit Workflow

After every edit to a Python file, run Ruff from the repository root:

```bash
make ruff
```

If `make ruff` changes files, re-run relevant tests. If Ruff reports issues it cannot fix, manually correct them and run `make ruff` again until clean. Ruff formats code, sorts imports, enforces the configured line length, and lint-checks repository-specific rules.

Recommended follow-up checks after Python edits:

```bash
pytest path/to/test_file.py
make quick_pyright
make pyright
```

Use focused `pytest` paths first. Broad commands such as the full core test suite or `tox -e py39-pytest` are useful near finalization but can be slow.

## Python Style Conventions

- Use type hints for all Python code.
- Use built-in generic annotations such as `list[str]`, `dict[str, Any]`, `set[str]`, and `tuple[int, str]`; do not import legacy `typing.List`, `typing.Dict`, `typing.Set`, or `typing.Tuple`.
- Prefer functional-style immutable data structures. Use `@record` from `dagster_shared.record` for lightweight immutable result/config/DTO classes unless mutability or external library integration requires `@dataclass`.
- Name immutable update helpers with `with_*`, such as `with_error(...)`, to signal that a new object is returned.
- Use absolute module imports. Keep imports at module scope except for `TYPE_CHECKING`, circular imports, optional dependencies, intentionally expensive lazy imports, or CLI startup performance.
- For CLI output, use `click.echo()` rather than `print()` in production code.
- Avoid global singleton services; pass service instances explicitly.
- Use `Literal` type aliases for reusable string-enum values.
- Avoid `try`/`except` for basic control flow when direct type-safe lookup or validation is clearer.
- Do not add imports to `__init__.py` unless explicitly requested or needed for a public API annotated with `@public`.

Known expensive modules that may justify lazy imports in CLI paths include `jinja2`, `requests`, `dagster_cloud_cli.*`, `urllib.request`, `yaml`, `typer`, and `pydantic`.

## UI Edit Workflow

Run UI validation from `js_modules/` after TypeScript/React edits:

```bash
cd js_modules
yarn tsgo
yarn lint
yarn jest
```

If a backend GraphQL schema change affects generated TypeScript types, regenerate first and wait for completion before typecheck or lint:

```bash
cd js_modules
make generate-graphql
yarn tsgo
yarn lint
yarn jest
```

For changes in `ui-components`, also run a production build:

```bash
cd js_modules
yarn build
```

If editing shared UI packages and an internal app-cloud checkout is available, the repository instructions call for an app-cloud `yarn tsgo` check. Treat that as optional unless the environment and user policy make the internal checkout available.

For local UI development, start a Dagster webserver that serves GraphQL in one terminal and the webapp in another:

```bash
dagster-webserver -p 3333 -f path/to/example_job.py
cd js_modules
make dev_webapp
```

Do not start long-running services as validation unless the user asks.

## Docs Workflow

Docs live under `docs/` and source pages under `docs/docs/`. Typical local docs commands:

```bash
cd docs
yarn install
yarn start
yarn build
```

After API `.rst` changes or changes that affect generated API docs, use the docs API build target:

```bash
cd docs
yarn build-api-docs
```

If a change touches Python and docs together, still run `make ruff` after the Python edit, then pick focused Python tests and the smallest docs build command that covers the changed docs surface.

## Safe Test Selection

Use changed paths to choose a focused validation set:

- `python_modules/dagster/dagster/**`: run `make ruff`, focused `pytest python_modules/dagster/dagster_tests/...`, and type checks when APIs or annotations changed.
- `python_modules/dagster-graphql/**`: run `make ruff`, focused GraphQL package tests, and UI GraphQL generation if schema output changed.
- `python_modules/dagster-webserver/**`: run `make ruff`, focused webserver tests, and UI checks if UI-facing behavior or schema changes.
- `python_modules/dagster-pipes/**`: run `make ruff` and focused Pipes tests.
- `python_modules/libraries/dagster-shared/**`: run `make ruff`, focused shared tests, and selected downstream tests if a shared behavior changes.
- `js_modules/**`: run UI checks from `js_modules/`; include `yarn build` for `ui-components` edits.
- `docs/**`: run docs build or API-doc build as appropriate; include Python checks only if Python snippets or source code changed.
- `setup.py`, package metadata, or CLI entry point changes: reinstall the affected editable package with `uv pip install -e .` before checking CLI behavior.

Avoid `.tox` when searching Python code. Avoid Docker, credentialed services, external networks, full examples, and broad integration-library suites unless specifically requested or necessary for the changed code.

## Git and Stack Constraints

- Never run `git push` directly without asking the user.
- Do not automatically run `git commit --amend`; it can obscure what the agent changed.
- When the user mentions stack operations, inspect `gt log` first because Graphite stack metadata is the source of truth for branch relationships and PR status.
- If searching for GitHub usernames, commit search can reveal exact handles from co-authored commits, but this is a support workflow rather than routine validation.

## Helper Script

Use the bundled command selector to get a conservative command plan from changed paths:

```bash
python scripts/select_validation_commands.py python_modules/dagster/dagster/_core/example.py docs/docs/example.md
```

The script prints command suggestions only. It does not inspect git state and does not run any validation command.
