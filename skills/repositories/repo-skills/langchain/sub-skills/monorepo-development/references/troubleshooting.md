# LangChain Monorepo Troubleshooting

## `uv` Is Missing

Symptoms:

- `uv: command not found`.
- `make test`, `make lint`, or `make type` fails before running package tools.
- A host environment has Python but not the LangChain-required package manager.

Recovery:

1. Do not substitute `pip`, `poetry`, `conda`, or an ad-hoc virtual environment.
2. Report that LangChain development workflows require `uv`.
3. Continue with read-only inspection, static edits, or metadata checks that do not need dependency installation.
4. Mark tests/lint/type checks as skipped because `uv` is unavailable.

## Running From the Wrong Directory

Symptoms:

- `uv` cannot find `pyproject.toml`.
- `pytest` cannot import package-local editable dependencies.
- `make` has no target or runs a different package's targets.
- Dependency groups appear missing even though they exist in the package metadata.

Recovery:

1. Find the nearest owning package directory under `libs/` that contains `pyproject.toml` and `uv.lock`.
2. `cd` into that package directory before running `uv`, `pytest`, `ruff`, `mypy`, or package Make targets.
3. For partner packages, use `libs/partners/<provider>`, not `libs/partners` or the repository root.
4. Use `python <this-skill>/scripts/inspect_langchain_package.py <package-dir>` to confirm the package name and groups.

Example:

```bash
cd libs/langchain_v1
uv run --group test pytest tests/unit_tests/agents/test_create_agent.py
```

## Test or Lint Dependency Group Confusion

Symptoms:

- `pytest` is missing.
- `mypy` or type stubs are missing.
- `ruff` is missing.
- Optional provider packages are unexpectedly installed or missing.

Recovery:

- Use `--group test` for unit tests.
- Use `--group lint` for ruff-only package commands.
- Use `--group typing` for mypy and stubs when running direct type checks.
- Use `--group test --group test_integration` only for integration tests.
- Use `--all-groups` only when a package Makefile expects it or broad validation is necessary.
- Inspect `[dependency-groups]` in the owning package's `pyproject.toml` rather than assuming all packages define identical groups.

## Public API Signature Risk

Symptoms:

- A change removes, reorders, renames, or changes defaults for arguments on an exported symbol.
- Tests or examples call the API positionally.
- The symbol is imported from package `__init__.py` or appears in public docs.

Recovery:

1. Preserve existing signature shape if possible.
2. Add new parameters after `*` as keyword-only.
3. Keep default behavior unchanged unless the user explicitly accepts a breaking change.
4. Add tests for old and new call styles.
5. Update docstrings with Google-style Args/Returns/Raises and single backticks for code references.
6. Warn that the requested change may break external users if compatibility cannot be preserved.

## Stale Model IDs in Docs

Symptoms:

- Examples mention old preview, beta, or retired model names.
- A doc update introduces a model ID from memory rather than current provider docs.
- Model profile data does not match provider capabilities.

Recovery:

1. Verify current generally available model IDs from provider documentation before editing docs/examples.
2. Prefer GA model names over preview or beta names unless no GA equivalent exists.
3. Do not silently change shipped code defaults just to modernize docs.
4. For capability flags or context windows, use the `langchain-profiles` workflow rather than hand-editing generated profile data.
5. If provider docs cannot be checked, leave a clear skip note instead of guessing.

## Optional Dependency Over-Installing

Symptoms:

- Setup attempts to install all provider SDKs or large NLP/model packages for a narrow change.
- A local test unexpectedly requires network, large model downloads, or API credentials.
- `uv sync --all-groups` is slow or fails on unrelated optional packages.

Recovery:

1. Identify the smallest package and dependency group needed.
2. Prefer `uv sync --group test` for unit tests.
3. Add `test_integration` only for explicitly requested integration tests.
4. Avoid installing optional extras unrelated to the changed code path.
5. If a test needs a heavy optional package, either install the narrow group/extra that owns it or skip with a clear reason.

## Integration Test Requires Credentials or Network

Symptoms:

- Tests reference provider API keys, VCR recording, cassettes, Docker services, or live endpoints.
- Unit-test Make targets disable sockets but integration tests do not.

Recovery:

1. Run package-local unit tests first.
2. Do not run live integration tests unless the user requested them and credentials/network are available.
3. Prefer playback-only VCR tests when the package Makefile provides a safe target.
4. Record skipped integration tests and why.

## Import or Version Checks Fail

Symptoms:

- `make check_imports` prints source paths and tracebacks.
- `make check_version` reports mismatch between `pyproject.toml` and package version artifacts or snapshots.

Recovery:

1. Read the package-local `scripts/check_imports.py` or `scripts/check_version.py` to understand the expected invariant.
2. Fix import-time errors without adding broad optional dependencies unless the imported module genuinely requires them.
3. Keep package version strings and generated metadata consistent when a version bump is in scope.
4. Do not assume every package's version script checks the same files.
