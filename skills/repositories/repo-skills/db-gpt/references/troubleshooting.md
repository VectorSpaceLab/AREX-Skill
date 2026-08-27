# Cross-Cutting Troubleshooting

| Symptom | Likely boundary | Check and recovery |
|---|---|---|
| `dbgpt` is missing or imports fail | Install/package selection | Confirm the Python environment, install `dbgpt-app` rather than only a core package, run `pip check`, then add only the route's optional extra. |
| Optional module `ImportError` | Provider/parser/store/backend extra | Identify the named module and install the documented matching extra; do not install every extra as a blind fix. Re-run the smallest import check. |
| TOML parses but startup fails | Config path, schema, placeholder, or missing secret | Validate structure with the route helper, confirm DB-GPT home/path expansion and required model roles, then check the provider environment variable without printing its value. |
| Web UI/process starts but chat fails | Provider/model/embedding or downstream service | Check the resolved profile, provider base URL, model name, embedding role, logs, and one minimal operation. A listening port is not model health. |
| `model ... --help` or `list` times out/returns 502 | Dynamic controller discovery | Treat model CLI metadata as controller-dependent. Verify controller address/health, registry/heartbeat, and service logs; do not report a successful deployment. |
| `dbgpt start web --port ...` is rejected | Version-specific CLI shape | In 0.8.1 configure `[service.web].port` in TOML; use `stop webserver --port` only for narrow process selection. Recheck installed help for another release. |
| RAG returns no useful context | Loader/chunker/index/model mismatch | Inspect accepted documents/chunks and source metadata, enforce non-empty chunks and `chunk_overlap < chunk_size`, verify embedding model and vector dimension, then test retrieval before chat. |
| External database/vector/graph operation fails | Service/driver/auth/backend | Preserve the endpoint and status with secrets redacted. Check the connector extra, service availability, credentials, schema, and compatibility. Do not substitute a local SQLite smoke as proof of the external service. |
| Client gets 400/401/404/409/5xx | Request or service boundary | Confirm API base/version/prefix, JSON vs query vs multipart placement, Bearer auth, returned identifiers, dependency order, and idempotency. Avoid blind retries for create/delete/upload. |
| Async client or stream leaks resources | Lifecycle | Close `httpx.AsyncClient` in `finally`, consume SSE until `[DONE]`, and clean temporary files, flow/session IDs, and uploads. |
| Sandbox refuses to start | Runtime/image/policy | Container auto-selection fails closed without Docker/Podman/Nerdctl and an image. Explicit local runtime is weaker than isolation and needs opt-in; verify policy, timeout, cleanup, and path boundaries. |
| Sandbox code is rejected or escapes expectations | Safety boundary | Treat simple pattern checks as advisory. Do not pass secrets or host paths; reject network/filesystem access, use a container for untrusted code, and assert session/artifact cleanup. |
| Migration would delete or downgrade data | Destructive command | Stop and inspect target config. Prefer `upgrade --sql-output` for review. Require both explicit confirmation and any required drop confirmation; never use `-y` merely to make automation pass. |

## Reporting rule

For every unresolved issue report: package/release, route, exact command or API
path, redacted config/provider role, status/exception, whether the failure was
local or live, prerequisites not exercised, and the next safe check. Keep local
checkout, virtualenv, machine, and secret details out of reusable skill content.
