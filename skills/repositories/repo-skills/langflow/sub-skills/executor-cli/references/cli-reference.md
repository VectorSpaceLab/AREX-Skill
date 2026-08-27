# LFX CLI Reference

This reference distills the Langflow Executor (`lfx`) command surface for future agents. Commands are generic for an installed package or a Langflow checkout; use `lfx ...`, `uv run lfx ...`, or `uvx lfx ...` depending on the user's environment.

## Command Map

| Command | Purpose | Notes |
| --- | --- | --- |
| `lfx --version` | Print installed LFX version. | Verified package family includes `lfx` 1.10.1 in the inspected environment. |
| `lfx init [project_dir]` | Scaffold a Flow DevOps project. | Creates `flows/`, `tests/`, `.lfx/environments.yaml`, CI helpers unless disabled. |
| `lfx login` | Validate remote Langflow credentials. | Uses `.lfx/environments.yaml`, `--target`, or env-var fallback. |
| `lfx create NAME` | Create a flow JSON from a built-in template. | Use `--list` for templates, `--template`, `--output-dir`, `--overwrite`. |
| `lfx validate [paths...]` | Validate flow JSON without executing it. | Levels 1-4: structure, components, edge types, required inputs. |
| `lfx requirements FLOW.json` | Generate dependencies for a flow. | Can write to `--output`; use `--no-lfx` or `--no-pin` when needed. |
| `lfx upgrade FLOW.json` | Check/apply component compatibility updates. | `--write` applies safe upgrades; `--strict` fails on pending safe upgrades. |
| `lfx extension ...` | Author and inspect Langflow extensions. | Includes `validate`, `list`, `reload`, `schema`, `init`, and `dev` style workflows. |
| `lfx run` | Execute a flow locally and print output. | Supports JSON files, Python graph scripts, `--stdin`, and `--flow-json`. |
| `lfx serve` | Serve flows as FastAPI endpoints. | Requires `LANGFLOW_API_KEY` or `LFX_API_KEY`; supports multi-flow serving and uploads. |
| `lfx status` | Compare local flow JSON against a remote Langflow instance. | Exits non-zero when anything is not synced. |
| `lfx push` | Upsert local flow JSON to a remote Langflow instance. | Uses stable JSON `id`; supports `--dry-run`, `--project`, and normalization. |
| `lfx pull` | Pull remote flows into local JSON files. | Normalizes and strips secrets by default. |
| `lfx export` | Normalize local JSON or export remote flow(s). | Good for clean diffs; can strip volatile fields/secrets. |
| `lfx-mcp` | Start the Langflow MCP server. | Connects to a running full Langflow server, not an `lfx serve` instance. |

## Installing and Invoking

Use one of these patterns:

```bash
# Installed package or active virtual environment
lfx --help

# From a source checkout where dependencies are managed by uv
uv run lfx --help

# Temporary isolated execution without permanent install
uvx lfx --help
```

If Langflow OSS is installed, `lfx` is included. If only standalone `lfx` is installed, components in a flow may still require extra packages such as provider integrations, LangChain packages, document loaders, or vector store dependencies.

## `lfx run`

`lfx run` executes a flow once and writes the result to stdout. It does not require a Langflow server API key.

### Path Mode

```bash
lfx run flows/my-flow.json "Hello world"
lfx run flows/my-flow.json --input-value "Hello world" --format json
lfx run flows/my-flow.json --input-value "Hello world" --format text
```

Supported output formats:

- `json`: structured result with success/type/logs/output details.
- `text`, `message`, `result`: print the selected text-like output.

Useful options:

| Option | Use |
| --- | --- |
| `--input-value TEXT` | Explicit input value; required with `--stdin` or `--flow-json`. |
| `--format json|text|message|result` | Select stdout format; default is `json`. |
| `--check-variables` / `--no-check-variables` | Validate global variables before running; default checks. |
| `--session-id ID` | Attach a non-empty session id; empty/whitespace is rejected. |
| `--upgrade-flow check` | Refuse to run if any component is incompatible. |
| `--upgrade-flow safe` | Apply safe in-memory upgrades, abort on breaking/blocked components. |
| `--timing` | Include timing metadata in JSON output. |
| `-v`, `-vv`, `-vvv` | Increase diagnostics; `-vvv` includes component logs. |

### Stdin Mode

Use stdin when a flow is generated or transformed before execution. The positional argument is no longer available for user input, so pass `--input-value`.

```bash
cat flows/my-flow.json | lfx run --stdin --input-value "Hello world" --format json
```

### Inline JSON Mode

```bash
lfx run --flow-json '{"data":{"nodes":[],"edges":[]}}' --input-value "Hello world"
```

Use this only for small examples; for real flows prefer a file or stdin so shell quoting does not corrupt JSON.

### Python Script Mode

A Python graph script must expose a discoverable graph, commonly a `graph = Graph(...)` assignment or an async graph factory expected by LFX's script loader. Run only trusted scripts because import-time code executes.

```bash
lfx run my_flow.py "Hello world" --verbose
```

`--upgrade-flow` is only for JSON sources, not `.py` scripts.

## `lfx serve`

`lfx serve` starts a FastAPI server for one or more flows. Execution endpoints require an API key via the `x-api-key` header or `?x-api-key=` query parameter.

### Required API Key

Generate or provide a token before startup:

```bash
export LANGFLOW_API_KEY="replace-with-local-token"
lfx serve flows/my-flow.json --host 127.0.0.1 --port 8000
```

For LFX, this token can be any strong local token. It is different from a full Langflow database-backed API key unless you intentionally point clients at a full Langflow server.

### Environment File

```bash
cat > .env <<'EOF'
LANGFLOW_API_KEY=replace-with-local-token
OPENAI_API_KEY=replace-with-provider-key
EOF

lfx serve flows/my-flow.json --env-file .env
```

Variables must exist before the server starts unless supplied per request through `global_vars` with `--no-env-fallback`.

### Input Modes

```bash
# Serve one JSON flow
lfx serve flows/my-flow.json

# Serve multiple explicit JSON files
lfx serve flows/a.json flows/b.json

# Serve top-level JSON files in a directory, non-recursive
lfx serve flows/

# Serve stdin JSON
cat flows/my-flow.json | lfx serve --stdin

# Serve inline JSON
lfx serve --flow-json '{"data":{"nodes":[],"edges":[]}}'

# Start empty and upload flows later
lfx serve
```

Only one source type can be used at a time: paths, `--stdin`, or `--flow-json`.

### HTTP Endpoints

All `/flows` routes require `x-api-key` except `/health`.

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/health` | `GET` | Health check with flow count. |
| `/flows` | `GET` | List loaded flows and metadata. |
| `/flows/upload/` | `POST` | Upload a Langflow export JSON; use `replace=true` for duplicate IDs. |
| `/flows/{flow_id}/info` | `GET` | Get metadata for one flow. |
| `/flows/{flow_id}/run` | `POST` | Run a flow and return one response. |
| `/flows/{flow_id}/stream` | `POST` | Run a flow and stream server-sent events. |
| `/flows/{flow_id}` | `DELETE` | Remove a registered flow. |
| `/docs` | `GET` | FastAPI OpenAPI UI. |

Example run request:

```bash
curl -X POST "http://localhost:8000/flows/$FLOW_ID/run" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LANGFLOW_API_KEY" \
  -d '{"input_value":"Hello world","session_id":"demo-session"}'
```

Example streaming request:

```bash
curl -N -X POST "http://localhost:8000/flows/$FLOW_ID/stream" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LANGFLOW_API_KEY" \
  -d '{"input_value":"Hello world","input_type":"chat","output_type":"chat"}'
```

### `--no-env-fallback` and Request Variables

By default, components may fall back to process environment variables. Use `--no-env-fallback` when each request should provide its own credentials and process-wide provider keys must not be read.

```bash
lfx serve flows/my-flow.json --no-env-fallback --env-file .env
```

Supply request-scoped credentials in the `global_vars` map:

```bash
curl -X POST "http://localhost:8000/flows/$FLOW_ID/run" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LANGFLOW_API_KEY" \
  -d '{
    "input_value": "Hello world",
    "global_vars": {
      "LANGFLOW_REQUEST_VARIABLES": "{\"OPENAI_API_KEY\":\"replace-with-request-key\"}"
    }
  }'
```

`global_vars` may also contain raw keys such as `OPENAI_API_KEY` or aliases like `x-langflow-global-var-openai-api-key`; explicit keys override values inside the `LANGFLOW_REQUEST_VARIABLES` JSON blob.

### Multi-worker and `--flow-dir`

Use `--workers` with `--flow-dir` when multiple uvicorn workers should see the same uploaded/started flows.

```bash
lfx serve flows/ --workers 4 --flow-dir ./lfx-flow-store
```

Important rules:

- Without `--flow-dir`, each worker has its own isolated in-memory registry; uploads to one worker are not visible to others.
- With `--flow-dir`, startup flow JSON and uploads are stored as `{flow_id}.json`; workers warm from that store.
- `.py` script flows cannot be used with `--workers > 1 --flow-dir` because Python graphs are not serializable to the flow store.
- A network-mounted `--flow-dir` can add per-request latency because workers check store state to detect cross-worker deletes.

### Compatibility Gate

Use the same compatibility modes as `lfx run`:

```bash
lfx serve flows/my-flow.json --upgrade-flow check
lfx serve flows/my-flow.json --upgrade-flow safe
```

For `lfx serve`, `--upgrade-flow` supports inline JSON, stdin, or exactly one `.json` file. It rejects directories, multiple paths, and `.py` scripts.

## Flow DevOps Commands

### Scaffold a Project

```bash
lfx init my-flow-project
lfx init . --no-github-actions
```

The generated `.lfx/environments.yaml` is safe to commit because it stores API key environment variable names, not key values.

### Create and Validate Flow JSON

```bash
lfx create hello --template hello-world --output-dir flows
lfx create --list
lfx validate flows/hello.json --level 4 --strict
lfx validate flows/ --skip-credentials --format json
```

Validation levels:

1. Structural JSON fields such as `id`, `name`, `data.nodes`, `data.edges` plus orphan/unused-node and version warnings.
2. Component existence in the installed LFX component registry.
3. Best-effort edge type compatibility.
4. Required inputs and missing credential warnings.

### Requirements

```bash
lfx requirements flows/my-flow.json
lfx requirements flows/my-flow.json --output requirements.txt
lfx requirements flows/my-flow.json --no-pin
```

Use this when standalone `lfx` reports missing component dependencies before run/serve.

### Upgrade Compatibility

```bash
lfx upgrade flows/my-flow.json
lfx upgrade flows/my-flow.json --write
lfx upgrade flows/my-flow.json --strict
```

Status meanings:

- `ok`: component matches the current registry.
- `outdated_safe`: can be auto-upgraded.
- `outdated_breaking`: requires manual migration.
- `blocked`: not recognized or intentionally blocked in the current registry.

### Remote Environment Resolution

Remote commands resolve targets in this order:

1. `--target URL` plus optional `--api-key VALUE` inline.
2. `--env NAME` from `.lfx/environments.yaml` or `.toml` supplied by `--environments-file`.
3. Config discovery from `.lfx/environments.yaml` in the current/project parent directories, then user config.
4. Environment fallback with `LANGFLOW_URL`/`LANGFLOW_API_KEY` or `LFX_URL`/`LFX_API_KEY` when no config/env was requested.

### Status, Push, Pull, Export

```bash
# Compare local flows against a remote instance
lfx status --env staging --dir flows/
lfx status --target http://localhost:7860 --api-key "$LANGFLOW_API_KEY" --remote-only

# Push by stable ID; dry-run first for production
lfx push --dir flows/ --env staging --dry-run
lfx push flows/my-flow.json --env staging --project "My Project"

# Pull and normalize remote flows
lfx pull --env staging --output-dir flows/
lfx pull --env staging --flow-id "$FLOW_ID"

# Normalize local JSON for git-friendly diffs
lfx export flows/my-flow.json --in-place
lfx export flows/a.json flows/b.json --output-dir normalized/

# Remote export
lfx export --env staging --flow-id "$FLOW_ID" --output-dir flows/
lfx export --env staging --project-id "$PROJECT_ID" --output-dir flows/
```

Remote `push`, `pull`, `status`, and `export` rely on `langflow-sdk`; route implementation-level SDK questions to the SDK/API sub-skill.

## Extension Commands

Use `lfx extension` for extension authoring and server-side bundle reload workflows.

```bash
lfx extension validate path/to/extension
lfx extension validate path/to/extension --execute-imports
lfx extension list
lfx extension list --format json
lfx extension reload lfx-arxiv --target http://localhost:7860 --api-key "$LANGFLOW_API_KEY"
lfx extension reload --all --target http://localhost:7860 --api-key "$LANGFLOW_API_KEY"
```

Default `extension validate` is offline and checks manifest discovery, path safety, schema validation, and AST-level bundle inspection. `--execute-imports` imports bundle modules in a subprocess and should be opt-in because imports can run package code.

## `lfx-mcp`

`lfx-mcp` starts an MCP server that controls a running full Langflow instance over REST.

```bash
export LANGFLOW_SERVER_URL="http://localhost:7860"
export LANGFLOW_API_KEY="replace-with-server-api-key"
lfx-mcp
```

Important distinctions:

- `lfx-mcp` connects to a full Langflow server URL and uses `/api/v1/...` routes.
- It is not the same as `lfx serve`; `lfx serve` exposes lightweight `/flows/{id}/run` executor routes.
- MCP tools include login, flow creation, component discovery, component configuration, connections, validation, execution, batch operations, and flow edits.
- The MCP client sends both `Authorization: Bearer ...` when logged in and `x-api-key` when an API key is available.
- MCP redacts sensitive template fields by names resembling API keys, passwords, secrets, and tokens.

## Safe Inspection Pattern

Before running or serving a flow, use the bundled helper to parse and summarize it without executing components:

```bash
python scripts/validate_lfx_flow.py flows/my-flow.json
```

Then run LFX's own offline validator:

```bash
lfx validate flows/my-flow.json --level 4 --strict
```

Only after those checks should you run or serve the flow, and only if required dependencies and credentials are available.
