# Development Workflows

This repo is a Nx workspace of Python packages managed with `uv`.
Use `uv` for Python commands inside a package, and use Nx for workspace orchestration.

## One-time workspace setup

- Run `npm ci` at the workspace root so Nx commands are available.
- Keep `uv` installed for package-level Python commands.

## Workspace entry points

| Task | Recommended command pattern | Notes |
| --- | --- | --- |
| Install one package | `npx nx run <package>:install` | Package targets usually run `uv sync --all-groups`. |
| Install changed packages | `npx nx affected -t install` | Best after edits that touch multiple packages. |
| Lint one package | `npx nx run <package>:lint` | Usually runs `uv run ruff check .`. |
| Lint changed packages | `npx nx affected -t lint --parallel=3` | Match CI-style parallelism when useful. |
| Test one package | `npx nx run <package>:test` | Usually runs `uv run pytest tests/`. |
| Test changed packages | `npx nx affected -t test --parallel=2` | Prefer affected tests over whole-workspace runs. |
| Type-check the SDK | `npx nx run traceloop-sdk:type-check` | Only packages with a `type-check` target support this. |
| Build one package | `npx nx run <package>:build` | Uses the Python build executor. |
| Release build one package | `npx nx run <package>:build-release` | Maintainer-only caveat; see source-script map. |
| Lock one package | `npx nx run <package>:lock` | Wraps `uv lock`. |
| Inspect the graph | `npx nx graph` | Useful when package dependencies change. |

## Package-level `uv` patterns

Run these from the package directory when you need direct Python tooling.

| Purpose | Command pattern |
| --- | --- |
| Sync dependencies | `uv sync --all-groups` |
| Lint | `uv run ruff check .` |
| Test | `uv run pytest tests/` |
| Single file or node | `uv run pytest tests/<path>::<node> -q` |
| Lock | `uv lock` |
| Type-check SDK | `uv run mypy traceloop/sdk` |

## Package conventions to remember

- `project.json.name` should match the package directory and the Nx target name.
- `project.json.sourceRoot` points to the import root inside the package.
- `pyproject.toml` usually owns version, dependencies, optional extras, entry points, and Ruff config.
- Most instrumentation packages expose an `opentelemetry_instrumentor` entry point and an `instruments` optional extra.
- `traceloop-sdk` uses many local editable `tool.uv.sources` entries for sibling packages.
- `sample-app` is an application package, not a publishable library.
- `opentelemetry-semantic-conventions-ai` is lightweight and should stay free of provider-client baggage.

## Code quality conventions

- Ruff line length is 120.
- Ruff lint selection is limited to `E`, `F`, and `W`.
- Common excludes include `.git`, `__pycache__`, `build`, `dist`, `.venv`, and `.pytest_cache`.
- Keep package metadata and Nx targets in sync when renaming or adding a package.

## CI version shape

- Lint runs on Python 3.11.
- Package builds run on Python 3.11.
- Package tests run on Python 3.10, 3.11, and 3.12.

## Semantic package patterns

### SDK package

- Use `traceloop-sdk` for SDK initialization, decorators, manual spans, and package-level maintenance checks.
- Keep local sibling package sources synchronized when a new instrumentation package is added.

### Semantic-conventions package

- Use `opentelemetry-semantic-conventions-ai` for shared span-attribute constants and compliance checks.
- Prefer this package when a change only touches attribute names, alias migration, or compliance tests.

### Instrumentation packages

- Each package typically wraps one provider, vector DB, framework, or protocol client.
- Keep the package import root, entry point, and optional dependency aligned.
- Use the narrowest direct package test that matches the changed integration surface.

### Sample app

- Treat `sample-app` as a consumer/integration package.
- Use it for package-wiring checks, not for release packaging.

## Discovery helper

Use [scripts/list_openllmetry_projects.py](../scripts/list_openllmetry_projects.py) to inspect package names, source roots, test files, entry points, and local source mappings before guessing the workspace shape.
