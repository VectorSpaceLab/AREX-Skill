# Troubleshooting

This page is for safe maintainer troubleshooting inside a target `gptme` checkout. It avoids publishing, credentials, or full-suite brute force.

## First check: are you in the checkout?

Most commands in this sub-skill assume the **target gptme repository root**.

If a command seems to "not find" files, make sure you are not accidentally standing in the generated skill tree.

## Branch / commit / PR policy problems

Symptoms:

- a branch is on `master`
- a commit message does not match Conventional Commits
- too many files were staged at once
- a PR mixes unrelated cleanup with feature work

Fix:

- create a new branch with the repository's prefix convention (`feat/`, `fix/`, `docs/`, `refactor/`)
- restage only the intended files with explicit `git add <path>`
- rewrite the commit message before pushing
- open the PR after the branch is clean

## Dependency and project-metadata problems

Symptoms:

- `poetry.lock` is out of sync
- package version metadata feels inconsistent
- console scripts are present in `pyproject.toml` but not behaving as expected in the installed environment

Use the bundled project-health helper from this sub-skill directory, or use the linked script path explicitly:

```bash
python scripts/check_python_project_health.py --root "$TARGET_GPTME_CHECKOUT"
```

That helper checks the target checkout metadata without contacting external services.

Typical maintainer follow-up in the checkout:

- reinstall the editable package if the installed entry points are stale
- verify the script target module exists under `gptme/`
- rerun the helper after editing `pyproject.toml` or `poetry.lock`

## RST and docs problems

Symptoms:

- nested bullets render oddly
- a docs page fails late in `make docs`
- a small `.rst` edit breaks formatting in CI

Use the bundled RST helper from this sub-skill directory, or use the linked script path explicitly:

```bash
python scripts/check_rst_patterns.py "$TARGET_GPTME_CHECKOUT/docs"
```

Then, if the docs change is non-trivial, run `make docs` in the target checkout root.

Common mistake:

- inserting a nested list immediately after a parent bullet without a blank line

## Test selection problems

Symptoms:

- a change touches both backend and Web UI, but only one side was checked
- a test command is too broad and pulls in slow or API-backed tests
- a file-level change needs a smaller command set

Use the bundled focused selector helper from this sub-skill directory, or use the linked script path explicitly:

```bash
python scripts/suggest_focused_tests.py --root "$TARGET_GPTME_CHECKOUT" <changed-path> ...
```

Practical examples:

- `gptme/server/api_v2_sessions.py` + `webui/src/...` → run the focused server tests and the matching Web UI command, not `make test` alone.
- docs-only change → start with the RST helper, not Python tests.
- `pyproject.toml` / `poetry.lock` change → start with the project-health helper, then the narrowest relevant tests.

Marker reminders:

- default fast tests usually exclude `slow` and `requires_api`
- `make test SLOW=1` broadens the suite, but it is still not a substitute for choosing the smallest useful subset first

## Web UI problems

Symptoms:

- `webui` unit tests pass, but the server still serves the wrong bundle
- the release artifact is missing the modern UI
- a change updates one markdown path but not the other
- a conversation view renders stale or inconsistent metadata

Fix order:

1. Rebuild the frontend: `cd webui && npm run build`
2. Rebundle: `make bundle-webui`
3. Recheck packaging: `make validate-release-package` from the checkout, or run the bundled checker from this sub-skill directory: `python scripts/check_release_package_contents.py "$TARGET_GPTME_CHECKOUT"/dist/*.whl "$TARGET_GPTME_CHECKOUT"/dist/*.tar.gz`
4. Re-run the focused server tests plus `cd webui && npm test`

If the issue involves rendering or metadata, revisit the two-path rendering and SSE data-flow notes in [webui-development.md](webui-development.md).

## Release/package problems

Symptoms:

- wheel or sdist is missing `gptme/server/webui-dist/index.html`
- the archive has `index.html` but no `assets/` payload
- a release artifact was built before the frontend bundle was copied into the package tree

Use the bundled release-package checker from this sub-skill directory, or use the linked script path explicitly:

```bash
python scripts/check_release_package_contents.py "$TARGET_GPTME_CHECKOUT"/dist/*.whl "$TARGET_GPTME_CHECKOUT"/dist/*.tar.gz
```

If that helper fails, the usual cause is an out-of-order build:

- `webui/dist` was not rebuilt
- `make bundle-webui` was skipped
- `poetry build` was run before the bundle step

## Performance / size regressions

Symptoms:

- imports got slower
- startup time regressed
- a change added a heavy dependency or unnecessary work at import time

Useful maintainer checks from the checkout root:

```bash
make bench-import
make bench-startup
make tiny
make metrics
```

These are diagnostic checks, not the default verification path.

## When to stop and escalate

If you are about to:

- publish a release
- use GitHub or package-manager credentials
- run a full suite just to compensate for missing scope

stop and switch to the appropriate maintainer or release workflow instead of guessing.
