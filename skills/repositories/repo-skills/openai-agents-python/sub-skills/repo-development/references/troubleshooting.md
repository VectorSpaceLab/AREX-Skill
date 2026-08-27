# Repo Development Troubleshooting

Use this matrix when local repository development, verification, or maintainer handoff fails.

## Quick Triage

| Symptom | Likely cause | First checks |
| --- | --- | --- |
| `uv` command not found | Development toolchain missing. | Install or expose `uv`, then run `make sync`. |
| `agents` imports from the wrong place | Wrong environment or stale editable install. | Use `uv run python -c "import agents; print(agents.__file__)"` and avoid system Python for repo commands. |
| `pip check` or dependency resolution fails | Optional extras, stale lock/environment, or index constraints. | Run `make sync`; inspect `pyproject.toml` changes and `uv.lock` expectations. |
| Snapshot test fails | Intentional output change or unexpected behavior regression. | Inspect the inline diff; only run snapshot fix/create after confirming the change is intended. |
| Ruff format/lint fails | Formatting, import order, pyupgrade, bugbear, or comprehension lint issue. | Run `make format` for safe fixes, then `make lint`. |
| Mypy or pyright fails | Type signature drift, generic mismatch, optional import assumptions, or missing stub behavior. | Run the narrower failing checker with the reported file, then `make typecheck`. |
| Docs build fails | Stale API reference stub, invalid MkDocs nav, bad snippet, or generated docs mismatch. | Run `make build-docs`; verify changed docs against source signatures. |
| Optional service test fails | Missing Docker, browser/audio stack, database, provider key, or hosted service. | Confirm whether the test is optional/service-backed before treating it as product failure. |
| Dirty tree blocks confident handoff | Formatter, snapshot, docs generation, or helper changed files. | Inspect `git diff` and `git status`; separate intended changes from generated artifacts. |
| `RunState` deserialization rejects schema | Unsupported/newer schema version or missing migration/default. | Check `CURRENT_SCHEMA_VERSION`, `SCHEMA_VERSION_SUMMARIES`, and legacy-read tests. |

## UV and Environment Issues

The repository expects Python commands through `uv` so dependencies, optional groups, and workspace paths match project configuration.

Recovery sequence:

1. Confirm `uv` is available.
2. Run `make sync` after dependency or environment drift.
3. Run import probes through `uv run`, not bare `python`.
4. If imports resolve to a global package, recreate or resync the project environment.
5. If optional extras are needed, confirm the relevant extra is installed before running that test subset.

Base install imports `agents`, `RealtimeAgent`, `RealtimeRunner`, `RealtimeSession`, and sandbox base classes. Voice imports require the voice extra.

## Snapshot Failures

Inline snapshots live inside test files. A failing snapshot is either expected output drift or a bug.

Safe handling:

1. Read the diff and identify the product behavior that changed.
2. If the new output is wrong, fix code instead of snapshots.
3. If the new output is intended, run `make snapshots-fix` or `make snapshots-create`.
4. Inspect mutated test files.
5. Rerun `make tests` after snapshot updates.

Do not use snapshot updates as a broad repair tool after unrelated failures.

## Typecheck and Lint Failures

Ruff is configured for formatting, import sorting, pycodestyle, pyflakes, bugbear, comprehensions, and pyupgrade. Mypy is strict, and pyright has a dedicated config.

Useful sequence:

```bash
make format
make lint
make typecheck
```

If `make typecheck` fails after parallel execution, run the failing checker directly through its make target (`make mypy` or `make pyright`) to get a cleaner error stream.

Common root causes:

- New optional field lacks explicit type.
- Public dataclass default is mutable or inserted in a compatibility-sensitive position.
- Test helper uses untyped call shapes that strict mypy rejects.
- Optional extras are imported without existing ignore/guard patterns.
- A compatibility shim returns `Any` where a generic type is expected.

## Docs Build Failures

`make build-docs` runs reference-file generation before MkDocs build. Failures often come from:

- `mkdocs.yml` nav entry pointing at a missing file.
- Generated API ref stub missing for a new public module.
- Markdown syntax or admonition indentation problems.
- Docs snippet using a stale API signature.
- Plugin/import errors caused by source code or dependency changes.

Recovery:

1. Run `make build-docs` from the repo root.
2. If reference stubs are generated, inspect them before committing.
3. Verify runnable snippets against current source signatures.
4. Do not patch generated translation files to fix English-source docs build failures.
5. Use full translation build only when translation maintenance is in scope.

## Optional Service and Integration Tests

The test tree includes areas that may need optional extras or local services. Examples include sandbox backend providers, Docker-based flows, database session backends, realtime/voice surfaces, browser/audio dependencies, and provider-specific behavior.

Handling rules:

- Prefer base-install unit tests first.
- If a test fails because an optional service is unavailable, record it as an environment skip/failure in the handoff.
- Do not weaken product code or tests just to pass in an environment lacking the required service.
- When changing optional integration code, document which service-backed tests were run and which were not available.

## Dirty Tree and Provenance Issues

Before final handoff, inspect changed files. Common accidental changes include:

- Ruff formatting across unrelated files.
- Snapshot updates outside the intended behavior area.
- Generated docs reference stubs from `make build-docs`.
- Local environment files.
- Review/test artifacts placed in runtime skill or source directories.

Keep runtime code/docs changes separate from review artifacts. If a generated file changed unexpectedly, decide whether it belongs in the task or should be reverted before handoff.

## RunState Schema Version Mismatch

Failure modes:

- Import-time assertion because `CURRENT_SCHEMA_VERSION` lacks a summary entry.
- New `to_json()` emits a shape that `from_json()` cannot read.
- Legacy payloads lack a newly required field.
- Nested agent/tool/sandbox state omits new serialization data.
- Older SDK rejects a newer `$schemaVersion`, which is intentional fail-fast behavior.

Recovery checklist:

1. Add or correct the chronological `SCHEMA_VERSION_SUMMARIES` entry.
2. Ensure `SUPPORTED_SCHEMA_VERSIONS` includes only intended readable versions.
3. Add defaults/migrations for older payloads when released snapshots remain supported.
4. Add a focused new-version round-trip test.
5. Add a legacy-read test for each changed old-payload behavior.
6. Include nested state cases if the new field appears in tool approvals, agent-as-tool state, sandbox state, trace state, session persistence, or generated items.

## Public API Positional Regression

Symptoms:

- Compatibility tests fail after adding a dataclass field.
- A value passed positionally binds to the new field instead of the old target.
- Users would need to rewrite released positional calls.

Recovery:

1. Move the new optional field to the end of the public field order when possible.
2. If the new field must appear earlier internally, add an explicit compatibility layer and preserve old public positional meaning.
3. Add a regression test that calls the old positional pattern.
4. Prefer keyword arguments in new repo call sites.

## PR Summary or Verification Omitted

If final handoff is blocked because mandatory policy steps were missed:

- For runtime/test/example/build-config changes, run or explicitly report inability to run `make format`, `make lint`, `make typecheck`, and `make tests` in order.
- For behavior-impacting docs, report docs build and relevant source/snippet verification.
- For eligible changes, prepare the PR draft summary block before final response.
- If policy cannot be satisfied due to environment limits, state exactly what failed and what remains for a maintainer to run.
