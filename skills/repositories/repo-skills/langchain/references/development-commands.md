# Development Commands

## Package-Local Setup

LangChain packages are independently versioned and use package-local `uv.lock` files. Start in the package that owns the change:

```bash
cd libs/<package>
uv sync --group test
```

Use `--group lint`, `--group typing`, `--group test_integration`, or `--all-groups` only when the task requires those dependencies. Avoid broad dependency installation when a targeted group covers the change.

## Tests

Prefer the narrowest deterministic unit test first:

```bash
uv run --group test pytest tests/unit_tests/path/to/test_file.py
```

Broaden to a package test suite only after targeted tests pass or when the change affects shared behavior. Integration tests often require credentials, provider services, sockets, Docker services, VCR cassettes, or large optional dependencies; skip them unless the user explicitly requests them and prerequisites are available.

## Lint, Format, Type, and Import Checks

Common package patterns include:

```bash
make lint_package
make lint_tests
make format
make type
make check_imports
make check_version
```

Check the package `Makefile` before assuming every target exists. Import/version scripts are useful smoke checks for changed import surfaces and package version metadata.

## Validation Escalation

1. Syntax or static script checks for bundled helper changes.
2. Targeted unit tests for the changed module.
3. Package-local import/version checks.
4. Package lint/type checks when signatures, imports, or typing changed.
5. Broader package tests.
6. Credentialed or service-backed integration tests only with explicit permission and prerequisites.

## Common Skip Reasons

Record skips explicitly when `uv` is unavailable, dependency groups are not synced, provider credentials are absent, a local vector database/service is not running, a test requires network sockets, a notebook/example downloads data, or a command would mutate cassettes/release state.
