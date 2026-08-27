---
name: onyx
description: "Onyx repository operating knowledge for backend, RAG/indexing,
  agents/Craft, web, mobile, CLI, deployment, and maintainer workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Onyx Repo Skill

Use this skill when the task is about understanding, changing, testing, or troubleshooting the Onyx repository. Onyx is a Gen-AI application platform with a Python/FastAPI backend, Celery workers, OpenSearch-backed RAG/indexing, Next.js web app, Expo mobile app, Go-based CLIs, Docker/Helm deployment assets, and Enterprise Edition overlays.

Start here, then route to the smallest sub-skill that owns the workflow. Keep runtime work in the target checkout, but use the bundled references first so common Onyx rules do not have to be rediscovered.

## Fast Orientation

- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout.
- Read [references/repo-maintenance.md](references/repo-maintenance.md) for cross-cutting contribution, security, testing, and repository-boundary rules.
- Read [references/troubleshooting.md](references/troubleshooting.md) when setup, imports, services, secrets, generated files, or local toolchains block progress.
- Run [scripts/check_onyx_environment.py](scripts/check_onyx_environment.py) for a read-only sanity check of a checkout, optional source imports, and available host tools.

## Route Map

| Task signal | Read first |
|---|---|
| FastAPI route, auth/RBAC, SQLAlchemy, Alembic migration, Celery task/queue, file store, backend test, tenant/security boundary | [backend-platform](sub-skills/backend-platform/SKILL.md) |
| Connector, `DocumentSource`, credential/permission sync, file-backed document, chunking, embedding, OpenSearch, indexing pipeline, RAG retrieval | [rag-indexing-connectors](sub-skills/rag-indexing-connectors/SKILL.md) |
| Chat turn, custom agent/persona, tool/action, MCP, deep research, Craft build mode, sandbox, skills, code execution, agentic streaming | [agents-craft-and-tools](sub-skills/agents-craft-and-tools/SKILL.md) |
| Next.js web UI, Opal design system, frontend API proxy, SWR/data fetching, web chat/admin/Craft UI, Jest, Playwright | [web-frontend](sub-skills/web-frontend/SKILL.md) |
| Expo/React Native mobile app, mobile chat/auth/API, NativeWind, MMKV/TanStack Query, mobile tests, web-parity porting | [mobile-client](sub-skills/mobile-client/SKILL.md) |
| `onyx-cli`, `ods`, Docker Compose, Helm, local service orchestration, deployment lifecycle, generated compose, release/devtools | [cli-deployment-devtools](sub-skills/cli-deployment-devtools/SKILL.md) |

## Cross-Cutting Defaults

- Python backend work assumes Python 3.13 and `uv`; the Onyx root project is not installed as a normal Python distribution, so backend imports normally resolve from the checkout/PYTHONPATH conventions described in the backend references.
- Typical backend setup from a checkout is `uv sync --frozen --group backend --group dev --group ee` (add specialized groups only when the task requires them). Use the repo-managed `.venv` or `uv run`; do not publish private environment prefixes.
- Frontend and mobile JavaScript work assumes Bun-managed dependencies in the relevant package directory, for example `bun install --frozen-lockfile` from `web/` or `mobile/` before native JS checks. Do not silently install Bun or Go on a host; report missing toolchains or ask before host-level changes.
- Go source work for `cli/` and `tools/ods/` needs Go plus the repo-specific command guidance in `cli-deployment-devtools`.
- Live backend calls should go through the frontend proxy, for example `http://localhost:3000/api/...`, not the backend port directly.
- Prefer integration tests for product behavior when services are running; use unit tests for isolated logic and external-dependency unit tests when real dependencies are needed without full app processes.
- Test secrets are resolved by Onyx test utilities. Never add API keys, OAuth secrets, service-account JSON, or private tokens to source, tests, fixtures, examples, or generated skill files.
- Destructive operations (DB drop/restore, index reset, deployment uninstall, Helm namespace deletion, force-push/merge/close PRs, audit allowlist upload) require explicit user approval.

## Initial Checks

From a checkout, use the bundled environment checker before deep work:

```bash
python skills/onyx/scripts/check_onyx_environment.py --repo-root .
```

When a Python environment is available and you want import evidence:

```bash
python skills/onyx/scripts/check_onyx_environment.py --repo-root . --check-python-imports
```

The checker is read-only. It does not start Onyx services, install packages, contact the network, run tests, or mutate Docker/Kubernetes/DB state.

## When Multiple Sub-Skills Apply

- New connector option or source: start with `rag-indexing-connectors`, then use `backend-platform` for API/DB/migrations and `web-frontend` for admin connector form changes.
- Craft issue visible in the web UI: start with `agents-craft-and-tools`, then use `web-frontend` for packet/UI state and `backend-platform` for route/session/Celery mechanics.
- Mobile chat mismatch: start with `mobile-client`, then use `agents-craft-and-tools` for backend chat protocol and `web-frontend` only for parity evidence.
- Deployment or CLI bug that points into backend code: start with `cli-deployment-devtools`, then route implementation changes to the owning backend sub-skill.
