---
name: "unstract"
description: "Use Unstract to operate its document-extraction APIs, hosted MCP
  servers, workers, shared SDK/tool packages, frontend, and test rig."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Unstract Repo Skill

Use this skill when a task involves the Unstract platform repository: launching the stack, working on backend APIs or hosted MCP servers, operating workers, authoring or validating tool packages, changing the frontend, or running repo-wide tests.

## Start Here

- `sub-skills/platform-deployment/SKILL.md` — service startup, `run-platform.sh`, container entrypoints, ports, and deployment troubleshooting.
- `sub-skills/backend-platform/SKILL.md` — Django / DRF routes, auth, API families, hosted MCP server behavior, and backend configuration.
- `sub-skills/workers/SKILL.md` — Celery and PG-queue workers, queue routing, health ports, and worker operations.
- `sub-skills/sdk-and-tools/SKILL.md` — the shared Python packages under `unstract/*`, tool protocol, tool registry, and tool authoring.
- `sub-skills/frontend/SKILL.md` — React / Vite / Bun routing, runtime config, build, and browser-side troubleshooting.
- `sub-skills/testing-rig/SKILL.md` — `tests/rig`, group manifests, runtime selection, coverage aggregation, and critical-path reporting.

## Install And Smoke Check

Pick the smallest workflow-specific environment you need:

- Python services and packages: `cd backend && uv sync`, `cd platform-service && uv sync`, `cd workers && uv sync`, or `cd unstract/sdk1 && uv sync --group test`.
- Frontend: `cd frontend && bun install`.
- Full-stack local deployment: `./run-platform.sh` after Docker is available and the service env files are ready.

Run the bundled shared checker from this skill tree for a safe package / backend import pass:

```bash
python scripts/check_unstract_packages.py
```

Add `--backend` when you want the backend route and hosted-MCP modules imported as part of the same check, and `--tool-registry --tool-registry-config <dir>` when you want to validate a registry directory without loading images.

## Cross-Cutting Notes

- The Python services target Python 3.12.
- `backend.settings.test` is the safest Django settings module for inspection.
- `window.RUNTIME_CONFIG` is generated at container start for the frontend; `VITE_*` env vars are the development source of truth.
- `MCP_PLATFORM_SERVER_ENABLED` controls whether the org-scoped hosted MCP server is mounted.
- `tests/rig` is the source of truth for repo-wide group selection, runtime mode, and critical-path coverage.
- Keep worker import order careful: the `workers/` tree can shadow backend packages if paths are inserted in the wrong order.

## Shared References

- `references/package-layout.md` — repo layout and package / service ownership map.
- `references/service-map.md` — service roles, ports, and startup relationships.
- `references/installation-and-env.md` — install and environment matrix by workflow.
- `references/troubleshooting.md` — cross-cutting import, environment, runtime, and deployment failures.
- `references/repo-provenance.md` — source snapshot and evidence paths for staleness checks.
- `references/repo-routing-metadata.json` — structured scenario metadata for `repo-skills-router`.

## Common Task Routing

| User request | Read next |
| --- | --- |
| "Start the full stack" / "run the platform" | `sub-skills/platform-deployment/SKILL.md` |
| "Why is this API or MCP call failing?" | `sub-skills/backend-platform/SKILL.md` |
| "Which worker handles this queue?" | `sub-skills/workers/SKILL.md` |
| "How do the shared Python packages or tools fit together?" | `sub-skills/sdk-and-tools/SKILL.md` |
| "Why is the frontend build or runtime config wrong?" | `sub-skills/frontend/SKILL.md` |
| "Which tests cover this path?" | `sub-skills/testing-rig/SKILL.md` |

## Safety Boundaries

- Do not assume Docker, Redis, PostgreSQL, RabbitMQ, MinIO, or browser toolchains are available unless the task asks for them.
- Do not send users back to the original repository files for runtime instructions; the skill tree and bundled scripts are the public source of truth.
- Do not mix deployment, backend, worker, frontend, SDK, and test-rig guidance in one answer when a single sub-skill already owns the workflow.
- Do not leak local environment paths, private credentials, or per-machine prefixes into the public skill files.
