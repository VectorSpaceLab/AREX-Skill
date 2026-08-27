# LangChain Development Workflows

Run package-local commands from the owning package directory. The repository root has no root `pyproject.toml`, so `uv run`, `uv sync`, `pytest`, `ruff`, and `mypy` workflows should normally begin with `cd libs/<package>`.

## Inspect Package Metadata

Use the bundled helper from the generated skill tree when you need a quick read-only summary:

```bash
python <this-skill>/scripts/inspect_langchain_package.py libs/core
python <this-skill>/scripts/inspect_langchain_package.py libs/partners/openai --json
```

The helper reads `pyproject.toml` only. It does not install dependencies, import LangChain packages, contact the network, mutate files, or require `uv`.

## Environment Setup

Preferred package-local setup:

```bash
cd libs/core
uv sync --group test
```

For linting or typing:

```bash
uv sync --group lint
uv sync --group typing
```

For broad local validation when the package Makefile expects all optional developer groups:

```bash
uv sync --all-groups
```

Skip setup and explain the skip when `uv` is unavailable in the host environment. Do not replace it with `pip`, `poetry`, `conda`, or manual virtual environment activation.

## Unit Tests

From the owning package directory:

```bash
uv run --group test pytest tests/unit_tests/path/to/test_file.py
```

or, when the package Makefile wraps environment cleanup/socket blocking correctly:

```bash
make test TEST_FILE=tests/unit_tests/path/to/test_file.py
```

Validation signals:

- Tests collect from the package's `tests/unit_tests/` tree.
- Unit tests should avoid network calls; many package Makefiles use `--disable-socket --allow-unix-socket`.
- Failures should point to changed behavior, missing test groups, import errors, or snapshot updates.

Skip conditions:

- `uv` is not installed.
- The test target starts Docker services or other heavy services and the user has not approved it.
- The test is an integration/provider test requiring credentials, network, or VCR cassette changes.

## Lint, Formatting, and Typing

Common package-local targets:

```bash
make lint_package
make lint_tests
make lint_diff
make type
```

Formatting commands:

```bash
make format
make format_diff
```

Use formatting targets only when it is appropriate to modify files. Many packages configure ruff with Google-style docstring checks, no relative imports, and per-file ignores for tests and scripts. Respect package-local `pyproject.toml` instead of assuming one global ruff/mypy configuration.

## Import and Version Checks

Many packages provide:

```bash
make check_imports
make check_version
```

`check_imports` scripts load source files by path to catch import-time failures. `check_version` scripts compare `pyproject.toml` versions with package-specific version files or generated snapshots. These scripts are package-specific; inspect their local behavior before extrapolating across packages.

## Public API Change Workflow

1. Identify whether the symbol is exported in a package `__init__.py` or documented as public.
2. Search tests and examples for existing call patterns.
3. Preserve existing positional parameters, names, defaults, and return contracts.
4. Add new knobs as keyword-only parameters.
5. Update type hints and Google-style docstrings.
6. Add unit tests for the happy path and compatibility path.
7. Run targeted package-local tests.
8. Run lint/type checks if signatures, docstrings, or imports changed.
9. Warn the user if the requested change could break existing external code.

Example command sequence for a core API parameter addition:

```bash
cd libs/core
uv sync --group test --group lint --group typing
uv run --group test pytest tests/unit_tests/path/to/test_file.py
make lint_package
make type
make check_imports
```

## Dependency Workflow

When adding or changing dependencies:

1. Confirm the owning package from `references/package-map.md`.
2. Add runtime dependencies to `[project].dependencies` only when import-time or normal runtime behavior needs them.
3. Add optional provider or feature dependencies to `[project.optional-dependencies]` when users opt in explicitly.
4. Add test-only dependencies to `[dependency-groups].test` or `test_integration`.
5. Add lint/type-only dependencies to `lint` or `typing`.
6. Prefer package-local `[tool.uv.sources]` entries for in-repo editable dependencies.
7. Regenerate or check the package-local `uv.lock` with `uv lock` or `uv lock --check` from that package.

Avoid over-installing optional dependencies. If only one optional path is being tested, install the narrowest group or extra that exercises that path.

## Cross-Package Lockfile Checks

The `libs/Makefile` has cross-package targets for core package lockfiles:

```bash
cd libs
make check-lock
make lock
```

These operate across `core`, `text-splitters`, `langchain`, `langchain_v1`, and `model-profiles`. They do not cover every partner package. Use them only when lockfiles across those packages are in scope.

## Model Profile Refresh

For model profile data, work from `libs/model-profiles` and point `--data-dir` at the integration package's data directory:

```bash
cd libs/model-profiles
uv run langchain-profiles refresh --provider openai --data-dir ../partners/openai/langchain_openai/data
```

For external integration repositories, the maintainer guidance requires confirmation before writing outside the package workspace. Do not invent model capabilities or stale model IDs; verify current generally available model IDs against provider documentation before changing docs or profile data.

## Integration Package Workflow

For `libs/partners/<provider>` packages:

```bash
cd libs/partners/<provider>
uv sync --group test
uv run --group test pytest tests/unit_tests/path/to/test_file.py
make lint_package
make type
```

Provider integration tests may need API keys, network access, VCR cassettes, Docker services, or local caches. Run only safe unit tests by default and record any skipped integration validation.

## PR and Contribution Conventions

When asked for PR/commit guidance:

- Use Conventional Commit titles with a scope, such as `fix(core): preserve tool call metadata` or `feat(openai): add response format support`.
- Start the description after `type(scope):` lowercase unless the first word is a proper noun or code symbol.
- Wrap code symbols in backticks in PR titles and descriptions.
- Branch names use `<github-username>/<scope>/<short-description>`.
- PR descriptions should explain who benefits, what problem they had, and how the change solves it.
- Include a brief note that an AI agent assisted when applicable.

Do not deep-link future agents to repository workflow files from this skill; summarize the conventions instead.
