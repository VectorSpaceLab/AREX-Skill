# Troubleshooting

Read this when a service command, UI launch, MCP transport, or connection flow
fails. Each row names the symptom, likely cause, and the next safe check.

| Symptom | Likely cause | Recovery / next check |
| --- | --- | --- |
| Remote CLI calls use the wrong credential or fail with 401/403 | `--api-key` / `COGNEE_API_KEY` and `--api-token` / `COGNEE_API_TOKEN` have different header mappings. `--api-key` wins over `--api-token` in delegated CLI mode. MCP API mode uses `--api-token` / `COGNEE_BASE_URL` differently from cloud mode. | Re-run the command with the exact credential style the server expects. For delegated CLI calls, prefer `--api-key` when the server wants `X-Api-Key`; use `--api-token` only when the server accepts Bearer auth. Check `references/cli-reference.md` for the precedence ladder. |
| `cognee-mcp` behaves differently in Docker than on the host | Docker uses environment variables through the container entrypoint; direct `cognee-mcp` uses command-line flags. | Use `TRANSPORT_MODE`, `API_URL`, and `API_TOKEN` inside Docker. Use `--transport`, `--api-url`, and `--api-token` when invoking the entry point directly. Do not mix the two styles. |
| Browser UI is blocked by CORS or auth errors | API and MCP CORS origins are not set, or auth posture is inconsistent. `REQUIRE_AUTHENTICATION=false` cannot remain false when multi-tenant access control is on. | Set `CORS_ALLOWED_ORIGINS` / `UI_APP_URL` for the API server and `MCP_CORS_ALLOW_ORIGINS` for MCP. Keep `REQUIRE_AUTHENTICATION` aligned with `ENABLE_BACKEND_ACCESS_CONTROL`. Use the service reference to confirm which process owns the setting. |
| The UI profile fails on macOS | No Docker-compatible runtime is running, or the container cannot reach host services. | Start Docker Desktop or Colima. If the container must reach a host API server, use a host-reachable address rather than raw `localhost`. See `references/deployment.md` for the container networking notes. |
| `visualize_graph_ui` or workspace helpers say the bundle is missing | The MCP app bundle has not been built yet. | Build the MCP workspace bundle with the package's documented frontend build step, then retry the MCP command. The helper should stop with a clear build hint rather than a silent failure. |
| The API server or MCP server exits immediately with a port error | The port is already occupied. The API server binds its socket early, so conflicts fail fast with `EADDRINUSE`. | Free the port or change it (`HTTP_API_PORT`, `--port`, or the Compose port mapping). Common defaults are API `8000`/`8011`, MCP `8000` or host `8001`, and UI `3000`. |
| `cognee-cli --api-url` refuses a command or `--dry-run` | That command is not supported in delegated API mode, or dry-run was requested remotely. | Run the command locally without `--api-url`, or choose a supported remote command (`add`, `cognify`, `search`, `memify`, `datasets`, `delete`, `remember`, `recall`, `improve`, `forget`). |
| Sync returns `409` | A sync is already running for the current user, or the cloud service cannot accept a new transfer yet. | Call `GET /api/v1/sync/status` to inspect the active run, or wait for the existing sync to finish before starting a new one. |
| An MCP workspace helper works in direct mode but not in API mode | Some helpers are intentionally direct-mode only (`create_dataset_json`, `list_dataset_data_json`, and explicit dataset selection in `visualize_graph_ui`). | Drop the restricted helper call, switch to direct mode, or use the API/server route that owns the operation instead. |
| A service command appears to hang | The command is a long-running service or background task, not a one-shot CLI action. | Keep the process in a dedicated terminal or container session and watch its logs. Use `--background` only where the command explicitly supports it. |

## Quick verification loop

When in doubt, run the bundled safe checks first:

```bash
python scripts/check_cli_surface.py --help
python scripts/check_cli_surface.py
python scripts/check_mcp_surface.py --help
python scripts/check_mcp_surface.py
```

- `check_cli_surface.py` should pass when the `cognee-cli` entry point is installed.
- `check_mcp_surface.py` should either pass or explain clearly that the `mcp` package / `cognee-mcp` entry point is missing.
