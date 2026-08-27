# Troubleshooting

Use this reference when validation, standard tests, snapshots, or model profile workflows fail.

## Missing `uv` Or Dependency Groups

Symptoms:

- `uv: command not found`.
- `No such option: --group` or dependency group resolution fails.
- Imports fail for packages that should be installed from local editable sources.

Actions:

1. Do not fall back to `pip`, `poetry`, `conda`, or ad-hoc virtualenvs for LangChain development.
2. Report that validation is blocked by missing or broken `uv`.
3. From the package directory, propose the exact setup command, for example `uv sync --group test`, `uv sync --group lint --group typing`, or `uv sync --all-groups`.
4. Confirm the package has a local `pyproject.toml` and `uv.lock`; there is no root package config for the whole monorepo.

## Pytest Socket Or Network Blocking

Symptoms:

- Failures mention socket use, blocked network calls, `pytest-socket`, HTTP clients, VCR, or provider SDKs.
- Unit tests unexpectedly try to reach a provider service.

Actions:

1. Treat the failure as a test safety signal, not as permission to enable network.
2. Check whether the test belongs under `tests/integration_tests/`, has `@pytest.mark.vcr`, uses provider credentials, or depends on a local service.
3. For unit tests, mock network clients or use fake/local implementations.
4. For integration tests, ask for explicit permission and required credentials/services before rerunning.
5. Record skipped network tests in the handoff.

## Integration Credentials, Cassettes, And Services

Symptoms:

- Missing environment variables such as provider API keys.
- Cassette not found, cassette mismatch, or VCR recording errors.
- Tests require Docker, local model servers, databases, browser services, or remote APIs.

Actions:

1. Do not invent credentials or run live provider calls by default.
2. Prefer unit tests and standard unit conformance classes for default verification.
3. If the user requests integration verification, list required env vars/services and run only the named subset.
4. Do not re-record cassettes unless the user confirms network access and intended cassette updates.

## Strict Markers And Strict Config

Symptoms:

- `PytestUnknownMarkWarning` becomes an error.
- Collection fails because a marker is not registered.
- Invalid pytest config fails before tests run.

Actions:

1. Inspect the owning package `pyproject.toml` for `[tool.pytest.ini_options]`.
2. Use only registered markers such as `requires`, `compile`, and `scheduled` when present.
3. Add new markers to the package config only if the package needs them and tests document their semantics.
4. Keep marker expressions simple, for example `-m "not scheduled"`, and avoid referencing undeclared markers.

## Optional `requires` Marker Skips

Symptoms:

- Tests are skipped with messages like `Requires pkg: ...`.
- HTML, NLP, tokenizer, or provider tests skip because optional dependencies are unavailable.

Actions:

1. Treat expected skips as acceptable when the optional dependency is unrelated to the change.
2. Install broader dependency groups only when the task needs those tests.
3. For text splitters, avoid pulling heavy NLP/model packages unless the modified splitter requires them.

## Syrupy Snapshot Failures

Symptoms:

- Snapshot assertion mismatch.
- Warnings about unused snapshots from `--snapshot-warn-unused`.
- Version metadata mismatch inside snapshot files.

Actions:

1. Inspect the diff to determine whether the serialized output change is intentional.
2. Do not run snapshot update flags automatically.
3. If intentional, ask the user before updating snapshots and rerun the narrow snapshot test.
4. For core version metadata, run the package's version check when available because it may validate snapshot-embedded version strings.

## Model Profile CLI Wrong `--data-dir`

Symptoms:

- No `profile_augmentations.toml` is found when one was expected.
- Generated `_profiles.py` appears in an unexpected location.
- The CLI warns about writing outside the current directory.
- Provider ID is not found in downloaded models.dev data.

Actions:

1. Point `--data-dir` at the provider data directory containing `profile_augmentations.toml`.
2. Run from `libs/model-profiles` for in-repo profile maintenance.
3. Confirm the provider ID matches the models.dev provider key used by the existing data files.
4. Approve external-directory writes only when the target is intentionally outside the current working directory.
5. Treat refresh as a network and file-mutating operation; skip it in no-network verification.

## Import Or Version Check Failures

Symptoms:

- `check_imports.py` prints a file and traceback.
- `lint_imports.sh` reports a disallowed import.
- `check_version.py` reports mismatched package metadata, version file, or snapshot version.

Actions:

1. Fix the underlying import direction, package export, or version artifact rather than suppressing the script.
2. Keep core/lower-level packages from importing higher-level packages unless the local script explicitly allows the import.
3. Rerun the exact failing script from the package directory.
4. If the mismatch is release-management related and outside the task, report it as a blocker instead of changing versions opportunistically.
