# Repo-development troubleshooting

Use this decision tree for repository-wide failures: setup, imports, CLI/API reachability, configuration, optional dependencies, harness telemetry workflow, pre-commit, release, scripts, and PR readiness. If the root cause belongs to a product layer, route to the owning sub-skill after collecting the safe evidence listed here.

## First triage

Run read-only checks first:

```bash
python skills/disco/observal/sub-skills/repo-development/scripts/inspect_observal_repo.py --repo-root . --pretty
git status --short
make help
```

Expected signals:

- Inspection JSON shows required markers present.
- `git status --short` explains whether generated files or local config are already dirty.
- `make help` lists documented targets and confirms you are at a repository root with the expected Makefile.

If a failure happens after a mutating script, inspect the diff before trying more commands:

```bash
git diff --stat
git diff --check
```

## Install and import failures

| Symptom | Likely cause | Safe recovery |
| --- | --- | --- |
| `uv: command not found` | uv is not installed or not on PATH | Install uv for the shell, restart shell, then rerun the exact command. |
| Python syntax/import errors on modern type hints | Python version below project minimum | Use Python 3.11+ for CLI/server and scripts. |
| `observal` command not found | CLI not installed as a tool | Run `uv tool install --editable .`; use `--reinstall` if entry points or project metadata changed. |
| CLI still shows old behavior after source edits | Editable install is stale because entry point/metadata changed | Run `uv tool install --editable . --reinstall`, then `observal --version` and focused command `--help`. |
| `ModuleNotFoundError` for server modules in direct pytest | Running from the wrong package context or missing extras | Run focused tests from `observal-server` and add required `uv run --with ...` packages. |
| `pyarrow` missing for migration/export/import paths | Optional migration dependency not installed | Use the migrate extra or add `--with pyarrow` to the focused `uv run` command. |
| Fuzz tests cannot import `atheris` | Fuzz dependency missing | Use `make test-fuzz` or add `--with atheris --with hypothesis` for focused fuzz commands. |
| Node/pnpm install fails due version mismatch | Active Node is older than package manifest requirements | Use the package manifest as source of truth and switch Node version before installing. |
| Playwright cannot find browsers | Browser binaries not installed for the active pnpm store | Run the web package install flow and Playwright browser install for the local environment. |

Do not solve import failures by broadening Python path globally, writing to real home directories in tests, or installing unpinned global packages when a focused `uv run --with ...` command is sufficient.

## CLI and API local-stack failures

| Symptom | Evidence to collect | Recovery |
| --- | --- | --- |
| `observal auth login` cannot reach server | `curl http://localhost/health`, `make logs`, Docker compose service status | Start or rebuild the stack; wait for API health before retrying. |
| Health endpoint is unavailable | Docker compose status and API logs | Use `make up` for first start, `make rebuild-fast` after app/dependency changes, or `make rebuild` after topology changes. |
| OpenAPI docs not reachable through `http://localhost/docs` | Direct API port status | Local docs are available on the direct API port; the load balancer blocks docs paths in production-like routing. |
| Authentication fails unexpectedly | `observal auth status`, Redis status/logs, demo account role used | Local demo accounts are seeded on first stack boot; Redis failure is auth-fail-closed by design. |
| CLI command path is uncertain | `observal --help` and subgroup `--help` | Confirm actual Typer path before documenting; `agent pull` is a subcommand, not a top-level command. |
| CLI syntax changed but skill docs/tests fail | Generated command reference is stale | Run `make sync-skill`, inspect bundled skill diff, and run focused sync tests. |

For server route internals, auth dependencies, GraphQL, migrations, data models, jobs, or insights behavior, route to `server` after gathering the failure signal. For Typer command tree or CLI bundled skills, route to `cli`.

## Configuration and local state failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Stack starts with wrong ports | Host port conflict or overridden env vars | Set port override env vars consistently before compose start; report chosen ports in handoff. |
| `.env` appears in staged files | Secret guard caught a local config file | Unstage/remove `.env`; only `.env.example` belongs in source control. |
| Logs directory permission errors in containers | Host log dir ownership/ACL issue | Run Make targets that call the host-dir preparation step rather than ad hoc compose commands. |
| State is inconsistent after many rebuilds | Old volumes or images | Try `make rebuild` first; use `make rebuild-clean` or `make reset` only after confirming destructive data loss is acceptable. |
| Runtime setting edited through env var has no effect | Setting is dynamic and stored in DB/cache | Use the project dynamic-settings path for runtime-tunable settings; route implementation details to `server`. |
| User configuration was touched by tests | Test did not sandbox HOME/USERPROFILE/cwd | Fix the test to use temp directories and rollback any accidental local config changes. |

Never commit private harness/editor directories, tool local state, worktrees, `.env`, or generated review artifacts.

## Optional dependency and package-manager failures

| Area | Common failure | Recovery |
| --- | --- | --- |
| Python optional migration/export | Missing `pyarrow` | Use the migrate extra or focused `uv run --with pyarrow`. |
| Fuzzing | Missing `atheris` or seed corpus assumptions | Use `make test-fuzz`; keep fuzz smoke tests separate from normal quick iteration. |
| LiteLLM/model catalogs | Network or upstream format change during snapshot refresh | Do not patch around blindly; inspect generated catalog diff and route behavioral impact to `server` or `harness-telemetry`. |
| Web build | TypeScript/Vite/ESLint errors | Route component/API hook details to `web`; repo-development only decides when build/E2E/screenshot evidence is needed. |
| Playwright | Local server not started or CI/baseURL mismatch | Run from the web package; local config starts Vite dev server, CI expects the Docker/LB base URL. |
| Release tooling | Missing `gh`, dirty tree, not on `main`, tags missing, unauthenticated GitHub CLI | Run `make release-preview` only after preflight is satisfied; do not start full release until human-approved. |

## Telemetry and harness workflow failures

Repo-development owns the contributor workflow, not harness implementation. Collect these safe signals, then route to `harness-telemetry` if the failure is deeper than local setup:

```bash
observal scan
observal doctor patch --all-harnesses
observal doctor
observal reconcile --dry-run
observal ops telemetry status
observal auth status
```

Expected signals:

- `scan` is read-only and reports installed harness configurations.
- `doctor patch` installs or updates managed telemetry hooks without wrapping MCP commands.
- `doctor` reports hook/config status.
- `reconcile --dry-run` shows sessions that would be backfilled without uploading them.
- `ops telemetry status` and `auth status` expose local delivery buffer state.

Rules:

- Do not add OTLP environment variables or telemetry command wrappers to solve missing sessions.
- Preserve user-owned hook/config entries; only managed entries should be rewritten by patch/cleanup flows.
- Harness-specific adapter, hook-spec, registry, parser, and outbox behavior belongs to `harness-telemetry`.

## Pre-commit and policy failures

| Failing hook/check | Meaning | Recovery |
| --- | --- | --- |
| Ruff | Python lint or import ordering issue | Fix source or run `make format` if auto-fix is appropriate; inspect diff. |
| Ruff format | Formatting differs | Run `make format` and inspect diff. |
| `check-yaml`/`check-toml`/`check-json` | Config syntax invalid | Fix syntax; remember `tsconfig` may allow comments but most JSON files do not. |
| Large-file guard | File over configured size threshold | Remove artifact, use external storage, or justify with maintainers. |
| Merge-conflict guard | Conflict markers remain | Resolve conflict and rerun. |
| Private-key detector | Potential key material | Remove secret and rotate if exposure was real. |
| Secret scan | `.env` or token-like content staged | Unstage/remove secret; do not bypass. |
| Migration chain | Duplicate/fork/orphan Alembic revisions | Fix by generating/adjusting the new migration, not by editing unrelated old migrations. |
| SPDX update | Missing committer copyright line on staged files with headers | Let hook update, then inspect and stage the result. |
| Dockerfile lint | Docker best-practice issue | Fix Dockerfile or document explicit project exception. |

Bypassing hooks with `--no-verify` is not a normal recovery path. If a bypass is unavoidable, document the reason and get maintainer approval.

## Migration workflow failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `make new-migration` fails with usage | `MSG` missing | Run `make new-migration MSG="short description"`. |
| Alembic chain check reports multiple heads | Parallel migration branches | Create an intentional merge migration or regenerate the new migration on current head; route design to `server`. |
| ClickHouse schema changed in startup code | Wrong migration mechanism | Move schema change to ClickHouse migration SQL and route details to `server`. |
| Migration script was edited after merge/release | Unsafe history rewrite | Do not edit released migrations for new changes; add a new migration. |
| Live stack migration fails | Service/database state or SQL issue | Capture logs and route to `server`; do not reset volumes unless local destructive reset is acceptable. |

## Release and compliance failures

| Symptom | Recovery |
| --- | --- |
| Release preview refuses dirty tree | Commit, stash, or discard local changes; release tooling requires a clean tree. |
| Release preflight says not on `main` | Switch to `main`, update from upstream, and verify exact match. |
| GitHub CLI auth fails | Run `gh auth status` and authenticate before retry. |
| No stable tag or invalid release manifest | Stop and ask maintainers; do not invent release cutoffs. |
| Migration changes omitted from notes | Include database migrations in release notes; tooling intentionally blocks omission. |
| Release worktree or branch already exists | Inspect and recover/remove the prior release worktree/branch deliberately; never commit `.worktrees`. |
| License policy finds prohibited/restricted license | Treat as blocking until dependency/source is removed, replaced, or explicitly approved with notices. |
| Vulnerability script reports known issues | Triage exploitability and version constraints; do not silently ignore findings. |

For downloaded artifacts, verify checksums and provenance attestations; checksum-only verification is not enough to prove origin.

## Review and PR workflow failures

| Symptom | Recovery |
| --- | --- |
| PR template has placeholders | Replace every placeholder with concrete purpose, approach, testing, learning if useful, checklist, and AI assistance disclosure. |
| Frontend PR lacks screenshots | Capture affected screens and add them to PR body. |
| User-facing change lacks changelog | Add entry under `[Unreleased]`. |
| CLI syntax changed but bundled skills are stale | Regenerate command reference and update affected skill text. |
| AI-assisted PR lacks tool/version disclosure | Add disclosure and confirm human review/test ownership. |
| Review says scope is too broad | Split unrelated refactors/generated/dependency updates into separate PRs. |
| Security issue is being discussed publicly | Move to private vulnerability reporting and remove unnecessary public details. |

## When to stop and ask

Stop rather than improvising when:

- A command would delete volumes, alter live data, push branches, create a PR, or call production endpoints and the user has not approved it.
- A release cutoff, security disclosure path, license exception, or migration recovery strategy is unclear.
- Source evidence conflicts with package manifests or current code and the conflict affects tool choice.
- A failure belongs to another sub-skill’s implementation domain and requires domain-specific design.
- Verification cannot be completed because required tools, credentials, services, or optional dependencies are unavailable.
