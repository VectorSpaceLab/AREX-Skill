# Repo Maintenance Troubleshooting

This guide covers failures contributors hit while editing Docling itself.

## Dependency or Extras Drift

Symptoms:

- Minimal installs unexpectedly import heavy ML, OCR, VLM, ASR, or rendering libraries.
- Full `docling` installs miss an extra that `docling-slim` supports.
- Optional backend tests fail because a dependency moved between extras.

Recovery:

1. Decide whether the dependency belongs in base requirements, a granular `docling-slim` extra, a convenience bundle, a dependency group, or a full-package re-export.
2. Keep model, VLM, ASR, GPU/MLX, remote-serving, and advanced backend dependencies optional unless there is an explicit package-design change.
3. Update full-package extras if a public backwards-compatible extra should still exist.
4. Check environment markers for Python version and platform-specific packages.
5. Run dependency lock/check validation after intentional dependency changes.

## CLI Docs Not Regenerated

Symptoms:

- CLI tests pass, but generated docs show old flags or defaults.
- Docs build includes stale command tables.

Recovery:

1. Run `make docs-render` after CLI command changes.
2. Confirm the CLI reference generator can import both `docling` and `docling-tools` command trees in the current environment.
3. Re-run docs build when navigation or generated pages changed.
4. Include generated artifact changes only when the repository expects them to be committed for the touched area.

## Optional Test Skips

Symptoms:

- Tests are skipped because OCR, ASR, VLM, external services, or model artifacts are unavailable.
- A targeted test unexpectedly downloads models on first use.

Recovery:

1. Check pytest markers before widening a test run.
2. Install only the extra needed for the behavior under test.
3. Treat model downloads, GPU/MLX requirements, service URLs, API keys, and ffmpeg requirements as environment prerequisites, not code failures.
4. Record skipped optional coverage in handoff notes.

Public troubleshooting facts to preserve in docs and tests:

- Some converter imports require model-foundation dependencies for specific modules.
- Model artifacts may download on first use unless prefetched.
- Remote services require explicit remote-service enablement for pipeline internals.
- Service client and remote CLI commands need a service URL and may need an API key.
- ASR requires the ASR extra and ffmpeg.
- VLM and advanced backends may require GPU/MLX/API access or model downloads.

## Reference Data Generation

Symptoms:

- Conversion tests fail because serialized Markdown, JSON, YAML, DocTags, DocLang, table output, or image references differ.
- A broad snapshot diff appears after a small backend change.

Recovery:

1. First determine whether behavior changed intentionally.
2. Narrow the failing fixture or backend test before regenerating data.
3. Use the project-supported reference-data generation mode only for intended output changes.
4. Review generated diffs carefully and avoid accepting unrelated churn.

## Mutating Validation Hooks

Symptoms:

- `make validate` changes files.
- A second validation run fails after hooks reformatted code.

Recovery:

1. Inspect hook-modified files.
2. Keep only relevant formatting or generated changes.
3. Rerun `make validate` until it exits cleanly or record the unresolved blocker.
4. Use `make check` when a read-only verification pass is needed.

## Package Collision Between `docling` and `docling-slim`

Symptoms:

- Installing both packages changes which `docling/` modules are imported.
- CLI scripts work in editable workspace installs but fail in wheel/tool installs.
- The full package unexpectedly contains Python source modules.

Recovery:

1. Keep `docling-slim` as the only package that ships the importable `docling/` module.
2. Keep the full `docling` package dependency-only for source modules.
3. Preserve identical CLI script declarations where needed for tool installers.
4. Test import and script availability from a clean install when packaging metadata changes.

## Line Limit Guard Failures

Symptoms:

- The maximum-line checker reports new files above the configured threshold.
- Existing long files appear as warnings from accepted debt patterns.

Recovery:

1. Split new source, test, or docs files before adding ignore entries.
2. Use warning-only ignore patterns only for deliberate existing debt.
3. Use silent ignore patterns only for generated fixtures, snapshots, vendored data, or bulk data.
4. Run the bundled `scripts/check_max_lines.py` from a checkout root to reproduce failures without depending on the original repo script.

## Tach Module Coverage Failures

Symptoms:

- A new Python module is not covered by a configured Tach module path.
- Tach reports duplicate or stale module entries.

Recovery:

1. Add a deliberate module-boundary entry when the new module is a new boundary.
2. Move the module under an existing boundary when that is the intended ownership.
3. Remove stale Tach entries when modules are deleted or renamed.
4. Run Tach checks again before broad validation.
