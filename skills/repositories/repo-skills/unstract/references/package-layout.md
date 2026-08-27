# Package Layout

This repository is a multi-service monorepo. Use this map to decide which sub-skill owns a task and which directories are evidence only.

## Primary Source Roots

| Path | What it contains | Owns this surface |
| --- | --- | --- |
| `backend/backend/` | Django settings, URL composition, Celery setup, and shared backend boot code | `backend-platform` |
| `backend/account_v2/`, `backend/api_v2/`, `backend/file_management/`, `backend/pipeline_v2/`, `backend/platform_api/`, `backend/mcp_server/` | Backend route families, auth, API deployment, hosted MCP server, and tool registry logic | `backend-platform` |
| `platform-service/src/unstract/platform_service/` | Flask platform service used by SDK / tooling flows | `platform-deployment` |
| `runner/` | Flask runner service entrypoint and package metadata | `platform-deployment` |
| `tool-sidecar/` | Log-processing sidecar and its entrypoint | `platform-deployment` |
| `x2text-service/app/` | Flask bridge to text-extraction services | `platform-deployment` and `sdk-and-tools` |
| `workers/` | Celery and PG-queue workers, shared queue backend, worker lifecycle scripts, and worker tests | `workers` |
| `frontend/src/` | React router, pages, stores, config, and UI helpers | `frontend` |
| `unstract/connectors/src/` | Filesystem and database connector packages | `sdk-and-tools` |
| `unstract/core/src/` | Shared core helpers | `sdk-and-tools` |
| `unstract/filesystem/src/` | Storage abstractions for workflow execution | `sdk-and-tools` |
| `unstract/flags/src/` | gRPC feature-flag helpers | `sdk-and-tools` |
| `unstract/sdk1/src/` | SDK surface for tools, apps, LLM calls, storage, and utility helpers | `sdk-and-tools` |
| `unstract/tool-registry/src/` | Tool registry loading and metadata helpers | `sdk-and-tools` |
| `unstract/tool-sandbox/src/` | Tool container inspection and protocol helpers | `sdk-and-tools` |
| `unstract/workflow-execution/src/` | Workflow execution models and service objects | `sdk-and-tools` and `backend-platform` |
| `tools/` | Containerized example tools, protocol docs, and tool assets | `sdk-and-tools` |
| `tests/rig/` | Repo test-selection rig, runtime orchestration, coverage aggregation, and critical-path reporting | `testing-rig` |
| `tests/e2e/`, `tests/integration/` | Cross-service integration and end-to-end cases | `testing-rig` |

## Supporting Evidence

| Path | Why it matters |
| --- | --- |
| `README.md` | High-level product intent, deployment shape, and main feature set |
| `docs/ARCHITECTURE.md` | Service-layer architecture and responsibilities |
| `backend/README.md` | Backend install, auth, Celery, and API docs |
| `backend/mcp_server/README.md` | Deployment-vs-platform MCP design, tool authorization, spend guard, and exclusions |
| `frontend/README.md` | Vite/Bun install, runtime config, and build/lint/test commands |
| `workers/README.md`, `workers/ARCHITECTURE.md`, `workers/OPERATIONS.md` | Worker topology, operations, and troubleshooting |
| `tests/README.md` | Test-rig semantics, group manifests, runtime modes, and report outputs |
| `tools/README.md` | Tool protocol, `properties.json`, `spec.json`, and runtime-variable conventions |

## Exclusions For Skill Extraction

- Generated files, build outputs, cache directories, and `__pycache__/`.
- Container/image artifacts, lockfiles that are only build inputs, and other machine-generated outputs unless they define the public workflow.
- Pure IDE, packaging, or maintenance internals that do not help a future agent complete a user-facing repo workflow.

## Practical Routing Rule

If the task starts with "launch", "deploy", or "run the stack", go to `platform-deployment` first. If it starts with "why does the API / MCP call fail", use `backend-platform`. If it starts with "which queue / worker / callback / consumer", use `workers`. If it starts with "tool authoring / registry / SDK", use `sdk-and-tools`. If it starts with "frontend / Vite / runtime config / routes", use `frontend`. If it starts with "which tests / coverage / e2e", use `testing-rig`.
