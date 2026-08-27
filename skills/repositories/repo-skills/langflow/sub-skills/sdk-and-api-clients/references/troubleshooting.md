# SDK And API Client Troubleshooting

Use this guide to triage client-side Langflow integration failures before escalating to backend-runtime or deployment guidance.

## Install And Import Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'langflow_sdk'` | SDK package not installed in the active Python environment | Run `python -m pip install langflow-sdk` in the same environment that runs the client code. |
| `ImportError` from `tomllib` on older Python | Python below 3.11 without `tomli` fallback available | Use Python 3.11+ or install compatible TOML support with the SDK's requirements. |
| `pydantic` validation errors while importing or validating models | Incompatible dependency set or malformed payload | Reinstall a compatible `langflow-sdk` release and print the failing payload with secrets redacted. |
| CLI import failures mentioning optional packages such as `openai` | The server/CLI package path needs optional runtime dependencies, not the SDK itself | Install the server package dependencies or route server startup issues to deployment/backend guidance. |
| Transformer/PyTorch warnings | Model execution dependencies are absent | Treat as out of scope for client-only tasks unless the user is running provider/model components. |

Use `python - <<'PY'` smoke checks for imports:

```bash
python - <<'PY'
import langflow_sdk
from langflow_sdk import Client, AsyncClient, RunRequest, StreamChunk
print("langflow_sdk import ok")
PY
```

## Base URL And Network Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `LangflowConnectionError: Could not connect` | Server not running, wrong port, wrong host, or blocked network | Start Langflow, check `http://localhost:7860/health` or server logs, and use the root URL as `base_url`. |
| Repeated redirects or 404 on every SDK method | `base_url` includes `/api/v1` or another path segment | Use `Client("http://localhost:7860")`; SDK methods add `/api/v1/...`. |
| TLS/certificate errors | HTTPS endpoint has custom cert or proxy | Configure the underlying `httpx` client explicitly and inject it via `httpx_client`. |
| Timeouts on long runs | Default timeout too short for the flow | Increase `timeout` in the client constructor or use streaming/background patterns. |

Do not diagnose server import, database, or worker crashes solely from a client traceback; a `500` means the request reached the backend and backend logs are required.

## Auth And Permission Failures

| Status/exception | Meaning | Fix |
| --- | --- | --- |
| `LangflowAuthError` with `401` | Missing or invalid API key | Create/rotate a key and pass it as SDK `api_key` or `x-api-key`. |
| `LangflowAuthError` with `403` | Authenticated but not authorized | Check user role, share/ownership, and server authorization plugin policy. |
| `LangflowNotFoundError` with `404` | Resource missing or intentionally hidden | Re-list flows/projects for the current user; confirm UUID vs endpoint name. |

For REST examples, keep API keys in environment variables:

```bash
export LANGFLOW_URL="http://localhost:7860"
export LANGFLOW_API_KEY="..."
```

Avoid literal keys in `langflow-environments.toml`; use `api_key_env`.

## Request Schema And Data Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `LangflowValidationError` (`422`) | Request body does not match endpoint schema | Validate with `RunRequest`, `FlowCreate`, `FlowUpdate`, `ProjectCreate`, or `ProjectUpdate`. |
| `ValueError` from `client.push(...)` about missing `id` | Flow JSON file lacks top-level `id` | Export/pull a server flow first or add the stable flow UUID before push. |
| Flow run returns no text | Output shape does not include chat text in standard locations | Inspect `response.outputs` and component output keys; do not assume `first_text_output()` always returns a string. |
| `response.has_errors()` is true | Component output or artifacts contain an error | Inspect each `RunOutput.outputs` entry and backend logs for component-specific failures. |
| Tweaks are ignored | Tweaks keys do not match the flow's component IDs/field names | Use API access pane or flow JSON component IDs to build the tweaks object. |
| Project create moves flows unexpectedly | `flows_list`/`components_list` attach existing resources to the project | Warn users this moves resources rather than copying them. |

When debugging a `422`, log a redacted payload:

```python
payload = request.model_dump(mode="json", exclude_none=True)
print(payload)
```

Never print real API keys or component secret values.

## Streaming Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `401` or `403` before any chunks | HTTP auth failure | Catch `LangflowAuthError`; do not treat as stream event. |
| `500` before any chunks | Backend accepted route but failed before stream events | Catch `LangflowHTTPError`, report status/detail, and inspect backend logs. |
| No `end` event observed | Connection closed early, proxy buffering, or flow failure | Treat final response as optional; preserve partial tokens and surface missing-final-response state. |
| `error` event in stream | Flow runtime emitted an error after stream start | Check `chunk.is_error` and raise/report `chunk.data["error"]`. |
| Blank or malformed lines | Normal SSE spacing or transient bad data | SDK skips blank and malformed lines; custom clients should do the same. |
| Token text missing | Event is not `token` or lacks `data.chunk` | Check `chunk.text is not None` before printing. |

Robust stream loop pattern:

```python
final_response = None
for chunk in client.stream("flow-id-or-endpoint", input_value="Hello"):
    if chunk.is_token and chunk.text:
        print(chunk.text, end="", flush=True)
    elif chunk.is_error:
        raise RuntimeError(chunk.data.get("error") or "stream error")
    elif chunk.is_end:
        final_response = chunk.final_response()
```

## Flow Normalization Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Secret values disappear from output | `strip_secrets=True` default clears password/load-from-db fields | This is expected for git-safe output; rerun with `--no-strip-secrets` only for local debugging. |
| Node positions disappear | `strip_node_volatile=True` default removes UI keys | Rerun helper with `--keep-node-volatile` if layout changes are intentional. |
| Server metadata disappears | `strip_volatile=True` default removes instance-specific top-level keys | Rerun helper with `--keep-volatile` only when comparing raw server state. |
| Code fields become lists | `--code-as-lines` was used | Use this for diffs; omit it when the server expects code as a single string. |
| Output order changes | Recursive key sorting is enabled | Expected deterministic behavior; use `--no-sort-keys` only for debugging. |
| JSON parse error | Input file is not valid JSON | Validate with `python -m json.tool flow.json` before normalization. |

Safe git workflow:

```bash
python scripts/normalize_flow_file.py flows/my-flow.json --output flows/my-flow.json --code-as-lines
python -m json.tool flows/my-flow.json >/dev/null
```

Review diffs to ensure secret placeholders are blank before committing.

## API Example Validation Failures

| Signal | Interpretation | Action |
| --- | --- | --- |
| Method/path missing from OpenAPI spec | Docs or client example drift | Update the example or generated spec source; do not guess a route. |
| Python example imports raw `requests` and fails | Missing dependency or env vars | Install example dependencies or rewrite to SDK if the task allows. |
| JavaScript/TypeScript example fails before request | Node package or syntax issue | Verify package install and runtime module type; keep server debugging separate. |
| Curl example works but SDK fails | SDK model/helper mismatch or base URL issue | Compare final URL, headers, and JSON body; use injected `httpx` transport in tests. |
| SDK works but curl fails | Header, quoting, or environment variable expansion issue | Echo redacted URL/body and verify shell quoting. |

Run live examples only against an intentionally started local/test Langflow server. Provider-backed flows can require external credentials; skip them unless the user explicitly provides credentials and asks for a live run.

## Backend, Runtime, Credential, And Hardware Boundaries

Route away from this sub-skill when the failure is not client-side:

- Server startup, database migrations, auth service, route guards, and FastAPI implementation details belong to `backend-runtime`.
- Local stateless execution, `lfx run`, `lfx serve`, and executor environment handling belong to `executor-cli`.
- Docker, environment variables for server operation, PostgreSQL/storage, and production deployment belong to `deployment-and-operations`.
- Component provider credentials, GPU/PyTorch/transformer execution, and external API rate limits are runtime/component concerns; client code can surface the error but usually cannot fix it.

For a `500`, capture the SDK exception `status_code` and `detail`, the request route, and a redacted payload. Then inspect server logs or route to backend-runtime.
