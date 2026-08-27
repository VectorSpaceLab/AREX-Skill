# Troubleshooting MCP and services

## Fast triage

1. Identify transport: MCP stdio or HTTP socket.
2. Identify the actual executable/interpreter and process working directory.
3. For MCP, capture stdout and stderr separately. Every nonempty stdout line
   must be one JSON object.
4. Confirm the intended `.leann/indexes/<name>/documents.leann.meta.json` exists
   under that working directory.
5. Validate protocol/schema before testing model quality or provider behavior.
6. Redact passage text, credentials, home paths, and project paths before
   sharing traces.

## Decision matrix

| Symptom | Likely cause | Confirm | Recovery |
|---|---|---|---|
| `leann_mcp` not found | Entry point is outside the GUI/client PATH or package is absent | Compare `command -v leann_mcp` in a shell with the client's environment | Install in the intended context or configure `python -m leann.mcp` using an interpreter that contains `leann-core`; restart the client. |
| `No module named leann.mcp` | Wrong Python interpreter or incomplete/old package | Run the configured Python with `-c "import leann.mcp; print('ok')"` | Point config to the correct interpreter or repair installation; do not mix a global `leann` with another Python's MCP module. |
| Client stays on “initializing” | Process failed, unknown method got no usable response, or stdout is corrupted | Send one `initialize` line manually and parse the first stdout line | Fix startup first; current server returns `-32601` for unknown requests with ids, so silence usually means process/config/stdout trouble. |
| JSON parse error on first line | Banner/log/progress text was written to stdout | Capture raw stdout and inspect the first nonempty line | Move every diagnostic print/logger handler to stderr; do not wrap MCP with a launcher that prints to stdout. Restart and repeat `initialize`. |
| Error has `id: null` | Input line is malformed JSON or outer request shape raised before id handling | Parse the exact sent line with a strict JSON parser | Send one compact object per line; remove comments/trailing commas and include the expected `params.name`/`params.arguments`. |
| Unknown method, code `-32601` | Client used a method the server does not implement | Compare method with `initialize`, `notifications/initialized`, `tools/list`, `tools/call` | Correct the method or update the client adapter; notifications correctly receive no response. |
| Unknown tool, code `-1` | Tool name differs from discovery output | Inspect a fresh `tools/list` response | Use exactly `leann_search`, `leann_list`, `leann_build`, or `leann_status`; do not cache an older schema indefinitely. |
| `result` exists but operation failed | LEANN reports many operational errors as MCP text content, not top-level JSON-RPC errors | Inspect `result.content[0].text` for `Error`, `failed`, or timeout text | Fix the CLI/index issue and teach the client to inspect text content as well as top-level `error`. |
| Search says index missing | Wrong cwd, wrong index name, or index has not been built | Run `leann list` and inspect `.leann/indexes` from the child cwd; call `leann_status` | Start MCP in the owning project root or use a project-pinned generated config; then build/choose the correct index. |
| Status shows `unknown` backend/model for a populated index | The verified passage scan overwrites the variable holding index metadata | Read the index metadata through normal index inspection and compare chunk/file counts separately | Treat it as a known status-handler defect, not proof of missing configuration; use status for identity/location/counts until fixed. |
| `--base-dir` appears ignored | Verified server parses it but does not apply it to subprocess/status cwd | Compare process cwd and requested base directory | Do not rely on the flag in this implementation. Use the bundled generator's `--project-dir` module runner or configure the client's working directory. |
| Build works in shell but not MCP | GUI PATH/interpreter differs, docs are unreadable, or MCP timeout is reached | Reproduce with the exact configured Python and child cwd; inspect stderr | Align environments, grant only required path access, reduce scope or perform an authorized CLI build outside MCP. Build timeout is 600 seconds. |
| Search output cannot be decoded | CLI emitted non-JSON stdout or locale/old-version behavior differs | Run the same `python -m leann search ... --json --show-metadata --non-interactive` | Align package versions and remove stdout contamination. The server falls back to raw text if JSON decoding fails. |
| Tool input rejected or behaves oddly | Client used stale schema or relied on server-side validation | Refresh `tools/list`; compare types/ranges and required fields | Honor the current schema. The implementation itself does not fully enforce JSON Schema ranges. |
| Paths with spaces split into pieces | A shell string was used instead of JSON args/argv entries | Parse config and inspect `command` versus each `args` item | Regenerate config with `generate_service_config.py`; keep each path one JSON string and avoid `sh -c`. |
| OpenClaw MCP starts but agent does not call tools | Tool calling/model-provider setup is incompatible, or MCP discovery failed | First prove `tools/list` independently; then inspect OpenClaw provider logs | Fix MCP discovery here; route model/tool-calling provider configuration to `embeddings-and-chat`. |
| OpenClaw reports manifest mismatch | MCP config was confused with the separate `leann-memory` skill, or required manifest fields/entry are absent | Check whether setup is MCP-only; otherwise validate name, permissions, entry, tags, models, and referenced file | Keep `mcp-and-services` and `leann-memory` identities separate. Repair only the actual OpenClaw skill manifest. |
| HTTP import/start says dependencies missing | FastAPI, Pydantic, or Uvicorn extra is absent | Import the packages with the same Python that runs `leann` | Install `leann-core[server]` in that environment; restart. |
| HTTP health works but `/indexes` is empty | Service runs from the wrong directory or no local index exists | Inspect process cwd and call `leann list` there | Set the service working directory to the project root; build the index separately. Health alone is not an index check. |
| HTTP search returns 404 | Named meta file is absent in current project's index directory | Call `/indexes`; inspect the requested name | Use a listed name or build it before launch. There is no HTTP build endpoint. |
| HTTP search returns 422 | JSON body is missing `query` or has invalid field types | Read the FastAPI validation response | Send JSON matching the documented request model; do not send MCP tool arguments directly without conversion. |
| HTTP search returns 500 | Backend, embedding, model, or index failure escaped route handling | Inspect server stderr and reproduce through local LEANN search | Route search/index diagnosis to `api-and-indexing` and provider/runtime diagnosis to `embeddings-and-chat`. |
| Port already in use | Another process is bound or a stale service remains | Inspect the requested local port with an OS process tool | Stop the known owner or choose another reviewed port; do not kill an unidentified process. |
| Remote clients cannot connect | Service is loopback-only or blocked by firewall | Confirm bind address and local health before network testing | Prefer local use. If remote access is authorized, add authenticated TLS proxy/firewall controls before an explicit non-loopback bind. |
| Private paths appear in results | Passage metadata, status, list, or `/indexes.project_path` exposes them | Inspect one bounded response | Do not publish raw responses; restrict clients and redact metadata at an external boundary. The current HTTP API has no built-in redaction. |

## Recover stdout corruption safely

A valid MCP stdout capture looks like:

```text
{"jsonrpc":"2.0","id":1,"result":{...}}
{"jsonrpc":"2.0","id":2,"result":{...}}
```

If it instead begins with a log line:

```text
Starting LEANN MCP server...
{"jsonrpc":"2.0","id":1,"result":{...}}
```

change the wrapper/application logger to stderr. For Python:

```python
import logging
import sys

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
print("Starting LEANN MCP server...", file=sys.stderr)
```

Do not “recover” by making the client skip arbitrary non-JSON stdout lines;
that masks future protocol corruption and can discard valid messages. Restart
the child after fixing the output stream, then repeat initialize/list/call.

## Safe direct protocol probe

This probe launches a local stdio process and sends no build/search request:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | python -m leann.mcp
```

Parse every output line independently. Expect ids `1` and `2`; the tool list
should contain four names. If the command emits any other stdout line, fix
protocol hygiene before connecting a GUI client.

## Security escalation checklist

Stop rather than retry when any of these are unresolved:

- an untrusted client can invoke `leann_build` on arbitrary paths;
- an HTTP server is bound beyond loopback without authentication/TLS/firewall;
- logs or responses expose credentials or private passage text;
- the process runs with broader filesystem permissions than the indexed data
  requires;
- a proposed fix uses shell interpolation of client-controlled paths;
- the service's cwd or index identity cannot be established.
