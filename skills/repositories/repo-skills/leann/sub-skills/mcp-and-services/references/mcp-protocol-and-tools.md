# MCP protocol and tools

## Entry points and process lifecycle

LEANN installs the stdio entry point `leann_mcp`, mapped to `leann.mcp:main`.
The equivalent module form is:

```bash
python -m leann.mcp
```

The process reads UTF-8, newline-delimited JSON objects from stdin. For each
request that requires a response it writes one compact JSON object plus a
newline to stdout and flushes immediately. Closing stdin ends the loop and the
process. Do not use stdout for banners, progress, or logs; write diagnostics to
stderr because any non-JSON stdout line can break an MCP client.

The server invokes the LEANN CLI as the same Python interpreter:
`python -m leann ...`. Search/list use a 120-second subprocess timeout; build
uses 600 seconds. Subprocess arguments are passed as an array, not through a
shell.

## Protocol sequence

A minimal client sequence is:

1. Send `initialize` with an id. The server returns protocol version
   `2024-11-05`, server name `leann-mcp`, version `2.0.0`, and tool capability.
2. Send `notifications/initialized` without an id. The server intentionally
   sends no response.
3. Send `tools/list` with an id to discover the current schemas.
4. Send `tools/call` with `params.name` and `params.arguments`.

Example probe input (one JSON object per line):

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

The implementation returns a `-32601` JSON-RPC error for an unknown request
method that has an id. It stays silent for unknown notifications. It does not
perform full JSON Schema validation itself; clients should honor the schema
from `tools/list` and servers should still be tested with malformed input.

## Tool catalog

| Tool | Required input | Optional input and defaults | Operation |
|---|---|---|---|
| `leann_search` | `index_name: string`, `query: string` | `top_k: integer = 5` (schema 1..20), `complexity: integer = 32` (schema 16..128) | Runs non-interactive JSON search with metadata and formats results as Markdown code blocks with source path and score. |
| `leann_list` | none | none | Runs `leann list`; output is returned as text and may include registered projects, not only the current project. |
| `leann_build` | `docs: string[]` | `index_name: string`, `backend_name: "hnsw" | "ivf" = "ivf"`, `force: boolean = false` | Builds or incrementally updates through the CLI. An existing named index contributes its stored embedding model/mode when readable. |
| `leann_status` | `index_name: string` | none | Reads current-project metadata/passages and reports backend, embedding, dimensions, chunks, files, size, and location. |

### Search call

```json
{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"leann_search","arguments":{"index_name":"project-docs","query":"request authentication","top_k":5,"complexity":32}}}
```

The successful result is MCP text content:

```json
{"jsonrpc":"2.0","id":10,"result":{"content":[{"type":"text","text":"Found 2 results for 'request authentication':\n..."}]}}
```

Each CLI JSON item is expected to contain `text`, `score`, and optional
`metadata`. The formatter chooses `metadata.file_path`, then
`metadata.source`, then `unknown`. Search semantics and tuning belong to
`api-and-indexing`; this transport layer only forwards `top_k` and
`complexity`.

### Build call

```json
{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"leann_build","arguments":{"index_name":"project-docs","docs":["src","README.md"],"backend_name":"ivf","force":false}}}
```

`docs` entries are passed as distinct subprocess arguments, so a path containing
spaces remains one path. The MCP process must have read permission for every
file and write permission for the project's `.leann/indexes` directory. Build
can be expensive and mutating; expose it only to trusted clients. Backend and
incremental-update decisions belong to the indexing/backend sub-skills.

### List and status calls

```json
{"jsonrpc":"2.0","id":12,"method":"tools/call","params":{"name":"leann_list","arguments":{}}}
{"jsonrpc":"2.0","id":13,"method":"tools/call","params":{"name":"leann_status","arguments":{"index_name":"project-docs"}}}
```

`leann_status` is current-working-directory relative. It expects:
`.leann/indexes/<index_name>/documents.leann.meta.json` and, when present,
`documents.leann.passages.jsonl`. It counts nonempty passage lines and distinct
`metadata.file_path` or `metadata.source` values.

Implementation caveat: while scanning passages, the verified handler reuses the
variable that held index metadata. After at least one valid passage record,
backend/model/mode/dimensions can therefore display `unknown` unless those keys
also occur in the last passage's metadata. Treat status location/chunk/file
counts as useful, but confirm backend and embedding configuration from the
index metadata or normal indexing APIs until that implementation defect is
fixed.

## Result and error envelopes

LEANN distinguishes protocol/dispatch errors from operational tool failures:

| Condition | Envelope |
|---|---|
| Known tool succeeds | `result.content[0]` with `type: "text"` |
| Missing search/build/status input | A successful JSON-RPC `result` whose text starts with `Error:` |
| CLI nonzero exit or timeout | A successful JSON-RPC `result` containing `Search failed`, `Build failed`, `Error listing indexes`, or `Error: Command timed out.` |
| Unknown tool | JSON-RPC `error` with code `-1` |
| Exception inside tool dispatch | JSON-RPC `error` with code `-1` |
| Unknown request method with id | JSON-RPC `error` with code `-32601` |
| Malformed JSON or an outer-loop exception | JSON-RPC `error` with id `null` and code `-1` |
| Notification | No response |

Therefore, a client must inspect both the top-level `error` member **and** the
text content of a nominal `result`. Do not treat every `result` envelope as a
successful LEANN operation.

## Working-directory caveat

The MCP parser exposes `--base-dir`, but in the verified implementation the
parsed value is not passed as `cwd` to CLI subprocesses and is not used by
`leann_status`. Do not rely on that flag to select a project. Start the child in
the desired project directory instead. The bundled config generator uses a
shell-free Python module runner to change directory before starting MCP when
`--project-dir` is supplied.

## Security model

- `leann_build` grants filesystem reads over caller-supplied paths and writes an
  index. Restrict the MCP process account and client permissions.
- Search results can reveal private passage text and source paths.
- `leann_list` and `leann_status` can reveal project/index locations.
- The stdio server itself opens no listening socket, but selected embedding
  providers may use local daemons or networks; configure those separately.
- Never echo credentials or diagnostic logs to stdout. Redact paths before
  sharing protocol captures.
