# Release And Docs

Use this reference for release preparation, engineering release notes, canonical notebooks, public docs/site generation, and maintainer-safe publishing boundaries.

## Release boundaries

Releases are maintainer-owned. A contributor or agent may prepare a readiness report, run tests/builds, and draft changelog text, but must not publish or tag without explicit maintainer direction.

Hard stops unless explicitly authorized:

- Do not modify package versions in `pyproject.toml` or `pycaret/__init__.py` as part of ordinary work.
- Do not run `uv publish`, `twine upload`, `npm publish`, or equivalent.
- Do not push tags or push directly to `main`.
- Do not rewrite old changelog entries.

## Version locations

The publishable engine version lives in:

- `packages/engine/pyproject.toml` (`[project].version`)
- `packages/engine/pycaret/__init__.py` (`__version__`) when present in the current source

The server package version lives in `services/api/pyproject.toml` and its package metadata. The verified source facts for this skill were `pycaret==4.0.0a8` and `pycaret-server==0.1.0a0`.

## Engineering release notes

`docs/revamp/release_notes_pycaret4.md` is the detailed engineering log. For non-trivial changes, append a concise bullet under the current session block with one or more tags:

`BREAKING`, `REMOVED`, `ADDED`, `CHANGED`, `FIXED`, `DEPRECATED`, `SECURITY`, `DOCS`, `BUILD`, `TESTS`, `DEPS`, `INTERNAL`.

Good entries include:

- Path or subsystem changed.
- User-visible impact or internal invariant.
- Test evidence or reason a check was not run.
- Dependency/version implications.
- Whether a migration or manual operator action is required.

Avoid dumping implementation details that the diff already shows. Record why the change matters.

## CHANGELOG.md

`CHANGELOG.md` is user-facing and summarized from the engineering log at release time. Do not hand-edit historical release entries. During release prep:

1. Read the current version from package metadata.
2. Confirm `CHANGELOG.md` has a top entry for that version.
3. Summarize `docs/revamp/release_notes_pycaret4.md` into user-facing categories.
4. Prominently call out breaking changes.
5. Keep older entries stable.

## Release process checklist

The documented release sequence is:

1. All tests green across the CI matrix.
2. Canonical notebooks regenerated and, for release confidence, executed:
   ```bash
   uv run python scripts/build_notebooks.py --run
   ```
3. Maintainer bumps versions together.
4. Generate the user-facing `CHANGELOG.md` entry from engineering notes.
5. Commit as `Release <version>`.
6. Maintainer signs/tags (`v<version>`) and pushes the tag.
7. Release workflow builds wheel/sdist, smoke-installs artifacts, and publishes via trusted publishing.
8. GitHub release uses the changelog entry.
9. Post-release dev-version bump when appropriate.

Contributors can run a non-publishing readiness report:

```bash
gh issue list --repo pycaret/pycaret --label Approved --state open
uv run pytest packages/engine/tests/ -q
uv run ruff check . && uv run ruff format --check .
cd apps/site && npm run build
uv run --package pycaret-server python -c "from pycaret_server.app import create_app; create_app()"
```

## Release workflow behavior

`.github/workflows/release.yml` is tag-triggered (`v*`) or manual. It:

- Reads the engine version from `packages/engine/pyproject.toml`.
- Runs `uv build --package pycaret` from the workspace root.
- Checks built distributions with Twine.
- Smoke-installs the wheel on Ubuntu and Windows across Python 3.11, 3.12, and 3.13.
- Smoke-imports PyCaret public surface including five task classes, `save_model`, `load_model`, `pycaret.api.list_models`, and `MemoryLogger`.
- Publishes to PyPI or TestPyPI via trusted publishing.

If smoke install fails, inspect dependency metadata and package inclusion first; do not bypass the smoke matrix.

## Canonical notebooks

`scripts/build_notebooks.py` generates the five canonical PyCaret 4 notebooks:

- `notebooks/01_classification.ipynb`
- `notebooks/02_regression.ipynb`
- `notebooks/03_clustering.ipynb`
- `notebooks/04_anomaly_detection.ipynb`
- `notebooks/05_time_series.ipynb`

Commands:

```bash
# Regenerate notebooks only.
uv run python scripts/build_notebooks.py

# Regenerate and execute; used by nightly/manual CI and releases.
uv run python scripts/build_notebooks.py --run
```

The notebooks are examples, not exhaustive tests. Keep them short, OOP-only, and aligned with the current public engine surface. If notebook execution fails because of optional time-series/anomaly dependencies, verify the environment was synced with the required extras.

## Public site/docs generation

The site workflow in `.github/workflows/site.yml` builds `apps/site/`:

```bash
cd apps/site
npm install
uv run --with griffe python scripts/gen_api_tree.py
node scripts/sync-content.mjs
npm run typecheck
npm run build
```

Package scripts expose the common shortcuts:

```bash
cd apps/site
npm run sync       # sync release notes/changelog content
npm run gen:api    # generate API tree with griffe
npm run typecheck
npm run build
```

When engine public modules/classes/functions change, regenerate or at least run the API-tree check so the site does not drift from source. When release notes or changelog change, run the sync/build path.

## Docs update rules

| Change | Docs likely required |
| --- | --- |
| Public engine API, task behavior, optional extra, or package install behavior | `docs/revamp/release_notes_pycaret4.md`, possibly `CHANGELOG.md` during release, site docs if user-facing. |
| Backend route or Control Plane behavior | Release notes; API docs/OpenAPI changes are code-driven; UI docs if user-facing. |
| UI surface/route | Release notes; site/user docs if the page is user-visible and shipped. |
| Architecture/dependency decision | New `docs/revamp/DECISIONS.md` ADR plus release notes. |
| Finished/deferred roadmap item | `docs/revamp/STATUS.md` and/or `ROADMAP.md`. |
| Removed feature/dependency | Release notes and, only with maintainer approval, `KILL_LIST.md` if it becomes settled policy. |

## Issue triage docs

The source script `scripts/triage_issues.py` reads a raw GitHub issue JSON dump and writes `docs/revamp/github_issues/triage.md` and `.json`. It is source-checkout-specific and mutates docs, so this generated skill bundles a safer standalone classifier:

```bash
python skills/disco/pycaret/sub-skills/repo-development/scripts/classify_issue_text.py --title "mlflow logging fails" --body "..."
```

Use the bundled classifier for a quick signal, then confirm against [kill-list-and-decisions.md](kill-list-and-decisions.md) before closing or implementing.

## Secret scanning

The repository script `scripts/check-secrets.sh` is safe to run manually and as a pre-push hook. This generated skill includes an adapted copy at `scripts/check_secrets.sh` with `--help` and `--root` so it can scan any checkout without depending on the original script location.

Common usage:

```bash
bash skills/disco/pycaret/sub-skills/repo-development/scripts/check_secrets.sh --root .
```

Allow a test fixture line only with a clear inline pragma:

```text
# pragma: allow-secret
```

Prefer rotating/removing credentials over allow-listing them.
