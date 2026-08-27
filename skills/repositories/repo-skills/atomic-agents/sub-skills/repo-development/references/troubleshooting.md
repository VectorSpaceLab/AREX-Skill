# Repo Development Troubleshooting

## Workspace commands fail

**Symptom:** `uv sync`, `uv run`, or a repo test command fails immediately.

**Cause:** the local environment is missing a dependency, the active Python version is too old, or the checkout is dirty in a way that changes the build path.

**Fix:** verify the Python version from `pyproject.toml`, rerun the workspace sync, and narrow the command to the smallest relevant package or test file.

## Formatting or linting appears inconsistent

**Symptom:** black or flake8 reports style drift.

**Cause:** the command target list is incomplete or the repo was edited outside the expected package directories.

**Fix:** rerun the documented format/lint commands against all repo surfaces touched by the change.

## Docs build failure

**Symptom:** `cd docs && make html` fails.

**Cause:** the docs environment is missing Sphinx or one of the extension packages.

**Fix:** rebuild the workspace dependencies and inspect the docs-specific configuration before changing code.

## Release confusion

**Symptom:** a maintainer asks for release steps or version bumping.

**Cause:** the release helper is not a general runtime command.

**Fix:** treat release as a maintainer-only workflow and keep credentialed actions, push steps, and publication steps out of public runtime instructions unless explicitly requested.

## Do not over-verify

- For ordinary repo edits, prefer focused checks over full-suite runs unless the changed surface requires broader coverage.
- Keep example execution and live provider calls out of ordinary development verification unless the task explicitly requires them.
