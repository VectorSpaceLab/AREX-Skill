# Monorepo Layout

## Package Roots

- `pyproject.toml` at the repository root defines the umbrella `llama-index` distribution and shared developer tooling.
- `llama-index-core/` is the core distribution (`llama-index-core`) and contains the primary `llama_index.core` package.
- `llama-index-integrations/<category>/<package>/` contains integration distributions such as LLMs, embeddings, readers, vector stores, callbacks, tools, and related plugin packages.
- `llama-index-utils/<package>/` contains utility distributions discovered by `llama-dev` package discovery.
- `llama-index-instrumentation/` is a separate package root included by `llama-dev` discovery.
- `llama-dev/` is its own Python project for monorepo automation and is not an integration package.

## Metadata Checks

Each package root should have a `pyproject.toml` with a `[project]` table. For maintenance work, verify:

- `project.name`: distribution name published or installed by package managers.
- `project.version`: current package version; do not modify versions unless explicitly asked for release preparation.
- `project.requires-python`: compatibility range used by test automation to skip incompatible packages.
- `project.dependencies`: runtime dependencies; avoid adding broad dependencies to integrations.
- `[dependency-groups].dev`: package-local test and tooling dependencies for `uv run -- pytest`.
- `[tool.uv.sources]`: local path overrides that may affect editable development.
- `[tool.llamahub]`: integration metadata, when present, including import paths and exposed classes.

## Path and Name Conventions

- Package path arguments to `llama-dev` are repository-relative paths, not distribution names.
- Distribution names use hyphens, for example `llama-index-llms-openai`.
- Import namespaces use underscores and usually begin with `llama_index`, for example `llama_index.llms.openai`.
- Integration category names in paths may be plural or domain-specific, such as `llms`, `embeddings`, `vector_stores`, `readers`, or `storage`.

## Targeted Test Strategy

1. Start with the package that changed.
2. Prefer `cd <package>; uv run -- pytest` for one package.
3. Use `llama-dev test <package-path>` when you want the monorepo CLI to sync the package and install locally changed dependencies.
4. Use `llama-dev test --base-ref main` when a branch-level changed-package selection is appropriate.
5. Add `--workers 1` while debugging failures to keep logs understandable; increase workers only for stable broad runs.

## Docs and Examples

Docs contribution guidance uses `uv sync` at the repository root for global tooling, package-local `uv run -- pytest` for package tests, and `uv run make lint` after documentation changes. Docs build and conversion scripts can write generated files or target external documentation trees, so treat them as task-specific automation rather than default maintenance commands.
