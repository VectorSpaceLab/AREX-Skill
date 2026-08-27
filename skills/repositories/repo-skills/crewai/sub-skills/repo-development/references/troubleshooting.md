# Repo Development Troubleshooting

Use this matrix when repository-maintenance work fails or when a proposed change risks docs snapshots, workspace pins, slow tests, import-mode surprises, or release-state mutation.

| Symptom | Likely cause | Safe response |
| --- | --- | --- |
| A docs PR edits `docs/v...` files. | Frozen release snapshots were edited during normal development. | Move the content change to `docs/edge/<lang>/...`; revert frozen snapshot edits unless this is an explicit release-cut docs-freeze PR. |
| A docs PR deletes or renames a file under `docs/images/`. | Attempted replacement of a shared image asset. | Restore the original asset, add a new image filename, and update only Edge MDX references to the new file. |
| `docs/docs.json` link checks fail after adding a page. | New Edge page was not added to navigation, path prefix is wrong, or a redirect points to a stale/default path. | Ensure Edge paths use `edge/<lang>/...`; for release-versioning changes, validate with devtools docs versioning tests. |
| `mintlify broken-links` is unavailable. | Mintlify CLI is not installed in the environment. | Report the skipped docs-link check and still validate file paths/navigation manually; do not install global tooling unless user approves. |
| A root pytest run takes too long. | The root suite covers multiple packages with xdist, timeouts, network blocking, and many integration-like tests. | Stop broad escalation and choose focused test files from [testing.md](testing.md) or the native test selector. |
| Tests pass locally when run one way but fail under root pytest. | Root pytest uses `--import-mode=importlib`, strict asyncio, `--block-network`, and package testpaths. | Re-run the focused target through the root command shape with explicit paths; avoid changing pytest config unless the task is about test infrastructure. |
| Devtools tests are not discovered by a root `pytest` run. | Root `testpaths` omit `lib/devtools/tests`; devtools has its own package-local pytest config. | Run `uv run pytest lib/devtools/tests/test_docs_versioning.py -q` or `uv run pytest lib/devtools/tests/test_toml_updates.py -q` explicitly. |
| Ruff unexpectedly modifies files. | Root ruff config has `fix = true`. | Use `uv run ruff check --no-fix ...` for diagnostics; run fix mode only when requested. |
| Mypy misses test files or templates. | Root mypy excludes templates and test directories. | Use pytest and ruff for tests/templates, and mypy for package source paths. |
| Workspace package pins drift after a version bump. | A workspace member was not included in dependency rewrite logic or exact internal pins were not updated together. | Validate with `lib/devtools/tests/test_toml_updates.py`; ensure all workspace member package names are covered and internal `crewai*` pins align. |
| A freeze script creates `docs/v<X.Y.Z>/` unexpectedly. | Release freeze tooling was run outside release-cut context. | Stop, inspect changes, and revert unless explicitly authorized; use tests for versioning logic instead of freeze scripts. |
| Freeze rejects `v1.15.0`, `1.15`, or `1.15.0a1`. | Freeze expects a plain stable `X.Y.Z` version string. | Use stable release version format only in release-cut context; for prerelease logic, test lower-level version helpers rather than freezing docs. |
| A docs-generation helper asks for OpenAI credentials or makes LLM calls. | `crewai_devtools.docs_check` includes LLM-backed docs analysis/generation/translation behavior. | Treat it as credential-bound maintainer tooling; do not run by default as validation. |
| A CLI validation command executes user project code. | Commands like `crewai run`, `train`, `test`, `replay`, `chat`, and checkpoint resume can execute local Python, tools, callbacks, LLMs, or mutable state. | Prefer help output and CLI unit tests; run execution commands only after inspecting the project and getting approval. |
| A tool or integration test attempts network access. | Some official tools wrap web, cloud, browser, database, or hosted services. | Keep root `--block-network` behavior, choose mocked/keyless tests, or skip with a clear credential/network note. |

## Recovery Playbooks

### Frozen Docs Were Edited

1. Identify all files under `docs/v...` in the change.
2. Move intended content changes to the matching `docs/edge/<lang>/...` page if the change is valid for current docs.
3. Revert frozen snapshot edits.
4. Run docs link validation if tooling is available.
5. Mention that frozen snapshots are release artifacts and are not patched during normal development.

### Docs Image Was Removed or Renamed

1. Restore the removed/renamed asset path so old snapshots remain valid.
2. Add a new asset under `docs/images/` if the visual needs replacement.
3. Update only Edge MDX references to the new asset.
4. Run docs link checks or static path checks.

### Broad Tests Are Too Slow

1. Use the changed paths to map to a package and capability area.
2. Run a focused pytest file or selected tests first.
3. Add `ruff check --no-fix` on the changed source paths.
4. Escalate to package-level or root-level tests only if focused checks pass and the change spans packages.

### Import-Mode Confusion

1. Reproduce with explicit test file paths through the root pytest command shape.
2. Check for assumptions about package-relative imports, current working directory, or test package layout.
3. Avoid adding `sys.path` hacks or changing root `--import-mode=importlib` unless the task is explicitly about test infrastructure.

### Workspace Pins Drift

1. List the workspace member package names: `crewai`, `crewai-cli`, `crewai-tools`, `crewai-files`, `crewai-core`, `crewai-devtools`.
2. Confirm internal exact pins are updated together where present.
3. Run the devtools TOML update tests.
4. Avoid changing one package pin without checking dependent package manifests and template install commands.

### Release Freeze Ran Accidentally

1. Stop before running any further release automation.
2. Inspect for new or modified `docs/v<X.Y.Z>/` snapshots and `docs/docs.json` changes.
3. Revert accidental snapshot/navigation/redirect changes unless the user confirms release-cut context.
4. Replace validation with `uv run pytest lib/devtools/tests/test_docs_versioning.py -q`.

## Prevention Checklist

- For docs: Edge only, images append-only, frozen snapshots immutable.
- For tests: focused first, broad later, no live credentials/network by default.
- For ruff: add `--no-fix` unless applying changes is intended.
- For devtools: test helper functions; do not run release/freeze commands casually.
- For CLI: prefer help and unit tests before commands that execute project code.
