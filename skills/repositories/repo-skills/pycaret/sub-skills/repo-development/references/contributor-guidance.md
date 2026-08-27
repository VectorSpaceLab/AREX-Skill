# Contributor Guidance

This reference distills PyCaret maintainer rules for source-tree changes. It is self-contained for future agents; use public repository paths and commands, not local checkout paths.

## Monorepo map

PyCaret is a monorepo with four top-level families:

| Path | Purpose | Ships as / notes |
| --- | --- | --- |
| `packages/engine/` | Stateless PyCaret 4 engine. OOP-only task classes, typed results, event logger, Plotly plots, model registries. | PyPI distribution `pycaret` (`4.0.0a8` in the verified source). |
| `services/api/` | FastAPI Control Plane backend: auth, workspaces, projects, experiments, runs, data sources, deployments, LLM advisories, scheduler, webhooks, registry, backup/restore. | PyPI distribution `pycaret-server` (`0.1.0a0`). |
| `packages/sdk-python/` | Python HTTP SDK for the Control Plane. | Package name `pycaret-client`; V2 polish but source exists. |
| `apps/web/` | React 18 + Vite + TypeScript Control Plane UI. | Internal npm package `@pycaret/ui`; Node >=20, Node 22 primary. |
| `apps/site/` | Public docs/marketing site. | Next.js static export; syncs release notes and API tree. |
| `services/worker/`, `services/deployment-runtime/`, `apps/desktop/`, `infra/helm/`, `infra/terraform/` | Planned or stubbed V2/V3 surfaces. | Do not overclaim production maturity. |
| `infra/docker/`, `compose.yml` | Self-hosted local container path and Dockerfiles. | See operations sub-skill for deployment runbooks. |
| `docs/revamp/` | Product vision, architecture, roadmap, status, decisions, kill list, engineering release notes. | Treat as authoritative design history; update only when the workflow requires it. |
| `docs/for_developers/` | Setup, testing, coding style, release, god-class drain playbooks. | Use for maintainer tasks. |
| `.github/workflows/` | CI, release, site build, CodeQL, stale/lock manual workflows. | CI is the contract for broad validation. |
| `.claude/` | Claude Code commands, agents, settings. | Useful as maintainer workflow evidence, but not required for non-Claude agents. |

The workspace-root `pyproject.toml` is a uv workspace manifest and shared tool config. It is not the publishable `pycaret` package; the engine package metadata lives in `packages/engine/pyproject.toml`.

## Universal non-negotiables

- Engine is stateless: use `result = engine.run(config)` or OOP `Experiment(...).fit(data)`, not implicit module state.
- PyCaret 4 is OOP-only. The 3.x functional API and `_CURRENT_EXPERIMENT`/`ContextVar` state were deliberately deleted.
- `RunConfig` / run spec is the shared contract across notebooks, API, UI, and LLM-generated payloads. Do not invent a private shape for one layer.
- Artifacts are immutable. Promotion/retraining creates new pipeline artifacts; deployments point at specific versions.
- LLM functionality is advisory. It returns `suggested_config_json`, `suggested_action`, `reasoning_summary`, and `risk_flags`; users approve before deterministic execution.
- Public engine verbs return typed result dataclasses such as `CompareResult`, `TuneResult`, and `PredictResult`, not bare DataFrames.
- Long-running engine work emits structured events through `self.logger.log(EventKind.X, ...)`; avoid `print()` inside engine modules.
- No upper-bound pins on NumPy, pandas, scipy, scikit-learn, or joblib unless a documented transitional compatibility reason exists.
- Do not reintroduce kill-listed dependencies or APIs. See [kill-list-and-decisions.md](kill-list-and-decisions.md).

## Tooling conventions

### Python

- Python 3.13 is primary; 3.11 is the supported floor.
- Use `uv` for environment and workspace commands.
- Build backend is `hatchling`.
- Lint/format with Ruff. Root config: line length 100, target Python 3.13, selected rules `E`, `F`, `I`, `UP`, `B`.
- Use absolute imports inside `pycaret/` and `pycaret_server/`. No star imports.
- Lazy-import heavy optional dependencies inside the function that needs them.
- Add `from __future__ import annotations` to new Python modules.
- Type-hint public functions. Use `TYPE_CHECKING` guards for hint-only heavy imports.
- Public docstrings use concise numpydoc style and explain why.
- Raise errors from the PyCaret error hierarchy where applicable; messages are actionable single sentences ending with a period.
- Frozen dataclasses are the pattern for public result/card/event types.

### TypeScript / web

- React 18 + Vite + TypeScript strict mode with `verbatimModuleSyntax`.
- Use the `@/` alias to `src/` and prefer named exports.
- Use `import type` for type-only imports.
- The UI should be data-driven from backend introspection (`describe_setup_params`, `list_models`, `list_metrics`) rather than hardcoding engine parameter/model/metric catalogs.
- Match existing dark-mode-first design tokens and component primitives.

### Pre-commit

The repository contains `.pre-commit-config.yaml` with isort, flake8, and black hooks. The current developer docs and CI use Ruff as the primary formatter/linter. If hooks are installed, do not bypass them; if hook behavior conflicts with current Ruff policy, report the conflict rather than silently rewriting large unrelated files.

## Change-record rules

Every non-trivial change should update the engineering log in `docs/revamp/release_notes_pycaret4.md` under the current session block. Use tags such as:

`BREAKING`, `REMOVED`, `ADDED`, `CHANGED`, `FIXED`, `DEPRECATED`, `SECURITY`, `DOCS`, `BUILD`, `TESTS`, `DEPS`, `INTERNAL`.

Update other records only when the trigger applies:

| File | Update when |
| --- | --- |
| `docs/revamp/STATUS.md` | You finish a roadmap item or materially change what is currently landed/in play. |
| `docs/revamp/ROADMAP.md` | You close a phase, add/remove scope, or explicitly defer/advance planned work. |
| `docs/revamp/DECISIONS.md` | You make a non-obvious architecture/product/dependency decision or add a new top-level dependency. Newest entries go first. |
| `docs/revamp/KILL_LIST.md` | Only maintainer-approved removals or explicit changes to settled removals. Treat current entries as settled evidence. |
| `CHANGELOG.md` | Generated/summarized during release prep, not ad hoc for ordinary development. Do not rewrite old entries. |

Some agent configurations disallow editing `docs/revamp/` without explicit approval because those files are archival design records. If so, still identify the required update in your handoff and ask for approval before editing.

## Common implementation workflows

### Add a backend route

1. Check `CONTROL_PLANE_SPEC`, `ROADMAP`, `STATUS`, and `DECISIONS` for intended shape.
2. Add or update SQLAlchemy models in `services/api/pycaret_server/db/models.py` if needed.
3. Generate/review an Alembic migration in `services/api/pycaret_server/migrations/versions/`.
4. Add Pydantic schemas in `services/api/pycaret_server/api/schemas.py` when request/response objects need them.
5. Create or extend the router under `services/api/pycaret_server/api/` and mount it in `app.py`.
6. Write integration tests under `services/api/tests/` using the existing TestClient/DB fixture pattern.
7. Run the server test subset, then add release notes. Update STATUS/ROADMAP/DECISIONS only if triggered.

### Add or change engine behavior

1. Confirm the request is not killed and does not restore implicit state.
2. Keep public signatures and typed result shapes stable unless explicitly doing a breaking change.
3. Prefer native sklearn/sktime/Plotly implementation over resurrecting removed legacy internals.
4. Emit the same structured events for long-running operations.
5. Add fast shape tests where possible and E2E tests when model fitting behavior changes.
6. Run engine tests and Ruff checks.

### Drain or revise a historical god-class verb

The legacy god-class has already been drained and removed in the verified source. If a task mentions god-class drain, interpret it as maintaining native behavior:

- Preserve OOP signatures and typed results.
- Do not import `pycaret/internal/pycaret_experiment/` or restore `oop.py` wrappers.
- Use `docs/for_developers/DRAINING_THE_GODCLASS.md` only as a historical migration playbook for invariants: same signatures, same events, golden notebook path green, release notes with `CHANGED`/`INTERNAL`.

### Work on issues

- Non-trivial work should start from an issue, preferably maintainer-approved.
- Read the issue and comments, reproduce bugs before fixing, and write a failing behavior-level test first.
- Check the kill list before implementing feature restoration.
- Open a PR against `main`; do not push directly to `main` or auto-merge.
- If the issue is ambiguous or touches prohibited areas, comment/ask and stop rather than creating a half-baked PR.

## Maintainer automation evidence

The `.claude/` directory contains useful patterns even for non-Claude agents:

- `commands/work-on-approved-issue.md`: list Approved issues, check kill list, branch, delegate fix, open PR.
- `agents/issue-fixer.md`: reproduce → failing test → fix → focused/broad tests → lint → commit → PR → issue comment.
- `agents/kill-list-checker.md`: read kill list, grep decisions, and report whether a feature is safe, on-list, or adjacent.
- `commands/release-prep.md`: release readiness report; it explicitly does not publish.
- `settings.json`: deny force-push, push to main, hook bypass, destructive reset, package publishing.

Use those as conservative guardrails; do not copy Claude-specific files into runtime tasks.
