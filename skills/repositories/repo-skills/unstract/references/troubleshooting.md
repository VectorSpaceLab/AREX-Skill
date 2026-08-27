# Troubleshooting

This file covers the cross-cutting failures that recur across multiple Unstract surfaces. For workflow-specific failures, read the nearest sub-skill troubleshooting file.

## Fast Triage Table

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| Django import fails during `backend` inspection | Missing test env vars or wrong settings module | Use `backend.settings.test`, set the default backend env vars, and keep the repo source root on `PYTHONPATH` |
| `ModuleNotFoundError: No module named 'plugins.apps'` | Worker paths were added before the backend source root, so the worker `plugins/` package shadowed the backend one | Put the backend source root ahead of worker paths when building `sys.path` |
| Platform MCP returns 403 for a read key | The org-scoped MCP server uses HTTP POST for every tool call, so the middleware rejects `read` keys | Use a `read_write` key or the deployment-scoped MCP server |
| The frontend ignores changed env vars | The runtime config was not regenerated | Re-run the runtime-config generator before testing the production build |
| A worker or service will not start | Docker, Redis, PostgreSQL, RabbitMQ, or service env files are missing | Check the owning sub-skill's install and startup references |
| `tests.rig` says a critical path is uncovered | The covered group did not run green, or the path has no active group | Run the owning group and check the baseline / coverage mapping |
| Tool registry loading fails | `TOOL_REGISTRY_CONFIG_PATH` or storage credentials are missing | Point the tool registry at a config directory and provide the storage credential envs |

## Cross-Cutting Failure Modes

### Backend and MCP
- `backend.backend.urls` and `backend.mcp_server.registry` depend on the repo's Django settings contract. If they fail at import time, the usual cause is missing defaults rather than broken syntax.
- Pre-signed S3 URLs can exceed Django's default `URLValidator` length cap. The backend raises the limit for that reason; if a change regresses it, long document URLs start failing validation.
- `MCP_PLATFORM_SERVER_ENABLED=false` means the org-scoped hosted MCP server is intentionally absent. Do not treat that as a missing route bug unless the flag is on.

### Workers
- Worker imports are sensitive to `sys.path` order. The `workers/` tree contains its own `plugins/` package, so it can accidentally mask backend code if the path order is wrong.
- PG-queue roles have their own health ports and env overrides. If a PG worker appears dead while the Celery workers look healthy, check the PG queue-specific ports and override variables.

### Frontend
- `window.RUNTIME_CONFIG` wins over `VITE_*` env vars at runtime. If the UI still shows old values, check whether the generated config file was refreshed and whether the browser cached the old asset.
- Missing optional plugin pages can be normal. The Vite config bundles absent plugin imports as empty modules so the app can still build.

### Tool registry and tool containers
- `ToolRegistry` expects a config directory and storage credentials. A missing config path is a setup error, not a runtime bug.
- The tool example containers use the protocol in `tools/README.md`: input via stdin/args, output as newline-delimited JSON, metadata via `properties.json`, and runtime variables via `runtime_variables.json`.
- `load_tools_to_json.py` is operational, not a smoke test. It can pull images and write JSON; use a validation helper or a dry inspection path when you only need confidence.

### Test rig
- `UNSTRACT_LLM_MOCK_RESPONSE` is required for execute-path e2e flows that should not call a live provider.
- `testcontainers` only provisions infra today. If a full-platform e2e scenario needs the backend or frontend started too, use the compose runtime.
- The rig's `groups.yaml` and `critical_paths.yaml` are authoritative; do not infer group coverage from ad hoc pytest paths.

## What Not To Chase First

- Do not debug the backend or worker code before confirming the service env and import path order.
- Do not debug frontend route bugs before confirming runtime config regeneration and the backend URL wiring.
- Do not debug MCP authorization before checking the key tier and the server type being used.
- Do not debug tool registry loading before checking the registry path and storage credentials.
- Do not debug e2e coverage gaps before checking the group manifest and the critical-path registry.
