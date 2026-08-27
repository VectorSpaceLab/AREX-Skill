# MCP Reference

This reference covers the M-flow MCP server, its tools, its transports, and the remote API mode used by IDEs and other automation.

## Tool set

The server exposes 11 tools:

| Tool | Core arguments | Notes |
| --- | --- | --- |
| `memorize` | `data`, `dataset_name`, `wait` | returns a `task_id`; `wait=True` waits for completion |
| `save_interaction` | `data`, `wait` | same task-tracking model as `memorize` |
| `search` | `search_query`, `recall_mode`, `top_k`, `datasets`, `system_prompt`, `enable_hybrid_search` | raw MCP search surface |
| `list_data` | `dataset_id` | dataset listing; detailed dataset view is not available in remote API mode |
| `delete` | `data_id`, `dataset_id`, `mode` | soft/hard delete |
| `prune` | `graph`, `vector`, `metadata`, `cache` | guarded destructive cleanup |
| `memorize_status` | `task_id` | per-task lookup, or dataset-level status if omitted |
| `learn` | `datasets`, `episode_ids`, `run_in_background` | procedural extraction |
| `update_data` | `data_id`, `data`, `dataset_id` | replace existing content |
| `ingest` | `data`, `dataset_name`, `skip_memorize` | one-step ingestion |
| `query` | `question`, `datasets`, `mode`, `top_k` | simplified natural-language query |

### Query and recall modes

- `search` uses `CHUNKS_LEXICAL`, `TRIPLET_COMPLETION`, `CYPHER`, `EPISODIC`, or `PROCEDURAL`
- `query` uses `episodic`, `triplet`, `chunks`, `procedural`, or `cypher`

## Transports

| Transport | Typical use | Launch cue |
| --- | --- | --- |
| `stdio` | local IDE integrations | default when running the server locally |
| `sse` | Docker and browser-based clients | `--transport sse` |
| `http` | streamable HTTP clients | `--transport http --path /mcp` |

Common launch flags and env vars:

- `--transport`
- `--host`
- `--port`
- `--path`
- `--api-url`
- `--api-token`
- `--no-migration`
- `TRANSPORT_MODE`
- `MCP_PORT`
- `MCP_LOG_LEVEL`

## API mode

When `--api-url` is set, the MCP server talks to a remote M-flow backend instead of calling the package in-process.

Remote-mode endpoint mapping:

| MCP operation | Remote API endpoint |
| --- | --- |
| `query` | `POST /api/v1/search/query` |
| `learn` | `POST /api/v1/procedural/extract-from-episodic` |
| `update_data` | `PATCH /api/v1/update` |
| `ingest` | `POST /api/v1/ingest` |
| `list_data` | `GET /api/v1/datasets` |
| `memorize_status` | `GET /api/v1/datasets/status` for pipeline status, or in-memory task lookup when `task_id` is supplied |
| `prune_data` | `POST /api/v1/prune/data` |
| `prune_system` | `POST /api/v1/prune/system` |

Important remote-mode limits:

- `learn(..., episode_ids=...)` is not implemented remotely.
- `prune` is admin-gated and may return 401/403/409/429 depending on auth, master switch, active pipelines, or cooldown.
- `memorize_status(task_id=...)` is the reliable way to inspect asynchronous task outcomes for `memorize` and `save_interaction`.

## IDE configuration cues

### Cursor

```json
{
  "mcpServers": {
    "m_flow": {
      "url": "http://localhost:8001/sse",
      "transport": "sse"
    }
  }
}
```

### Claude Desktop

```json
{
  "mcpServers": {
    "m_flow": {
      "command": "python",
      "args": ["-m", "src.server", "--transport", "stdio"],
      "cwd": "/path/to/m_flow-mcp"
    }
  }
}
```

### VS Code + Continue

```json
{
  "mcpServers": [
    {
      "name": "m_flow",
      "transport": {
        "type": "sse",
        "url": "http://localhost:8001/sse"
      }
    }
  ]
}
```

## Validation cues

- `memorize` and `save_interaction` should surface a `task_id` in the response.
- `memorize_status(task_id=...)` should show the final task state, not just a start message.
- `query` should collapse to an answer string in triplet mode or to context text in other modes.
- If IDE discovery fails, first check transport mode, then port/path, then whether you are in API mode instead of local mode.
