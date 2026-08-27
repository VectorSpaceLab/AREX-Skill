---
name: monorepo-development
description: "Navigate LangChain's Python monorepo packages, package-local uv
  workflows, validation commands, API stability checks, PR conventions, and
  docs/model-reference guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LangChain Monorepo Development

Use this sub-skill when a task changes repository structure, package metadata, public Python APIs, tests, lint/type workflows, documentation examples, or contributor-facing conventions in the LangChain Python monorepo.

## Start Here

1. Identify the package that owns the change with [package-map.md](references/package-map.md).
2. Inspect package metadata safely with [inspect_langchain_package.py](scripts/inspect_langchain_package.py) when you need the package name, version, dependency groups, Python range, local editable sources, or optional extras.
3. Run commands from the package directory, not from the repository root, unless [development-workflows.md](references/development-workflows.md) explicitly describes a cross-package command.
4. Validate with the narrowest package-local target first, then broaden only if the changed area requires it.
5. Use [troubleshooting.md](references/troubleshooting.md) when `uv`, package roots, dependency groups, public API checks, model IDs, or optional dependencies are unclear.

## Package Routing

- `libs/core`: Core primitives and abstractions in `langchain-core`; use for base interfaces, schemas, messages, tools, runnables, callbacks, serialization, and API contracts shared across packages.
- `libs/langchain_v1`: Actively maintained `langchain` package; use for high-level public utilities and agent/application APIs that depend on `langchain-core` and LangGraph.
- `libs/langchain`: `langchain-classic`; treat as legacy/classic surface and avoid new feature work unless the user specifically targets classic behavior or compatibility.
- `libs/text-splitters`: `langchain-text-splitters`; use for text chunking utilities and splitter-specific tests.
- `libs/partners/<provider>`: Team-maintained integration packages such as OpenAI, Anthropic, Ollama, DeepSeek, xAI, and others; keep provider-specific behavior here and route deeper provider implementation to the integrations sub-skill if present at `../integrations/SKILL.md`.
- `libs/standard-tests`: `langchain-tests`; use for standardized conformance tests shared by integrations.
- `libs/model-profiles`: `langchain-model-profiles`; use for model profile data tooling and profile refresh operations.

## Default Workflow

```bash
cd libs/<package>
uv sync --group test
uv run --group test pytest tests/unit_tests/path/to/test_file.py
make lint_package
make type
```

Adjust groups by package metadata: use `--group lint` for lint-only commands, `--group typing` or `--all-groups` when mypy needs optional typing dependencies, and add `--group test_integration` only for explicitly requested integration tests. Do not use `pip`, `poetry`, `conda`, or ad-hoc virtual environments for LangChain package development.

## Public API Guardrails

Before changing a public function, class, method, or exported symbol:

- Check whether it is exported from a package `__init__.py` or documented as public.
- Search existing tests and examples for positional and keyword usage.
- Preserve existing argument names, positions, defaults, and return types whenever possible.
- Add new parameters as keyword-only, for example `*, new_option: str | None = None`.
- Add or update deterministic unit tests under the owning package's `tests/unit_tests/` tree.
- Use Google-style docstrings for public APIs with Args/Returns/Raises where relevant, single backticks for inline code, and type hints in signatures.

Warn the user before making a signature change that could break code written against last week's release.

## Validation Signals

Prefer package-local validation from the owning directory:

- Unit tests: `uv run --group test pytest tests/unit_tests/...` or `make test TEST_FILE=tests/unit_tests/...`.
- Lint and formatting check: `make lint_package`, `make lint_tests`, or `make lint_diff` when the package Makefile supports them.
- Formatting fix: `make format` or `make format_diff` only after confirming it is appropriate for the task.
- Type checking: `make type` or the package's mypy command through `uv run`.
- Import checks: `make check_imports` where available; package scripts load source files to catch import-time failures.
- Version checks: `make check_version` where available; these compare package metadata with package-specific version artifacts.

Skip or defer integration tests when they need network credentials, provider services, Docker services, or heavy optional dependencies and the user did not ask for them. Record the skip condition in the handoff.

## Documentation and Model References

- Use current generally available model names in docs and examples; verify against provider documentation before introducing or updating model IDs.
- Do not change shipped default model parameters casually because defaults are public behavior.
- For profile data, use the model-profiles workflow in [development-workflows.md](references/development-workflows.md) rather than manually editing generated profile data.
- Keep documentation examples minimal, deterministic, and aligned with the package that owns the API.

## Maintainer-Level Package Changes

For adding packages or integrations, keep work at an operational level unless the user explicitly asks for provider-specific implementation:

- Add or update package-local `pyproject.toml`, `uv.lock`, package Makefile, tests, and scripts following existing package patterns.
- Wire local editable sources through `[tool.uv.sources]` for in-repo dependencies.
- Update contributor-facing package labels, release/change detection, and issue dropdown configuration as required by maintainer guidance, but do not deep-link future agents to source workflow files from this skill.
- Route provider-specific behavior, credentials, standard integration tests, and model feature details to the integrations sub-skill if available.

## Required References

- [Package map](references/package-map.md)
- [Development workflows](references/development-workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Package metadata inspector](scripts/inspect_langchain_package.py)
