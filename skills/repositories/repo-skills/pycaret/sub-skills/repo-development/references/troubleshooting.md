# Troubleshooting

This reference covers predictable contributor and maintainer failures. It avoids machine-specific paths; run commands from the repository root unless a command explicitly changes directories.

## `uv sync` or imports fail

Symptoms:

- `ModuleNotFoundError: pycaret` or `pycaret_server` after sync.
- `uv run --package pycaret-server ...` cannot find the package.
- Tests import an installed PyPI version instead of the workspace source.

Actions:

```bash
uv python install 3.13
uv sync --all-packages --all-extras
uv run python -c "import pycaret; print(pycaret.__version__)"
uv run --package pycaret-server python -c "from pycaret_server import __version__; print(__version__)"
```

If imports still resolve incorrectly, check that you are at the monorepo root and that `packages/engine` and `services/api` are workspace members in root `pyproject.toml`. Do not install broad unrelated extras to fix a path issue.

## Ruff or formatting failures

Run the same scope CI uses:

```bash
uv run --with ruff ruff check packages/engine services/api
uv run --with ruff ruff format --check packages/engine services/api
```

If formatting fails and the change is in scope:

```bash
uv run --with ruff ruff format packages/engine services/api
uv run --with ruff ruff check packages/engine services/api
```

Do not reformat excluded legacy paths or large unrelated files just because old pre-commit config mentions black/isort/flake8.

## Engine tests fail

First isolate:

```bash
uv run pytest packages/engine/tests/path_or_test.py::test_name -v
```

Common causes:

| Signal | Likely cause | Response |
| --- | --- | --- |
| Import of `pycaret.classification.setup` or implicit current experiment state fails | Test or feature is trying to restore 3.x functional API | Update to OOP `ClassificationExperiment(...).fit(data)` or reject restore request. |
| Missing `pyod`, `sktime`, `statsmodels`, `pmdarima`, `shap` | Optional task/interpret extra not installed | Install/select the relevant extra for that test, or narrow to core tests. Do not claim optional coverage from a core-only env. |
| Plot image export fails | `kaleido`/`pycaret[export]` missing | For figure-return tests, avoid static export; for export tests, install export extra. |
| Unknown model id | Registry/model id mismatch | Use `pycaret.api.list_models(task)` or task-specific registry to find valid ids. |
| Golden notebook path breaks | Public workflow regression | Treat as high priority; do not adjust notebooks to hide an engine bug. |

For behavior changes, tests should assert typed result fields, events, metrics shape, and fitted pipeline behavior rather than legacy internals.

## Backend tests or migrations fail

Run a focused test first:

```bash
uv run --package pycaret-server pytest services/api/tests/ -q -k "<area>"
```

Migration conflict checklist:

1. Confirm the model change exists in `services/api/pycaret_server/db/models.py`.
2. Inspect the Alembic version file for the intended columns/indexes/constraints.
3. Confirm `down_revision` matches the current head chain.
4. Avoid destructive data drops unless explicitly approved.
5. If bootstrap tests fail with missing tables, inspect dev auto-migrate/stamping logic before blaming route code.

Frequent server signals:

| Signal | Likely cause | Response |
| --- | --- | --- |
| `OperationalError: no such table` | Migration not applied or bootstrap stamped incorrectly | Run/inspect Alembic migration and bootstrap path. |
| 401/403 in tests | Missing auth fixture, role guard, or API-key header | Verify roles and auth dependency, not just response body. |
| `PYCARET_SECRETS_KEY` warning | Dev mode generated ephemeral Fernet key | Accept for isolated tests; for persistent manual runs set a stable key. |
| Encrypted secret cannot decrypt after restart | Key rotated or volume did not persist | In ops contexts inspect persisted key handling; for tests use deterministic settings. |
| LLM route imports provider directly | Provider abstraction bypassed | Move provider-specific imports under `pycaret_server/llm/providers/`. |

## Web UI checks fail

Run the full local UI gate:

```bash
cd apps/web
npm run typecheck
npm run lint
npm test
npm run build
```

Common failures:

| Signal | Likely cause | Response |
| --- | --- | --- |
| TypeScript import error with `verbatimModuleSyntax` | Value import used for a type | Change to `import type`. |
| ESLint warnings fail build | `--max-warnings 0` | Fix warnings; do not suppress globally. |
| Component test cannot find text because it appears twice | Ambiguous fixture names or query | Use distinct fixture names and semantic queries. |
| Form hardcodes engine params/models | Violates introspection-driven UI | Move metadata to backend/introspection; keep UI generic. |
| Route builds but 404s at runtime | Missing `App.tsx` route or Layout/nav mismatch | Update route table, typed links, and tests together. |

## Optional dependencies and backend limitations

Verified source facts for this generated skill selected CPU as the required backend. CUDA hardware may be visible in some environments but is not required for repo-development validation.

- Do not require CUDA to prove maintainer workflows.
- Do not add GPU-specific dependencies to engine/server core for a contributor task.
- If a future task explicitly changes GPU/distributed behavior, route operational setup to `platform-operations` and engine algorithm details to `engine-workflows`.

## Secret scanner failures

Use the bundled scanner when outside the original source tree:

```bash
bash skills/disco/pycaret/sub-skills/repo-development/scripts/check_secrets.sh --root .
```

If it reports a secret:

1. Remove the value from source and rotate the credential if it was real.
2. If it is a legitimate fixture, add `# pragma: allow-secret` to that exact line and explain why in the PR.
3. If an entire generated/test fixture file must be excluded, use a local allowlist file (`scripts/.secrets-allowlist`) with one path/glob per line.
4. Re-run the scanner.

Do not weaken scanner patterns to make a PR pass without explaining the false positive.

## Stale docs or path mismatches

Historical docs may mention old flat paths such as `tests/` or old version strings. Prefer current source and CI when conflicts appear:

- Engine tests: `packages/engine/tests/`.
- Server tests: `services/api/tests/`.
- Web app: `apps/web/`.
- Site app: `apps/site/`.
- Engine package metadata: `packages/engine/pyproject.toml`.
- Workspace metadata: root `pyproject.toml`.

If stale docs caused confusion and the fix is in scope, update docs and add a `DOCS` release-note entry.

## Release prep failures

| Step | Failure | Response |
| --- | --- | --- |
| Open Approved issues exist | Release not ready | List them and ask maintainer whether they block the release. |
| Version mismatch | Package metadata and `__version__` differ | Maintainer-owned version bump required; do not silently change versions. |
| Missing changelog entry | Release docs incomplete | Draft/update only with maintainer approval. |
| Notebook execution fails | Public tutorial path broken or env missing extras | Reproduce with full extras; fix engine/notebook as appropriate. |
| Site build fails after API change | API tree/content sync stale | Run `npm run gen:api`/`npm run sync` in `apps/site` and inspect generated diff. |
| Release workflow smoke install fails | Packaging/dependency metadata issue | Fix package inclusion or dependency declarations; do not bypass smoke. |

## Issue triage false positives

The issue classifier is heuristic. It may mark a recent issue `out_of_scope` because a body includes a pip freeze with killed packages. Confirm title/body context manually.

- Strong signal: killed feature in the title or requested behavior.
- Weak signal: killed package only in environment dump.
- If adjacent to a killed feature, ask maintainer whether the new request is truly distinct.

## Generated skill tree validation

When editing the generated repo skill tree, run:

```bash
python skills/disco/pycaret/sub-skills/repo-development/scripts/verify_skill_tree.py \
  skills/disco/pycaret
```

It checks SKILL.md frontmatter basics, public absolute checkout path leaks, and Markdown links that point outside the generated skill tree. It is a runtime helper for future agents, not a replacement for the final verification workflow.
