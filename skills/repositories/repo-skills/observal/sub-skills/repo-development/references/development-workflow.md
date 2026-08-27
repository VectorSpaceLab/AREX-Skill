# Development workflow

This reference distills repository-wide contributor workflow from the repository guidance, setup notes, policy files, Makefile, package manifests, and review standard. It is self-contained: use original file names only as source-evidence labels, not as instructions to reopen them.

## Scope owned here

Repo-development owns:

- Contributor setup and local development loop.
- Make target selection and safe escalation from focused checks to full checks.
- Branch, commit, changelog, documentation, PR, AI-policy, and review readiness workflow.
- Cross-layer update planning: which tests/docs/skills/screenshots must accompany a CLI, server, web, harness, release, or compliance change.

Repo-development does not own detailed implementation in these layers:

| Layer | Owner | Route there when the main change is about |
| --- | --- | --- |
| CLI | `cli` | Typer command tree, CLI adapters outside general workflow, bundled command syntax. |
| Server | `server` | FastAPI routes, schemas, services, PostgreSQL/Alembic, ClickHouse migrations, jobs, auth/admin, insights. |
| Harness telemetry | `harness-telemetry` | Harness registry entries, CLI/server adapters, hook specs, session parsers, session push/reconcile. |
| Web | `web` | Vite/React/TanStack Router UI, TanStack Query hooks, auth storage, frontend types, Playwright screens. |

Use this reference around those owners to answer: “what else must I update, test, document, and disclose before this is PR-ready?”

## Repository markers and tool expectations

Use the bundled inspection helper to summarize the current checkout without modifying it:

```bash
python skills/disco/observal/sub-skills/repo-development/scripts/inspect_observal_repo.py --repo-root . --pretty
```

Expected signal: JSON reports present/absent markers such as `Makefile`, `pyproject.toml`, `observal-server/pyproject.toml`, `package.json`, `web/package.json`, Docker compose files, `tests/`, package-local test directories, repository scripts, and policy files.

Tool expectations distilled from setup and manifests:

| Tool | Expected use | Notes |
| --- | --- | --- |
| Python | Run CLI, server tests, repo scripts | Python 3.11+ is required by Python project metadata. |
| uv | Python package/test runner and CLI editable install | Prefer `uv tool install --editable .` for local CLI development. |
| Docker Engine + Compose v2 | Full local stack, service health, integration/E2E scripts | Use `docker compose`, not legacy `docker-compose`. |
| Node.js + pnpm | Web build, lint, Playwright | Use the package manifests as the source of truth for exact Node/pnpm constraints. |
| Git + GitHub CLI | Normal contribution flow and release tooling | Release preparation requires `git`, `gh`, and `uv`. |

If a setup document and a package manifest disagree, prefer the manifest for local command execution and note the discrepancy in the handoff.

## First-time local development loop

Use this sequence when the user asks how to get a development checkout ready:

```bash
make hooks
cp .env.example .env
make up
uv tool install --editable .
observal --version
observal auth login
observal auth status
```

Expected signals:

- `make hooks` installs pre-commit, commit-msg, and pre-push hooks and prints a success message.
- `make up` starts the Docker stack; all long-running services should be `healthy` or `running`, while the init container exits after migrations.
- `curl http://localhost/health` returns JSON with status `ok` after the stack is healthy.
- `observal --version` prints the installed CLI version from the editable package.
- `observal auth status` shows the configured server, authenticated account, and local session-delivery buffer state.

Default local demo accounts are seeded on first stack startup. Use them only for local development and never commit `.env` files or secrets.

## Choosing Make targets

Use Make targets for standard repo operations. Prefer the narrowest target that exercises the changed area.

| Situation | Target | Expected signal |
| --- | --- | --- |
| Show available documented targets | `make help` | Sorted target list with descriptions. |
| Start the local stack | `make up` | Docker services start; health can be checked with compose and `/health`. |
| Stop the stack | `make down` | Containers stop without deleting volumes. |
| Rebuild after normal backend/frontend/dependency changes | `make rebuild-fast` | Rebuilds API and web images, starts stack, waits for API health. |
| Rebuild after Compose topology/image/volume/network changes | `make rebuild` | Full stack rebuild and health wait. |
| Rebuild from scratch without Docker cache | `make rebuild-clean` | Destructive/no-cache rebuild; use only when cache/state is suspect. |
| Destroy volumes and reset all local data | `make reset` | Destructive reset; state and demo data are recreated. |
| Tail Docker logs | `make logs` | Last service logs stream. |
| Run default Python tests | `make test` | Runs root `tests/` from the server package context with xdist. |
| Run verbose Python tests | `make test-v` | Same suite with verbose output. |
| Lint Python | `make lint` | Ruff check exits 0. |
| Format Python | `make format` | Ruff format and auto-fix complete; inspect resulting diff. |
| Full pre-commit over all files | `make check` | All configured hooks pass; slower and broader than lint/test. |
| Install hooks | `make hooks` | Hooks installed for pre-commit, commit-msg, and pre-push. |
| Check Alembic migration chain | `make check-migrations` | Linear migration chain is reported OK. |
| Create new Alembic migration | `make new-migration MSG="describe change"` | New migration file appears in the Alembic versions directory; inspect before use. |
| Regenerate bundled Observal command reference | `make sync-skill` | Command reference is in sync or regenerated. |
| Release preview | `make release-preview` | Release notes preview renders without branch or PR creation. |
| Release PR preparation | `make release` | Interactive release flow creates branch/PR only after human confirmation. |

## Change-to-update matrix

Use this matrix when the user asks “which tests/docs/skills should I update for this change?”

| Change type | Update beside code | Focused checks before broad checks |
| --- | --- | --- |
| CLI command added/removed/renamed or flag semantics changed | Bundled CLI skill files and generated command reference; user docs/changelog if user-facing | Focused CLI tests, `make sync-skill`, command help check, then `make test` and `make lint`. |
| CLI behavior without command syntax change | CLI tests and docs/changelog if user-facing | Focused `observal_cli/tests/test_cmd_*.py` or root `tests/test_cmd_*.py`, then broad checks as needed. |
| Server route/schema/service behavior | Route/service tests, migration files if schema changes, user/admin docs and changelog if user-facing | Focused route/service tests, migration chain checks, then `make test`/`make lint`. |
| PostgreSQL schema | New Alembic migration; never edit an existing migration for a new change | Migration chain script plus focused tests that prove upgraded behavior. |
| ClickHouse schema | New SQL migration under the ClickHouse migration system; no runtime startup DDL | ClickHouse migration tests or focused service tests plus migration review. |
| Web UI or frontend API use | Centralized API types, API wrapper/query hook, screenshots for changed screens, changelog if user-facing | `cd web && pnpm build`; targeted Playwright only when UI flow or screenshot evidence is needed. |
| Harness support or telemetry delivery | Registry/adapters/hook specs/session parsers/tests; route to `harness-telemetry` | Harness registry/adapters/parser/session-delivery tests and helper checks from that sub-skill. |
| Release/compliance/SBOM/license work | Release manifest/notes/changelog/notices/VEX/license evidence as applicable | Preview/dry-run or read-only script first; inspect generated diff; run relevant policy checks. |
| Security-sensitive fix | Private disclosure process if not public; qualified security review; regression tests | Focused security regression tests, no public vulnerability detail unless already disclosed. |
| User-facing behavior | Changelog under `[Unreleased]`; docs or skill text where users rely on syntax | Focused behavior test plus docs/changelog review. |
| AI-assisted implementation | PR AI disclosure with tool/version; human review and test evidence | Human self-review of entire diff; normal tests still required. |

## Branch, commit, and PR workflow

Repository conventions:

1. Branch from current `main`; never commit directly to `main`.
2. Keep PRs focused on one coherent change. Split unrelated refactors, generated updates, and dependency changes unless required by the same change.
3. Rebase on latest `main` before PR readiness checks.
4. After rebase or amend, push with `--force-with-lease`, not plain `--force`.
5. Use Conventional Commits. Examples:
   - `feat(cli): add skill submit command`
   - `fix(telemetry): handle null span timestamps`
   - `docs: update setup guide`
6. Avoid fixup commits in final history. Amend small corrections into the relevant commit.
7. Add changelog entries under `[Unreleased]` for user-facing changes.
8. Fill every PR template section with concrete content; placeholders are not acceptable.

## AI policy obligations

AI tools may help write, refactor, review, test, and draft PR content only when an accountable human directs the work and owns the result.

Before a PR with nontrivial AI assistance is ready:

- A human has read the full diff.
- A human can explain every changed line and material design choice.
- The appropriate local checks have been run and reported.
- The PR explicitly labels AI use and includes tool name/version.
- Any generated PR text, comments, and review replies have been human-reviewed and approved.

Unattended agents independently choosing work, implementing it, and submitting a PR are not acceptable.

## Final PR readiness checklist

Before claiming completion or asking for review, report:

- Owning sub-skill/layer used for implementation.
- Focused tests run and exact expected signals observed.
- Whether `make test`, `make lint`, and `make check` were run; if not, why not.
- Whether Docker, Playwright, or live integration scripts were needed; if not, state that unit tests were hermetic and Docker/E2E was intentionally skipped.
- Docs, changelog, bundled skills, screenshots, release notes, or compliance artifacts updated or deemed unnecessary.
- SPDX/license status for new files and any copied/adapted material.
- AI assistance disclosure status.
- Known gaps, risk areas, and review questions.
