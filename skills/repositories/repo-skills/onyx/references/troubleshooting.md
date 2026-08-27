# Cross-Cutting Troubleshooting

Read this when an Onyx task is blocked before a specific sub-skill owns the failure.

## Python and uv

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: onyx` from outside `backend/` | The root project is source-only (`tool.uv.package=false`) | Run through `uv run` from the repo root or add `backend` to `PYTHONPATH` for read-only inspection helpers. |
| `pip check` reports mitmproxy/pyopenssl conflicts | Onyx intentionally loosens some dependency caps via uv overrides | Prefer lockfile/`uv sync` consistency and actual import/test results over raw `pip check` for those known conflicts. Do not pin around them casually. |
| Wrong Python version | Onyx requires Python 3.13 | Use the repo-pinned uv environment or a Python 3.13 interpreter. |
| Import starts hitting services | Some backend modules initialize settings/loggers or import service clients | Use targeted imports, avoid lifespan/service startup for inspection, and route live verification through the backend testing references. |

## Services and Live Calls

| Symptom | Likely cause | Recovery |
|---|---|---|
| Backend call works on `:8080` but fails through UI | Bypassed the frontend proxy/cookies | For agent/live tests, call `http://localhost:3000/api/...` unless a backend-only test explicitly requires direct access. |
| Integration tests hang or fail connection checks | Postgres, Redis, OpenSearch, MinIO, API server, web server, or Celery worker missing/stale | Check Onyx service logs and the relevant sub-skill test reference before rerunning. Celery worker code changes may require a user restart. |
| DB client missing | Host lacks `psql` | Use the Docker fallback only when appropriate and never with `-it` in non-TTY agent shells. |
| Test secrets unavailable | Required secret not in env or `.vscode/.env`, and AWS Secrets Manager not authenticated | Ask the user for the secret or authorization; do not hardcode or commit it. |

## Web, Mobile, and Go Toolchains

| Symptom | Likely cause | Recovery |
|---|---|---|
| `bun: command not found` | Bun not installed on host | Report the missing toolchain or ask before host-level installation. Do not substitute `npm`/`npx` when repo docs require Bun. |
| Playwright missing browser | Browser binary not installed even if dependencies exist | From `web/`, use the repo-pinned Playwright install path only after Bun/deps are available. |
| Mobile tests crash on reanimated/worklets | Unit test imported a reanimated-heavy barrel | Follow the mobile testing reference: import leaf components and central mocks. |
| `go: command not found` | Go not installed | Source-inspect CLI/ODS or ask before installing Go. Do not claim native Go tests passed. |

## Generated Artifacts

- Backend/OpenAPI-generated clients, generated Compose files, and shared package build outputs have owning workflows. Do not hand-edit generated outputs to make a local failure disappear.
- If generated output is stale, route to `backend-platform` for API/schema generation, `web-frontend` for generated web types, or `cli-deployment-devtools` for Compose/devtool generation.

## Destructive or Shared-State Operations

Stop and ask for explicit approval before:

- Resetting/dropping/restoring databases or indexes.
- Running deployment uninstall, Helm uninstall, namespace deletion, or compose down on shared stacks.
- Force-pushing branches, approving/closing PRs, queueing merges, uploading audit allowlists, or tagging releases.
- Installing host runtimes/managers such as Bun, Go, Docker, Helm, or Kubernetes tooling.

## Choosing the Next Reference

- Backend route/auth/db/migration/Celery issue: `sub-skills/backend-platform/references/troubleshooting.md`.
- Connector/indexing/search issue: `sub-skills/rag-indexing-connectors/references/troubleshooting.md`.
- Chat/Craft/MCP/sandbox issue: `sub-skills/agents-craft-and-tools/references/troubleshooting.md`.
- Web UI/test/proxy issue: `sub-skills/web-frontend/references/troubleshooting.md`.
- Mobile RN/auth/chat issue: `sub-skills/mobile-client/references/troubleshooting.md`.
- CLI/ODS/deploy issue: `sub-skills/cli-deployment-devtools/references/troubleshooting.md`.
