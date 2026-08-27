# CLI and transport reference

This page is the quick reference for safe command-line and transport checks.
All synthetic examples stay local and avoid long-running listeners.

## 1) Zero-side-effect probes

Use these first when you want to confirm the package is installed and the CLI
entry points are reachable:

```bash
openmed --help
openmed --version
openmed-mcp --help
openmed-mcp --version
```

If the console scripts are missing from `PATH`, the same probes can be run with
module execution:

```bash
python -m openmed.cli.main --help
python -m openmed.cli.main --version
python -m openmed.mcp.server --help
python -m openmed.mcp.server --version
```

These probes do not start a REST server, gRPC server, or external service.

## 2) CLI output contract

Most `openmed` subcommands accept `--json`. Use it whenever you want stable
machine-readable output instead of human text.

Success envelope:

```json
{
  "ok": true,
  "command": "fhir validate",
  "data": {}
}
```

Error envelope:

```json
{
  "ok": false,
  "command": "fhir validate",
  "error": {
    "code": "validation_error",
    "message": "Request validation failed"
  }
}
```

Exit codes:

- `0` — success
- `1` — runtime or gate failure
- `2` — usage or validation error

## 3) One-shot interop commands

Use the CLI when the task is finite and can end after one response.

Common interop-oriented commands include:

- `openmed fhir validate`
- `openmed omop load`
- `openmed ground`
- `openmed doctor`
- `openmed config`

Synthetic example patterns:

```bash
openmed fhir validate \
  --input synthetic_bundle.json \
  --version R4 \
  --profile ips \
  --json

openmed omop load \
  --input synthetic_grounded_notes.jsonl \
  --json
```

Use `--json` so the caller can inspect the returned `OperationOutcome` or load
summary without scraping prose.

## 4) REST, gRPC, and MCP start points

### REST

```bash
uvicorn openmed.service.app:app --host 127.0.0.1 --port 8080
```

### gRPC

```python
from openmed.service.grpc_server import serve

server = serve("127.0.0.1:50051")
server.wait_for_termination()
```

### MCP stdio

```bash
openmed-mcp --transport stdio
```

### MCP streamable HTTP

```bash
openmed-mcp \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8081 \
  --streamable-http-path /mcp
```

Use stdio for local agents and streamable HTTP only when the client needs a URL.

## 5) Typed Python client

The REST client is useful when your workflow is already Python-based and you
want typed request/response handling.

```python
from openmed.service.client import OpenMedAPIError, OpenMedClient

with OpenMedClient("http://127.0.0.1:8080", timeout=300.0) as client:
    print(client.loaded_models())
    print(client.analyze("Synthetic assessment: asthma treated with albuterol."))
```

Client methods:

- `analyze`
- `extract_pii`
- `extract_pii_stream`
- `deidentify`
- `privacy_gateway`
- `loaded_models`
- `unload_model`
- `unload_all_models`

`OpenMedAPIError` exposes `status_code`, `code`, `message`, `details`, and
`request_id`.

## 6) Registry and adapter helpers

Use the registry when a caller needs the canonical tool list or framework-
specific adapter views.

```python
from openmed.interop import available_adapters, to_function_tools, to_tool_use_tools
from openmed.mcp.tool_registry import TOOL_REGISTRY

print(available_adapters(include_plugins=False))
print([spec.name for spec in TOOL_REGISTRY.latest_specs()])
```

Useful helpers:

- `available_adapters(include_plugins=False)`
- `adapter_tool_definitions(name)`
- `to_function_tools()`
- `to_tool_use_tools()`
- `get_langchain_tools()`
- `get_llamaindex_tools()`
- `TOOL_REGISTRY.latest_specs()`

## 7) When the CLI is the wrong choice

Do not force a CLI workflow when you actually need:

- a shared service runtime;
- async jobs or webhooks;
- browser-origin requests;
- a long-lived MCP server;
- a typed RPC client;
- adapter rendering for another agent framework.

In those cases, switch to REST, gRPC, MCP, or a framework adapter instead of
adding more shell logic.
