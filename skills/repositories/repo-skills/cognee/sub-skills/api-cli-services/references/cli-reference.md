# Cognee CLI Reference

Read this when you need to use `cognee-cli` without reopening the source repository.
It focuses on the public command surface, service-related routing, and the flags
that matter for remote vs local operation.

## Global flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--version` | Print the installed Cognee version. | Safe and non-destructive. |
| `--debug` | Show full stack traces on CLI failures. | Helpful when a command fails before dispatch. |
| `-ui` | Start the Cognee UI stack. | Launches the frontend, API backend, and MCP server together. |
| `--user-id` | Set the user/agent identity. | Useful for multi-agent isolation and API delegation. |
| `--api-url` | Delegate supported commands to a running API server. | See the delegation rules below. |
| `--api-key` | Send an API key when `--api-url` is used. | Wins over `--api-token`. Falls back to `COGNEE_API_KEY`. |
| `--api-token` | Send a Bearer token when `--api-url` is used. | Used only when no API key is supplied. Falls back to `COGNEE_API_TOKEN`. |

## Command catalog

### Ingestion, graph build, and memory

| Command | What it does | Notable options / notes |
| --- | --- | --- |
| `add` | Ingest raw text or files into a dataset. | Accepts mixed text/path inputs and `--dataset-name` / `-d`. |
| `remember` | Ingest data and build the knowledge graph in one step. | `--dataset-name`, `--chunk-size`, `--chunker`, `--background`, `--dry-run`. |
| `cognify` | Transform ingested data into a graph. | `--datasets`, `--chunk-size`, `--ontology-file`, `--chunker`, `--background`, `--verbose`, `--dry-run`. |
| `memify` | Enrich an existing graph. | `--dataset-name` or `--dataset-id`, `--node-name`, `--data`, `--background`. |
| `improve` | Enrich the graph and bridge session feedback. | `--dataset-name` or `--dataset-id`, `--session-ids`, `--feedback-alpha`, `--background`. |
| `search` | Query the processed knowledge graph. | `--query-type`, `--datasets`, `--top-k`, `--system-prompt`, `--output-format`. |
| `recall` | Memory-oriented query helper. | `--query-type`, `--datasets`, `--session-id`, `--top-k`, `--output-format`. |
| `forget` | Remove data from the graph. | `--dataset`, `--dataset-id`, `--data-id`, `--everything`. |
| `delete` | Delete datasets or all stored data. | `--dataset-name`, `--all`, `--force`. |

### Service and connection

| Command | What it does | Notable options / notes |
| --- | --- | --- |
| `serve` | Connect to a Cognee instance. | `--url`, `--api-key`, `--management-url`, `--logout`. |
| `push` | Export a local dataset and import it into Cognee Cloud. | `dataset`, `--target-dataset`, `--mode`, `--url`, `--api-key`, `--background`. |
| `datasets` | Manage datasets and dataset status. | `list`, `create`, `data`, `status`, `graph`, `delete`. |
| `agents` | Manage agent registrations and connections. | `create`, `list`, `get`, `delete`, `register`, `unregister`, `connections`. |
| `sessions` | Inspect session history. | `get`, `--last-n`, `--format`. |
| `feedback` | Add or remove feedback on Q&A entries. | `add`, `delete`. |
| `config` | Read or change Cognee settings. | `get`, `set`, `list`, `unset`, `reset`. |

### Maintenance and evaluation

| Command | What it does | Notable options / notes |
| --- | --- | --- |
| `eval` | Run the memory-quality benchmark pipeline. | Benchmark and engine selection live in the command help; optional extras may be needed. |
| `upgrade` | Apply data and relational migrations. | `revision`, `--alembic`, `--alembic-path`. |
| `downgrade` | Revert data and optionally schema migrations. | `revision`, `--alembic`, `--alembic-path`, `--dataset`, `--force`. |
| `history` | Show the migration history. | Read-only. |
| `current` | Show the currently stamped migration state. | Read-only. |
| `stamp` | Update the stored migration revision without running migrations. | `revision`, `--dataset`, `--force`. |

## `--api-url` delegation

When `--api-url` is set, `cognee-cli` forwards only these commands to the API
server instead of running them in-process:

- `add`
- `cognify`
- `search`
- `memify`
- `datasets`
- `delete`
- `remember`
- `recall`
- `improve`
- `forget`

Key rules:

1. `--api-key` wins over `--api-token`.
2. `COGNEE_API_KEY` and `COGNEE_API_TOKEN` are the environment fallbacks.
3. `--user-id` is forwarded as `X-User-Id` for isolation-aware API servers.
4. `--dry-run` is not supported in `--api-url` mode.
5. Unsupported commands must run locally or through a different service entry point.

Auth header mapping for delegated requests:

| Input | Header sent |
| --- | --- |
| `--api-key` or `COGNEE_API_KEY` | `X-Api-Key` |
| `--api-token` or `COGNEE_API_TOKEN` | `Authorization: Bearer ...` |

## Common service patterns

- Use `cognee-cli serve --logout` to disconnect and clear saved connection state.
- Use `cognee-cli push` when you want to move a local dataset graph to a remote instance without re-deriving it from raw files.
- Use `cognee-cli -ui` when you want the browser UI, API backend, and MCP server to come up together.
- For backend/provider selection or storage/database matrices, switch to [configuration-backends](../../configuration-backends/SKILL.md).
- For transport, Docker, and MCP-specific details, read [services-mcp.md](services-mcp.md).
