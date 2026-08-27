# Runtime operations troubleshooting

Use this when a SAM runtime, task submission, gateway probe, docs server, tools inventory, or REST client call fails. Keep the first question explicit: was the action a dry inspection or a live task/run?

## Fast triage

1. **Command availability**: verify the active shell/environment exposes `sam`, `solace-agent-mesh`, or `sam-rest-cli` as appropriate.
2. **Gateway type**: `sam task send/run` expects the Web UI HTTP SSE gateway (`/api/v1/message:stream` and `/api/v1/sse/...`). `sam-rest-cli` expects the REST gateway plugin (`/api/v2/tasks`).
3. **URL and port**: confirm host, scheme, port, and base path with `python scripts/check_gateway.py --url ...`.
4. **Auth**: if endpoints return 401/403, pass a bearer token through `--token` or `SAM_AUTH_TOKEN`.
5. **Agent name**: inspect `/api/v1/agentCards` through the gateway checker or task CLI debug output; match exact agent names when possible.
6. **Timeout phase**: distinguish startup/agent discovery timeout from task execution/SSE timeout from REST polling timeout.
7. **Artifacts and files**: verify local upload paths exist and generated artifacts are tied to the returned session/context ID.

## `sam run` failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `sam: command not found` | Console script not on PATH or package not installed in active environment. | Activate the intended SAM environment or run through the environment's Python/module entry point if available. |
| `Configuration directory ... not found` | Running outside a SAM project or no explicit config paths supplied. | Change to project root, provide YAML files/directories, or route project creation to `project-bootstrap`. |
| `No configuration files to run after filtering` | Skip rules removed all YAML, provided files were non-YAML, or only `_`/`shared_config` files are present. | Recheck `-s/--skip`, filenames, and config paths. |
| `.env file not found` warning | No dotenv file found from current directory upward. | Export required environment variables or run from the project root. Use `--system-env` when relying only on shell env. |
| Logging config not applied | `LOGGING_CONFIG_PATH` missing, wrong, or points to invalid YAML. | Set it to a valid file; remember relative values from `.env` are resolved by the command. |
| Startup hangs or exits with connector errors | Broker, model provider, database, auth, plugin import, or port configuration problem. | Use the emitted final config list and logs to identify the failing app. For one-shot tasks, inspect `sam.log` in the output directory. |
| Browser cannot reach Web UI from Docker | FastAPI bound to loopback inside container or port not published. | Set FastAPI host to `0.0.0.0` for container access and publish the container port to the host. |

## `sam task send` failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Failed to connect to URL` | Web UI gateway not running, wrong port/scheme, container port not exposed, or base path wrong. | Run `check_gateway.py --url URL`; start `sam run` with the Web UI gateway config or correct the URL. |
| Agent list warning or HTTP 401/403 | Auth is required or token lacks access to agent cards. | Pass `--token` or `SAM_AUTH_TOKEN`; verify user scopes. |
| `Agent 'X' not found` | Target agent name not advertised or filtered by authorization. | Use `check_gateway.py --expect-agent X --json` or run without `--agent` to inspect default behavior; use exact names from agent cards. |
| 404 on `/api/v1/message:stream` | URL points to a REST gateway, docs server, platform service, or wrong base path. | Use the Web UI gateway URL for `sam task`; use `sam-rest-cli` for REST gateway. |
| SSE timeout | Task is slow, stream is idle, network/proxy closes streaming, or timeout too low. | Increase `--timeout`; add `--debug`; inspect `sse_events.yaml`, `response.txt`, and server logs. |
| No final text | The task produced artifacts only, returned non-text parts, or failed before text. | Inspect `sse_events.yaml` and `.stim`; check artifacts directory. |
| Artifact/STIM download warning after task success | Artifact service unavailable, wrong session context, insufficient auth, or task logging disabled. | Treat response text separately from artifact/STIM retrieval; inspect warnings and gateway logs. |
| File upload rejected before send | Path missing or is a directory. | Use existing files; repeat `--file` for multiple attachments. |
| Large upload causes latency/memory issues | CLI base64-embeds file parts in JSON. | Use smaller files, external artifact mechanisms, or increase timeouts after confirming gateway limits. |

## `sam task run` failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Fails before startup | Config discovery found no usable YAML. | Provide `-c` paths or fix project `configs/` tree. |
| `Timeout waiting for agent` | Web UI gateway not started, target agent unavailable, auth blocked agent cards, or app startup slow. | Increase `--startup-timeout`; verify selected configs include Web UI gateway and target agent; inspect `sam.log`. |
| Task starts but does not finish | LLM/tool/broker workflow slow or failing. | Increase `--timeout`, use `--debug`, inspect output directory and logs. |
| Command leaves noisy logs in terminal | Normal app logging mixed with task output. | Use `--output-dir` and inspect `sam.log`; the runner lowers stdout noise when file logging is configured. |
| Need `.env` skipped | Current `.env` overrides desired variables. | Use `--system-env` and export only intended environment values. |

## Gateway checker interpretation

`check_gateway.py` performs GET probes only. It reports each endpoint as `ok`, `auth-required`, `redirect`, `missing`, `http-error`, or `unreachable`.

- `ok` on `/api/v1/version` suggests a Web UI gateway API is reachable.
- `ok` on `/api/v1/agentCards` gives agent names if JSON parsing succeeds.
- `auth-required` means the service is reachable but a token is needed or insufficient.
- `missing` on Web UI endpoints with `ok` on `/health` may indicate the URL points to a management server or another service, not the gateway API.
- No reachable probes usually means wrong URL, stopped service, DNS/TLS issue, proxy problem, or firewall block.

## REST client failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `sam-rest-cli: command not found` | REST client package not installed in active client environment. | Install `sam-rest-client` in a dedicated client environment. |
| Installing REST client changes SAM dependency pins | Known `pydantic`/`rich` pin conflict. | Keep REST client and main SAM runtime in separate environments. |
| Submit status 404/405 | Wrong gateway type or base URL. | Confirm REST gateway plugin is configured and reachable on the expected port. |
| Submit status 401/403 | Missing/invalid token. | Pass `--token` or `SAM_AUTH_TOKEN`; refresh token if needed. |
| `SAMTaskTimeoutError` | Async polling exceeded timeout while `/api/v2/tasks/{taskId}` stayed pending. | Increase timeout, inspect server logs, and verify target agent/tools. |
| `SAMTaskFailedError` | Final REST task result contains an error object. | Inspect `error_details` and raw log (`--log` or `log_file_handle`). |
| No text from `get_text()` | Final message parts are missing, non-text, or task failed. | Inspect `raw_result`; artifact-only tasks may still have useful artifacts. |
| Artifact download fails | Wrong session ID, missing artifact, auth failure, or artifact storage unavailable. | Use the result `sessionId` for artifact operations and inspect raw artifact list. |

## Docs and tools command failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `sam docs` cannot find docs directory | Installed distribution lacks bundled docs or dev docs were not built. | Use a package/build that includes docs; for pure runtime work, prefer CLI help and bundled skill references. |
| Docs port busy | Default 8585 already used. | Pass `--port` with a free port. |
| `sam tools list` import error | Package environment incomplete or optional dependency missing during registry import. | Verify main SAM install; do not fix by installing `sam-rest-client` into the same env unless pin changes are acceptable. |
| Invalid tool category | Category name typo or changed registry. | Run `sam tools list --json` or an invalid category once to see valid installed categories. |
| Tool appears locally but not through gateway | Gateway agent cards are filtered by user scopes. | Check token/user scopes and agent card filtering. |

## When to escalate to sibling sub-skills

- Missing or malformed project files: `project-bootstrap`.
- YAML workflow schema or node dependency errors: `workflow-authoring`.
- REST gateway plugin install/config creation: `plugin-lifecycle` for plugin operations, then return here for live REST calls.
- Evaluation setup or `sam eval` timeouts: `evaluation`.
