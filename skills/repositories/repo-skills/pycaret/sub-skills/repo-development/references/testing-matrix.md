# Testing Matrix

Choose the smallest validation that proves the touched surface, then broaden when the change crosses boundaries or affects public contracts.

## Fast selection guide

| Change | First checks | Broader checks before handoff |
| --- | --- | --- |
| Engine public API, task behavior, typed results, plots, persistence | `uv run pytest packages/engine/tests/ -q -k "<pattern>"` | `uv run pytest packages/engine/tests/ -q`; `uv run --with ruff ruff check packages/engine`; `uv run --with ruff ruff format --check packages/engine` |
| Engine dependency or packaging | Engine tests above; import smoke in a fresh uv environment if practical | CI-equivalent matrix is Ubuntu/Windows × Python 3.11/3.12/3.13; release workflow smoke installs the built wheel. |
| Backend route/model/migration/orchestrator | `uv run --package pycaret-server pytest services/api/tests/ -q -k "<pattern>"` | `uv run --package pycaret-server pytest services/api/tests/ -q`; Ruff on `services/api`; import/create_app smoke. |
| Alembic migration | Targeted migration/bootstrap test; inspect generated migration for destructive operations | Full server tests; verify dev auto-migrate behavior when the change touches bootstrap. |
| Web UI component/page/API client | `cd apps/web && npm test -- <test-or-pattern>` when a focused Vitest target exists | `cd apps/web && npm run typecheck && npm run lint && npm test && npm run build` |
| Site/docs generation | `cd apps/site && npm run sync` or `npm run typecheck` depending on change | `cd apps/site && npm run build`; `uv run --with griffe python scripts/gen_api_tree.py` when API docs changed. |
| Notebooks | `uv run python scripts/build_notebooks.py` for generation-only changes | `uv run python scripts/build_notebooks.py --run` for release/nightly confidence. |
| Secrets or repo hygiene | `bash scripts/check-secrets.sh` or bundled `scripts/check_secrets.sh --root .` | Include in release/security-sensitive handoff; scan before pushing. |
| Cross-layer feature | Run the relevant subset in each touched layer | Engine + server + web full local checks matching CI. |

## Engine tests

The current source tree places engine tests under `packages/engine/tests/`. Use the package path from the repository root, not the older flat `tests/` examples in historical docs.

Common commands:

```bash
# Focused loop while editing one behavior.
uv run pytest packages/engine/tests/ -q -k "compare_models or my_test_name"

# Full engine suite.
uv run pytest packages/engine/tests/ -q

# One explicit test.
uv run pytest packages/engine/tests/test_e2e_oop.py::test_classification_e2e_oop -v

# Coverage when requested.
uv run pytest --cov=pycaret --cov-report=term-missing packages/engine/tests/

# Lint/format checks matching CI scope.
uv run --with ruff ruff check packages/engine
uv run --with ruff ruff format --check packages/engine
```

Write tests according to the behavior under change:

- Fast unit/shape tests for dataclasses, registry cards, error messages, config handling, and pure helpers.
- End-to-end task tests when a verb trains, predicts, persists, plots, or changes preprocessing/model selection.
- Do not test the removed 3.x functional API or module-level mutable state.
- Do not add tests for killed dependencies/features unless the test asserts they remain absent or rejected.
- Mark genuinely slow model-training tests with the existing `slow` marker if the surrounding suite uses it.

## Backend tests

Server tests live under `services/api/tests/` and use FastAPI TestClient plus isolated database fixtures.

Common commands:

```bash
# Focused server loop.
uv run --package pycaret-server pytest services/api/tests/ -q -k "runs or deployments"

# Full backend suite.
uv run --package pycaret-server pytest services/api/tests/ -q

# App import smoke.
uv run --package pycaret-server python -c "from pycaret_server.app import create_app; create_app(); print('ok')"

# Ruff checks for backend.
uv run --with ruff ruff check services/api
uv run --with ruff ruff format --check services/api
```

When adding a route:

- Test auth/permission behavior, success response shape, and at least one actionable failure.
- For DB-backed changes, test persistence and idempotency/rollback where relevant.
- For migrations, review generated files manually. Migrations are exempt from some Ruff rules but must still be safe and comprehensible.
- For LLM advisory routes, assert the advisory is persisted and the output envelope is advisory-only; do not let tests encode destructive side effects.

## Web UI checks

The web app lives under `apps/web/` and uses npm scripts from `apps/web/package.json`.

```bash
cd apps/web
npm run typecheck
npm run lint
npm test
npm run build
```

Useful focused commands depend on Vitest pattern support in the local npm/Vitest version. Prefer package scripts when unsure:

```bash
cd apps/web
npm test -- RunDetail
npm test -- src/components/MyComponent.test.tsx
```

Expectations:

- TypeScript strict mode must pass.
- ESLint runs with `--max-warnings 0`.
- Component tests should assert user-visible behavior and API payloads, not implementation details.
- UI forms that mirror engine setup/model metadata should rely on introspection payloads, not hard-coded duplicated lists.
- Run `npm run build` before handoff for route or bundling changes.

## CI workflows

`.github/workflows/test.yml` defines the main CI contract:

- `lint`: Ruff check and format check on `packages/engine services/api` with Python 3.13.
- `test`: Ubuntu and Windows across Python 3.11, 3.12, 3.13; runs `uv sync --all-packages --all-extras`, environment summary, engine tests, and server tests.
- `ui`: Node 22, npm install/ci, `typecheck`, `lint`, `test`, `build` in `apps/web`.
- `notebooks`: scheduled/manual only; executes canonical notebooks via `scripts/build_notebooks.py --run`.
- `ci-status`: aggregate required status for lint/test/ui.

`.github/workflows/release.yml` is tag/manual release automation:

- Builds `pycaret` with `uv build --package pycaret` from workspace root.
- Runs `twine check` on artifacts.
- Smoke-installs the built wheel on Ubuntu/Windows × Python 3.11/3.12/3.13.
- Publishes to PyPI/TestPyPI through trusted publishing. Do not trigger publishing unless the maintainer explicitly asks.

`.github/workflows/site.yml` builds the public site:

- Node 22 and Python 3.13.
- Generates API tree with griffe.
- Runs content sync, typecheck, and build.
- Deploys to GitHub Pages on `main` push or manual dispatch.

Manual maintenance workflows:

- `codeql-analysis.yml`: scheduled weekly Python CodeQL.
- `stale.yml`: manual stale sweep; not automatic during revamp.
- `lock_old_threads.yml`: manual lock old issues/PRs.

## Release-readiness validation

For a release-prep report, do not publish. Check:

```bash
gh issue list --repo pycaret/pycaret --label Approved --state open
uv run pytest packages/engine/tests/ -q
uv run ruff check . && uv run ruff format --check .
cd apps/site && npm run build
uv run --package pycaret-server python -c "from pycaret_server.app import create_app; create_app()"
```

Also confirm the current engine version in `packages/engine/pyproject.toml`, that `CHANGELOG.md` has the intended entry, and that `docs/revamp/release_notes_pycaret4.md` has a current session block.

## Interpreting failures

- A failing focused test introduced by your change blocks completion; fix it before marking done.
- If a broader suite fails in an unrelated pre-existing area, report the exact first failing test and evidence that your focused tests pass. Do not hide the failure.
- If optional dependencies are missing, either install the relevant extra for the selected workflow or narrow the test to the CPU/core path; do not claim optional-backend coverage from a CPU-only import.
- If CI and docs disagree on paths (`tests/` vs `packages/engine/tests/`), prefer current repository structure and CI.
