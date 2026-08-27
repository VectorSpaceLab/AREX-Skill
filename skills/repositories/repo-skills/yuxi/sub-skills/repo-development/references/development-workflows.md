# Development workflows

This reference maps the maintainer surfaces owned by `repo-development` and the safest way to validate them.

## Monorepo map

| Area | What lives there | Usual edit loop | Safe check |
| --- | --- | --- | --- |
| `backend/` | FastAPI + LangGraph backend package and backend tests | Edit `server/` or `package/`, then rerun the smallest Python check that covers the change | Package import or backend pytest |
| `web/` | Vue 3 + Vite frontend | Edit `src/`, then rerun the relevant unit or lint command | Frontend unit tests or ESLint check |
| `packages/yuxi-cli/` | Standalone Python CLI package | Edit `src/` or `tests/`, then rerun CLI pytest | `uv run --group test pytest` |
| `docs/` | VitePress docs and maintainer guides | Edit the page, then rebuild docs if the page is user-visible | `cd docs && pnpm install && pnpm build` |
| `scripts/` | Human-run maintenance helpers | Update only when a script is safe enough to be bundled or clearly documented | Validate the script itself with a dry run or explicit usage |
| Docker Compose | Canonical dev/runtime topology | Change only when service topology, health checks, or image wiring change | Inspect compose files and service logs |

## Hot-reload loop

1. Start the stack manually with `docker compose up -d` when the task needs live services.
2. Check the service state with `docker ps`.
3. Read the latest logs instead of guessing:
   - `docker logs api-dev --tail 100`
   - `docker logs worker-dev --tail 100`
   - `docker logs web-dev --tail 100`
4. Edit the mounted source tree.
   - Backend API and worker hot-reload from `backend/server` and `backend/package`.
   - Frontend hot-reloads from `web/src`, `web/public`, `web/index.html`, and `web/vite.config.js`.
5. Re-run only the smallest relevant check.

## Edit boundaries

- Keep route code thin and put business logic in the service or repository layer that already owns it.
- Keep frontend API clients under `web/src/apis` rather than scattering ad hoc request code.
- Put tests under the layer they actually validate: backend unit, backend integration, backend e2e, CLI tests, or frontend unit tests.
- If a change is user-visible, pair it with the matching docs or changelog update instead of leaving the repo half-documented.
- Do not widen the edit just because the surrounding file has unrelated cleanup opportunities.

## Command matrix

| Need | Command | Prerequisites | Notes |
| --- | --- | --- | --- |
| Backend package import smoke | `cd backend && uv run --group test pytest test/unit/test_package_import.py` | Python 3.12+ and backend Python dependencies | No live services needed; this is the fastest check for package import drift. |
| Backend unit tests | `docker compose exec api uv run --group test pytest test/unit -m "not slow"` | Running API container | Use for pure backend logic that does not need real services. |
| Backend integration tests | `docker compose exec api uv run --group test pytest test/integration` | Running Compose stack | Requires real API and backing services; the helper script will not start them. |
| Backend e2e tests | `docker compose exec api uv run --group test pytest test/e2e -m e2e` | Running Compose stack | Use for full-path regressions that need the live stack. |
| CLI pytest | `cd packages/yuxi-cli && uv run --group test pytest` | Python 3.12+ and CLI dependencies | Pure package test suite; no Docker services required. |
| Frontend unit tests | `cd web && pnpm test:unit` | Node + pnpm dependencies | Pure frontend check; keep it focused to the changed UI behavior. |
| Frontend lint check | `cd web && pnpm exec eslint . --cache --max-warnings 0` | Node + pnpm dependencies | No-write lint check. The repo's `pnpm run lint` target auto-fixes, so use it only when you want rewrites. |
| Repo-wide format | `make format` | Backend and frontend toolchains | Mutates files. Use only when you intend to accept formatting edits. |
| Docs build | `cd docs && pnpm install && pnpm build` | Node toolchain | Run when docs pages or nav change. |

## Command selection rules

- Use the import smoke test for packaging drift, not as a substitute for runtime or integration coverage.
- Use service-required tests only when the stack is already running and the change truly depends on it.
- Do not use the Compose-backed tests to validate a change that only needs a package import or a unit test.
- Do not let a broad cleanup request turn into a repo-wide format unless the user asked for it or the diff truly needs it.

## Files that often need coordinated updates

- Backend version alignment usually spans the backend package, the workspace manifest, the frontend package metadata, and Docker image tags.
- User-facing release notes belong in `docs/develop-guides/changelog.md`.
- New formal docs belong in the VitePress nav in `docs/.vitepress/config.mts`.
- PR-ready changes should be checked with `git diff --check` before committing.

## Notes on the repository lint path

The repository's maintained lint command currently mixes check and fix behavior because the frontend lint script runs ESLint with `--fix`. That is convenient for repair passes, but it is not a pure validation step. For a no-write gate, prefer the explicit ESLint command above or the bundled helper.
