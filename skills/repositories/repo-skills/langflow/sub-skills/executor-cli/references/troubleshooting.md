# Executor CLI Troubleshooting

Use this reference to diagnose `lfx`, `lfx run`, `lfx serve`, Flow DevOps commands, extensions, and `lfx-mcp` without opening source files.

## Quick Triage

1. Confirm the binary and version:
   ```bash
   lfx --version
   lfx --help
   ```
2. Validate flow JSON without execution:
   ```bash
   python scripts/validate_lfx_flow.py flows/my-flow.json
   lfx validate flows/my-flow.json --level 4 --strict
   ```
3. If validation passes, run with diagnostics:
   ```bash
   lfx run flows/my-flow.json --input-value "smoke" --format json -vv
   ```
4. If serving, verify endpoint auth and health:
   ```bash
   curl http://localhost:8000/health
   curl -H "x-api-key: $LANGFLOW_API_KEY" http://localhost:8000/flows
   ```
5. If the task needs durable users, saved flows, projects, DB-backed API keys, or full `/api/v1` server behavior, route to the full backend/server guidance rather than forcing LFX.

## Install and Import Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `lfx: command not found` | Package not installed or environment inactive. | Activate the environment, use `uv run lfx ...` in a checkout, or run `uvx lfx ...` for temporary execution. |
| `No module named 'lfx'` | Python interpreter differs from the one with LFX installed. | Run `python -m pip show lfx`, `which lfx`, and `python -c "import lfx"` in the same shell; reinstall into the active environment. |
| `No module named 'yaml'` while resolving `.lfx/environments.yaml` | PyYAML missing in a minimal environment. | Install `pyyaml` or use a TOML environments file. |
| `No module named 'tomli'` on older Python with TOML config | TOML parser missing. | Use Python 3.11+ or install `tomli`. |
| `No module named 'langflow_sdk'` for `push`, `pull`, `status`, or remote `export` | Remote Flow DevOps commands require `langflow-sdk`. | Install a package set that includes `langflow-sdk`, or use only local `run`, `serve`, `validate`, and local `export`. |
| `the bundled component registry is empty or missing` | Broken or incomplete LFX install. | Reinstall LFX, for example with a force reinstall, then retry `lfx validate` or `lfx upgrade`. |
| `No module named 'langchain_core.memory'` | Incompatible `langchain-core` 1.x pulled in by newer LangChain packages. | Install compatible versions such as `langchain-core>=0.3,<1.0`, `langchain-openai>=0.3,<1.0`, and matching community/text-splitter packages. |
| Provider import error such as `No module named 'langchain_openai'` | Standalone `lfx` does not include every provider dependency used by a flow. | Run `lfx requirements FLOW.json`, install missing provider/component packages, then retry. |

## Flow JSON and Schema Errors

| Symptom | Meaning | Fix |
| --- | --- | --- |
| `Invalid JSON content` or `Invalid JSON content from stdin` | JSON syntax or shell quoting is invalid. | Validate with `python -m json.tool FLOW.json`; prefer file/stdin over long `--flow-json` strings. |
| `Missing required top-level field: 'id'`, `'name'`, or `'data'` | Flow is not a full Langflow export shape. | Export from Langflow, use `lfx export`, or wrap the graph data with required metadata. |
| `'data.nodes' must be a JSON array` | Flow structure is malformed. | Regenerate/export the flow or repair `data.nodes` and `data.edges`. |
| `Unknown component type` | Component is missing, blocked by category filters, renamed, or built for a different version. | Check `LANGFLOW_COMPONENT_CATEGORY_ALLOWLIST/BLOCKLIST`, install the extension/provider, and run `lfx upgrade FLOW.json`. |
| `Possible type mismatch on edge` | Source output type may not match target input type. | Reconnect in the visual builder or edit the edge handles to compatible outputs/inputs. |
| `Required input ... has no value and no incoming edge` | A visible required component field is empty. | Fill the field, connect an edge, or supply an appropriate tweak/request variable where supported. |
| `Credential field ... has no value` | A password/secret field has no value, env var, or incoming edge. | Export the needed environment variable or pass request-scoped `global_vars` under `lfx serve`. |
| Version mismatch warning | Flow was built with a different Langflow version than installed. | Use `lfx upgrade`, re-export from the target version, or run with `--upgrade-flow safe` for safe in-memory updates. |

## `lfx run` Misuse

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No input source provided` | No path, `--stdin`, or `--flow-json`. | Provide exactly one source. |
| `Multiple input sources provided` | Path plus `--stdin` or `--flow-json` were combined. | Choose one source mode. |
| `--input-value` seems ignored with stdin/inline JSON | Positional input is unavailable because the flow source occupies that position. | Use `--input-value "..."` explicitly. |
| `File ... must be a .py or .json file` | Unsupported file extension. | Export to `.json` or provide a trusted `.py` graph script. |
| `No 'graph' variable found in the script` | Python script does not expose a graph in a discoverable form. | Add a top-level graph assignment/factory expected by LFX or export the flow to JSON. |
| `--upgrade-flow is only supported for JSON flows` | Tried compatibility gate on a `.py` graph script. | Export to JSON first or skip `--upgrade-flow`. |
| Empty or whitespace `session_id` rejected | Shell variable expanded to empty or argument is invalid. | Omit `--session-id` to auto-generate, or pass a non-empty stable value. |
| Output includes JSON error with `exception_type` | Graph loading/preparation/execution failed. | Retry with `-vv` or `-vvv`, inspect `exception_message`, and distinguish missing dependencies from component config/runtime errors. |

## `lfx serve` Misuse

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `LANGFLOW_API_KEY environment variable is not set` | Server auth token missing at startup. | Export `LANGFLOW_API_KEY` or `LFX_API_KEY`, or load it via `--env-file`. |
| Request returns `401 API key required` | No `x-api-key` header or query parameter. | Send `-H "x-api-key: $LANGFLOW_API_KEY"`. |
| Request returns `401 Invalid API key` | Request token differs from server token. | Use the exact token exported before server startup. |
| `Cannot combine path(s), --flow-json, and --stdin` | Multiple serve input modes used. | Use only one source mode. |
| `Path ... does not exist` | Startup file/directory is wrong. | Check relative path from current directory or pass an absolute path. |
| `... must be a .json or .py file` | Unsupported startup path file extension. | Use `.json`, `.py`, or a directory containing top-level `.json` files. |
| `--workers must be at least 1` | Invalid worker count. | Use `--workers 1` or higher. |
| Invalid log level | `--log-level` not one of `debug`, `info`, `warning`, `error`, `critical`. | Pick a supported value. |
| Warning about `--workers > 1 without --flow-dir` | Each worker has an isolated registry. | Add `--flow-dir` for JSON flows or use one worker. |
| `.py cannot be used with --workers > 1 and --flow-dir` | Python graphs cannot be serialized to the filesystem flow store. | Export to JSON, remove `--flow-dir`, or use one worker. |
| `409 Conflict` on upload | Flow ID already registered. | Upload with `?replace=true` only when replacement is intended. |
| `422 Invalid flow data` or `Flow preparation failed` | Uploaded JSON shape or component setup is invalid. | Run `lfx validate` and local `lfx run` before upload. |
| `404 flow not found` | Wrong ID, deleted flow, or upload reached a different worker without `--flow-dir`. | List `/flows`, enable `--flow-dir`, or re-upload. |
| Port silently changes | Requested port was in use; LFX selected a free port. | Read the startup panel or choose a known free `--port`. |

## `--no-env-fallback` and Credential Failures

| Symptom | Meaning | Fix |
| --- | --- | --- |
| Provider credential is `None` under `--no-env-fallback` | Component cannot read process env and request did not provide the variable. | Send `global_vars` with exact key or `LANGFLOW_REQUEST_VARIABLES`. |
| Credential works without `--no-env-fallback` but fails with it | The flow relies on ambient `os.environ`. | Keep env fallback for single-tenant runs or switch to request-scoped variables. |
| Invalid `LANGFLOW_REQUEST_VARIABLES` warning | JSON blob is malformed or not an object. | Send a JSON object string such as `"{\"OPENAI_API_KEY\":\"...\"}"`. |
| One caller's credential seems reused | Process environment fallback is enabled or a custom component writes to `os.environ`. | Use `--no-env-fallback` and audit custom components for process-env mutation. |

## Stateless Runtime Surprises

| Symptom | Explanation | Fix |
| --- | --- | --- |
| Memory is empty on the second `lfx run` despite same `--session-id` | LFX stamps session ids but has no durable Langflow message database. | Use full Langflow server/database or an external-memory component. |
| `lfx serve` request with same `session_id` does not retain prior messages | `NoopSession` commits nothing and queries return empty results. | Same as above; LFX is stateless for DB-backed memory. |
| Uploaded flows disappear after restart | Default flow registry is in memory. | Use `--flow-dir` for flow JSON persistence, or use full Langflow for app data. |
| Multiple workers list different flows | No shared flow store. | Start with `--flow-dir` or use one worker. |
| Deletes are not instantly visible on every worker | Workers evict stale cached store-backed flows on next request. | Retry/list after propagation or design around eventual per-request stale checks. |

## Flow DevOps Remote Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No --env, --target URL, or config file found` | Remote command cannot resolve a Langflow target. | Run `lfx init`, create `.lfx/environments.yaml`, pass `--target`, or export `LANGFLOW_URL`. |
| `Environment 'x' not found` | Config file lacks requested env. | Add the env block or use a valid `--env`. |
| API key is missing for remote command | Config references `api_key_env`, but that variable is unset. | Export the named env var or pass `--api-key` for inline usage. |
| `Path is outside the project root` during `push` | Project containment guard rejected a file outside `.lfx` root. | Copy the flow into the project or run from the intended project root. |
| `has no 'id' field. Run lfx export first` | Push needs stable IDs for upsert. | Normalize/export the flow or pull from remote first. |
| `status` exits 1 | At least one flow is ahead, behind, new, remote-only, invalid, or errored. | Read the status table; this is intentional for CI drift detection. |
| Remote `export` requires `--env` or `--target` | `--flow-id` or `--project-id` entered remote mode. | Provide a target environment or use local file paths for local mode. |

## Extension Command Errors

| Symptom | Meaning | Fix |
| --- | --- | --- |
| `Invalid --format` | Only `text` and `json` are accepted. | Use `--format text` or `--format json`. |
| `validate` reports manifest/path/AST errors | Extension manifest or bundle files are invalid. | Fix `extension.json`/`pyproject.toml`, unsafe paths, or Python syntax/import shape. |
| `extension list` shows no extensions | Wrong environment or no installed/seed extensions. | Check the Python executable printed by `extension list`; verify install in the same env. |
| `extension reload requires an extension id` | Missing target for reload. | Pass `lfx extension reload lfx-arxiv` or `--all`. |
| `no locally-discovered extension` | Bundle not installed locally or discovery cannot see it. | Run `lfx extension list`; pass `--bundle` if the server has it but local discovery does not. |
| Reload transport error | Target server URL/API key wrong or server not running. | Set `--target` and `--api-key` or `LANGFLOW_HOST`/`LANGFLOW_API_KEY`, then retry. |

## `lfx-mcp` Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| MCP tools cannot connect | No full Langflow server at `LANGFLOW_SERVER_URL`. | Start Langflow and set `LANGFLOW_SERVER_URL`, defaulting to `http://localhost:7860`. |
| MCP login fails | Username/password invalid or auth endpoint unreachable. | Verify credentials in the Langflow UI/server and network access. |
| MCP tools return HTTP 401/403 | Missing/invalid `LANGFLOW_API_KEY` or access token. | Export a valid server API key or call MCP `login`. |
| `search_component_types` or `describe_component_type` fails | Component registry could not be loaded from the server. | Confirm server health and installed extensions/components. |
| Flow validation fails after `create_flow_from_spec` | Spec references wrong component, field, output, input, or incompatible edge. | Use `search_component_types` and `describe_component_type`; fix node ids, field names, and edge types. |
| A partially created MCP flow remains after failure | Cleanup is best-effort. | Delete the flow by ID through MCP or the Langflow UI/API. |

## Network, Hardware, and Boundary Notes

- LFX itself does not require GPU/PyTorch for CLI inspection or simple executor tasks. A specific flow component may require model packages, GPU, network access, or provider credentials.
- Provider calls can fail with ordinary HTTP/connectivity/rate-limit errors; distinguish those from LFX CLI parsing or graph-preparation failures.
- `lfx serve` is a lightweight FastAPI executor, not the full Langflow `/api/v1/run` contract. If a user needs projects, folders, authz, user-scoped fetch, DB-backed API keys, audit logs, or full server run semantics, use full Langflow backend guidance.
- Never recommend committing `.env` files or literal API keys. `.lfx/environments.yaml` should reference env var names with `api_key_env`.
